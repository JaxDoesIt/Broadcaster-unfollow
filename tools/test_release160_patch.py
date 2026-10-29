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
        check(core.count('MCGATEWAY_XBOX_PRESENCE_POST_ACCEPTED status=200') == 1,'exact HTTP200 marker missing or duplicated')
        check('boolean presenceAccepted = false;' in core and 'if (presenceAccepted) {' in core,'presence HTTP200 guard missing')
        check('Presence update successful, scheduling presence update' not in core,'old unconditional misleading success remains')
        check('Presence update " + (presenceAccepted ? "accepted" : "unverified")' in core,'error scheduling not labeled unverified')
        check('logger.error("Failed to update presence, got status "' in core,'HTTP failure diagnostics lost')
        check('private int consecutivePresenceFailures = 0;' in core,'failure streak state missing')
        check('McgatewayPresenceRetryPolicy.failureDelaySeconds(' in core,'bounded retry policy call absent')
        check('McgatewayPresenceRetryPolicy.acceptedDelaySeconds(' in core,'accepted heartbeat validation missing')
        check('consecutivePresenceFailures = 0;' in core and 'status != 200' in core,'success-only streak reset missing')
        check('Thread.currentThread().interrupt();' in core,'interrupted HTTP request did not restore interrupt status')
        check('updatePresenceResponse.headers().firstValue("Retry-After")' in core,'server Retry-After ignored')
        policy=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayPresenceRetryPolicy.java'
        check(policy.read_bytes()==PATCH.with_name('release160').joinpath('McgatewayPresenceRetryPolicy.java').read_bytes(),'presence policy source mismatch')
        check('MAX_SERVER_RETRY_SECONDS = 3600;' in policy.read_text(),'retry delay ceiling missing')
        check('MCGATEWAY_RELAY_IDENTITY_V1' in relay and 'MCGATEWAY_RELAY_SIGNALLED_V1' in relay,'relay markers missing')
        check('friends remove is DENIED' in logger,'unsupported removal not denied')
        check('case "friendcountv2"' in logger and 'nonce=invalid ERROR unavailable' in logger,'nonce-bound proof console missing')
        helper=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayFriendCountProof.java'
        check(helper.read_bytes()==PATCH.with_name('release160').joinpath('McgatewayFriendCountProof.java').read_bytes(),'count helper source mismatch')
        check('mcgatewayFriendCountProof' in friend and 'HttpClient.Redirect.NEVER' in friend,'dedicated redirect-free count client missing')
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
        after=digest(root);check(after==before,'bad preflight wrote a file');check(not (root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayFriendCountProof.java').exists(),'bad preflight introduced helper')
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
    with tempfile.TemporaryDirectory(prefix='mcgateway160-retry-tamper.') as temp:
        root=Path(temp)/'source';clone(upstream,root)
        policy=root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewayPresenceRetryPolicy.java'
        policy.write_text('// unknown pre-existing policy\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0,'foreign policy accepted')
        check(digest(root)==before and policy.read_text()=='// unknown pre-existing policy\n','foreign-policy failure modified source')
        policy.unlink();check(run('python3',str(PATCH),str(root)).returncode==0,'initial policy apply failed')
        policy.write_text(policy.read_text()+'\n// tampered policy\n');before=digest(root);policy_before=policy.read_bytes()
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0,'tampered policy accepted')
        check(digest(root)==before and policy.read_bytes()==policy_before,'tampered policy failure modified source')
    print('test_release160_patch: ok (apply,idempotence,all-input-preflight,hash-guard,helper-and-policy-tamper,expiry-disabled,truth-markers)')
if __name__=='__main__': main()
