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
def java_method(text, signature):
    begin = text.index(signature)
    pos = text.index('{', begin)
    depth = 0
    state = 'code'
    quote = None
    index = pos
    while index < len(text):
        char = text[index]
        pair = text[index:index + 2]
        if state == 'line':
            if char == '\n': state = 'code'
        elif state == 'comment':
            if pair == '*/': state = 'code'; index += 1
        elif state == 'string':
            if char == '\\': index += 1
            elif char == quote: state = 'code'
        elif pair == '//': state = 'line'; index += 1
        elif pair == '/*': state = 'comment'; index += 1
        elif char in ('"', "'"): state = 'string'; quote = char
        elif char == '{': depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0: return text[begin:index + 1]
        index += 1
    raise AssertionError('unterminated Java method')

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
        workflow=PATCH.parent.parent/'.github/workflows/release160-friend-removal-v2-source.yml'
        check(all(item in friend for item in ('response.statusCode() != 200','missing people snapshot','incomplete paginated friend snapshot','invalid/duplicate friend identity or relationship','person.get("isFriend")')),'friend count guards missing')
        check('MCGATEWAY_FRIEND_REMOVE_V160_V2' in friend and 'MCGATEWAY_FRIEND_STATE_V160_V2' in friend,'v2 target receipts missing')
        state_segment=friend[friend.index('private enum McgatewayV2StateDiagnostic'):friend.index('    public String mcgatewayFriendRemoveV2')]
        diagnostics=('INVALID_REQUEST','NONCE_REJECTED','NORMAL_FRIEND_WORK_BUSY','SESSION_UNAVAILABLE','IDENTITY_CHANGED','TARGET_QUEUED','TIMEOUT','TRANSPORT','REDIRECT','HTTP_400','HTTP_401','HTTP_403','HTTP_404','HTTP_408','HTTP_409','HTTP_429','HTTP_500','HTTP_502','HTTP_503','HTTP_504','HTTP_OTHER','CONTENT_TYPE','HEADERS','DATE','AGE','BODY_LIMIT','UTF8','JSON','SCHEMA','INTERNAL')
        check(all(item in state_segment for item in diagnostics),'closed GET diagnostic enum incomplete')
        check('state=unknown verified=false stage=' in state_segment and 'mcgatewayV2HttpDiagnostic' in state_segment,'GET diagnostic frame/category mapping missing')
        check('catch (Exception error) { return mcgatewayV2StateUnknown' in state_segment and 'catch (Throwable error)' not in state_segment,'GET diagnostics must not mask fatal JVM errors')
        check('getMessage()' not in state_segment and 'error.toString' not in state_segment and '+ error' not in state_segment,'GET diagnostic leaks exception text')
        check('throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA)' in state_segment and 'throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON)' in state_segment,'GET duplicate/type/missing schema diagnostics absent')
        proof=(PATCH.parent/'release160/FriendStateV2DiagnosticProof.java').read_text()
        check(all(item in proof for item in ('for (Diagnostic diagnostic : Diagnostic.values())','token=secret','stage=internal category=internal','http-504')),'offline GET diagnostic proof incomplete')
        workflow_text=workflow.read_text()
        check('io.mcgateway.friend-state-diagnostics=1' in workflow_text and 'FriendStateV2DiagnosticProof.java' in workflow_text and ':core:mcgatewayFriendStateV2Diagnostics' in workflow_text,'diagnostic candidate image/proof gate missing')
        current_patch=PATCH.read_text()
        remove_start='    public String mcgatewayFriendRemoveV2'
        remove_source=java_method(current_patch, remove_start)
        check('Thread.sleep(250L)' in remove_source and 'never reissue DELETE' in remove_source,
              'V2 removal must poll settled absence without reissuing DELETE')
        check('ReentrantReadWriteLock mcgatewayV2Lock' in friend and 'mcgatewayV2Lock.writeLock().tryLock()' in friend and 'mcgatewayV2Lock.readLock().lock()' in friend and all(('MCGATEWAY_RELEASE160_V2_ADD_LOCK' in friend, 'MCGATEWAY_RELEASE160_V2_ADD_IF_REQUIRED_LOCK' in friend, 'MCGATEWAY_RELEASE160_V2_REMOVE_LOCK' in friend, 'MCGATEWAY_RELEASE160_V2_INTERNAL_LOCK' in friend)),'v2 mutation serialization missing')
        check('(phase == McgatewayV2ReadPhase.AFTER_DELETE || phase == McgatewayV2ReadPhase.BEFORE_RESTORE) && response.statusCode() == 404' in friend,'404 must be post-delete only')
        check(friend.index('if (postDelete404)') < friend.index('allValues("Content-Type")'),'post-delete 404 must not require response freshness headers')
        check('McgatewayV2ReadPhase.BEFORE_DELETE' in friend and 'McgatewayV2ReadPhase.OBSERVE' in friend,'read phase must be explicit')
        check('result=already-absent pre=absent' not in friend,'no admission/confirmation from absent pre-state')
        check('basis=target-404-after-delete' in friend and 'new McgatewayV2State("friendship-absent", false)' in friend,'separate friendship-only proof missing')
        check('owner-reviewed-recovery-v1' in friend and 'mcgatewayRecoveryBinding' in friend and 'TARGET_SHA256' in friend and 'ACCOUNT_SHA256' in friend,'exact recovery bindings missing')
        check('mcgatewayRecoveryRehearsalUsed = true' in friend and 'if (!restored.removable())' in friend,'rehearsal replay or strict post-GET gate missing')
        check('Thread.sleep(250L)' in friend and 'never reissue DELETE' in friend,'post-delete propagation poll missing')
        check('friendrehearsev160' in logger and 'friendrestorev160' in logger and 'commandNode.equals("friendrehearsev160")' in logger,'closed recovery command routing missing')
        check('friendRequestSent' in friend and 'friendRequestReceived' in friend and 'response.statusCode() != 200' in friend,'strict target state guards missing')
        check('McgatewayV2NonceWindow' in friend and 'MCGATEWAY_V2_MAX_NONCES = 4_096' in friend and 'MCGATEWAY_V2_NONCE_TTL_MS = 15L * 60L * 1_000L' in friend,'bounded expiring nonce window missing')
        check('consumed.entrySet().removeIf' in friend and 'consumed.size() >= MCGATEWAY_V2_MAX_NONCES' in friend and 'oldest.remove()' in friend,'nonce expiry/capacity eviction missing')
        check('mcgatewayV2Nonces.consume(nonce)' in friend and 'Never evict a nonce; capacity exhaustion fails closed' not in friend,'legacy nonce exhaustion behavior remains')
        check('mcgatewayV2BodyHandler()' in friend and 'MCGATEWAY_V2_MAX_BODY_BYTES = 16 * 1024' in friend and 'future.cancel(true)' in friend,'v2 response/deadline bound missing')
        check('mcgatewayV2Skip' in friend and 'if (depth > 8)' in friend and 'if (++count > 64)' in friend and 'if (!names.add(r.nextName()))' in friend,'v2 JSON depth/duplicate bounds missing')
        check('TimeUnit.SECONDS.toNanos(20)' in friend and 'Math.min(8_000L, mcgatewayV2Remaining(deadline))' in friend,'absolute/individual request budgets missing')
        check('DateTimeFormatter.RFC_1123_DATE_TIME' in friend and 'Cache-Control", "no-cache' in friend and '.followRedirects(HttpClient.Redirect.NEVER)' in friend and 'allValues("Age")' in friend and '!uri.equals(deleted.uri())' in friend,'freshness/redirect fencing missing')
        check('mcgatewayV2SessionIdentity' in friend and 'mcgatewayV2Hash(rawSession)' in friend and 'identity-before-delete' in friend,'session binding missing')
        check('lastFriendCache.removeIf' not in friend[friend.index('MCGATEWAY_RELEASE160_FRIEND_REMOVE_V2'):friend.index('    public void init')],'v2 code mutates cache')
        check('removeRelationship' not in friend and 'MCGATEWAY_TRANSFER_SUCCESS' not in relay,'invented legacy removal/success marker')
        check(all(item in core for item in ('MCGATEWAY_HEALTH_V160 initialized=','rta=','httpSignaling=','published=')),'health fields missing')
        check('MCGATEWAY_RELAY_IDENTITY_V1' in relay and 'MCGATEWAY_RELAY_SIGNALLED_V1' in relay,'relay markers missing')
        check('friends remove is DENIED' in logger and 'friendstatev160' in logger and 'friendremovev160' in logger and 'stage=input category=invalid-request' in logger,'v2 command/default denial missing')
        check('MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE' in logger and 'owner-reviewed-v2' in logger,'v2 explicit feature mode missing')
        check('MCGATEWAY_FRIEND_COUNT_V160 count=' in logger and 'MCGATEWAY_FRIEND_COUNT_V160 ERROR unavailable' in logger,'structured friendcount console missing')
        manager=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java').read_text()
        check('MCGATEWAY_RELEASE160_EXPIRY_HOLD' in manager,'upstream expiry hold missing')
        check('scheduledThreadPool.scheduleWithFixedDelay(this::expireFriends' not in manager,'upstream expiry still scheduled')
        check('private void expireFriends()' in manager,'unexpected SessionManager expiry implementation removed')
        config=(root/'core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java').read_text()
        check('if (originallyEmpty) {' in config and 'currentVersion != newVersion' not in config[config.index('if (originallyEmpty) {'):],'config persistence guard missing')
        workflow_text=workflow.read_text()
        check('FriendRemovalV2ContractProof.java' in workflow_text and 'FriendRemovalV2InterleavingProof.java' in workflow_text and 'mcgatewayFriendRemovalV2Interleaving' in workflow_text,'V2 proof workflow wiring missing')
        check('FriendNonceWindowProof.java' in workflow_text and 'mcgatewayFriendNonceWindow' in workflow_text,'nonce-window proof workflow wiring missing')
        check('friend-state-v2-nonce-window-v1' in workflow_text,'nonce-window candidate image label missing')
        check('Registry lookup did not prove the candidate tag absent.' in workflow_text and 'docker buildx imagetools inspect "$IMAGE"' in workflow_text,'immutable candidate workflow fence missing')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-bad.') as temp:
        root=Path(temp)/'source';clone(upstream,root);target=root/FILES[0];target.write_text(target.read_text()+'\n// MCGATEWAY_RELEASE160_READONLY_OVERLAY\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'injected marker bypassed hash guard')
        after=digest(root);check(after==before,'bad preflight wrote a file')
    with tempfile.TemporaryDirectory(prefix='mcgateway160-tampered.') as temp:
        root=Path(temp)/'source';clone(upstream,root);check(run('python3',str(PATCH),str(root)).returncode==0,'initial apply failed');target=root/FILES[2];target.write_text(target.read_text()+'\n// tampered\n');before=digest(root)
        failed=run('python3',str(PATCH),str(root));check(failed.returncode!=0 and 'hash mismatch' in failed.stderr,'tampered patched bytes accepted');check(digest(root)==before,'tampered preflight wrote a file')
    print('test_release160_patch: ok (apply,idempotence,six-file-preflight,hash-guard,expiry-scheduler-disabled,truth-markers)')
if __name__=='__main__': main()
