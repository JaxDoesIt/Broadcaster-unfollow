#!/usr/bin/env python3
"""Apply the MCGateway friend-removal overlay to current MCXboxBroadcast source.

V10 intentionally avoids rewriting upstream friend synchronization, pending-request
acceptance, retry scheduling, or rate-limit handling. It adds only the standalone
friends remove command, a two-direction relationship removal method, and null-safe
cache access. This keeps official release logic intact and greatly reduces future
merge breakage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

FRIEND_PATH = Path("core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java")
LOGGER_PATH = Path(
    "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
)
README_PATH = Path("README.md")

MARKER = "MCGATEWAY_FRIEND_SYNC_OVERLAY_V10"
PATCHER_VERSION = "V10"


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
    if MARKER in text and "removeRelationship(String xuid)" in text:
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
    if row in text:
        print(f"Already documented: {path}")
        return False

    account_row = (
        "| `accounts remove <sub-session-id>` | "
        "Removes an account from the list of accounts to use |"
    )
    if account_row in text:
        text = text.replace(account_row, account_row + "\n" + row, 1)
        path.write_text(text, encoding="utf-8")
        print(f"Patched: {path}")
        return True

    print(f"README command table was not recognized; functional patch continues without README edit: {path}")
    return False


def validate(root: Path) -> None:
    friend = (root / FRIEND_PATH).read_text(encoding="utf-8")
    logger = (root / LOGGER_PATH).read_text(encoding="utf-8")

    required = {
        "V10 overlay marker": MARKER in friend,
        "removeRelationship method": "removeRelationship(String xuid)" in friend,
        "delete helper": "requireSuccessfulRelationshipDelete" in friend,
        "null-safe cache": "lastFriendCache.stream()" not in friend,
        "official one-by-one acceptance retained": 'friends/v2/xuid(" + xuid + ")' in friend,
        "official isFriend response retained": "friendRequestAcceptResponse.isFriend" in friend,
        "obsolete bulk endpoint absent": "bulk/users/me/people/friends/v2?method=add" not in friend,
        "standalone friends command": 'case "friends"' in logger,
        "standalone help entry": "friends remove <xuid>" in logger,
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

    for relative in (FRIEND_PATH, LOGGER_PATH):
        if not (root / relative).is_file():
            fail(f"missing required file: {root / relative}")

    changed = False
    changed |= patch_friend_manager(root / FRIEND_PATH)
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
