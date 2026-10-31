#!/usr/bin/env python3
"""Offline-only overlay for a nonmutating, cache-warming PersonSummary test JAR.

Apply ONLY after original immutable Release160 patch and the original
one-shot PersonSummary overlay. Never modify the Dell or a running container.
"""
from pathlib import Path
import sys

FRIEND = "core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java"
MARKER = "MCGATEWAY_PERSONSUMMARY_READONLY_CACHE_V2"
PROBE_FROM = '''        if (lastFriendCache == null || lastFriendCache.isEmpty())
            return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
        String target = null;
        for (var person : lastFriendCache) {'''
PROBE_TO = '''        // MCGATEWAY_PERSONSUMMARY_READONLY_CACHE_V2
        // One authorized, read-only population attempt: pinned upstream
        // get() makes one Xbox friend-list GET, no relationship mutation.
        // The console has a bounded transport deadline; never retry.
        var snapshot = lastFriendCache;
        if (snapshot == null || snapshot.isEmpty()) {
            try {
                snapshot = get();
            } catch (Exception ignored) {
                return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
            }
        }
        if (snapshot == null || snapshot.isEmpty())
            return prefix + nonce + " http=unverified fields=no_cached_target can_authorize_removal=false";
        String target = null;
        for (var person : snapshot) {'''

# Deactivate every reviewed FriendManager relationship mutation/scheduler
# entrypoint for the short-lived candidate, irrespective of live config.
METHODS = {
    "    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) { autoFriend = false; return; }",
    "    public void add(String xuid, String gamertag) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    public boolean addIfRequired(String xuid, String gamertag) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return false;",
    "    public void remove(String xuid, String gamertag) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    private void internalProcess() {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    private void callInternalProcess() {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    public void acceptPendingFriendRequests() {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    private void initAutoFriend(CoreConfig.FriendSyncConfig friendSyncConfig) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
    "    private void declineFriendRequest(String xuid) throws Exception {":
        "        if (mcgPersonSummaryReadonlyCandidate()) throw new IllegalStateException(\"Read-only diagnostic cannot decline requests\");",
    "    public void sendInvite(String xuid) {":
        "        if (mcgPersonSummaryReadonlyCandidate()) return;",
}
METHOD = """    // MCGATEWAY_PERSONSUMMARY_READONLY_CACHE_V2
    // This image is for one controlled operator diagnostic, not normal service.
    private boolean mcgPersonSummaryReadonlyCandidate() { return true; }

"""
ANCHOR = "    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {"

def patch(root: Path):
    root = root.resolve()
    target = root / FRIEND
    require = [
        "MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT",
        "mcgPersonSummaryProbeConsumed.compareAndSet(false, true)",
        "MCGATEWAY_RELEASE160_EXPIRY_HOLD",
    ]
    expiry = root / "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java"
    console = root / "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
    if any(p.is_symlink() or not p.is_file() for p in (target, expiry, console)):
        raise ValueError("missing or unsafe source")
    original = target.read_text(encoding="utf-8")
    if any(r not in (original + expiry.read_text(encoding="utf-8")) for r in require):
        raise ValueError("prerequisite canary/expiry guard missing")
    if "friends remove is DENIED" not in console.read_text(encoding="utf-8"):
        raise ValueError("original Release160 command denial absent")

    if MARKER in original:
        if METHOD not in original or PROBE_TO not in original:
            raise ValueError("unknown or incomplete existing read-only patch")
        for method, guard in METHODS.items():
            if method + "\n" + guard not in original:
                raise ValueError("modified existing read-only guard")
        return False

    if original.count(PROBE_FROM) != 1 or original.count(ANCHOR) != 1:
        raise ValueError("probe source anchor missing/nonunique")
    for signature in METHODS:
        if original.count(signature) != 1:
            raise ValueError("mutation entrypoint missing/nonunique: " + signature)
    changed = original.replace(PROBE_FROM, PROBE_TO, 1)
    changed = changed.replace(ANCHOR, METHOD + ANCHOR, 1)
    for signature, guard in METHODS.items():
        changed = changed.replace(signature, signature + "\n" + guard, 1)
    target.write_text(changed, encoding="utf-8")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_readonly_friendcache_canary.py <offline-source-root>")
    print("CHANGED" if patch(Path(sys.argv[1])) else "UNCHANGED")
