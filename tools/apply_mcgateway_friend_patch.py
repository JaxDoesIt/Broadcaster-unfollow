#!/usr/bin/env python3
"""Apply the MCGateway friend-removal and resilient-sync overlay.

This intentionally keeps MCXboxBroadcast's upstream one-by-one pending-request
implementation untouched. It adds small, anchored changes around it so future
upstream releases are much less likely to conflict than the old 295-line
cherry-pick.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRIEND_PATH = Path("core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java")
LOGGER_PATH = Path("bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java")
README_PATH = Path("README.md")

MARKER = "MCGATEWAY_FRIEND_SYNC_OVERLAY_V7"


def fail(message: str) -> "NoReturn":
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def insert_before_once(text: str, anchor: str, block: str, label: str) -> str:
    return replace_once(text, anchor, block + anchor, label)


def patch_friend_manager(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"Already patched: {path}")
        return False

    # Guard against accidentally applying to the old bulk-request implementation.
    required_upstream_markers = (
        "public void acceptPendingFriendRequests()",
        "friends/v2/xuid(\" + xuid + \"",
        "friendRequestAcceptResponse.isFriend",
    )
    for marker in required_upstream_markers:
        if marker not in text:
            fail(
                f"{path}: upstream pending-request structure changed or is older than release 148/149; "
                f"missing marker: {marker!r}"
            )

    if "bulk/users/me/people/friends/v2?method=add" in text:
        fail(f"{path}: obsolete bulk pending-request implementation detected")

    text = replace_once(
        text,
        "import java.util.Set;\nimport java.util.concurrent.Future;",
        "import java.util.Set;\nimport java.util.concurrent.ConcurrentHashMap;\nimport java.util.concurrent.Future;",
        "ConcurrentHashMap import",
    )

    text = replace_once(
        text,
        "    private boolean initialInvite;\n    private boolean shouldAcceptPendingRequests = true;\n",
        "    private boolean initialInvite;\n"
        "    private boolean shouldAcceptPendingRequests = true;\n"
        f"    // {MARKER}\n"
        "    // Xbox can temporarily report a relationship as one-sided after a successful request.\n"
        "    // These short-lived guards stop repeated follow and invite operations across sync passes.\n"
        "    private static final long AUTO_FOLLOW_COOLDOWN_SECONDS = TimeUnit.MINUTES.toSeconds(30);\n"
        "    private static final long INVITE_COOLDOWN_SECONDS = TimeUnit.HOURS.toSeconds(6);\n"
        "    private static final long PENDING_SWEEP_COOLDOWN_SECONDS = TimeUnit.MINUTES.toSeconds(5);\n"
        "    private final Map<String, Instant> autoFollowRetryAfter = new ConcurrentHashMap<>();\n"
        "    private final Map<String, Instant> inviteRetryAfter = new ConcurrentHashMap<>();\n"
        "    private volatile Instant nextPendingRequestSweep = Instant.EPOCH;\n",
        "sync fields",
    )

    text = replace_once(
        text,
        "Optional<FollowerResponse.Person> foundFriend = lastFriendCache.stream().filter(person -> person.xuid.equals(xuid)).findFirst();",
        "Optional<FollowerResponse.Person> foundFriend = lastFriendCache().stream().filter(person -> person.xuid.equals(xuid)).findFirst();",
        "null-safe removal cache",
    )

    remove_relationship = r'''
    /**
     * Remove both relationship directions for one XUID.
     *
     * <p>The incoming follower relationship is removed first so automatic follow
     * cannot immediately queue the account again. A 404 is an idempotent success.</p>
     *
     * @param xuid The XUID to remove
     * @throws Exception If either Xbox Live request fails
     */
    public void removeRelationship(String xuid) throws Exception {
        if (xuid == null || xuid.isBlank() || xuid.chars().anyMatch(character -> character < '0' || character > '9')) {
            throw new IllegalArgumentException("XUID must contain only digits");
        }

        lastFriendCache();
        toAdd.remove(xuid);
        toRemove.remove(xuid);
        clearFriendSyncCooldowns(xuid);

        HttpRequest followerDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.FOLLOWER.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> followerResponse = httpClient.send(
            followerDeleteRequest,
            HttpResponse.BodyHandlers.ofString()
        );
        requireSuccessfulDelete("Follower relationship", followerResponse);

        HttpRequest friendDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.PEOPLE.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> friendResponse = httpClient.send(
            friendDeleteRequest,
            HttpResponse.BodyHandlers.ofString()
        );
        requireSuccessfulDelete("Outgoing friend relationship", friendResponse);

        toAdd.remove(xuid);
        toRemove.remove(xuid);
        lastFriendCache().removeIf(person -> xuid.equals(person.xuid));
        try {
            sessionManager.storageManager().playerHistory().clear(xuid);
        } catch (Exception e) {
            logger.warn(
                "Removed Xbox friend relationships for XUID " + xuid
                    + ", but local player history cleanup was deferred: " + e.getMessage()
            );
        }
    }

    private void requireSuccessfulDelete(String operation, HttpResponse<String> response) {
        int status = response.statusCode();
        if ((status < 200 || status >= 300) && status != 404) {
            throw new RuntimeException(operation + " removal failed with HTTP " + status + ": " + response.body());
        }
    }

'''
    text = insert_before_once(
        text,
        "    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {",
        remove_relationship,
        "removeRelationship insertion",
    )

    # Startup acceptance now gets the same runtime/null guard used by recurring sweeps.
    text = replace_once(
        text,
        "        // Accept any pending friend requests if enabled incase we got any while offline\n        acceptPendingFriendRequests();",
        "        // Accept any pending friend requests if enabled in case we got any while offline.\n"
        "        acceptPendingFriendRequestsSafely();",
        "startup pending sweep",
    )

    text = replace_once(
        text,
        "                logger.info(\"Added \" + friend.get().gamertag + \" (\" + xuid + \") as a friend\");\n"
        "                sendInvite(xuid);",
        "                Instant acceptedAt = Instant.now();\n"
        "                boolean repeated = isAutoFollowCoolingDown(xuid, acceptedAt);\n"
        "                markAutoFollowAttempt(xuid, acceptedAt);\n"
        "                if (repeated) {\n"
        "                    logger.debug(\"Received request for \" + friend.get().gamertag + \" (\" + xuid + \") was already handled recently\");\n"
        "                } else {\n"
        "                    logger.info(\"Added \" + friend.get().gamertag + \" (\" + xuid + \") as a friend\");\n"
        "                }\n"
        "                sendInviteOnce(xuid);",
        "pending acceptance cooldown",
    )

    helpers = r'''
    private boolean isAutoFollowCoolingDown(String xuid, Instant now) {
        Instant retryAt = autoFollowRetryAfter.get(xuid);
        if (retryAt == null) {
            return false;
        }
        if (!retryAt.isAfter(now)) {
            autoFollowRetryAfter.remove(xuid, retryAt);
            return false;
        }
        return true;
    }

    private void markAutoFollowAttempt(String xuid, Instant now) {
        autoFollowRetryAfter.put(xuid, now.plusSeconds(AUTO_FOLLOW_COOLDOWN_SECONDS));
    }

    private void clearFriendSyncCooldowns(String xuid) {
        autoFollowRetryAfter.remove(xuid);
        inviteRetryAfter.remove(xuid);
    }

    private void sendInviteOnce(String xuid) {
        Instant now = Instant.now();
        Instant retryAt = inviteRetryAfter.get(xuid);
        if (retryAt != null && retryAt.isAfter(now)) {
            logger.debug("Skipping repeated initial invite for XUID " + xuid + " while cooldown is active");
            return;
        }
        inviteRetryAfter.put(xuid, now.plusSeconds(INVITE_COOLDOWN_SECONDS));
        sendInvite(xuid);
    }

    /**
     * Run upstream's one-by-one pending-request implementation without rewriting it.
     * This wrapper supplies overlap prevention, a five-minute sweep interval, and
     * runtime/null safety while preserving future upstream protocol fixes.
     */
    private synchronized void acceptPendingFriendRequestsSafely() {
        if (!shouldAcceptPendingRequests) {
            return;
        }

        Instant now = Instant.now();
        if (nextPendingRequestSweep.isAfter(now)) {
            return;
        }
        nextPendingRequestSweep = now.plusSeconds(PENDING_SWEEP_COOLDOWN_SECONDS);

        try {
            acceptPendingFriendRequests();
        } catch (RuntimeException e) {
            logger.warn("Pending friend request processing failed safely and will retry later: " + e.getMessage());
        }
    }

'''
    text = insert_before_once(
        text,
        "    private void initAutoFriend(CoreConfig.FriendSyncConfig friendSyncConfig) {",
        helpers,
        "friend sync helpers",
    )

    # Patch only the small auto-follow portion inside initAutoFriend. The previous
    # version matched the entire scheduled loop byte-for-byte, which was too
    # brittle when upstream formatting or nearby comments changed.
    method_start = text.find("    private void initAutoFriend(CoreConfig.FriendSyncConfig friendSyncConfig) {")
    if method_start < 0:
        fail("scheduled friend sync loop: initAutoFriend method not found")

    method_end = text.find("    private boolean isGuestAccount(long xuid) {", method_start)
    if method_end < 0:
        fail("scheduled friend sync loop: isGuestAccount method anchor not found")

    method_text = text[method_start:method_end]

    loop_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)for\s*\(\s*FollowerResponse\.Person\s+person\s*:\s*get\(\)\s*\)\s*\{"
    )
    loop_matches = list(loop_pattern.finditer(method_text))
    if len(loop_matches) != 1:
        fail(f"scheduled friend sync loop: expected one follower loop, found {len(loop_matches)}")

    loop_match = loop_matches[0]
    loop_indent = loop_match.group("indent")
    loop_setup = (
        f"{loop_indent}Instant now = Instant.now();\n"
        f"{loop_indent}if (friendSyncConfig.autoFollow()) {{\n"
        f"{loop_indent}    acceptPendingFriendRequestsSafely();\n"
        f"{loop_indent}}}\n\n"
    )
    method_text = (
        method_text[:loop_match.start()]
        + loop_setup
        + method_text[loop_match.start():]
    )

    auto_follow_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)if\s*\(\s*friendSyncConfig\.autoFollow\(\)\s*&&\s*"
        r"person\.isFollowingCaller\s*&&\s*!person\.isFollowedByCaller\s*\)\s*\{\s*\n"
        r"(?P=indent)[ \t]+add\(person\.xuid,\s*person\.displayName\);\s*\n"
        r"(?P=indent)\}"
    )
    auto_follow_matches = list(auto_follow_pattern.finditer(method_text))
    if len(auto_follow_matches) != 1:
        fail(
            "scheduled friend sync loop: expected one upstream auto-follow block, "
            f"found {len(auto_follow_matches)}"
        )

    auto_follow_match = auto_follow_matches[0]
    indent = auto_follow_match.group("indent")
    auto_follow_replacement = (
        f"{indent}if (person.isFollowingCaller && person.isFollowedByCaller) {{\n"
        f"{indent}    autoFollowRetryAfter.remove(person.xuid);\n"
        f"{indent}}}\n\n"
        f"{indent}// Follow the person back, without repeating the same Xbox request every sync pass.\n"
        f"{indent}if (friendSyncConfig.autoFollow() && person.isFollowingCaller && !person.isFollowedByCaller) {{\n"
        f"{indent}    if (!isAutoFollowCoolingDown(person.xuid, now)) {{\n"
        f"{indent}        markAutoFollowAttempt(person.xuid, now);\n"
        f"{indent}        add(person.xuid, person.displayName);\n"
        f"{indent}    }}\n"
        f"{indent}}}"
    )
    method_text = (
        method_text[:auto_follow_match.start()]
        + auto_follow_replacement
        + method_text[auto_follow_match.end():]
    )

    text = text[:method_start] + method_text + text[method_end:]

    text = replace_once(
        text,
        "                        logger.info(\"Added \" + entry.getValue() + \" (\" + entry.getKey() + \") as a friend\");\n"
        "                        sendInvite(entry.getKey());",
        "                        logger.info(\"Added \" + entry.getValue() + \" (\" + entry.getKey() + \") as a friend\");\n"
        "                        sendInviteOnce(entry.getKey());",
        "invite cooldown in add processor",
    )

    text = replace_once(
        text,
        "                        if (header.isPresent()) {\n"
        "                            retryAfter = Integer.parseInt(header.get());\n"
        "                        }\n"
        "                        // Log the error",
        "                        if (header.isPresent()) {\n"
        "                            retryAfter = Integer.parseInt(header.get());\n"
        "                        }\n"
        "                        retryAfter = Math.max(retryAfter, 60);\n"
        "                        // Log the error",
        "rate-limit minimum",
    )

    force_pattern = re.compile(
        r"    public void forceUnfollow\(String xuid\) throws Exception \{.*?\n    \}\n"
        r"    /\*\*\n     \* Get the last friend cache",
        re.DOTALL,
    )
    force_match = force_pattern.search(text)
    if not force_match:
        fail("forceUnfollow: method anchor not found")
    replacement = r'''    public void forceUnfollow(String xuid) throws Exception {
        HttpRequest followerDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.FOLLOWER.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> response = httpClient.send(followerDeleteRequest, HttpResponse.BodyHandlers.ofString());
        requireSuccessfulDelete("Follower relationship", response);

        lastFriendCache().removeIf(person -> xuid.equals(person.xuid));
        try {
            sessionManager.storageManager().playerHistory().clear(xuid);
        } catch (Exception e) {
            logger.warn(
                "Removed follower relationship for XUID " + xuid
                    + ", but local player history cleanup was deferred: " + e.getMessage()
            );
        }
    }
    /**
     * Get the last friend cache'''
    text = force_pattern.sub(replacement, text, count=1)

    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return True


def patch_logger(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "case \"friends\"" in text and "friends remove <xuid>" in text:
        print(f"Already patched: {path}")
        return False

    command_block = r'''                case "friends" -> {
                    if (args.length != 2 || !args[0].equalsIgnoreCase("remove")) {
                        warn("Usage: friends remove <xuid>");
                        return;
                    }

                    String xuid = args[1];
                    if (xuid.isEmpty() || xuid.chars().anyMatch(character -> character < '0' || character > '9')) {
                        warn("Invalid XUID '" + xuid + "'. XUIDs must contain only digits.");
                        return;
                    }

                    var friendManager = StandaloneMain.sessionManager.friendManager();
                    String gamertag = friendManager.lastFriendCache().stream()
                        .filter(person -> xuid.equals(person.xuid))
                        .map(person -> person.gamertag)
                        .filter(name -> name != null && !name.isBlank())
                        .findFirst()
                        .orElse(null);
                    String target = "XUID " + xuid + (gamertag == null ? "" : " (" + gamertag + ")");

                    info("Removing all friend relationships for " + target + "...");
                    try {
                        friendManager.removeRelationship(xuid);
                        info("Successfully removed all friend relationships for " + target + ".");
                    } catch (Exception e) {
                        error("Failed to remove all friend relationships for " + target + ".", e);
                    }
                }
'''
    text = insert_before_once(
        text,
        "                case \"version\" -> info(\"MCXboxBroadcast Standalone \" + BuildData.VERSION);",
        command_block,
        "standalone friends command",
    )
    text = replace_once(
        text,
        "                    info(\"accounts remove <sub-session-id> - Remove a sub-account\");\n"
        "                    info(\"version - Display the version\");",
        "                    info(\"accounts remove <sub-session-id> - Remove a sub-account\");\n"
        "                    info(\"friends remove <xuid> - Remove both friend relationship directions for an XUID\");\n"
        "                    info(\"version - Display the version\");",
        "standalone help entry",
    )
    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return True


def patch_readme(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    row = "| `friends remove <xuid>` (Standalone Only) | Removes both friend relationship directions for an XUID |"
    if row in text:
        print(f"Already patched: {path}")
        return False
    text = replace_once(
        text,
        "| `accounts remove <sub-session-id>` | Removes an account from the list of accounts to use |",
        "| `accounts remove <sub-session-id>` | Removes an account from the list of accounts to use |\n" + row,
        "README command row",
    )
    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return True


def validate(root: Path) -> None:
    friend = (root / FRIEND_PATH).read_text(encoding="utf-8")
    logger = (root / LOGGER_PATH).read_text(encoding="utf-8")
    readme = (root / README_PATH).read_text(encoding="utf-8")

    required = {
        "overlay marker": MARKER in friend,
        "removeRelationship": "removeRelationship(String xuid)" in friend,
        "safe pending wrapper": "acceptPendingFriendRequestsSafely()" in friend,
        "upstream one-by-one acceptance": "friends/v2/xuid(\" + xuid + \"" in friend,
        "accepted request invite cooldown": "sendInviteOnce(xuid);" in friend,
        "upstream isFriend response": "friendRequestAcceptResponse.isFriend" in friend,
        "no obsolete bulk endpoint": "bulk/users/me/people/friends/v2?method=add" not in friend,
        "standalone command": 'case "friends"' in logger,
        "README command": "friends remove <xuid>" in readme,
    }
    failed = [name for name, okay in required.items() if not okay]
    if failed:
        fail("post-patch validation failed: " + ", ".join(failed))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="MCXboxBroadcast source root")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    for relative in (FRIEND_PATH, LOGGER_PATH, README_PATH):
        if not (root / relative).is_file():
            fail(f"missing required file: {root / relative}")

    changed = False
    changed |= patch_friend_manager(root / FRIEND_PATH)
    changed |= patch_logger(root / LOGGER_PATH)
    changed |= patch_readme(root / README_PATH)
    validate(root)
    print("PASS: future-compatible MCGateway friend overlay is present.")
    print("Changed files." if changed else "No changes were required.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
        raise SystemExit(1)
