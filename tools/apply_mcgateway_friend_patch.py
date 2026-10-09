#!/usr/bin/env python3
"""Apply the bounded MCGateway reliability overlay to MCXboxBroadcast release 154.

V11 intentionally avoids rewriting upstream authentication, NetherNet, session
recovery, friend synchronization, pending-request acceptance, retry scheduling, or
rate-limit behavior. It adds only exact social-count/status output, structured join
and transfer evidence, the standalone friends remove command, and null-safe cache
access. This keeps official release logic intact and makes Control Bot decisions
observable without changing the connection engine.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

FRIEND_PATH = Path("core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java")
SESSION_MANAGER_PATH = Path("core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java")
SESSION_CORE_PATH = Path("core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManagerCore.java")
REDIRECT_HANDLER_PATH = Path(
    "core/src/main/java/com/rtm516/mcxboxbroadcast/core/nethernet/RedirectPacketHandler.java"
)
LOGGER_PATH = Path(
    "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
)
README_PATH = Path("README.md")

MARKER = "MCGATEWAY_RELIABILITY_OVERLAY_V11"
PATCHER_VERSION = "V11"


def fail(message: str) -> NoReturn:
    raise RuntimeError(message)


def replace_regex_once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, found {count}")
    return updated


def find_method_span(text: str, signature_pattern: str, label: str) -> tuple[int, int]:
    """Return the [start, end) span of one Java method, using brace matching."""
    matches = list(re.finditer(signature_pattern, text, flags=re.MULTILINE))
    if len(matches) != 1:
        fail(f"{label}: expected exactly one method signature, found {len(matches)}")

    start = matches[0].start()
    brace_start = text.find("{", matches[0].end())
    if brace_start < 0:
        fail(f"{label}: opening brace not found")

    depth = 0
    in_string = False
    in_char = False
    escaped = False
    in_line_comment = False
    in_block_comment = False

    i = brace_start
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if in_char:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "'":
                in_char = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "'":
            in_char = True
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return start, end
        i += 1

    fail(f"{label}: closing brace not found")


def patch_friend_manager(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if (
        MARKER in text
        and "removeRelationship(String xuid)" in text
        and "SocialCounts socialCounts()" in text
    ):
        print(f"Already patched: {path}")
        return False

    required = (
        "public class FriendManager",
        "public void forceUnfollow(String xuid) throws Exception",
        "public List<FollowerResponse.Person> lastFriendCache()",
        "public void acceptPendingFriendRequests()",
        'friends/v2/xuid(" + xuid + ")',
        "friendRequestAcceptResponse.isFriend",
        "Constants.FOLLOWER",
        "Constants.PEOPLE",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        fail(
            f"{path}: upstream friend API structure changed; missing markers: "
            + ", ".join(repr(item) for item in missing)
        )
    if "bulk/users/me/people/friends/v2?method=add" in text:
        fail(f"{path}: obsolete bulk pending-request implementation detected")

    changed = False

    if MARKER not in text:
        text = replace_regex_once(
            text,
            r"(?m)^(public class FriendManager\s*\{\s*)$",
            r"\1\n    // " + MARKER,
            "overlay marker",
        )
        changed = True

    # Make every direct cache access use the existing null-safe accessor.
    replacements = (
        ("lastFriendCache.stream()", "lastFriendCache().stream()"),
        ("lastFriendCache.removeIf", "lastFriendCache().removeIf"),
    )
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True

    if "SocialCounts socialCounts()" not in text:
        init_matches = list(
            re.finditer(
                r"(?m)^    public void init\(CoreConfig\.FriendSyncConfig friendSyncConfig\)\s*\{",
                text,
            )
        )
        if len(init_matches) != 1:
            fail(f"socialCounts insertion: expected one init method, found {len(init_matches)}")

        social_block = r'''
    /** Exact Xbox relationship counts from one merged, XUID-deduplicated snapshot. */
    public record SocialCounts(int friends, int following, int followers) { }

    public SocialCounts socialCounts() throws XboxFriendsException {
        int friends = 0;
        int following = 0;
        int followers = 0;

        for (FollowerResponse.Person person : get()) {
            if (person.isFollowedByCaller) {
                following++;
            }
            if (person.isFollowingCaller) {
                followers++;
            }
            if (person.isFollowedByCaller && person.isFollowingCaller) {
                friends++;
            }
        }

        return new SocialCounts(friends, following, followers);
    }

'''
        insertion = init_matches[0].start()
        text = text[:insertion] + social_block + text[insertion:]
        changed = True

    if "public void removeRelationship(String xuid)" not in text:
        init_matches = list(
            re.finditer(
                r"(?m)^    public void init\(CoreConfig\.FriendSyncConfig friendSyncConfig\)\s*\{",
                text,
            )
        )
        if len(init_matches) != 1:
            fail(f"removeRelationship insertion: expected one init method, found {len(init_matches)}")

        block = r'''
    /**
     * Remove both Xbox relationship directions for one XUID.
     *
     * <p>HTTP 404 is treated as success because the requested relationship is
     * already absent.</p>
     *
     * @param xuid numeric Xbox user ID
     * @throws Exception if Xbox rejects either delete request
     */
    public void removeRelationship(String xuid) throws Exception {
        if (xuid == null || xuid.isBlank()
            || xuid.chars().anyMatch(character -> character < '0' || character > '9')) {
            throw new IllegalArgumentException("XUID must contain only digits");
        }

        toAdd.remove(xuid);
        toRemove.remove(xuid);

        HttpRequest followerDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.FOLLOWER.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> followerResponse = httpClient.send(
            followerDeleteRequest,
            HttpResponse.BodyHandlers.ofString()
        );
        requireSuccessfulRelationshipDelete("Follower relationship", followerResponse);

        HttpRequest friendDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.PEOPLE.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> friendResponse = httpClient.send(
            friendDeleteRequest,
            HttpResponse.BodyHandlers.ofString()
        );
        requireSuccessfulRelationshipDelete("Outgoing friend relationship", friendResponse);

        toAdd.remove(xuid);
        toRemove.remove(xuid);
        lastFriendCache().removeIf(person -> xuid.equals(person.xuid));

        try {
            sessionManager.storageManager().playerHistory().clear(xuid);
        } catch (Exception exception) {
            logger.warn(
                "Removed Xbox friend relationships for XUID " + xuid
                    + ", but local player history cleanup was deferred: "
                    + exception.getMessage()
            );
        }
    }

    private void requireSuccessfulRelationshipDelete(
        String operation,
        HttpResponse<String> response
    ) {
        int status = response.statusCode();
        if ((status < 200 || status >= 300) && status != 404) {
            throw new RuntimeException(
                operation + " removal failed with HTTP " + status + ": " + response.body()
            );
        }
    }

'''
        insertion = init_matches[0].start()
        text = text[:insertion] + block + text[insertion:]
        changed = True

    # Keep forceUnfollow's official purpose, but make it null-safe and idempotent.
    force_start, force_end = find_method_span(
        text,
        r"(?m)^    public void forceUnfollow\(String xuid\) throws Exception\s*",
        "forceUnfollow",
    )
    force_replacement = r'''    public void forceUnfollow(String xuid) throws Exception {
        HttpRequest followerDeleteRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.FOLLOWER.formatted(xuid)))
            .header("Authorization", sessionManager.getTokenHeader())
            .DELETE()
            .build();
        HttpResponse<String> response = httpClient.send(
            followerDeleteRequest,
            HttpResponse.BodyHandlers.ofString()
        );
        requireSuccessfulRelationshipDelete("Follower relationship", response);

        lastFriendCache().removeIf(person -> xuid.equals(person.xuid));
        try {
            sessionManager.storageManager().playerHistory().clear(xuid);
        } catch (Exception exception) {
            logger.warn(
                "Removed follower relationship for XUID " + xuid
                    + ", but local player history cleanup was deferred: "
                    + exception.getMessage()
            );
        }
    }
'''
    if text[force_start:force_end] != force_replacement:
        text = text[:force_start] + force_replacement + text[force_end:]
        changed = True

    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return changed


def patch_session_manager(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    attempt_line = '                    logger.info("MCGATEWAY_JOIN_ATTEMPT_V1 xuid=" + xuid);\n'
    if attempt_line not in text:
        anchor = '                    logger.debug("Generated nonce for XUID " + xuid + ": " + hex);\n'
        if text.count(anchor) != 1:
            fail(f"{path}: structured join-attempt anchor count was {text.count(anchor)}, expected 1")
        text = text.replace(anchor, anchor + attempt_line, 1)
        changed = True

    if "appendSocialCounts(List<String> messages" not in text:
        start, end = find_method_span(
            text,
            r"(?m)^    public void listSessions\(\)\s*",
            "listSessions",
        )
        replacement = r'''    public void listSessions() {
        List<String> messages = new ArrayList<>();
        coreLogger.info("Loading status of sessions...");

        messages.add("Primary Session:");
        messages.add(" - Gamertag: " + getGamertag());
        appendSocialCounts(messages, friendManager());

        if (!subSessionManagers.isEmpty()) {
            messages.add("Sub-sessions: (" + subSessionManagers.size() + ")");
            for (Map.Entry<String, SubSessionManager> subSession : subSessionManagers.entrySet()) {
                messages.add(" - ID: " + subSession.getKey());
                messages.add("   Gamertag: " + subSession.getValue().getGamertag());
                appendSocialCounts(messages, subSession.getValue().friendManager());
            }
        } else {
            messages.add("No sub-sessions");
        }

        for (String message : messages) {
            coreLogger.info(message);
        }
    }

    private void appendSocialCounts(List<String> messages, FriendManager manager) {
        try {
            FriendManager.SocialCounts counts = manager.socialCounts();
            messages.add("   Friends: " + counts.friends() + "/" + Constants.MAX_FRIENDS);
            messages.add("   Followers: " + counts.followers());
            messages.add("   Following: " + counts.following());
        } catch (Exception exception) {
            messages.add("   Friends: unavailable");
            messages.add("   Followers: unavailable");
            messages.add("   Following: unavailable");
            logger.warn("Unable to load exact Xbox social counts: " + exception.getMessage());
        }
    }
'''
        text = text[:start] + replacement + text[end:]
        changed = True

    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return changed


def patch_session_core(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "public String mcgatewayHealthLine()" in text:
        print(f"Already patched: {path}")
        return False

    anchor = '''    public Logger logger() {
        return logger;
    }
'''
    if text.count(anchor) != 1:
        fail(f"{path}: health-status anchor count was {text.count(anchor)}, expected 1")
    block = anchor + r'''

    /** A read-only machine-readable snapshot for the external fleet supervisor. */
    public String mcgatewayHealthLine() {
        boolean rtaOpen = rtaWebsocket != null && rtaWebsocket.isOpen();
        boolean netherNetOpen = netherNetChannel != null && netherNetChannel.isOpen();
        boolean sessionPublished = sessionInfo != null
            && sessionInfo.getHandleId() != null
            && !sessionInfo.getHandleId().isBlank();
        return "MCGATEWAY_HEALTH_V1 initialized=" + initialized
            + " rta=" + rtaOpen
            + " nethernet=" + netherNetOpen
            + " published=" + sessionPublished;
    }
'''
    text = text.replace(anchor, block, 1)
    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return True


def patch_redirect_handler(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    success_line = '                sessionManager.logger().info("MCGATEWAY_TRANSFER_SUCCESS_V1 xuid=" + identityData.xuid);\n'
    if success_line in text:
        print(f"Already patched: {path}")
        return False

    anchor = '                sessionManager.logger().info("Transferred bedrock client " + identityData.displayName + " (" + identityData.xuid + ") to target server.");\n'
    if text.count(anchor) != 1:
        fail(f"{path}: structured transfer-success anchor count was {text.count(anchor)}, expected 1")
    text = text.replace(anchor, anchor + success_line, 1)
    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return True


def patch_logger(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    if 'case "friends"' not in text:
        command_block = r'''                case "friends" -> {
                    if (args.length != 2 || !args[0].equalsIgnoreCase("remove")) {
                        warn("Usage: friends remove <xuid>");
                        return;
                    }

                    String xuid = args[1];
                    if (xuid.isEmpty()
                        || xuid.chars().anyMatch(character -> character < '0' || character > '9')) {
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
                    String target = "XUID " + xuid
                        + (gamertag == null ? "" : " (" + gamertag + ")");

                    info("Removing all friend relationships for " + target + "...");
                    try {
                        friendManager.removeRelationship(xuid);
                        info("Successfully removed all friend relationships for " + target + ".");
                    } catch (Exception exception) {
                        error("Failed to remove all friend relationships for " + target + ".", exception);
                    }
                }
'''
        version_matches = list(
            re.finditer(r'(?m)^                case "version"\s*->', text)
        )
        if len(version_matches) != 1:
            fail(f"standalone friends command: expected one version case, found {len(version_matches)}")
        insertion = version_matches[0].start()
        text = text[:insertion] + command_block + text[insertion:]
        changed = True

    if 'case "health" -> info(StandaloneMain.sessionManager.mcgatewayHealthLine());' not in text:
        health_line = '                case "health" -> info(StandaloneMain.sessionManager.mcgatewayHealthLine());\n'
        version_matches = list(re.finditer(r'(?m)^                case "version"\s*->', text))
        if len(version_matches) != 1:
            fail(f"standalone health command: expected one version case, found {len(version_matches)}")
        insertion = version_matches[0].start()
        text = text[:insertion] + health_line + text[insertion:]
        changed = True

    help_line = '                    info("friends remove <xuid> - Remove both friend relationship directions for an XUID");\n'
    if help_line not in text:
        version_help_matches = list(
            re.finditer(
                r'(?m)^                    info\("version - Display the version"\);',
                text,
            )
        )
        if len(version_help_matches) != 1:
            fail(f"standalone help entry: expected one version help line, found {len(version_help_matches)}")
        insertion = version_help_matches[0].start()
        text = text[:insertion] + help_line + text[insertion:]
        changed = True

    health_help = '                    info("health - Print MCGateway machine-readable readiness");\n'
    if health_help not in text:
        version_help_matches = list(
            re.finditer(
                r'(?m)^                    info\("version - Display the version"\);',
                text,
            )
        )
        if len(version_help_matches) != 1:
            fail(f"standalone health help: expected one version help line, found {len(version_help_matches)}")
        insertion = version_help_matches[0].start()
        text = text[:insertion] + health_help + text[insertion:]
        changed = True

    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")
    return changed


def patch_readme(path: Path) -> bool:
    """Document the command when a recognized command table exists, but never block a build."""
    text = path.read_text(encoding="utf-8")
    row = (
        "| `friends remove <xuid>` (Standalone Only) | "
        "Removes both friend relationship directions for an XUID |"
    )
    health_row = (
        "| `health` (Standalone Only) | "
        "Prints the machine-readable MCGateway readiness snapshot |"
    )
    if row in text and health_row in text:
        print(f"Already documented: {path}")
        return False

    account_row = (
        "| `accounts remove <sub-session-id>` | "
        "Removes an account from the list of accounts to use |"
    )
    if account_row in text:
        additions = [item for item in (row, health_row) if item not in text]
        text = text.replace(account_row, account_row + "\n" + "\n".join(additions), 1)
        path.write_text(text, encoding="utf-8")
        print(f"Patched: {path}")
        return True

    print(f"README command table was not recognized; functional patch continues without README edit: {path}")
    return False


def validate(root: Path) -> None:
    friend = (root / FRIEND_PATH).read_text(encoding="utf-8")
    session = (root / SESSION_MANAGER_PATH).read_text(encoding="utf-8")
    session_core = (root / SESSION_CORE_PATH).read_text(encoding="utf-8")
    redirect = (root / REDIRECT_HANDLER_PATH).read_text(encoding="utf-8")
    logger = (root / LOGGER_PATH).read_text(encoding="utf-8")

    required = {
        "V11 overlay marker": MARKER in friend,
        "removeRelationship method": "removeRelationship(String xuid)" in friend,
        "delete helper": "requireSuccessfulRelationshipDelete" in friend,
        "null-safe cache": "lastFriendCache.stream()" not in friend,
        "exact social counts": "SocialCounts socialCounts()" in friend,
        "exact friends output": 'messages.add("   Friends: " + counts.friends()' in session,
        "followers output": 'messages.add("   Followers: " + counts.followers())' in session,
        "following output": 'messages.add("   Following: " + counts.following())' in session,
        "structured join attempt": "MCGATEWAY_JOIN_ATTEMPT_V1 xuid=" in session,
        "machine-readable readiness": "MCGATEWAY_HEALTH_V1 initialized=" in session_core,
        "structured transfer success": "MCGATEWAY_TRANSFER_SUCCESS_V1 xuid=" in redirect,
        "official one-by-one acceptance retained": 'friends/v2/xuid(" + xuid + ")' in friend,
        "official isFriend response retained": "friendRequestAcceptResponse.isFriend" in friend,
        "obsolete bulk endpoint absent": "bulk/users/me/people/friends/v2?method=add" not in friend,
        "standalone friends command": 'case "friends"' in logger,
        "standalone help entry": "friends remove <xuid>" in logger,
        "standalone health command": 'case "health"' in logger,
    }
    failed = [name for name, okay in required.items() if not okay]
    if failed:
        fail("post-patch validation failed: " + ", ".join(failed))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="MCXboxBroadcast source root")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    print(f"MCGateway semantic friend overlay patcher {PATCHER_VERSION}")

    for relative in (
        FRIEND_PATH,
        SESSION_MANAGER_PATH,
        SESSION_CORE_PATH,
        REDIRECT_HANDLER_PATH,
        LOGGER_PATH,
    ):
        if not (root / relative).is_file():
            fail(f"missing required file: {root / relative}")

    changed = False
    changed |= patch_friend_manager(root / FRIEND_PATH)
    changed |= patch_session_manager(root / SESSION_MANAGER_PATH)
    changed |= patch_session_core(root / SESSION_CORE_PATH)
    changed |= patch_redirect_handler(root / REDIRECT_HANDLER_PATH)
    changed |= patch_logger(root / LOGGER_PATH)

    readme_path = root / README_PATH
    if readme_path.is_file():
        changed |= patch_readme(readme_path)

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
