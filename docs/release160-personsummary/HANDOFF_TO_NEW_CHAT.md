# Hand off this project to a new ChatGPT or Codex chat

The canonical entrypoint is:

**https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md**

This branch was deliberately created so a new assistant can start from **Git without needing the previous chat's memory**. All verified trial results, safety constraints, actual hashes, CI references and the next research gates are written in linked documents. GitHub's connected app can read these files and inspect branches/actions; it cannot operate the Dell directly.

## Paste this prompt into the next chat

> Pick up my MCGateway Release160 Xbox friend-list / PersonSummary diagnostic from Git. Start at:
>
> https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md
>
> Read that page AND its RULEBOOK.md, STATUS_AND_EVIDENCE.md, NEXT_STEPS.md, ENDPOINT_RESEARCH.md and HANDOFF_TO_NEW_CHAT.md in full. Also consult the historical checkpoint if you need details.
>
> Treat Git as the source of truth. Audit current relevant branch state and successful CI, maintain the safety gates, and continue only **authorized and incomplete gates** in NEXT_STEPS. The exact-status V4 offline source, immutable image and rollback runner are already fully proven, so do not repeat them. Update the canonical docs as you finish work. Don't mistake historical "waiting for approval" stages for the current status.
>
> V4 is now prepared offline: source/JAR CI `41161780744` (5,535 mocked Java assertions), immutable image CI `41162141697` (exact digest `sha256:4b39be565e373b5f6118716a85ec7bea8e4fab4f3bb967adba66e7b204f195ed`), and mock operator CI `41162253916` (25 tests). No fourth live test has been approved or executed. All source, image and runner hashes are in STATUS_AND_EVIDENCE.
>
> There were **three** owner-approved temporary Bot0-only live trials. Each restored the original immutable Release160 Bot0 image. The third returned `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_other can_authorize_removal=false`, and I confirmed **Bot0 is functional for players after that third rollback**.
>
> Friend cleanup remains intentionally paused at the last observed check. Do not delete/accept/add Xbox friends, unpause cleanup, restart the fleet, change the other 15 bots, or touch the original Compose config. Do not print account IDs, auth tokens or raw response bodies. No fourth live test is authorized. An ordinary "proceed" authorizes Git/offline work, not a production interruption.
>
> I want rigorous mock/offline testing, independent identity/digest verification, adversarial review, clear Git checkpoints, and one copy-paste Dell terminal command only when a specific live action is separately approved. Preserve an exact original-image rollback and stop on any failed recovery.
>
> The current task is **Gate G**: V4 can now reveal the precise protocol HTTP status that V3 grouped into `list_other`, but a fourth Bot0 interruption has NOT been approved. If the owner specifically authorizes a fourth trial, independently reverify preflight and use only the exact pinned V4 scripts and image listed in STATUS_AND_EVIDENCE. Otherwise continue public/static analysis and documentation only. Mark exactly what is and is not verified.

## Retrieval and continuity rules

- Use the GitHub connection to fetch exact content. If GitHub connector is unavailable, follow the public file links in a browser.
- The branch in the URL is **not the default `master` branch**. Do not accidentally open the README on master and conclude the runbook does not exist.
- Source and test files are on separate `fix/` and `build/` branches. Resolve any uncertain ref through Git history or the exact links/commit SHAs listed in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).
- The canonical docs branch is the place to write **status, rulebook and next steps**. V4 exact-code source and CI are already proven on `fix/release160-friendlist-http-code-v4-2026-10-30`; the matching image and operator runner are proven on `build/release160-friendlist-http-code-v4-2026-10-30`. For further changes use a NEW isolated `fix/` branch.
- Give the user a short, grounded status: current state, what you verified, next action, and risks. Do not dump confidential raw output. Do not offer asynchronous work without a real task scheduler.
- Keep documentation self-contained: future chats should not require accessing old conversations or guessing which trial is current.

## Why this exists

Previous work uncovered that the pinned Release160 upstream friend-list GET did not establish HTTP status, and the first two trials both returned `no_cached_target`. The third improved V3 probe classified an unexpected HTTP status as `list_other` while restoring Bot0 safely. The next assistant should **solve that narrower blocker**, not rebuild the entire bot fleet or restart friend cleanup.
