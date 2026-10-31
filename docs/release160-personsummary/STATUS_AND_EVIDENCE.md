# Release 160 PersonSummary | STATUS AND EVIDENCE

**Authoritative facts as of the owner report following the third live trial, 2026-10-30 CDT / 2026-10-31 UTC.** This is a versioned evidence ledger, not a live status panel. Consult [START_HERE](./START_HERE.md), [RULEBOOK](./RULEBOOK.md), and [NEXT_STEPS](./NEXT_STEPS.md).

## Current confirmed / last-reported production state

| Subject | Last evidence | Confidence and limit |
|---|---|---|
| Bot0 | Third trial ended in `RECOVERY VERIFIED: Bot0 original image running; maintenance hold cleared.` Owner then explicitly confirmed Bot0 **functional** for players. | **Confirmed at last report**, not a new active monitoring check. |
| Other 15 bots | Preflight `16/16 running`; V3 runner checks no other bot identity drift and restores Bot0. | Runner-reported isolation; independently recheck before new live intervention. |
| Friend cleanup | `cleanup paused` at third trial preflight; recovery guard checks paused. | Last observed **paused**; never unpause in this project. |
| Updater | Paused and rollout complete at third trial preflight. | Last observed only. |
| Watchtower | Required stopped by preflight. | Last observed only. |
| Maintenance hold | `maintenance hold cleared` after successful image rollback. | Last reported. |
| Hub real-world function | Owner answered **Bot0 good** after third rollback. | Independently owner-confirmed for Bot0; not a comprehensive end-to-end proof for all 16 at this moment. |
| PersonSummary GET | **No confirmed request or schema result** in any of 3 live trials. | Current unresolved blocker. |
| Friend deletion | No deletion was authorized by any trial, and diagnostic prints `can_authorize_removal=false`. | Do not resume deletion just from evidence here. |

## Three live trial ledger

### Trial 1: cache-only GET canary (completed)
- Image: `sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1`.
- Verified preflight, Bot0 temporary recreation, one sanitized console probe, original-image restoration and maintenance-hold clearance.
- Result: `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=no_cached_target can_authorize_removal=false`.
- Root problem: the early probe selected an existing `lastFriendCache` entry only; cache was unavailable or had no suitable target. **No PersonSummary GET occurred.**
- Source variant mismatch was subsequently identified: pinned upstream friend-sync code is not identical to the newer fork. A 120-second automatic-sync waiting scheme was withdrawn as unsafe/unproven.

### Trial 2: explicit GET to fill friend cache, mutation paths blocked (completed)
- Original proposed trial initially failed closed on preflight: `PREFLIGHT/SETUP STOPPED: Unsafe (details withheld)`. A read-only follow-up established Docker Compose label metadata recorded 2 files, including a **known deleted temporary `recovery.yml` override** from a prior image restoration. Exact runner fix passed 20 offline tests before the actual second trial.
- Image: `sha256:8768767c73ce9d29e80e81beaf2c1e6d3cbdbd4590e056fb06d32b1dde136722`.
- Result: `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=no_cached_target can_authorize_removal=false`.
- The old pinned upstream `FriendManager.get()` issues `GET https://peoplehub.xboxlive.com/users/me/people/friends`, but does not check the response HTTP status before parsing `people`. Thus a non-200 error body, empty success body and no valid XUID could all result in the same `no_cached_target`. **No PersonSummary response obtained.**
- Runner restored original immutable image and removed hold. Owner later confirmed Bot0 functional.

### Trial 3: V3 strict friend-list HTTP/category diagnostic (completed)
- Source: `fix/release160-friendlist-status-diagnostic-2026-10-30` at `04d7ae5906a50bcd8923813f76dcc4521ffea72a`.
- Image: `sha256:2f86cd48b94f298456f18e6937b38a5347e5de0d591d9c6107c209c159b04b80`.
- Runner: commit `0af042dcedc85a92e21fd9181e0c0a400923e7a6`.
- Owner-reported transcript:
```text
PREFLIGHT PASSED: cleanup paused, updater paused, 16/16 running, original image verified.
CANDIDATE STAGED: exact digest verified; no containers changed.
BOT0 HOLD ACTIVE: moving only Bot0 to candidate.
BOT0 CANDIDATE RECREATED: checking stable boot before explicit GET-only V3 diagnostic.
OBSERVATION VERIFIED: issuing exactly one V3 read-only probe command.
PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_other can_authorize_removal=false
RESTORING BOT0 original immutable digest.
RECOVERY VERIFIED: Bot0 original image running; maintenance hold cleared.
```
- The owner explicitly reconfirmed **Bot0 is functioning for players** following this restoration.
- **Precise meaning of `list_other`:** the single V3 GET `https://peoplehub.xboxlive.com/users/me/people/friends` produced an HTTP response at the expected URI with status **not** 200, 401, 403, 429, or any 5xx. Possible examples include 400, 404, 204, 206 and 3xx. **The actual status is unknown.** No PersonSummary GET occurred because the list request did not produce a validated target.
- Do not assert the endpoint is retired, that the status is 404, that the token was wrong, or that there are no Xbox friends. All these remain hypotheses.
- Last checkpoint after trial 3: [Git evidence commit](https://github.com/JaxDoesIt/Broadcaster-unfollow/commit/472a53df6db6ddd2b3ed7e0676dea233a4e837d5).

## Immutable images and proofs

| Artifact | Exact ID / SHA | State |
|---|---|---|
| Original production Release160 image | `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55` | **Original rollback target**, not superseded. |
| Trial 1 obsolete candidate | `sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1` | Tested and restored, **do not reuse**. |
| Trial 2 obsolete candidate | `sha256:8768767c73ce9d29e80e81beaf2c1e6d3cbdbd4590e056fb06d32b1dde136722` | Tested and restored, **do not reuse**. |
| Trial 3 V3 candidate | `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:2f86cd48b94f298456f18e6937b38a5347e5de0d591d9c6107c209c159b04b80` | Tested and restored, **do not repeat unchanged**. |
| Exact upstream source | `MCXboxBroadcast/Broadcaster@798d8b3a6107359643b525f1c9c3303c020ae09b` | Baseline for reproducible canary. |
| Original compatibility overlay | `tools/apply_mcgateway_release160_patch.py` blob `f4114376354b18e3b7541aa4af8bc6103b3b3b53` | Expiry-disabled, console friend-remove denied. |
| Trial 3 Java source proof | `04d7ae5906a50bcd8923813f76dcc4521ffea72a` | Reproducible source only. |
| Trial 3 owner runner | `tools/release160/owner_bot0_friendlist_status_v3_trial.py`, commit `0af042dcedc85a92e21fd9181e0c0a400923e7a6`, SHA-256 `007f7ebaad7ba288d3bff10dc5890b599e5273159684f38155047ec42eece7d7` | Executed once and restored. |
| Trial 3 sanitizer | `tools/release160/personsummary_console_result.py`, same commit, SHA-256 `ac9d3a7c5c78dcf517f7e8e2a9407f7f1bc2b1739b2c896e60300830965b74d8` | Allowlisted, one marker. |

## Completed CI proofs

| Stage | Run | Verified result |
|---|---|---|
| Trial 2 nonmutating source proof | [41153065633](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41153065633) | Success |
| Trial 2 immutable image | [41153311035](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41153311035) | Success |
| Trial 2 corrected runner mocks | [41158731527](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41158731527) | Success (4 sanitizer, 4 metadata, 12 lifecycle) |
| Trial 3 V3 source/JAR proof | [41160055385](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41160055385) | Success (305 Java list fake-GET/status/privacy assertions, Python patch/sanitizer tests, prior PersonSummary proof, full Gradle/JAR build) |
| Trial 3 immutable image | [41160318903](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41160318903) | Success; exact V3 digest as above |
| Trial 3 operator runner mock suite | [41160456805](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41160456805) | Success (5 sanitizer + 4 Compose + 15 lifecycle tests = 24) |

**V3 JAR source artifact:** `release160-friendlist-status-v3-proof-jar`, ID `13026612719`, ZIP digest `sha256:6c054eec37a11194dc712b49fdd32efb9df327546a0a4ee32dd9131161d78ec0`; this is the ZIP digest, **not** the JAR's own checksum. The immutable image CI checked the JAR itself.

The full chronological working notes exist in [the historical checkpoint](../release160-personsummary-canary-image-checkpoint-2026-10-30.md). Those notes preserve experiments, aborted approaches and older "next gate" language. **This file supersedes their dated status statements.**

## Known project design

- V3 Java helper `tools/release160/McgatewayXboxFriendListStatusV160.java` uses a single bounded GET with a no-redirect client, validates the expected URI, responses, metadata and body size/UTF-8/JSON, and either privately selects an eligible target or reports an allowlisted `fields=list_...` reason.
- Existing `McgatewayXboxPersonSummaryProbeV160.java` is a distinct bounded GET of the selected person's relationship summary. **It has not been reached in any live trial.**
- The one-shot hook `mcgatewayOneShotPersonSummaryProbe()` lives in the patched `FriendManager`; console command `personsummaryprobe` lives in `StandaloneLoggerImpl`. The command accepts an ephemeral nonce, not XUIDs or auth tokens.
- All candidate FriendManager automatic mutation paths are disabled at source level; original production still uses original intended code and is not being replaced by a diagnostic image.
- Sanitizer reports only `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=... fields=... can_authorize_removal=false` or a complete fail-closed `UNVERIFIED`. The word `http` in this marker represents **PersonSummary HTTP**, while `fields=list_other` represents friend-list category.

## Unresolved questions and approved work boundary

> [!WARNING]
> Actual friend-list HTTP response code and its reason remain unverified. No fourth live test is approved. Next action is offline research and an exact-code/status-bucket enhancement with fake HTTP unit tests.

See [NEXT_STEPS](./NEXT_STEPS.md) for prioritized, executable work. Production safety remains the overriding requirement.
