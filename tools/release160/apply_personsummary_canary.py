#!/usr/bin/env python3
"""Source-only, post-Release160-overlay one-shot PersonSummary GET canary hook.

Use ONLY on pinned, prevalidated upstream source after applying
apply_mcgateway_release160_patch.py. Never targets the Dell/prod filesystem.
Preflights every source file before writing anything. No network or HTTP here.
"""
from pathlib import Path
import sys

HELPER = 'tools/release160/McgatewayXboxPersonSummaryProbeV160.java'
CORE_TARGET = 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayXboxPersonSummaryProbeV160.java'
FRIEND_PATH = 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java'
CONSOLE_PATH = 'bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java'
FRIEND_ANCHOR = '    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {'
CONSOLE_ANCHOR = '                case "friends" -> warn("friends remove is DENIED: release160 removal contract requires a separate review.");'
FRIEND_INSERT = '''    // MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT: operator-only, never friend removal.
    // This state is intentionally local to the existing primary FriendManager.
    private final java.util.concurrent.atomic.AtomicBoolean mcgPersonSummaryProbeConsumed =
        new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final java.net.http.HttpClient MCG_PERSONSUMMARY_GET_CLIENT =
        java.net.http.HttpClient.newBuilder()
            .connectTimeout(java.time.Duration.ofSeconds(4))
            .followRedirects(java.net.http.HttpClient.Redirect.NEVER).build();

    public String mcgatewayOneShotPersonSummaryProbe(String nonce) {
        final String prefix = "MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=";
        if (nonce == null || !nonce.matches("[0-9a-f]{32}"))
            return prefix + "invalid http=unverified fields=unverified can_authorize_removal=false";
        if (!mcgPersonSummaryProbeConsumed.compareAndSet(false, true))
            return prefix + nonce + " http=unverified fields=already_used can_authorize_removal=false";
        // Read an existing IN-MEMORY friend cache only; do not refresh it or
        // expose a gamertag/XUID in a command, output, log or exception.
        if (lastFriendCache == null || lastFriendCache.isEmpty())
            return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
        String target = null;
        for (var person : lastFriendCache) {
            if (person != null && person.xuid != null && person.xuid.matches("[1-9][0-9]{0,19}")
                    && !person.xuid.equals(sessionManager.getXuid())) {
                target = person.xuid;
                break;
            }
        }
        if (target == null)
            return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
        try {
            return McgatewayXboxPersonSummaryProbeV160.capture(
                MCG_PERSONSUMMARY_GET_CLIENT, sessionManager.getTokenHeader(), target, nonce);
        } catch (Exception ignored) {
            return prefix + nonce + " http=unverified fields=unverified can_authorize_removal=false";
        }
    }

'''
CONSOLE_INSERT = '''
                // MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT: never accepts a player ID.
                case "personsummaryprobe" -> {
                    if (args.length != 1 || !args[0].matches("[0-9a-f]{32}")) {
                        warn("MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=invalid http=unverified fields=unverified can_authorize_removal=false");
                    } else {
                        info(StandaloneMain.sessionManager.friendManager().mcgatewayOneShotPersonSummaryProbe(args[0]));
                    }
                }'''


def patch(root: Path, helper_file: Path) -> bool:
    root = root.resolve()
    paths = [root / FRIEND_PATH, root / CONSOLE_PATH, root / CORE_TARGET]
    if helper_file.is_symlink() or not helper_file.is_file():
        raise ValueError('missing/unsafe helper')
    helper = helper_file.read_text(encoding='utf-8')
    if 'public final class McgatewayXboxPersonSummaryProbeV160' not in helper:
        raise ValueError('unexpected helper identity')
    before = []
    for p in paths:
        if p.is_symlink() or (p.exists() and not p.is_file()):
            raise ValueError('unsafe target')
        if p != paths[2] and not p.is_file():
            raise ValueError('missing pinned source')
        before.append(p.read_text(encoding='utf-8') if p.exists() else '')
    friend, console, old_helper = before
    if CONSOLE_ANCHOR not in console or console.count(CONSOLE_ANCHOR) != 1:
        raise ValueError('Release160 friends-remove denial not proven')
    # The upstream expiration hold must remain intact independently of the
    # FriendManager state, including when a second patch attempt is idempotent.
    expiry = root / 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java'
    if expiry.is_symlink() or not expiry.is_file() or 'MCGATEWAY_RELEASE160_EXPIRY_HOLD' not in expiry.read_text(encoding='utf-8'):
        raise ValueError('expiry guard absent')
    if friend.count(FRIEND_ANCHOR) != 1:
        raise ValueError('unexpected FriendManager shape')
    if 'MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT' in friend and FRIEND_INSERT not in friend:
        raise ValueError('unexpected modified friend hook')
    if 'case "personsummaryprobe" ->' in console and CONSOLE_INSERT not in console:
        raise ValueError('unexpected modified console hook')
    expected_friend = friend if FRIEND_INSERT in friend else friend.replace(FRIEND_ANCHOR, FRIEND_INSERT + FRIEND_ANCHOR, 1)
    expected_console = console if CONSOLE_INSERT in console else console.replace(CONSOLE_ANCHOR, CONSOLE_ANCHOR + CONSOLE_INSERT, 1)
    if expected_friend.count('MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT: operator-only') != 1:
        raise ValueError('repeated friend canary hook')
    if expected_console.count('case "personsummaryprobe" ->') != 1:
        raise ValueError('repeated console command')
    if old_helper and old_helper != helper:
        raise ValueError('helper does not match expected reviewed source')
    expected = [expected_friend, expected_console, helper]
    changed = any(a != b for a, b in zip(before, expected))
    for path, orig, new in zip(paths, before, expected):
        if orig != new:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new, encoding='utf-8')
    return changed


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: apply_personsummary_canary.py <pinned-upstream-root> <reviewed-helper-file>')
    print('CHANGED' if patch(Path(sys.argv[1]), Path(sys.argv[2])) else 'UNCHANGED')
