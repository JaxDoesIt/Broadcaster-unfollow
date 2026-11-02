# Release160 compatibility candidate

## November 1 source-only accurate-count HTTP/1.1 parity candidate and immutable image

**Current development branch:** `fix/release160-friendcount-request-parity-2026-11-01`, started from existing `fix/release160-friendcount-pagination-proof-2026-10-31`. Neither this branch nor its image has been deployed to the Dell.

**What was corrected:** The uninstalled V3 `McgatewayFriendCountProof` now constructs its PeopleHub friend-list request with contract7, the original upstream `accept-language: en-GB`, and no extra explicit Accept/Cache-Control headers. Its social summary request retains contract3 and no language header. The dedicated count diagnostic client's preferred HTTP protocol is now `HTTP_1_1`; redirects remain deliberately disabled (unlike the original general client's Redirect.NORMAL) to avoid silently issuing a second request. This corrects source request-shape differences observed in the prior V4 HTTP400 diagnostic, **not a proven diagnosis of the 400**.

**Proof:** Existing V3 consistent summary/list/summary count and strict incomplete/partial/invalid schema rejection retained; additional offline Java request-envelope tests and source-patch preflights added. Source-only [GitHub Actions 41371494696](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41371494696), exact commit `13ae4c13451e2d9ae1100bc1b60edb966fc13936`: **SUCCESS**, pinned original Release160 Java21 standalone compilation, count fixtures, config/expiry and friend-removal denial proof.

**Unique sealed candidate:** Full image-build [GitHub Actions 41371776711](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41371776711), exact source commit `23bfc83f48c8357d0a84a00efb0e38502c4621d9`: **SUCCESS**, `FriendCountProofTest: PASS`, full `BUILD SUCCESSFUL`, unique registry tag check and immutable pushed digest independently verified in job `125043571035`. Image tag:
`ghcr.io/jaxdoesit/mcgateway-broadcast:release-160-friendcount-http1-parity-23bfc83f48c8357d0a84a00efb0e38502c4621d9`

**Verified registry OCI index digest**:
`sha256:dcdf50d975d2b985fa6d4ce94759e4fc3a67a98b5fe095e1cf436e4fb510e702`

**Digest-pinned identity**:
`ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:dcdf50d975d2b985fa6d4ce94759e4fc3a67a98b5fe095e1cf436e4fb510e702`

Registry index digest is **not** the same as local Docker image ID or architecture-specific manifest; verify both on the operator host. OCI labels include `io.mcgateway.overlay-variant=friend-count-proof-v3-http1-parity`, `io.mcgateway.friend-count-protocol=2`, `io.mcgateway.friend-removal-protocol=unsupported`, `io.mcgateway.production-ready=false`, upstream Release160 hash. This image is for supervised observation, NOT assignment, cleanup, public verified count, or automatic rollout. Stable/test tags unchanged; no running bot, Docker volume, Xbox friend, controller or DB was modified.

**Next approval boundary:** This image would need a separately owner-approved, verified Bot0-only image change (with preserved original image and rollback) before an actual `friendcountv2 <32-char nonce>` capture. That producer is a bounded up-to-three-GET summary/list/summary observation, NOT a single GET and NOT guaranteed to return real complete counts. If HTTP status, response shape, paging, summary drift or auth fails, it must report unavailable and must not authorize capacity. The previous V4 PeopleHub response was HTTP400 under nonmatching client/header settings, and no live HTTP result has been observed for this new exact candidate. All 16 currently healthy service bots and Bot0 marker, paused updater, stopped Watchtower and paused cleanup remain under owner control. No fifth V4 trial is assumed authorized.



This branch builds exact upstream `798d8b3a6107359643b525f1c9c3303c020ae09b`
with a separate, read-only MCGateway observation overlay and Java21. It does not
replace the release154 overlay, workflow, test/stable tags, or any live bot.

The audit candidate is **not production-ready** and is incompatible with the
current Control Bot9.0.8 rollout proof contract. Never deploy it by changing a
channel tag or presenting its signaling evidence as a completed transfer.

## Candidate changes and tests

- Full original/generated-patched byte validation for every touched source file
  before any write. Reapplication is idempotent; altered inputs fail closed.
- `health`: distinct `MCGATEWAY_HEALTH_V160` snapshot of initialized, RTA,
  active HTTP signaling and published session handle.
- `friendcount`: distinct `MCGATEWAY_FRIEND_COUNT_V160 count=N` only after a
  successful complete PeopleHub response with valid unique identities and
  explicit relationship booleans. Failure emits ERROR, never a fake zero.
- Existing `accounts list` remains upstream; no fabricated followers/following.
- `MCGATEWAY_RELAY_IDENTITY_V1` and `MCGATEWAY_RELAY_SIGNALLED_V1` follow validated
  SDP identity and returned relay signaling. Neither proves ICE/Bedrock/Hub join.
- `friends` removal is explicitly denied. No legacy deletion receipt is emitted.
- Config transformations run in memory. Existing files are not rewritten, keeping
  release154 rollback configuration bytes intact. Empty/new configuration can
  still be initialized normally.

`tools/test_release160_patch.py <exact-upstream-checkout>` is a lightweight offline
source-preflight/truth/atomicity/idempotence suite. GitHub additionally compiles
upstream and runs the actual Java ConfigLoader proof for v2/v7 effective targets,
byte-identical repeated loads, new-file initialization and malformed-file safety.

## Required before deployment

1. Verify successful off-host build and exact immutable candidate identity.
2. Release/test a separate Control Bot160 adapter: structured count and health
   parsing, relay evidence separated from actual transfers, a bounded canonical
   acceptance proof, and rollback coverage. Preserve all current player data.
3. Verify cleanup paused and drained before a160 canary; the new removal contract
   is unsupported, so cleanup must remain held for every160 bot until reviewed.
4. Verify exact154 image rollback plus config/storage compatibility and backup.
5. Owner-present updated-client Bot0-to-Hub test. Current9.0.8 cannot truthfully
   mark its automated canary or staged rollout passed using relay-only logs.
6. Automated fleet progression needs durable Hub-join correlation to the exact
   candidate bot/boot and exact Xbox/Hub identity, excluding concurrent attempts
   through other bots. Otherwise use a separately reviewed supervised per-bot
   proof contract. Never synthesize a legacy transfer-success event.

No live action is performed or authorized by this build-only workflow. Consult
JaxDoesIt/MCGateway Git brain for the installed production baseline and audit.


## Immutable v2 safety improvement (2026-10-27)

Upstream pinned SessionManager.java schedules expireFriends() independently of console control and MCGateway Control Bot. Candidate v2 removes that scheduler at the exact-source overlay level, so the Release160 client cannot run the upstream inactivity friend-prune cycle. This avoids inadvertent friend deletions while old 154 accounts and the Control Bot cleanup authority are preserved. The private unused expireFriends method is retained to minimize diff; the only upstream schedule call is removed. Console `friends remove` is still DENIED. Original SessionManager full-source Git blob SHA-1 and original other-file SHA-256 are preflight validated together, atomically and idempotently. This does NOT substitute for verifying MCGateway Control Bot cleanup paused and drained before Bot0, or for a proper 160 deletion contract.

**v2 IMAGE**: `ghcr.io/jaxdoesit/mcgateway-broadcast:release-160-relay-audit-expiry-held-v2` (new immutable candidate tag; never overwrite v1 or test/stable). CI build and digest must be independently verified before treating it as built. Never deploy automatically.

## Candidate v3: source-only count proof, cleanup still denied

Branch `mcgateway/release-160-friends-v3` starts at exact installed v2source
`f0da506d12074d5c99666d7a8ef0f73cdb6d6f58`. It retains transport, config rollback,
expiry exclusion, all V1 diagnostic markers and the hard friend-removal denial.
It adds only `friendcountv2 <32-lowercase-hex-nonce>` and a lazy redirect-free
read-only HTTP client. The V2 helper checks an explicit integer mutual-friend
summary before and after a validated friend enumeration; all counts must agree.
Strict status/JSON/UTF-8/schema/duplicate/uint64/pagination/size/time checks fail
closed. No error becomes zero, and the marker contains no player identities.

The candidate is still NOT PRODUCTION READY. A V2 marker is a source/transport
crosscheck, not automatic count authority: production API semantics and high-count
capture need empirical canary proof, and the Control Bot must verify nonce,
container/image/start identity and observation/admission separation. No old held
cleanup attempt is retried. Count capability never authorizes removal.

The workflow builds only the separate `release-160-friend-count-proof-v3` tag;
consume a successful candidate by the recorded immutable digest, not by mutable
tag lookup. No test/stable tag, production image or live bot is changed. Java21
compile/config/count fixture gates run off-host before any image is published.
The Python source preflight also rejects foreign/tampered helper files without
changing any of the other upstream inputs.
