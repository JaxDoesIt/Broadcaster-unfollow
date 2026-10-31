#!/usr/bin/env python3
"""Offline-only V3 source patch, after verified original/PersonSummary/V2 overlays.

Never points to Dell. Refuses partial or drifted source. Java helper is copied
byte-identically into the offline pinned upstream tree.
"""
from pathlib import Path
import sys

from apply_readonly_friendcache_canary import (
    FRIEND, METHODS, METHOD, PROBE_TO,
)

HELPER = "tools/release160/McgatewayXboxFriendListStatusV160.java"
TARGET = "core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayXboxFriendListStatusV160.java"
V3_MARKER = "MCGATEWAY_FRIEND_LIST_HTTP_STATUS_V3"
V2_TAIL = '''            if (person != null && person.xuid != null && person.xuid.matches("[1-9][0-9]{0,19}")
                    && !person.xuid.equals(sessionManager.getXuid())) {
                target = person.xuid;
                break;
            }
        }
        if (target == null)
            return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
'''
V2_BODY = PROBE_TO + "\n" + V2_TAIL
V3_BODY = '''        // MCGATEWAY_FRIEND_LIST_HTTP_STATUS_V3
        // No auto friend sync. Exactly one explicit bounded read-only list GET
        // and, if a valid in-memory target is selected, one PersonSummary GET.
        // Only coarse allowlisted labels may leave this JVM.
        McgatewayXboxFriendListStatusV160.Selection selected;
        try {
            selected = McgatewayXboxFriendListStatusV160.capture(
                MCG_PERSONSUMMARY_GET_CLIENT,
                sessionManager.getTokenHeader(), sessionManager.getXuid());
        } catch (Exception ignored) {
            return prefix + nonce + " http=unverified fields=list_unverified can_authorize_removal=false";
        }
        if (selected.target() == null)
            return prefix + nonce + " http=unverified fields=" + selected.reason()
                + " can_authorize_removal=false";
        String target = selected.target();
'''

def patch(root: Path, helper: Path) -> bool:
    root = root.resolve()
    path = root / FRIEND
    output = root / TARGET
    expiry = root / "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java"
    console = root / "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
    inputs = [path, expiry, console, helper]
    if any(p.is_symlink() or not p.is_file() for p in inputs):
        raise ValueError("required reviewed input missing or unsafe")
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise ValueError("unsafe helper target")
    code = path.read_text(encoding="utf-8")
    candidate = helper.read_text(encoding="utf-8")
    if "public final class McgatewayXboxFriendListStatusV160" not in candidate:
        raise ValueError("unexpected helper identity")
    if "MCGATEWAY_RELEASE160_EXPIRY_HOLD" not in expiry.read_text(encoding="utf-8"):
        raise ValueError("missing original expiration hold")
    if "friends remove is DENIED" not in console.read_text(encoding="utf-8"):
        raise ValueError("missing operator removal denial")
    if METHOD not in code:
        raise ValueError("V2 all-mutation denial missing")
    for signature, guard in METHODS.items():
        if code.count(signature + "\n" + guard) != 1:
            raise ValueError("missing verified V2 mutation guard")
    if "MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT" not in code or \
       "mcgPersonSummaryProbeConsumed.compareAndSet(false, true)" not in code:
        raise ValueError("one-shot prerequisite missing")
    if V3_MARKER in code:
        if code.count(V3_BODY) != 1 or V2_BODY in code:
            raise ValueError("unexpected existing V3 content")
        next_code = code
    else:
        if code.count(V2_BODY) != 1:
            raise ValueError("V2 cache diagnostic anchor missing or ambiguous")
        next_code = code.replace(V2_BODY, V3_BODY, 1)
    existing_helper = output.read_text(encoding="utf-8") if output.exists() else ""
    if existing_helper and existing_helper != candidate:
        raise ValueError("existing helper differs from verified source")
    # All checks complete before any write to temporary, offline source.
    changed = next_code != code or existing_helper != candidate
    if code != next_code:
        path.write_text(next_code, encoding="utf-8")
    if existing_helper != candidate:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(candidate, encoding="utf-8")
    return changed

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: apply_friendlist_status_v3.py <offline-upstream> <reviewed-helper>")
    print("CHANGED" if patch(Path(sys.argv[1]), Path(sys.argv[2])) else "UNCHANGED")
