# Release 160 PersonSummary investigation | RULEBOOK

Read [START_HERE](./START_HERE.md), [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md), and [NEXT_STEPS](./NEXT_STEPS.md) before taking action. **This rulebook is normative for this specific diagnostic project.** Production changes require the owner's separate permission, not merely an assistant's decision to "proceed."

## 1. Mission, correct success criteria and scope

**Business/user goal:** Enable correct, reliable friend relationship status verification for the 16-bot MCGateway fleet without damaging player access, Xbox friendships or the healthy Hub. Existing friend cleanup is paused with a large backlog; **the backlog must not be processed merely because a diagnostic succeeds**.

**Technical goal:** Find a *verified* read-only Xbox response contract sufficient to choose a legitimate friend target and inspect PersonSummary relationship fields. Separate transport, HTTP, response-shape and domain semantics. A valid PersonSummary schema is only evidence for a later contract review, **not permission to remove or alter a friendship**.

**Current blocker:** `list_other` from the third Bot0 trial. The V3 helper bucket includes any HTTP status other than 200, 401, 403, 429 or 500 through 599, after matching the expected final URI. The actual HTTP code and body are unobserved. The only supportable inference is "the request obtained an HTTP reply whose status fell into that category." Do **not** infer 404, endpoint retirement, a Microsoft policy change, unauthorized token, or an empty friend list.

Done criteria are sequential:
1. Verified, minimally revealing list GET status and response semantics using only allowlisted diagnostic information.
2. Authenticated read-only PersonSummary GET with a validated, real friend target, if ethically and operationally appropriate.
3. Mock/tested, reviewable relation-field contract that accounts for malformed, stale, rate-limited, or incomplete data.
4. Explicitly separate future review of cleanup receipt/protocol, dry runs, safety gates and rollback, **never enable live deletion by default**.

## 2. Safety invariants

> [!CAUTION]
> **Do not** unpause friend cleanup, enable mass removal, delete friend relationships, add/accept friend requests, change existing production Compose/config or release tags, or restart the fleet for this investigation.

- **Bot0 only** for any future approved live test. Require owner approval for the precise interruption and network request count immediately before delivering an executing command. Approval for any prior trial is spent.
- Other **15 bots are outside scope**. Require preflight and postflight identity checks, not just an assumption.
- Never mutate or rely on active production databases for a diagnostic. Read only minimum safe state (e.g., cleanup pause) without printing tables or records.
- Preserve Control Bot, updater, Watchtower and maintenance guard behavior. Before any test reconfirm: cleanup paused persistently, updater paused, Watchtower stopped, rollout complete, Bot0 original digest, 16/16 containers running, zero unexpected supervisor interference, and all other 15 identities unchanged.
- **Stable and `test` tags are not rollback targets.** Always restore Bot0 by exact immutable original digest:
  `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`.
- The candidate may modify Bot0 for the approved trial only. Stop after a bounded request or failure and restore the original digest. Clear private maintenance hold **only after verified original-image restoration**. On `RECOVERY NOT VERIFIED`, preserve hold and stop for operator-directed recovery; never loop/retry blindly.
- Existing `mcgatewaybot-docker` Docker Compose metadata includes an obsolete, deleted temporary `mcgateway-bot0-canary-*/recovery.yml` entry from earlier rollback. The tested operator runner explicitly recognizes that one absent path **only**, still rejecting active/unknown overrides. Do not "repair" the original Compose config to accommodate this.
- The candidate's `FriendManager` must have explicit gates blocking automatic friend-sync mutation, incoming friend-request acceptance, add/remove, internal processing and invites, independent of the user's existing `friend-sync` settings.
- Original production image continues to run normal production behavior. A test image marked `production-ready=false` is diagnostic only, not a replacement release.
- A successful `RECOVERY VERIFIED` is **Docker/image/hold recovery**, not proof a Minecraft player can join. Record the owner's separate Hub/player functional confirmation whenever available.

## 3. Data privacy and network rules

> [!CAUTION]
> Never print or store Xbox authorization headers, session tokens, refresh tokens, player XUIDs, gamertags, private Compose paths, raw Xbox HTTP headers/bodies, account lists or sensitive environment variables in chat, workflow logs or Git.

- Use a narrow fixed allowlist of status/shape strings. Do not print values sampled from Xbox responses, not even a "redacted" full dump.
- One-shot diagnostic is nonce-correlated, and the raw console capture stays inside an ephemeral owner-private process. The Python sanitizer **must** verify exactly one well-formed, nonce-matched, allowlisted marker and emit only the safe summary.
- Prefer isolated mock fetchers with fake tokens and fake response objects. No real Xbox GET, live container, Docker daemon or Dell connection in CI.
- Respect **one** bounded friend-list GET and at most **one** PersonSummary GET in a live trial. No redirects, transparent retries, hidden paging loops or fallback requests unless separately reviewed and explicitly authorized. If an endpoint is modified, treat that as a new request contract.
- Fully bound network bytes and time, including streamed bodies, close/cancel on overflow or timeout; use exact expected HTTPS host/URI, and disallow redirect following.
- Preserve distinction between actual Xbox HTTP status and PersonSummary status. For V3, `http=unverified` means **PersonSummary HTTP was not established** even when `fields=list_other` represents an observed friend-list HTTP response.
- A response must not authorize removal without a separately established business contract, correct identity and receipt semantics, stale-data gates and owner-approved rollout. **All diagnostic outputs always end in `can_authorize_removal=false`.**

## 4. Git workflow and source-of-truth requirements

**Authoritative path:** [START_HERE](./START_HERE.md) in `docs/release160-personsummary-continuation-2026-10-30`. Keep status, outstanding gates and exact identities in this branch.

- Use a fresh **`fix/` branch** for a proposed source change and a separate **`build/` branch** for a new test image/runner; do not rewrite prior pinned evidence commits or promote stable/test tags.
- Always work from the **pinned upstream baseline** `MCXboxBroadcast/Broadcaster@798d8b3a6107359643b525f1c9c3303c020ae09b` and the exact original `relay-audit-expiry-held-v2` overlay (unless a separately documented change is justified). Do not silently substitute the newer `Broadcaster-unfollow` fork's current Java source because its `autoFollow/autoUnfollow` and friend list implementation differ.
- Treat all GitHub source files and CI runs as immutable evidence **only at a full commit SHA and verified artifact digest**. A branch name/tag alone is insufficient proof.
- For Java source changes, create/update a source-only overlay patch with exact anchors, original file identity guards and idempotence, and refusing unknown code drift or missing mutation gates. For runtime execution, one preflighted, hash-verified, self-contained operator command.
- For every change, do a critical review: alternate hypotheses, edge/error cases, bad inputs, concurrency and retries, resource budgets, unsafe output, and redundant/unused paths. Distinguish **required fix**, **optional optimization**, and **safely removable**. Mark a section "completed" only when the relevant proof was actually run and succeeded.
- Every new Git update must also update [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md) and [NEXT_STEPS](./NEXT_STEPS.md), with links to specific successful or failed run IDs and the next gate.
- Never hide a failed CI run. Record what failed, correct it on a new commit, and prove the final commit separately. Source proof success does **not** imply image proof or a live trial happened.
- Use severity conventions in notes: **HIGH** for possible player interruption, relationship mutation, secret leak, corrupt state or inability to recover; **MEDIUM** for nonauthoritative diagnostic results or CI gaps; **LOW** for docs/readability/optional cleanup. Use GitHub `[!CAUTION]`, `[!WARNING]`, `[!NOTE]` alerts to render colored emphasis without emoji.

## 5. Mandatory offline proof before any live action

Perform all applicable steps **on mocked/GitHub CI** before declaring a new candidate deployable:

1. Pin the original upstream SHA, source overlay hashes and all helper/test hashes; fail closed on source mismatch, symlinks, unexpected additional files or preexisting patch.
2. Verify original expiry hold and console friend-remove denial are intact; **all** automatic friend mutation entrypoint guards remain.
3. Exercise fake HTTP response statuses (success, auth, rate limit, redirects, other 4xx, server), response body/header validation, malformed and duplicate JSON keys, truncation/oversize, Unicode/UTF-8, pagination/continuation, no valid target, correct target and self-filtering.
4. Prove the request count and method, exact endpoint, disabled redirects, no retry, bounded time/body, no token/player/raw-response leakage. A known HTTP 200 with invalid JSON is not equivalent to transport uncertainty.
5. Compile the **actual pinned, patched upstream Java project**, run the Java mock proofs, build the actual standalone JAR, inspect required classes and checksum. Tests that only inspect strings are not enough.
6. For an image, verify provenance of the exact successful JAR artifact; build from immutable original base; verify the JAR bytes **inside** the image, image labels, runtime user and working directory. Publish a **new unique candidate tag only** and record its registry digest. Never overwrite a candidate or retag stable/test.
7. Create a **new** operator runner pinned to that image digest, retaining existing recovery/hold/preflight behavior. Mock success, fail-closed preflights, startup failure, status no-target, timeout, rollback failure, sanitizer mismatch, hold behavior, unexpected other-bot drift and stale Compose labels. CI must print checksums.
8. Document source/image/runner commits, CI URLs, SHA-256 and new owner approval gate. Stop here until explicitly authorized.

## 6. Owner-command protocol for a separately authorized trial

Only after full offline proof and fresh authorization:
- Give **one terminal copy-paste block**. First download scripts from an **exact Git SHA**, verify **SHA-256**, and run the operator script with sudo and the explicit `--execute-authorized-bot0-only` flag. Do not paste a long series of manual state-changing commands. Never ask the owner to execute raw, unreviewed Java or network code directly against Xbox.
- The script must perform fresh fail-closed checks for cleanup, updater, fleet state, original image, Compose isolation and Watchtower, then prepare the candidate.
- Change **Bot0 alone** using a private minimal Compose override; maintain the private Control Bot maintenance hold; one bounded one-shot console command; restore original exact digest in `finally` even on error.
- Collect only sanitized result and recovery lines. Require post-run owner confirmation of real-world Bot0 functionality before considering the trial closed.
- If preflight fails, **do not guess or repeatedly retry**. Identify the rejecting gate with a read-only, privacy-safe diagnostic first.

## 7. Not allowed to claim or infer

- "Cleanup is definitely still paused" from an old report. Say **"last observed paused"** and recheck fresh.
- "16/16 healthy now" from a prior timestamp. Describe exactly the time and source of last observation.
- "Xbox returned HTTP 404" from `list_other`. Exact code is **unknown**.
- "PersonSummary works" or "field names validated": there was **never a PersonSummary GET result** in the three live trials.
- "Production fully restored" from an image check without the owner's player-functionality confirmation.
- "Complete" when only CI source, but no JAR/image/runner or no actual test, has passed.
- "Will perform later/background" without an actual scheduled automation. Git docs and commands are synchronous handoff artifacts, not an active monitoring job.

## 8. Session wrap-up / handoff checklist

Before finishing a work session:
- Re-open canonical [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md) and [NEXT_STEPS](./NEXT_STEPS.md); update each with the verified latest state.
- Log exact Git commits, passing/failing GitHub Actions URLs, artifacts, what was **not** done, blockers, and any exposed operational risk.
- Include a single next concrete task for the new assistant; do not leave "proceed" ambiguous.
- Preserve STOP gates and approvals; avoid unnecessary repeated live trials.
- Give the user the canonical START_HERE GitHub URL for any new chat.
