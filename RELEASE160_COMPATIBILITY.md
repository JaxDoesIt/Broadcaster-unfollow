# Release160 compatibility candidate

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
