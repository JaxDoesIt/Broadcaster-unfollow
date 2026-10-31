# Release 160 PersonSummary | NEXT STEPS AND TASK PATHWAY

Read [START_HERE](./START_HERE.md), [RULEBOOK](./RULEBOOK.md) and [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md) first.

## Immediate objective

Third owner-approved V3 test proved `fields=list_other` from one read-only friend-list GET, while Bot0 was restored and then independently confirmed functional. **Exact HTTP status is unknown.** The only legitimate next action without new owner permission is **offline investigation**.

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
- [ ] **Gate H (awaiting operator's fourth-trial output):** interpret exact outcome, update every canonical Git file, decide if PersonSummary validation can safely proceed. **No friend deletion or cleanup resume is implicit.**

## V4 completed source proof and active image gate

- Exact V4 source branch `fix/release160-friendlist-http-code-v4-2026-10-30`, commit `66cfa52ecfa51714220a8ef6c051e44018745ebb`.
- [Source/JAR CI run 41161780744](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41161780744): **SUCCESS**, 5,535 mocked Java assertions plus source patch and Python sanitizer tests, pinned upstream compilation and standalone JAR.
- Artifact `release160-friendlist-http-code-v4-proof-jar`, ID `13027806128`, ZIP SHA-256 `603980600ad6d0003ad5e4b7504a6f8346f13dfbea44a593694373201cb62686`. Do not conflate artifact ZIP hash with its internal JAR hash.
- V4 keeps the same one-GET URL, method, headers and no-redirect policy as V3. It changes only a privacy-bounded returned status label to `fields=list_http_NNN` for 100..499 excluding 200/401/403/429, with all other existing classifications preserved.
- **Superseded by the final offline readiness section below:** the V4 image and mocked runner both passed. The next open gate is separate owner approval for an actual fourth live trial.

## V4 final offline readiness: all tests passed; explicit live gate remains

**Gates A through F have been completed as OFFLINE work.** Official endpoint research, exhaustive exact-status classification, reproducible pinned Java/JAR proof, immutable image and a new mocked Bot0 rollback runner are recorded in [STATUS_AND_EVIDENCE](./STATUS_AND_EVIDENCE.md).

- Exact source/JAR proof [41161780744](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41161780744): **success**, 5,535 mocked Java assertions; source commit `66cfa52ecfa51714220a8ef6c051e44018745ebb`.
- Verified V4 immutable image [41162141697](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41162141697): **success**, candidate digest `sha256:4b39be565e373b5f6118716a85ec7bea8e4fab4f3bb967adba66e7b204f195ed`.
- Verified V4 owner operator [41162253916](https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41162253916): **success**, 25 offline mocks; exact script checksums documented in STATUS_AND_EVIDENCE.
- Gate E decision: public documentation and the previous redacted output **cannot determine** which actual HTTP code V3 saw. A single additional owner-approved, temporary Bot0-only, read-only trial with V4 can now distinguish the exact code. However it **does briefly interrupt Bot0 and may not by itself solve endpoint compatibility**. Do not run automatically.
- **Gate G owner authorization: COMPLETE.** The owner has now explicitly approved exactly one fourth Bot0-only V4 diagnostic. **Next is the operator's single checked Dell execution and interpretation**, followed by independent player functionality confirmation. If authorized, independently reverify live state and prepare a single checksummed command from the exact runner commit. The test allows at most one bounded friend-list GET plus one optional PersonSummary GET. After restoration, require independent player-functionality confirmation. Do **not** use the earlier V3 command or image.
- **Gate H remains pending:** exact HTTP code from a successful future test, endpoint/contract decision and any later PersonSummary evidence. No friendship deletion or cleanup resume.
- If the owner does not want another interruption, pause at this fully documented offline checkpoint. Continue only static research and mock tests.

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
