# Hand off this project to a new ChatGPT or Codex chat

The canonical entrypoint is:

**https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md**

This branch was deliberately created so a new assistant can start from **Git without needing the previous chat's memory**. All verified trial results, safety constraints, actual hashes, CI references and the next research gates are written in linked documents. GitHub's connected app can read these files and inspect branches/actions; it cannot operate the Dell directly.

## Paste this prompt into the next chat

> Pick up my MCGateway Release160 Xbox friend-list / PersonSummary diagnostic from Git. Start at:
>
> https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md
>
> Read that page AND its RULEBOOK.md, STATUS_AND_EVIDENCE.md, NEXT_STEPS.md and HANDOFF_TO_NEW_CHAT.md in full. Also consult the historical checkpoint if you need details.
>
> Treat Git as the source of truth. Audit current relevant branch state and successful CI, maintain the safety gates, and continue the **first unfinished offline step** in NEXT_STEPS. Update the canonical docs as you finish work. Don't mistake historical "waiting for approval" stages for the current status.
>
> There were **three** owner-approved temporary Bot0-only live trials. Each restored the original immutable Release160 Bot0 image. The third returned `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_other can_authorize_removal=false`, and I confirmed **Bot0 is functional for players after that third rollback**.
>
> Friend cleanup remains intentionally paused at the last observed check. Do not delete/accept/add Xbox friends, unpause cleanup, restart the fleet, change the other 15 bots, or touch the original Compose config. Do not print account IDs, auth tokens or raw response bodies. No fourth live test is authorized. An ordinary "proceed" authorizes Git/offline work, not a production interruption.
>
> I want rigorous mock/offline testing, independent identity/digest verification, adversarial review, clear Git checkpoints, and one copy-paste Dell terminal command only when a specific live action is separately approved. Preserve an exact original-image rollback and stop on any failed recovery.
>
> First task: determine which **actual HTTP status** is hidden inside `list_other` without another blind repeat, and investigate endpoint compatibility safely. See NEXT_STEPS for the ordered tasks. Before claiming success, prove the source patch, mocked status/privacy cases, Java compilation, JAR and, only if appropriate, a separate image and runner. Mark exactly what you did and did not verify.

## Retrieval and continuity rules

- Use the GitHub connection to fetch exact content. If GitHub connector is unavailable, follow the public file links in a browser.
- The branch in the URL is **not the default `master` branch**. Do not accidentally open the README on master and conclude the runbook does not exist.
- Source and test files are on separate `fix/` and `build/` branches. Resolve any uncertain ref through Git history or the exact links/commit SHAs listed in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).
- The canonical docs branch is the place to write **status, rulebook and next steps**. New V4 source/CI changes should live on a new isolated `fix/` branch.
- Give the user a short, grounded status: current state, what you verified, next action, and risks. Do not dump confidential raw output. Do not offer asynchronous work without a real task scheduler.
- Keep documentation self-contained: future chats should not require accessing old conversations or guessing which trial is current.

## Why this exists

Previous work uncovered that the pinned Release160 upstream friend-list GET did not establish HTTP status, and the first two trials both returned `no_cached_target`. The third improved V3 probe classified an unexpected HTTP status as `list_other` while restoring Bot0 safely. The next assistant should **solve that narrower blocker**, not rebuild the entire bot fleet or restart friend cleanup.
