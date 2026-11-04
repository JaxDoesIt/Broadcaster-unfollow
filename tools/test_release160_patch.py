#!/usr/bin/env python3
"""Offline proof for the release160 read-only overlay; no Gradle execution."""
import hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

PATCH=Path(__file__).with_name('apply_mcgateway_release160_patch.py')
def run(*args): return subprocess.run(args,text=True,capture_output=True)
def check(value,message):
    if not value: raise AssertionError(message)
def clone(source,target): shutil.copytree(source,target,ignore=shutil.ignore_patterns('.git','build','.gradle'))
FILES=[Path(item) for item in ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java','core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java','core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManagerCore.java','core/src/main/java/com/rtm516/mcxboxbroadcast/core/nethernet/HttpRelaySignaling.java','bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java','core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java')]
def digest(root): return {item:hashlib.sha256((root/item).read_bytes()).hexdigest() for item in FILES}
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_release160_patch.py <release160-upstream>')
    upstream=Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='mcgateway160-proof.') as temp:
        root=Path(temp)/'source';clone(upstream,root)
        first=run('python3',str(PATCH),str(root));check(first.returncode==0,first.stderr)
        second=run('python3',str(PATCH),str(root));check(second.returncode==0 and 'No changes were required.' in second.stdout,'apply is not idempotent')
        friend=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java').read_text()
        core=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManagerCore.java').read_text()
        relay=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/nethernet/HttpRelaySignaling.java').read_text()
        logger=(root/'bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java').read_text()
        check(all(item in friend for item in ('response.statusCode() != 200','missing people snapshot','incomplete paginated friend snapshot','invalid/duplicate friend identity or relationship','person.get("isFriend")')),'friend count guards missing')
        check('MCGATEWAY_FRIEND_REMOVE_V160_V2' in friend and 'MCGATEWAY_FRIEND_STATE_V160_V2' in friend,'v2 target receipts missing')
        check('mcgatewayV2Lock.tryLock()' in friend and 'MCGATEWAY_RELEASE160_V2_INTERNAL_LOCK' in friend,'v2 mutation serialization missing')
        check('friendRequestSent' in friend and 'friendRequestReceived' in friend and 'response.statusCode() != 200' in friend,'strict target state guards missing')
        check('mcgatewayV2BodyHandler()' in friend and 'MCGATEWAY_V2_MAX_BODY_BYTES = 16 * 1024' in friend and 'future.cancel(true)' in friend,'v2 response/deadline bound missing')
        check('mcgatewayV2Skip' in friend and 'if (depth > 8)' in friend and 'if (++count > 64)' in friend and 'if (!names.add(r.nextName()))' in friend,'v2 JSON depth/duplicate bounds missing')
        check('TimeUnit.SECONDS.toNanos(20)' in friend and 'Math.min(8_000L, mcgatewayV2Remaining(deadline))' in friend,'absolute/individual request budgets missing')
        check('DateTimeFormatter.RFC_1123_DATE_TIME' in friend and 'Cache-Control", "no-cache' in friend,'freshness fencing missing')
        check('mcgatewayV2SessionIdentity' in friend and 'mcgatewayV2Hash(rawSession)' in friend,'session binding missing')
        check('lastFriendCache.removeIf' not in friend[friend.index('MCGATEWAY_RELEASE160_FRIEND_REMOVE_V2'):friend.index('    public void init')],'v2 code mutates cache')
        check('removeRelationship' not in friend and 'MCGATEWAY_TRANSFER_SUCCESS' not in relay,'invented legacy removal/success marker')
        check(all(item in core for item in ('MCGATEWAY_HEALTH_V160 initialized=','rta=','httpSignaling=','published=')),'health fields missing')
        check('MCGATEWAY_RELAY_IDENTITY_V1' in relay and 'MCGATEWAY_RELAY_SIGNALLED_V1' in relay,'relay markers missing')
        check('friends remove is DENIED' in logger and 'friendstatev160' in logger and 'friendremovev160' in logger,'v2 command/default denial missing')
        check('MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE' in logger and 'owner-reviewed-v2' in logger,'v2 explicit feature mode missing')
        check('MCGATEWAY_FRIEND_COUNT_V160 count=' in logger and 'MCGATEWAY_FRIEND_COUNT_V160 ERROR unavailable' in logger,'structured friendcount console missing')
        manager=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java').read_text()
        check('MCGATEWAY_RELEASE160_EXPIRY_HOLD' in manager,'upstream expiry hold missing')
        check('scheduledThreadPool.scheduleWithFixedDelay(this::expireFriends' not in manager,'upstream expiry still scheduled')
        check('private void expireFriends()' in manager,'unexpected SessionManager expiry implementation removed')
        config=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java').read_text()
        check('if (originallyEmpty) {' in config and 'currentVersion != newVersion' not in config[config.index('if (originallyEmpty) {'):],'config persistence guard missing')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-bad.') as temp:
        root=Path(temp)/'source';clone(upstream,root);target=root/FILES[0];target.write_text(target.read_text()+'\n// MCGATEWAY_RELEASE160_READONLY_OVERLAY\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'injected marker bypassed hash guard')
        after=digest(root);check(after==before,'bad preflight wrote a file')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-tampered.') as temp:
        root=Path(temp)/'source';clone(upstream,root);check(run('python3',str(PATCH),str(root)).returncode==0,'initial apply failed');target=root/FILES[2];target.write_text(target.read_text()+'\n// tampered\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'tampered patched bytes accepted');check(digest(root)==before,'tampered preflight wrote a file')
    print('test_release160_patch: ok (apply,idempotence,six-file-preflight,hash-guard,expiry-scheduler-disabled,truth-markers)')
if __name__=='__main__': main()
