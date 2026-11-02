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
        check('removeRelationship' not in friend and 'MCGATEWAY_TRANSFER_SUCCESS' not in relay,'invented removal/success marker')
        check(all(item in core for item in ('MCGATEWAY_HEALTH_V160 initialized=','rta=','httpSignaling=','published=')),'health fields missing')
        check('MCGATEWAY_RELAY_IDENTITY_V1' in relay and 'MCGATEWAY_RELAY_SIGNALLED_V1' in relay,'relay markers missing')
        check('friends remove is DENIED' in logger,'reviewed removal default-deny path missing')
        check('MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE' in logger and 'mcgatewayReviewedRemoveOnce(args[1])' in logger,'reviewed console compatibility missing')
        check('mcgatewayRemovalInFlight.compareAndSet(false, true)' in friend,'one-inflight removal gate missing')
        check('HttpResponse.BodyHandlers.discarding()' in friend and 'sendAsync(request' in friend,'one-shot body-discarding async request missing')
        check('mcgatewayRemovalInFlight.set(false)' in friend,'reviewed removal release fence missing')
        check('Removed Unknown (' in friend and 'response.statusCode()' in friend,'verified-only success log missing')
        reviewed=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayReviewedFriendRemove.java'
        check(reviewed.read_bytes()==PATCH.with_name('release160').joinpath('McgatewayReviewedFriendRemove.java').read_bytes(),'reviewed remove helper source mismatch')
        check('owner-reviewed-v160' in reviewed.read_text() and 'public static boolean permitted' in reviewed.read_text(),'reviewed removal gate missing')
        check('case "friendcountv2"' in logger and 'nonce=invalid ERROR unavailable' in logger,'nonce-bound proof console missing')
        helper=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayFriendCountProof.java'
        check(helper.read_bytes()==PATCH.with_name('release160').joinpath('McgatewayFriendCountProof.java').read_bytes(),'count helper source mismatch')
        check('mcgatewayFriendCountProof' in friend and 'HttpClient.Redirect.NEVER' in friend and 'HttpClient.Version.HTTP_1_1' in friend,'dedicated pinned HTTP1.1 redirect-free count client missing')
        check('MCGATEWAY_FRIEND_COUNT_V160 count=' in logger and 'MCGATEWAY_FRIEND_COUNT_V160 ERROR unavailable' in logger,'structured friendcount console missing')
        manager=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java').read_text()
        check(manager.count('MCGATEWAY_ACCOUNTS_LIST_V160 result=provisional reason=ok') == 1,
              'Release160 accounts list display-only completion missing or duplicated')
        check('MCGATEWAY_RELEASE160_EXPIRY_HOLD' in manager,'upstream expiry hold missing')
        check('scheduledThreadPool.scheduleWithFixedDelay(this::expireFriends' not in manager,'upstream expiry still scheduled')
        check('private void expireFriends()' in manager,'unexpected SessionManager expiry implementation removed')
        config=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java').read_text()
        check('if (originallyEmpty) {' in config and 'currentVersion != newVersion' not in config[config.index('if (originallyEmpty) {'):],'config persistence guard missing')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-bad.') as temp:
        root=Path(temp)/'source';clone(upstream,root);target=root/FILES[0];target.write_text(target.read_text()+'\n// MCGATEWAY_RELEASE160_READONLY_OVERLAY\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'injected marker bypassed hash guard')
        after=digest(root);check(after==before,'bad preflight wrote a file');check(not (root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayFriendCountProof.java').exists(),'bad preflight introduced helper')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-summary-partial.') as temp:
        root=Path(temp)/'source';clone(upstream,root)
        check(run('python3',str(PATCH),str(root)).returncode==0,'summary patch apply failed')
        manager=root/FILES[0]
        marker='            coreLogger.info("MCGATEWAY_ACCOUNTS_LIST_V160 result=provisional reason=ok");'
        check(marker in manager.read_text(),'expected summary marker missing')
        manager.write_text(manager.read_text().replace(marker,'            // unexpected partial summary change'))
        before=digest(root)
        failed=run('python3',str(PATCH),str(root))
        check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,
              'partially modified summary was accepted')
        check(digest(root)==before,'partial source modified after failed preflight')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-tampered.') as temp:
        root=Path(temp)/'source';clone(upstream,root);check(run('python3',str(PATCH),str(root)).returncode==0,'initial apply failed');target=root/FILES[2];target.write_text(target.read_text()+'\n// tampered\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'tampered patched bytes accepted');check(digest(root)==before,'tampered preflight wrote a file')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-helper-tamper.') as temp:
        root=Path(temp)/'source';clone(upstream,root)
        helper=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayFriendCountProof.java'
        helper.write_text('// unknown pre-existing helper\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0,'foreign helper accepted')
        check(digest(root)==before and helper.read_text()=='// unknown pre-existing helper\n','foreign-helper failure wrote source')
        helper.unlink();check(run('python3',str(PATCH),str(root)).returncode==0,'initial helper apply failed')
        helper.write_text(helper.read_text()+'\n// tampered helper\n');before=digest(root);helper_before=helper.read_bytes()
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0,'tampered helper accepted')
        check(digest(root)==before and helper.read_bytes()==helper_before,'tampered helper failure modified source')
    print('test_release160_patch: ok (apply,idempotence,hash-guard,friend-count,reviewed-removal-default-deny,expiry-disabled)')
if __name__=='__main__': main()
