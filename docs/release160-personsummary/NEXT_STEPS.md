# Release 160 PersonSummary | NEXT STEPS AND TASK PATHWAY

## Latest October 31 repair and next exact CI gate

- [x] Two owner **read-only** log inspections now showed repeated `accounts list` and Loading on Bot0/1/2, but no recognized result/errors. Second scan read **both stdout and stderr**, classified labels only, no private identifiers and no new Xbox command or GET.
- [x] Upstream Release160 `SessionManager.listSessions()` logs Loading synchronously and buffers the rest in an unguarded scheduled worker. A failed/null/non-200 social summary **can** abort or yield invalid count, but exact live response/error remains unknown.
- [x] On separate public production-variant base `fix/release160-accounts-list-producer-unavailable-2026-10-31` added 4 **new-only source files** for bounded strict HTTP200 count field parsing, sanitized unavailable receipt, guarded patch preserving old friend-expiry/removal holds, and Java21 mocked compile workflow. Workflow commit `562228cb42cd72e754d94791cbf8f7b375319a0c`. No runtime changes.
- [ ] **NEXT:** independent GitHub Actions status/logs for `.github/workflows/release160-accounts-list-producer-proof-ci.yml` on branch above; fix CI if red. Do NOT deploy until pinned baseline compile and mock tests pass.
- [ ] Consider owner-approved observational canary only after safety/rollback/digest review; do not perform a fifth live trial solely to reproduce known PeopleHub HTTP 400.
- [ ] Keep friend count **provisional**. Source output fixes cannot itself establish genuine Xbox friendship truth for capacity; friend cleanup remains paused pending independent two-direction verified removal receipts and explicit one-target approval.


Read [START_HERE](./START_HERE.md), [RULEBOOK](./RULEBOOK.md) and [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md) first.

## Cross-repository implementation handoff (October 31, newer than V4-only tasks)

The private MCGateway source-only fastpath advanced beyond the V4 endpoint investigation:
- Old Release154 vs. Release160 count/cleanup contract matrix completed under `docs/operations/RELEASE160_FRIEND_CONTRACT_MATRIX_2026-10-31.md`.
- Standalone **non-authoritative** Release160 `accounts list` primary-session parser plus four locally green fake-log test groups are committed on private branch `fix/release160-count-display-adapter-2026-10-31`. Exact hashes and safety gates live in its `docs/operations/RELEASE160_ACCOUNTS_LIST_DISPLAY_ADAPTER_2026-10-31.md`. No production wiring; original three CI runs were verified FAILURE because of a bad test import, fixed in commit `0bed60acad70179b0d1f53c9b001258f4b92cf43`. Corrected test bytes passed 4/4 locally; new CI still unverified.
- Additional source-only PeopleHub HTTP 400/page-window fail-closed proof exists on public branch `fix/release160-friendcount-pagination-proof-2026-10-31`. GitHub Actions result unknown. Do not deploy.
- **Highest-priority next check:** obtain fresh GitHub Actions run ID/status/logs for those exact workflows, fix any red CI, and independently validate only sanitized genuine `accounts list` output shape before wiring display-only on an isolated branch. Source-only tests do not establish true Xbox count, so do not update confirmed capacity or cleanup.
- This is a *count repair* continuation, not permission to repeat the V4 PeopleHub test or bypass any original Bot0 rollback/cleanup gate.


**October 31 CI verification:** [Broadcaster source-only run 41244399850](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41244399850) at commit `0545880830bd9ea2241a9b167d2df3b59b7d132d` completed **SUCCESS**. Connected GitHub confirmed job `124664707435`, pinned Java21 count/config fake tests and standalone compilation succeeded. No image was promoted and no Xbox GET was executed by this workflow.

## Verified CI update (October 31, latest)

The private MCGateway display-only parser CI [run 41245456281](https://github.com/JaxDoesIt/MCGateway/actions/runs/41245456281) at corrected test-import commit `0bed60acad70179b0d1f53c9b001258f4b92cf43` completed **SUCCESS**. Independent job `124667827492` and logs confirm safety guard + **4/4 Node mocked log-frame tests PASS**. The three earlier red runs were all a wrong relative test import, now superseded. Public Broadcaster run `41244399850` at `0545880830bd9ea2241a9b167d2df3b59b7d132d` remains **SUCCESS** with pinned Java source mocks + standalone build.

**Next is not more fake CI:** safely inspect existing sanitized (no player identifiers) real Release160 `accounts list` Docker log frames for timestamp/ANSI/INFO/order, with NO new bot command or Xbox request. Only then source-stage **provisional display** wiring may be considered. Neither green CI means friend count is confirmed accurate, authoritative capacity update is permitted, or friend cleanup may resume. Follow private `fix/release160-count-display-adapter-2026-10-31` `docs/CURRENT_STATE.md`, `docs/TODO.md` and `docs/operations/RELEASE160_ACCOUNTS_LIST_DISPLAY_ADAPTER_2026-10-31.md`.

## Immediate objective

Fourth owner-approved V4 test returned **friend-list HTTP 400 Bad Request** on the exact original PeopleHub friends endpoint. The runner verified original Bot0 restoration and hold clearance; the owner separately confirmed real player functionality. The *HTTP status* is known; the *reason* is unknown. No fifth live trial is approved. Continue only offline analysis of the exact request and service contract.

## Checklist, in dependency order

- [x] Establish canonical documentation pathway, source-of-truth, rulebook and complete handoff.
- [x] Preserve exact three-trial evidence, safe restoration and owner's latest Bot0 functional confirmation.
- [x] **Gate A: inspect V3 source and official endpoint documentation (offline).** See [ENDPOINT_RESEARCH.md](./ENDPOINT_RESEARCH.md). The pinned V3 GET targets `peoplehub.xboxlive.com/users/me/people/friends` (contract version 7), while Microsoft's documented caller people collection is `social.xboxlive.com/users/me/people`. No authenticated live request was made and this contrast does **not** prove an endpoint migration.
- [x] **Gate B: implement narrow exact/bucketed HTTP result labeling offline.** Add a new source-only `fix/` branch based on pinned V3 commit `04d7ae5906a50bcd8923813f76dcc4521ffea72a`. Preserve original exact upstream, expiry hold and all V2 mutation guards. Modify only the V3 friend-list status classifier and the controlled sanitizer. Examples: `list_http_400`, `list_http_404`, `list_http_405`, `list_http_410`, `list_http_204`, `list_redirect`/specific 3xx, `list_client_other`, `list_success_other`, `list_other`. Use a finite fixed allowlist, **never** print a dynamic response body or headers.
- [x] **Gate C: comprehensive isolated tests.** Fake one-GET HTTP statuses (each allowlisted exact code, uncommon/unexpected codes, 200 success/invalid, auth, rate limit, 5xx, transport, 3xx with disabled redirects), input bounds and output redaction. Verify sanitizer rejects unknown statuses and forbids `can_authorize_removal=true`. Strict source-patch drift guards, no PUT/POST/DELETE path and preserved nonmutating canary gates.
- [x] **Gate D: pinned Java compilation and reproducible JAR source proof.** Run full upstream compatibility patch + prior GET-only helpers + new scoped change on `MCXboxBroadcast/Broadcaster@798d8b3a6107359643b525f1c9c3303c020ae09b`, with source hashes, fake HTTP proof and full standalone JAR. New unique GitHub Action run must be **green**. Document the exact run SHA and artifact digest.
- [x] **Gate E: decide if a fourth live trial is even necessary.** Prefer valid read-only evidence from public docs, CI, non-sensitive provider metadata, or a safer existing controlled context. Compare possible endpoint changes and scope. Do **not** jump to a fourth Bot0 interruption if only the same status is likely.
- [x] **Gate F (conditional): prepare immutable image and new mock-tested Bot0 runner** only if further real-world evidence is necessary and worth a short Bot0 interruption. Use original image at immutable digest and one new unique canary tag/digest; preserve prior image identity, single-service Compose override, paused cleanup and original restoration; unit-test changes.
- [x] **Gate G (separate explicit owner authorization):** show the proposed trial's purpose, bounded GET count and Bot0 interruption; only then provide one checksum-verified Dell terminal command. Await sanitized result and independent post-restore player functionality.
- [x] **Gate H (fourth trial executed and interpreted):** interpret exact outcome, update every canonical Git file, decide if PersonSummary validation can safely proceed. **No friend deletion or cleanup resume is implicit.**

## V4 completed source proof and active image gate

- Exact V4 source branch `fix/release160-friendlist-http-code-v4-2026-10-30`, commit `66cfa52ecfa51714220a8ef6c051e44018745ebb`.
- [Source/JAR CI run 41161780744](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41161780744): **SUCCESS**, 5,535 mocked Java assertions plus source patch and Python sanitizer tests, pinned upstream compilation and standalone JAR.
- Artifact `release160-friendlist-http-code-v4-proof-jar`, ID `13027806128`, ZIP SHA-256 `603980600ad6d0003ad5e4b7504a6f8346f13dfbea44a593694373201cb62686`. Do not conflate artifact ZIP hash with its internal JAR hash.
- V4 keeps the same one-GET URL, method, headers and no-redirect policy as V3. It changes only a privacy-bounded returned status label to `fields=list_http_NNN` for 100..499 excluding 200/401/403/429, with all other existing classifications preserved.
- **Superseded by the final offline readiness section below:** the V4 image and mocked runner both passed. Historical note: that fourth trial has now executed, so the current gate is offline HTTP400 contract analysis.

## V4 final offline readiness: all tests passed; explicit live gate remains

**Gates A through F have been completed as OFFLINE work.** Official endpoint research, exhaustive exact-status classification, reproducible pinned Java/JAR proof, immutable image and a new mocked Bot0 rollback runner are recorded in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).

- Exact source/JAR proof [41161780744](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41161780744): **success**, 5,535 mocked Java assertions; source commit `66cfa52ecfa51714220a8ef6c051e44018745ebb`.
- Verified V4 immutable image [41162141697](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41162141697): **success**, candidate digest `sha256:4b39be565e373b5f6118716a85ec7bea8e4fab4f3bb967adba66e7b204f195ed`.
- Verified V4 owner operator [41162253916](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41162253916): **success**, 25 offline mocks; exact script checksums documented in STATUS_AND_EVIDENCE.
- Gate E decision: public documentation and the previous redacted output **cannot determine** which actual HTTP code V3 saw. A single additional owner-approved, temporary Bot0-only, read-only trial with V4 can now distinguish the exact code. However it **does briefly interrupt Bot0 and may not by itself solve endpoint compatibility**. Do not run automatically.
- **Gate G and fourth-trial execution: COMPLETE.** Trial 4 returned `fields=list_http_400`, followed by `RECOVERY VERIFIED`; the owner confirmed Bot0 works for players. This approval is consumed. No automatic repeat or fifth test.
- **Gate H remains pending:** exact HTTP code from a successful future test, endpoint/contract decision and any later PersonSummary evidence. No friendship deletion or cleanup resume.
- If the owner does not want another interruption, pause at this fully documented offline checkpoint. Continue only static research and mock tests.

## STRATEGY PIVOT: reuse old working count/cleanup, don't rebuild it

The owner challenged the overly narrow PersonSummary/PeopleHub diagnostic emphasis. Source review confirmed this was warranted: **the fourth GET HTTP400 is on a distinct URL from the existing Release160 friend-removal DELETE**, and older count and cleanup application logic remains in private Control Bot source. See [REUSE_FIRST_REPAIR_STRATEGY.md](./REUSE_FIRST_REPAIR_STRATEGY.md) for the prioritized plan and factual evidence.

**Current highest-priority offline gate:** create an exact old Release154 versus Release160 contract matrix covering command input, output, delivery framing, Xbox endpoint, result/receipt semantics, count history, cleanup protection, and adaptation steps. Audit/reuse the existing Release160 `friendcountv2` producer and Control Bot observer before developing any new redundant diagnostic. Do not move immediately to a fifth PeopleHub GET test. Preserve all cleanup, backup, and owner-permission fences.

## ACTIVE NEXT WORK after fourth trial: explain HTTP 400, offline first

1. **READ-ONLY SOURCE DIFFERENTIAL: COMPLETED.** Pinned original upstream `FriendManager.get()` and V4 have identical GET/URI/Authorization source/contract version 7, but different headers (original `Accept-Language: en-GB`, V4 `Accept: application/json` and `Cache-Control: no-store`). **Additionally, original shared client is Methanol HTTP/1.1, redirects NORMAL, request timeout default 5s. V4 uses separate plain Java HttpClient, redirects NEVER, Java default HTTP/2 preference, request timeout 7s.** This is code-verified only; 400 cause remains unknown. Details in [ENDPOINT_RESEARCH](./ENDPOINT_RESEARCH.md).
2. **OFFICIAL CONTRACT REVIEW:** The Microsoft-documented read-only collection is `social.xboxlive.com/users/me/people`, while pinned upstream uses `peoplehub.xboxlive.com/users/me/people/friends`. Microsoft's 400 definition for its **social** API mentions malformed query parameters/user IDs but does **not** establish why the different PeopleHub endpoint replied 400. See [ENDPOINT_RESEARCH](./ENDPOINT_RESEARCH.md).
3. **MOCKED REQUEST-PARITY GATE (not yet implemented):** Build a source-only, offline audit/testing path that checks GET method, fixed URI, version header, locale/Accept/cache policy, no redirects, single network request, XSTS header never logged, and existing friend-mutation denials. Prefer a change with one causal variable at a time. No new image/runner until a concrete hypothesis is prioritized and fake tests pass.
4. **PAGINATION/SEMANTIC SAFETY:** Any alternate social collection API with `totalCount`/paging requires no-partial-list-as-empty tests. A successful GET still cannot authorize cleanup.
5. **FIFTH LIVE GATE:** A new, specific owner authorization is required even if an offline candidate is built. A trial must not silently change endpoints plus multiple headers, follow redirects, retry, disclose response body, or touch other 15 bots. Prove exact rollback and owner-confirmed functionality after it.
6. **CURRENT PRODUCTION STATUS:** Last owner report confirms Bot0 working; cleanup paused at fourth preflight/recovery. Do not interpret this as a fresh live check on subsequent dates. Nothing was changed in production after this report.

## Hypotheses to investigate, not yet facts

| Hypothesis | Evidence currently available | Nonmutating way to check |
|---|---|---|
| The endpoint returns HTTP 404 or 410 | V3 `list_other` can contain them, but does not identify either. | Add exact allowlisted label and mock proof. Investigate official endpoint documentation. |
| The endpoint expects different query headers/contract version | The pinned upstream uses `peoplehub.xboxlive.com/users/me/people/friends` with `x-xbl-contract-version: 7`; another public Xbox API family uses `social.xboxlive.com`. | Read official docs and pinned upstream declarations. Never switch endpoints or headers blindly on production. |
| A redirect occurred | V3 client disables redirects and groups 3xx as `list_other`. | Classify 3xx via status without following `Location` or printing it. |
| Unexpected 2xx or 4xx | All non-200 2xx and non-auth/non-rate-limit 4xx can produce `list_other`. | Finite status allowlist for single HTTP reply. |
| Bot0 lacks friends | Unproven: neither trial 1 nor 2 established a successful HTTP 200 friends list. | Only accept as fact after a verified valid HTTP 200 complete `people=[]` response. |
| Friend-list API needs a separate grant / user context | Unproven; `list_other` is not 401 or 403 as classified by the V3 probe. | Check official docs, authentication contract and fail-safe test output. |

## Decisions and stop gates

> [!CAUTION]
> **Stop immediately** if any task proposes actual relationship mutations, logs secrets/player identities, touches other 15 bots, resumes friend cleanup, alters stable/test labels, or performs live Xbox requests without explicit new permission.

- **HIGH:** Player interruption, relationship mutation, unrelated container changes, token leak, destructive cleanup, rollback uncertainty. Requires redesign or explicit approval; cannot be accepted as an optional optimization.
- **MEDIUM:** Incomplete diagnostics, unreliable status classification, failing mocks/CI, unverified artifact provenance. Resolve offline before live.
- **LOW:** Naming, formatting or redundant documentation. May be corrected independently.

**Owner's preference:** Deep review and adversarial stress tests; challenge existing systems and recommend safe removals when redundant; do not declare a section done because a few tests passed. Prefer one reliable implementation over layers of redundant fallbacks.

## How to log progress

After each meaningful finding:
1. Update this checklist on the canonical docs branch.
2. Update [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md): observed fact, source, uncertainty, CI URL, commit, exact artifact. Never replace a missing result with an inference.
3. Update [RULEBOOK](./RULEBOOK.md) only if the procedure/guard changes. Preserve safety invariants.
4. Give owner a concise summary of **what is complete, what remains, and whether the Dell changed**.
5. Leave one exact next task in this document. If CI is running at the end of a turn, record its run ID and state and say it is incomplete.

## Safe branch hygiene

- Living docs: `docs/release160-personsummary-continuation-2026-10-30`
- Last verified V3 source: `fix/release160-friendlist-status-diagnostic-2026-10-30` at full commit `04d7ae5906a50bcd8923813f76dcc4521ffea72a`
- Last verified V3 image and runner: `build/release160-friendlist-status-v3-2026-10-30` at `0af042dcedc85a92e21fd9181e0c0a400923e7a6`
- Proposed next source branch: `fix/release160-friendlist-http-code-v4-2026-10-30` (create from known V3 proof SHA, and record its actual created base).
- **Do not modify GitHub `master` for this investigation without a separate reason and explicit permission.**

No unattended automations or changes to the Dell are part of this pathway.

## October 31 existing-log discovery: count producer may fail before emitting output

A privacy-sanitized read-only Docker logs sample from Bot0/1/2 displayed repeated `accounts list` prompt plus `Loading status of sessions...`, but **none** of the expected `Primary Session:`, `Friends: N/1000` or `No sub-sessions` results in stdout. This is not proof the Xbox endpoint failed: initial filter omitted stderr and only accepted strict INFO framing. The exact upstream `SessionManager.listSessions()` logs Loading synchronously then runs `scheduledThreadPool.execute`: `socialSummary().targetFriendCount()` must complete before *any* result lines are logged, and that worker has no enclosing try/catch. Source-level null/non-200 handling is incomplete; an exception may stop that task silently. **Next action**: read-only sanitized classify both Docker streams for count frames/errors and timestamps, no new console command, GET, bot restart, cleanup unpause or source deployment. On missing results, prioritize *producer* error/response repair over wiring an output parser. Details and explicit no-action gates: private `JaxDoesIt/MCGateway:fix/release160-count-display-adapter-2026-10-31`, `docs/CURRENT_STATE.md`.
