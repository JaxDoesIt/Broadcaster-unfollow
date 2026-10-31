# Hand off this project to a new ChatGPT or Codex chat

The canonical entrypoint is:

**https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md**

This branch was deliberately created so a new assistant can start from **Git without needing the previous chat's memory**. All verified trial results, safety constraints, actual hashes, CI references and the next research gates are written in linked documents. GitHub's connected app can read these files and inspect branches/actions; it cannot operate the Dell directly.

## Paste this prompt into the next chat

> Pick up my MCGateway Release160 Xbox friend-list / PersonSummary diagnostic from Git. Start at:
>
> https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md
>
> Read that page AND its RULEBOOK.md, STATUS_AND_EVIDENCE.md, NEXT_STEPS.md, ENDPOINT_RESEARCH.md, CROSS_REPO_MAP.md and HANDOFF_TO_NEW_CHAT.md in full. Also consult the historical checkpoint if you need details.
>
> Treat Git as the source of truth. Audit current relevant branch state and successful CI, maintain the safety gates, and continue only **authorized and incomplete gates** in NEXT_STEPS. The exact-status V4 offline source, immutable image and rollback runner are already fully proven, so do not repeat them. Update the canonical docs as you finish work. Don't mistake historical "waiting for approval" stages for the current status.
>
> The **fourth V4 live trial was completed**. Result: `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_http_400 can_authorize_removal=false`. The runner reported exact original Bot0 image rollback and hold clearance; I independently confirmed Bot0 is functional after this fourth rollback. The specific HTTP 400 cause is still unknown. Source/JAR CI `41161780744`, image CI `41162141697`, and operator-mock CI `41162253916` were already green. **No fifth trial is approved.**
>
> There were **three** owner-approved temporary Bot0-only live trials. Each restored the original immutable Release160 Bot0 image. The third returned `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_other can_authorize_removal=false`, and I confirmed **Bot0 is functional for players after that third rollback**.
>
> Friend cleanup remained paused in the fourth trial. Do not add/remove friends, unpause cleanup, restart the fleet, change other 15 bots, touch original Compose, or show tokens/IDs/raw responses. **The fourth-trial authorization was consumed**; `proceed` allows offline work only, not a fifth test.
>
> I want rigorous mock/offline testing, independent identity/digest verification, adversarial review, clear Git checkpoints, and one copy-paste Dell terminal command only when a specific live action is separately approved. Preserve an exact original-image rollback and stop on any failed recovery.
>
> The current task is offline investigation of the actual **HTTP 400**. Compare the original upstream `FriendManager.get()` request with V4's GET: the original includes `Accept-Language: en-GB`, V4 does not; V4 adds `Accept: application/json` and `Cache-Control: no-store`. Also compare the different Microsoft-documented social endpoint. These are hypotheses only. Update Git docs with grounded findings, source-only tests and no production modifications.

## Updated engineering direction after owner challenge

The project direction is now **reuse the old proven application architecture and adapt only changed Release160 interfaces**. Read [REUSE_FIRST_REPAIR_STRATEGY.md](./REUSE_FIRST_REPAIR_STRATEGY.md) before building another standalone probe. Friend-count refresh had a known `accounts list`/console framing mismatch; the original cleanup command and Control Bot queue logic still exist. The fourth HTTP400 came from PeopleHub GET, **not** the separate social friendship DELETE endpoint. First make an old/new compatibility matrix and continue the existing source-only friend-count proof project in the private MCGateway repo; only research PeopleHub further if it directly unblocks the selected adapter. No production action is authorized.

## Retrieval and continuity rules

- Use the GitHub connection to fetch exact content. If GitHub connector is unavailable, follow the public file links in a browser.
- The branch in the URL is **not the default `master` branch**. Do not accidentally open the README on master and conclude the runbook does not exist.
- Source and test files are on separate `fix/` and `build/` branches. Resolve any uncertain ref through Git history or the exact links/commit SHAs listed in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).
- The canonical docs branch is the place to write **status, rulebook and next steps**. V4 exact-code source and CI are already proven on `fix/release160-friendlist-http-code-v4-2026-10-30`; the matching image and operator runner are proven on `build/release160-friendlist-http-code-v4-2026-10-30`. For further changes use a NEW isolated `fix/` branch.
- Give the user a short, grounded status: current state, what you verified, next action, and risks. Do not dump confidential raw output. Do not offer asynchronous work without a real task scheduler.
- Keep documentation self-contained: future chats should not require accessing old conversations or guessing which trial is current.

## Why this exists

Previous work uncovered that the pinned Release160 upstream friend-list GET did not establish HTTP status, and the first two trials both returned `no_cached_target`. The third improved V3 probe classified an unexpected HTTP status as `list_other` while restoring Bot0 safely. That V3 blocker was solved by V4: **HTTP 400 confirmed**. The next assistant should research why, not rebuild the fleet or restart cleanup.
