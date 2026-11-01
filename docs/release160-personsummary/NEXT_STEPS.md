# Release 160 PersonSummary | NEXT STEPS AND TASK PATHWAY

## 2026-11-01: Bot0-only canary authorized, actual Dell gate remains incomplete

Owner explicitly **authorized Bot0-only reversible trial**, nothing fleet-wide or friend-delete. The next owner-operated **read-only** host preflight showed 16/16 running, original Bot0 image ID `sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55` **MATCH**, original image present, Bot0 restartCount0, Compose project/service `mcgateway/mcgatewaybot-docker`, sole mount destination `/opt/app/config`, Control Bot active NRestarts0, Watchtower stopped, updater **paused** and both updater/staged rollout stages **complete**, 231.5 GiB free. But Bot0 maintenance marker is **NOT ACTIVE**, in-process cleanup/console lease drain **NOT VERIFIED**, and Compose's currently resolved image ref **does not equal** the actual container configured image (often mutable tag vs digest but not yet proven). Therefore **do not recreate Bot0 with bare Compose or direct Docker container synthesis**.

**NEXT safe action:** verify host Compose topology/reference differences without exposing source/env values; stage the already-published GHCR candidate by immutable digest with `docker pull` but do not start/recreate any container. Candidate index digest `sha256:21847ef429de7f5b80e31a6f8c7fa990a9b749a49a444bf68ecd96bec7c7fb39`; expected `linux/amd64` and provisional-only overlay labels. Then activate verified Bot0 maintenance marker, wait for in-process drain evidence, and use owner-authorized one-service override plus original image rollback. The restart/cleanup hold must be confirmed *active in installed Control Bot*, not merely source-present; actual data/credentials may not be overwritten. Keep other15 online, no cleanup resume, no capacity admission based on the Xbox social summary.


## 2026-11-01: VERIFIED SEALED NONPRODUCTION GHCR CANDIDATE, NEXT BOT0 APPROVAL

Independent job/log verification of [GitHub Actions run 41334127982](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41334127982) at source commit `e479c24a146227b8999468e50d4a55edb03ab1df`: job `124930223643` all steps green; pinned original upstream/overlay hashes, original expiry/removal holds, 146 strict mocked social-summary HTTP checks, old config compatibility and full standalone JAR build PASS; unique image tag preflight, Docker GHCR push and immutable digest check PASS. This is genuine **published candidate**, not installed production code.

**Registry tag:** `ghcr.io/jaxdoesit/mcgateway-broadcast:release-160-accounts-list-producer-e479c24a146227b8999468e50d4a55edb03ab1df`

**Verified OCI index digest:** `sha256:21847ef429de7f5b80e31a6f8c7fa990a9b749a49a444bf68ecd96bec7c7fb39`

**Digest-pinned candidate reference:** `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:21847ef429de7f5b80e31a6f8c7fa990a9b749a49a444bf68ecd96bec7c7fb39`

OCI index digest must not be confused with original Bot0 local `sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55` image ID. Candidate only changed the async account-list count response producer; source labels include `production-ready=false`, `count-evidence=provisional-only`, `overlay-variant=relay-audit-expiry-held-v2-accounts-list-producer-v1`.

Latest owner **read-only** host preflight before candidate build: 16/16 bots running, original Bot0 image available for rollback, Bot0 restarts0, Control Bot active, Watchtower stopped, disk 231.6 GiB free. This was historical at that check, not fresh after image push. **NEXT** reconfirm current status and approve exact one-bot rollback-controlled canary separately. A Bot0 recreate briefly interrupts that bot and must not change other 15, DB, updater/Watchtower, authoritative capacity, or cleanup. No new Xbox social API probe needed: existing paced `accounts list` checks can observe the producer after installation. Candidate may return `unavailable`, never false zero; real Xbox API semantics still unknown. Friend DELETE producer remains separately paused and unverified.


## November 1 owner rollback preflight and new candidate build source

Dell owner read-only preflight: all **16/16 bots running**, Bot0 original Release160 immutable image **sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55** available locally (and original historical image present), **0 restarts**, image overlay label `relay-audit-expiry-held-v2`, original source revision `f0da506d12074d5c99666d7a8ef0f73cdb6d6f58`; Control Bot active NRestarts0, Watchtower not running, disk free 231.6 GiB. No Dell modifications. This confirms rollback **availability**, not a guaranteed future state.

On isolated public branch `fix/release160-accounts-list-producer-unavailable-2026-10-31` added fifth file, source commit `e479c24a146227b8999468e50d4a55edb03ab1df`: `.github/workflows/release160-accounts-list-producer-image-candidate.yml`. Workflow builds original exact upstream and production expiry-held overlay with the strict read-only producer patch, tests 146 fake HTTP responses + config proof + full standalone JAR, pins reviewed source blobs, then attempts publishing only distinct GHCR `release-160-accounts-list-producer-<full workflow SHA>`, marks `production-ready=false`, refuses tag overwrite, records immutable pushed digest. It does not target existing stable/bot tags, Dell containers or friends. **Image workflow run outcome and digest not yet verified.**

**NEXT:** verify source SHA `e479c24...` candidate-image GitHub Actions push run and inspect actual job/digest; if red, repair source only. Do not perform a Bot0 recreate, new Xbox GET, Docker pull, or cleanup resume until separate narrowly scoped operator approval and final rollback/candidate identity check. Provisional count must never feed verified V4.4 capacity. Private canonical checklist: `JaxDoesIt/MCGateway:fix/release160-count-display-adapter-2026-10-31/docs/TODO.md`.


## October 31 producer source proof fully green, no live use

GitHub [source-only run 41247445897](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41247445897) at exact `ad0f0fe3a652940c8197618c5ee313bed631a3d9` completed **SUCCESS** and was independently inspected via job `124673710425` and decoded logs: pinned original `mcgateway/release-160-compat` source overlay reconstruction/safety PASS, Java compile PASS, **146 fake HTTP/zero/missing-field checks PASS**, config compatibility PASS, standalone classes PASS, BUILD SUCCESSFUL, no image built/pushed and zero live Xbox requests. Previous red `41246603544` (missing config proof class fixture) is superseded.

**Current actionable next step:** read-only current Dell Bot0 image/container identity and preserved immutable rollback image preflight; confirm Control Bot running, watchtower status and source-variant labels before considering a candidate build. The new patch's social summary count remains **non-authoritative**, actual Xbox endpoint and social schema remain unknown, and it has never been installed. Source path `fix/release160-accounts-list-producer-unavailable-2026-10-31`, from exact original production overlay, only 4 added source/CI files. Any one-bot install, Docker recreate, updater/watchtower change, Xbox diagnostic command, or cleanup unpause still requires separately scoped owner authorization. Do not call this a live repair yet.


## Latest exact CI continuation, October 31

- [x] Public producer CI run [41246603544](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41246603544), source SHA `562228cb42cd72e754d94791cbf8f7b375319a0c`: original Release160 variant proof PASS, core Java compile PASS, new mocked strict social-summary parser **146/146 PASS**. Existing Gradle config proof FAIL only because its fixture Java class was not copied, so standalone compilation was not reached. Not a demonstrated actual Xbox failure.
- [x] Corrected isolated public **workflow-only** commit `ad0f0fe3a652940c8197618c5ee313bed631a3d9` adds copy of original `ConfigCompatibilityProof.java` into the config proof source directory; production-pinned overlay, Java producer and deletion hold unchanged.
- [ ] **NEXT:** exact new Actions status/job/log for `.github/workflows/release160-accounts-list-producer-proof-ci.yml` on `fix/release160-accounts-list-producer-unavailable-2026-10-31`, commit `ad0f0fe3a652940c8197618c5ee313bed631a3d9`. Do not consider full compile/CI green without verified conclusion.
- [ ] If green, source-only privacy/safety review and rollback plan before independently owner-authorized Bot0-only trial; never activate cleanup or treat provisional count as authoritative from this source patch.


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
