# Release 160: Xbox friend-list / PersonSummary diagnostic | START HERE

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


## Latest October 31 producer build failure and workflow correction

The producer source-only Actions run `41246603544` at `562228cb42cd72e754d94791cbf8f7b375319a0c` **failed**, but its pinned original-overlay preflight passed; patched Java `:core:compileJava` passed; the new fake social summary test reported **146 checks passed**. Failure occurred in the *preexisting config compatibility task* `:core:mcgatewayConfigCompatibility` with `ClassNotFoundException: ...ConfigCompatibilityProof`: the CI workflow forgot to copy that original proof file. The task stopped before standalone compilation could be verified.

Corrected **workflow only**, no producer source changes, commit `ad0f0fe3a652940c8197618c5ee313bed631a3d9` on public `fix/release160-accounts-list-producer-unavailable-2026-10-31`. It now copies `overlay/tools/release160/ConfigCompatibilityProof.java` to `upstream/core/src/mcgatewayProof/java/com/rtm516/mcxboxbroadcast/core/configs/` before Gradle. **Fresh CI conclusion still unknown.** Next: verify new push-triggered workflow run for exact fixed commit, fetch job/errors if red, no image/production changes or Xbox calls.


## Latest October 31 producer repair branch, not deployed

The owner supplied a second **read-only stdout+stderr** Docker log audit of three production bots: Bot0/1/2 had respectively **4/12/12** `accounts list` commands and same count `Loading status of sessions...` frames, with **no recognized primary-session, friend-count, completed result, or known error frames**. This narrows the observed break to async producer response generation or logging, not Control Bot command delivery; exact Xbox failure remains unknown.

The pinned upstream Release160 `SessionManager.listSessions()` logs Loading first, then runs `scheduledThreadPool.execute`. Inside that worker it gathers `socialSummary().targetFriendCount()` before logging any result lines, with no catch/always-final status marker. `SessionManagerCore.socialSummary()` does not check HTTP status, field presence or non-null body. A swallowed exception is plausible, not confirmed.

**New focused public branch:** `JaxDoesIt/Broadcaster-unfollow:fix/release160-accounts-list-producer-unavailable-2026-10-31`, created from exact deployed-image source baseline `mcgateway/release-160-compat`. Four **new source-only files** add strict fake-tested social-summary response parsing, explicit sanitized unavailable receipt on failure, a source/production-overlay pinning patcher, and pinned Java21 build CI. Workflow source commit `562228cb42cd72e754d94791cbf8f7b375319a0c`. **New GitHub Actions CI not yet verified**. Importantly: the actual original overlay and any live image, Control Bot, DB, cleanup, friend mutation path all remain unchanged. Do not treat a provisional count as exact or let it change capacity.

**Next:** Verify `release160-accounts-list-producer-proof-ci.yml` Actions run for the new public branch and inspect logs if failed; repair only source, then evaluate an approved one-bot diagnostic/deployment pathway separately. Private updated canonical recovery notes: `JaxDoesIt/MCGateway:fix/release160-count-display-adapter-2026-10-31` at `docs/CURRENT_STATE.md` and `docs/TODO.md`.


**Canonical handoff entrypoint for new ChatGPT/Codex sessions.** Read this file and all linked documents in order **before inspecting, changing or executing anything**.

> **LATEST, October 31 2026 CDT:** Four authorized **Bot0-only** live trials were completed. The fourth V4 probe returned `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_http_400 can_authorize_removal=false`, proving that the **friend-list GET received HTTP 400 Bad Request**; it does **not** reveal the error reason. The runner verified original immutable Bot0 image restoration and maintenance-hold clearance; the owner independently confirmed **Bot0 works for players afterward**. Cleanup was still paused at recovery. **All fourth-trial approval is spent. No fifth trial is authorized.**

## Latest continuation (October 31, source-only)

The dedicated private MCGateway fastpath has now completed the old/new contract matrix and created a newer **display-only Release160 `accounts list` parser**, based on the already-existing upstream command, rather than promoting the three-GET PeopleHub count candidate. The source-only adapter is on private `JaxDoesIt/MCGateway:fix/release160-count-display-adapter-2026-10-31`, with details in `docs/operations/RELEASE160_ACCOUNTS_LIST_DISPLAY_ADAPTER_2026-10-31.md` and updated `docs/CURRENT_STATE.md` / `docs/TODO.md` on that branch. Initial Control Bot CI ran three times and failed before assertions due to a wrong self-test relative import. A corrected test was committed in private MCGateway at `0bed60acad70179b0d1f53c9b001258f4b92cf43`. The exact corrected JS/test blobs were independently executed locally, 4/4 PASS; new corrected-import push CI is still **unverified**. This parser is **NOT installed, wired into Control Bot, or authoritative for capacity or cleanup**.

The upstream `SessionManager.listSessions()` prints `Friends: N/1000` from `socialSummary().targetFriendCount()`, but upstream does not strictly verify HTTP status or missing count fields, so the candidate explicitly refuses zero and marks positive counts provisional. The public `friendcountv2` 3-GET candidate's additional HTTP400/page-hint source-only tests are on `fix/release160-friendcount-pagination-proof-2026-10-31`, also **CI UNVERIFIED**. Do not infer the actual candidate endpoint returned 400 or that either candidate can be deployed.

**New-chat default:** Continue from the private latest branch's documentation for the count/display repair, while retaining this public V4 rulebook as the separate Xbox request/rollback diagnostic evidence. Next is independent CI status proof and review of sanitized real log framing, then a fresh isolated nonauthoritative integration gate. No fifth trial, no production modification, no friend removal or cleanup unpause is authorized.


**October 31 CI verification:** [Broadcaster source-only run 41244399850](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41244399850) at commit `0545880830bd9ea2241a9b167d2df3b59b7d132d` completed **SUCCESS**. Connected GitHub confirmed job `124664707435`, pinned Java21 count/config fake tests and standalone compilation succeeded. No image was promoted and no Xbox GET was executed by this workflow.

## Verified CI update (October 31, latest)

The private MCGateway display-only parser CI [run 41245456281](https://github.com/JaxDoesIt/MCGateway/actions/runs/41245456281) at corrected test-import commit `0bed60acad70179b0d1f53c9b001258f4b92cf43` completed **SUCCESS**. Independent job `124667827492` and logs confirm safety guard + **4/4 Node mocked log-frame tests PASS**. The three earlier red runs were all a wrong relative test import, now superseded. Public Broadcaster run `41244399850` at `0545880830bd9ea2241a9b167d2df3b59b7d132d` remains **SUCCESS** with pinned Java source mocks + standalone build.

**Next is not more fake CI:** safely inspect existing sanitized (no player identifiers) real Release160 `accounts list` Docker log frames for timestamp/ANSI/INFO/order, with NO new bot command or Xbox request. Only then source-stage **provisional display** wiring may be considered. Neither green CI means friend count is confirmed accurate, authoritative capacity update is permitted, or friend cleanup may resume. Follow private `fix/release160-count-display-adapter-2026-10-31` `docs/CURRENT_STATE.md`, `docs/TODO.md` and `docs/operations/RELEASE160_ACCOUNTS_LIST_DISPLAY_ADAPTER_2026-10-31.md`.

## Read in this order

1. **[RULEBOOK.md](./RULEBOOK.md)**: nonnegotiable safety, execution limits, approvals, exact source/recovery proof, Git workflow, and the standard of testing.
2. **[STATUS_AND_EVIDENCE.md](./STATUS_AND_EVIDENCE.md)**: verified results of every live trial; latest proven state; exact image digests, source commits, CI run IDs, and uncertainty.
3. **[NEXT_STEPS.md](./NEXT_STEPS.md)**: active research pathway and prioritized, testable next tasks. Continue from the **first unchecked gate**; do not skip directly to another live restart.
4. **[ENDPOINT_RESEARCH.md](./ENDPOINT_RESEARCH.md)**: official Microsoft people/summary REST docs compared against pinned upstream endpoints and unresolved compatibility questions.
5. **[CROSS_REPO_MAP.md](./CROSS_REPO_MAP.md)**: links the separate private MCGateway Control Bot, friend-count and cleanup sources, with independent approval gates.
6. **[HANDOFF_TO_NEW_CHAT.md](./HANDOFF_TO_NEW_CHAT.md)**: copyable handoff text and how another assistant should recover context directly from this Git branch.
7. **[Historical chronological checkpoint](../release160-personsummary-canary-image-checkpoint-2026-10-30.md)**: older cumulative findings and experimental states. **Some sections are historical** (e.g., "not deployed" or "awaiting approval" before completed trials). When in conflict, this START_HERE and the current STATUS_AND_EVIDENCE take precedence.

**Current engineering priority:** [REUSE_FIRST_REPAIR_STRATEGY.md](./REUSE_FIRST_REPAIR_STRATEGY.md) explains why we should adapt the working Release154 friend-count and cleanup application to Release160 using narrow adapters, rather than assume the HTTP400 on a different read-only endpoint means removal is broken. The next step is a source-only old/new contract matrix and reuse of existing Release160 count-proof work. No production changes or fifth trial are approved.

## Goal

Diagnose the Release 160 Xbox friendship relationship semantics and **prove, without risking players or friendships**, which Xbox GET endpoint and response fields can safely support downstream MCGateway friend-cleanup correctness. The current narrower blocker: the fourth GET-only friend-list probe definitively returned **HTTP 400 Bad Request**, but the reason and supported request contract are unknown. PersonSummary schema was never observed in any of the three trials. **No friendship deletion is justified.**

## Production boundary

- Dell Ubuntu machine controls a 16-bot MCGateway Xbox/Bedrock fleet, with one live Nodecraft Bedrock Hub. GitHub connectors can change Git **but cannot operate the Dell**; the owner runs one self-contained copy-paste command at a time when explicitly approved.
- Friend cleanup is intentionally **paused**; updater paused; Watchtower stopped at the last reported preflight. Future state **must be rechecked**, not assumed persistent.
- The original immutable Bot0 Release 160 rollback image is `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`. Stable/test tags are **not** rollback identities.
- The other 15 bots and existing production Control Bot must not be modified, restarted, or interrupted by diagnostic work.
- Do not trigger friend removals, unpause cleanup, mutate Xbox relationships, change Compose originals, rotate credentials, or promote experimental test images.
- **Every separate Bot0 live interruption requires explicit owner authorization for its exact scope**, even after an offline artifact is ready. The fourth V4 trial has already executed and the operator confirmed Bot0 recovered for players; no fifth trial, retry, cleanup change or promotion is authorized.

## Git branch topology

| Role | Branch / commit | Meaning |
|---|---|---|
| **Canonical living runbook** | `docs/release160-personsummary-continuation-2026-10-30` | This file, rules, evidence, next steps, handoff. Update here whenever facts, decisions, CI state or blockers change. |
| Cumulative historical checkpoint | `build/release160-readonly-friendcache-canary-2026-10-30` | [Prior detailed checkpoint](../release160-personsummary-canary-image-checkpoint-2026-10-30.md); may contain old stage statements. |
| Last proven V3 Java source | `fix/release160-friendlist-status-diagnostic-2026-10-30`, commit `04d7ae5906a50bcd8923813f76dcc4521ffea72a` | Exact bounded list GET/status helper, one-shot PersonSummary helper, existing friend-mutation denials; source-only proof CI. |
| Last proven V3 image and Dell runner | `build/release160-friendlist-status-v3-2026-10-30`, runner commit `0af042dcedc85a92e21fd9181e0c0a400923e7a6` | Exact-image V3 canary and mock-tested Bot0 rollback script. **Do not rerun unchanged.** |
| Current V4 exact-status source proof | `fix/release160-friendlist-http-code-v4-2026-10-30`, commit `66cfa52ecfa51714220a8ef6c051e44018745ebb` | 5,535 mocked Java assertions, full pinned JAR build and sanitizer proof. |
| Current V4 immutable image and mocked runner | `build/release160-friendlist-http-code-v4-2026-10-30`, operator commit `614f7611f945dc75b579eea128cdcbbc403f35bf` | Verified image digest `sha256:4b39be565e373b5f6118716a85ec7bea8e4fab4f3bb967adba66e7b204f195ed`; 25 mocked operator tests. **Trialed once, then restored to original image. NOT PROMOTED.** |

## Default continuation behavior

**If user says "proceed":** read the linked documents, verify latest Git refs and CI, then continue **offline request-contract/HTTP400 differential investigation and mock tests**. Do NOT rerun V4, restart Bot0, unpause cleanup or change production without separate, specific owner permission. The fourth V4 trial is finished and its authorization is spent.

**If user pastes Dell command output:** interpret exactly; distinguish Docker recovery from independent real-world Xbox/Hub functionality; update evidence and the next gate; never claim an Xbox HTTP status that the sanitized output does not provide.

**New-chat starting point:** open this URL:
https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md

_This is a Git documentation pathway, not a scheduled job or a standing permission to touch production._

## October 31 existing-log discovery: count producer may fail before emitting output

A privacy-sanitized read-only Docker logs sample from Bot0/1/2 displayed repeated `accounts list` prompt plus `Loading status of sessions...`, but **none** of the expected `Primary Session:`, `Friends: N/1000` or `No sub-sessions` results in stdout. This is not proof the Xbox endpoint failed: initial filter omitted stderr and only accepted strict INFO framing. The exact upstream `SessionManager.listSessions()` logs Loading synchronously then runs `scheduledThreadPool.execute`: `socialSummary().targetFriendCount()` must complete before *any* result lines are logged, and that worker has no enclosing try/catch. Source-level null/non-200 handling is incomplete; an exception may stop that task silently. **Next action**: read-only sanitized classify both Docker streams for count frames/errors and timestamps, no new console command, GET, bot restart, cleanup unpause or source deployment. On missing results, prioritize *producer* error/response repair over wiring an output parser. Details and explicit no-action gates: private `JaxDoesIt/MCGateway:fix/release160-count-display-adapter-2026-10-31`, `docs/CURRENT_STATE.md`.
