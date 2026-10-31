# Release 160: Xbox friend-list / PersonSummary diagnostic | START HERE

**Canonical handoff entrypoint for new ChatGPT/Codex sessions.** Read this file and all linked documents in order **before inspecting, changing or executing anything**.

> **Status at last operator report (2026-10-30 CDT / 2026-10-31 UTC):** Three explicitly approved, isolated **Bot0-only** live diagnostics have been run. The third produced `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=list_other can_authorize_removal=false`. Its runner reported successful restoration of Bot0's **original immutable Release 160 image**, removal of the private maintenance hold, and continued cleanup pause. **The owner subsequently confirmed Bot0 was functional for players.** **V4 exact HTTP-status diagnostic is fully prepared and mock-tested offline** (source/JAR, immutable image, and Bot0 rollback runner all passed). **The owner has now explicitly approved exactly one fourth V4 Bot0-only trial. No fourth trial output has been received or independently verified yet.**

## Read in this order

1. **[RULEBOOK.md](./RULEBOOK.md)**: nonnegotiable safety, execution limits, approvals, exact source/recovery proof, Git workflow, and the standard of testing.
2. **[STATUS_AND_EVIDENCE.md](./STATUS_AND_EVIDENCE.md)**: verified results of every live trial; latest proven state; exact image digests, source commits, CI run IDs, and uncertainty.
3. **[NEXT_STEPS.md](./NEXT_STEPS.md)**: active research pathway and prioritized, testable next tasks. Continue from the **first unchecked gate**; do not skip directly to another live restart.
4. **[ENDPOINT_RESEARCH.md](./ENDPOINT_RESEARCH.md)**: official Microsoft people/summary REST docs compared against pinned upstream endpoints and unresolved compatibility questions.
5. **[CROSS_REPO_MAP.md](./CROSS_REPO_MAP.md)**: links the separate private MCGateway Control Bot, friend-count and cleanup sources, with independent approval gates.
6. **[HANDOFF_TO_NEW_CHAT.md](./HANDOFF_TO_NEW_CHAT.md)**: copyable handoff text and how another assistant should recover context directly from this Git branch.
7. **[Historical chronological checkpoint](../release160-personsummary-canary-image-checkpoint-2026-10-30.md)**: older cumulative findings and experimental states. **Some sections are historical** (e.g., "not deployed" or "awaiting approval" before completed trials). When in conflict, this START_HERE and the current STATUS_AND_EVIDENCE take precedence.

## Goal

Diagnose the Release 160 Xbox friendship relationship semantics and **prove, without risking players or friendships**, which Xbox GET endpoint and response fields can safely support downstream MCGateway friend-cleanup correctness. The current narrower blocker: the GET-only friend-list probe returned **`list_other`**, a grouped non-200 HTTP status. Its exact HTTP status is unknown. PersonSummary schema was never observed in any of the three trials. **No friendship deletion is justified.**

## Production boundary

- Dell Ubuntu machine controls a 16-bot MCGateway Xbox/Bedrock fleet, with one live Nodecraft Bedrock Hub. GitHub connectors can change Git **but cannot operate the Dell**; the owner runs one self-contained copy-paste command at a time when explicitly approved.
- Friend cleanup is intentionally **paused**; updater paused; Watchtower stopped at the last reported preflight. Future state **must be rechecked**, not assumed persistent.
- The original immutable Bot0 Release 160 rollback image is `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`. Stable/test tags are **not** rollback identities.
- The other 15 bots and existing production Control Bot must not be modified, restarted, or interrupted by diagnostic work.
- Do not trigger friend removals, unpause cleanup, mutate Xbox relationships, change Compose originals, rotate credentials, or promote experimental test images.
- **Every separate Bot0 live interruption requires explicit owner authorization for its exact scope**, even after an offline artifact is ready. One fourth V4 Bot0-only diagnostic has now been explicitly approved; it is not a standing authorization for retries or further trials.

## Git branch topology

| Role | Branch / commit | Meaning |
|---|---|---|
| **Canonical living runbook** | `docs/release160-personsummary-continuation-2026-10-30` | This file, rules, evidence, next steps, handoff. Update here whenever facts, decisions, CI state or blockers change. |
| Cumulative historical checkpoint | `build/release160-readonly-friendcache-canary-2026-10-30` | [Prior detailed checkpoint](../release160-personsummary-canary-image-checkpoint-2026-10-30.md); may contain old stage statements. |
| Last proven V3 Java source | `fix/release160-friendlist-status-diagnostic-2026-10-30`, commit `04d7ae5906a50bcd8923813f76dcc4521ffea72a` | Exact bounded list GET/status helper, one-shot PersonSummary helper, existing friend-mutation denials; source-only proof CI. |
| Last proven V3 image and Dell runner | `build/release160-friendlist-status-v3-2026-10-30`, runner commit `0af042dcedc85a92e21fd9181e0c0a400923e7a6` | Exact-image V3 canary and mock-tested Bot0 rollback script. **Do not rerun unchanged.** |
| Current V4 exact-status source proof | `fix/release160-friendlist-http-code-v4-2026-10-30`, commit `66cfa52ecfa51714220a8ef6c051e44018745ebb` | 5,535 mocked Java assertions, full pinned JAR build and sanitizer proof. |
| Current V4 immutable image and mocked runner | `build/release160-friendlist-http-code-v4-2026-10-30`, operator commit `614f7611f945dc75b579eea128cdcbbc403f35bf` | Verified image digest `sha256:4b39be565e373b5f6118716a85ec7bea8e4fab4f3bb967adba66e7b204f195ed`; 25 mocked operator tests. **NOT DEPLOYED.** |

## Default continuation behavior

**If user says "proceed":** read the linked documents, verify Git refs/CI and proceed with safe **offline-only** review, research or documentation. **V4 source, image and rollback runner are already completely mock-proven.** The owner has **explicitly approved one fourth temporary Bot0-only V4 test**. Use only the exact verified execution command described in STATUS_AND_EVIDENCE; do not treat "proceed" as approving any repeat, deployment promotion or cleanup change. Prefer proof over repetition, and label findings as confirmed, inferred, or unresolved.

**If user pastes Dell command output:** interpret exactly; distinguish Docker recovery from independent real-world Xbox/Hub functionality; update evidence and the next gate; never claim an Xbox HTTP status that the sanitized output does not provide.

**New-chat starting point:** open this URL:
https://github.com/JaxDoesIt/Broadcaster-unfollow/blob/docs/release160-personsummary-continuation-2026-10-30/docs/release160-personsummary/START_HERE.md

_This is a Git documentation pathway, not a scheduled job or a standing permission to touch production._
