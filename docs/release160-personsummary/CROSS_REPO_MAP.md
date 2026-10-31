# Cross-repository map | broadcaster, Control Bot, and friend cleanup

Read [START_HERE](./START_HERE.md) and [RULEBOOK](./RULEBOOK.md) first. This document is a **navigation map**, not a production approval or a reconciliation of all historical commits.

## Repositories

| Repository | Visibility and responsibility | Relevant refs |
|---|---|---|
| [JaxDoesIt/Broadcaster-unfollow](https://github.com/JaxDoesIt/Broadcaster-unfollow) | Public source and CI for pinned MCXboxBroadcast Release160 compatibility overlay and GET-only diagnostic. | V4 source `fix/release160-friendlist-http-code-v4-2026-10-30` at `66cfa52ecfa51714220a8ef6c051e44018745ebb`; V4 image/operator `build/release160-friendlist-http-code-v4-2026-10-30` at `614f7611f945dc75b579eea128cdcbbc403f35bf`. |
| [JaxDoesIt/MCGateway](https://github.com/JaxDoesIt/MCGateway) | **Private** authoritative MCGateway Control Bot / fleet / friend-count / friend-cleanup / Hub project, not part of this public image CI. | Verified navigation snapshot branch `fix/release160-presence-continuation-2026-10-29` at tree `f2d1cafeab869752855ed5001fd11467b859e803`. Recheck current branch before citing its operational status; private `main` is not necessarily current. |
| [MCXboxBroadcast/Broadcaster](https://github.com/MCXboxBroadcast/Broadcaster) | External pinned upstream source; not the MCGateway operational repository. | Exact upstream Java SHA `798d8b3a6107359643b525f1c9c3303c020ae09b`. |

## Private MCGateway documents to read for changes affecting Control Bot or cleanup

These links require authorized access to the private repository. They are **historical source material**, not automatically current runtime evidence:

- [AGENTS.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/AGENTS.md): repository-specific maintainer instructions; read before any MCGateway source edit.
- [docs/CURRENT_STATE.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/CURRENT_STATE.md) and [docs/TODO.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/TODO.md): branch-local project state, may include newer or older gates than this specific diagnostic.
- [FRIEND_REFRESH_CHATGPT_HANDOFF_2026-10-28.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/handoffs/FRIEND_REFRESH_CHATGPT_HANDOFF_2026-10-28.md): separate friend-count refresh source work and continuation guardrails.
- [RELEASE160_FRIENDS_REPAIR_2026-10-28.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/plans/RELEASE160_FRIENDS_REPAIR_2026-10-28.md): separate count producer, Control Bot count observer, friendship cleanup acceptance and rollout gates.
- [FRIEND_COUNT_RELEASE160_AUDIT_2026-10-28.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/audits/FRIEND_COUNT_RELEASE160_AUDIT_2026-10-28.md): evidence of Release160 legacy count parser mismatch, stale-count problems and distinct cleanup hold as of that older audit date.
- [DEPLOYMENT_SAFETY.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/operations/DEPLOYMENT_SAFETY.md): global Dell, Control Bot and Hub safe-change boundaries.
- [RELEASE160_BOT0_SUPERVISED_RUNBOOK.md](https://github.com/JaxDoesIt/MCGateway/blob/fix/release160-presence-continuation-2026-10-29/docs/operations/RELEASE160_BOT0_SUPERVISED_RUNBOOK.md): historical Bot0 rollback concepts. Its "NOT APPROVED" heading is dated; never use the old source-only procedure verbatim for the V4 diagnostic. Use the separately CI-proven V4 runner only after fresh owner approval.

## Private MCGateway back-link to this handoff

A docs-only private bridge has also been created at [RELEASE160_PERSONSUMMARY_V4_GIT_POINTER_2026-10-30.md](https://github.com/JaxDoesIt/MCGateway/blob/docs/release160-personsummary-bridge-2026-10-30/docs/handoffs/RELEASE160_PERSONSUMMARY_V4_GIT_POINTER_2026-10-30.md), commit `425c617594baf537b49d0d5f1971809062986039`. It points back to the canonical public runbook and separates private Control Bot/count/cleanup acceptance gates. No Control Bot source, service or production state was changed.

## Three separate gates, NEVER conflate

1. **Friend-list/PersonSummary contract discovery (this handoff).** Read-only Xbox GET(s), coarse status/shape evidence, diagnostic only. Current last live result: V3 `list_other` of unknown exact HTTP code. V4 offline-proven exact-code helper is **not installed on Dell** and is waiting for specific fourth-trial owner approval.
2. **Friend count and capacity refresh (MCGateway Control Bot project).** Legacy count receipts may not match Release160. The separate producer/observer project must prove authoritative counts, complete lists, and assignment correctness before any capacity admission. Its source-progress documents do not grant deployment to this PersonSummary diagnostic.
3. **Friend removal / cleanup resumption (separate MCGateway acceptance gate).** Requires a safe operation identity, version-aware relationship postcondition, uncertainty quarantine, fresh backups, activity veto, per-bot controlled proof and explicit owner approval. **No PersonSummary/HTTP/schema diagnostic alone can authorize removal or unpause cleanup.**

## Cross-repo safety workflow

- Only use this Broadcaster repo for **read-only diagnostic Java, isolated image, and offline operator mock** work. Do not modify the Control Bot repository to make a list GET work or bypass a failed diagnostic.
- If a candidate threatens Control Bot supervision, maintainer scripts, final cleanup dispatch, scheduling, or production records, first read `AGENTS.md` and the private deployment-safety files above and move that change into a new separately reviewed MCGateway branch. Do not change production Control Bot as a side effect of a Bot0 HTTP test.
- The Dell is separate: GitHub source/CI cannot prove live installation. Only the operator's fixed, hash-verified, specifically approved terminal action provides live evidence.
- Preserve the authoritative initial release and original-image recovery digest listed in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).
- Do not quote private repo source containing secrets or internal credentials in public Git; only cite safe file paths, branch/ref navigation and nonsecret acceptance gates.
- When an MCGateway doc says a task was "in progress" on a historical date, do not override a later live user observation or assume the task has since completed. Fetch the current source and read-only runtime evidence.

**This document is a cross-repo index, not a copy of the private operational code or data.**
