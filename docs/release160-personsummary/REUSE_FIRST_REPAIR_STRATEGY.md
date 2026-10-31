# Reuse-first Release160 repair strategy: port the proven system, adapt the interfaces

> **Status:** Source review and proposed engineering direction, **not a production authorization or completed fix**. Created in response to the owner's challenge: "If it worked before, why don't we just adapt what we built to Release160?" The answer is **yes, preserving the proven application logic should be the default**. A fourth live probe established PeopleHub list GET HTTP 400, but that is NOT a test of the removal endpoint. Bot0 was restored and owner confirmed it works. Cleanup remains paused.

## Distinct layers, critical difference

1. **MCGateway Control Bot** is the existing authoritative owner of assignment/capacity/count history/cleanup queue/anti-retry safeguards. **Retain and repair this source, do not rewrite the application.** Canonical private repository is `JaxDoesIt/MCGateway`; consult its `AGENTS.md`, `docs/CURRENT_STATE.md`, Release160 friend repair plan, and latest branch first.
2. **MCXboxBroadcast Release160** provides console commands, Xbox session tokens, endpoint bindings and SDK networking. **Update only the old Control Bot-to-broadcaster contract** and version-specific source integration while retaining Release160's new Minecraft connection/relay behavior.
3. **Xbox HTTP API** has several distinct surfaces: PeopleHub friend-list GET, `social.xboxlive.com/users/me/people/friends/v2/xuid(...)` friendship DELETE, social summary, and possible PersonSummary GET. **Success/failure of one does not prove another.** Do not infer that friend deletion is broken because the V4 list GET returned HTTP 400.

## Confirmed source changes/gaps

### Count pipeline

- Old Control Bot `index.js` uses `AUTO_FRIEND_COUNT_COMMAND=accounts list`, parses a legacy Friends/Followers/Following receipt, and integrates it with count scheduler, history, and `v44.onFriendCountUpdated()`.
- Pinned Release160 broadcaster `SessionManager.java` now prints account `Friends: <targetFriendCount>/<limit>`. The prior source audit found the legacy console delivery/response capture failed with `interrupted-by-command`, not just an incorrect integer parser. Therefore **fix both the console framing/receipt adapter and source of verified counts**, not just a regex.
- The existing separate count-producer/Control Bot observer development on `JaxDoesIt/MCGateway` and Broadcaster fork `mcgateway/release-160-friends-v3` already has strict source mocks and a built candidate; **reuse/audit this work instead of creating another independent producer**. It is source-only, not installed/authority. The SDK `targetFriendCount` wrapper must reject an error/absent value masquerading as zero.
- `v44.onFriendCountUpdated()` writes capacity and reclassifies overflow. Never feed unverified count output directly into production DB. Retain current capacity/history/assignments, preview deltas, and make authoritative admission a separate approved rollout.

### Friend removal pipeline

- Existing Control Bot `lib/v44-core.js` has dispatch queue, recent activity and assignment protection, durable intent, rate limits, uncertainty quarantine, console lease and receipt classifier, and `friends remove <XUID>` integration. **Preserve this application logic.** Historical success under Release154 does not certify the new console/remote protocol.
- Pinned Release160 upstream Java `FriendManager.java` still implements `remove()` and queues a `DELETE` request to `Constants.FRIEND = https://social.xboxlive.com/users/me/people/friends/v2/xuid(%s)`, declaring success for HTTP 200/204; however the exact semantics and real-world idempotency are not yet independently proven. Existing Release160 compatibility overlay deliberately **holds** expiry and friend-mutation paths, while the Control Bot's durable `release160CleanupBlockedOnDisk()` fence denies removal even if cleanup were unpaused.
- The four live read-only canaries examined **`GET https://peoplehub.xboxlive.com/users/me/people/friends`**, with the fourth V4 returning HTTP 400. That result does **not** establish whether the separate friend-removal DELETE endpoint would work; earlier effort overfocused on an indirect read path.
- Do not remove the fences to "see if it works" or blindly resend existing uncertain rows. No unique Xbox operation ID is included in older `friends remove` receipts. Existing cleanup attempts have uncertain history; full replay risks damaging friendships.
- **Desired adapter:** determine whether the Release160 console `friends remove` command and bounded completion signal still exist, then offline model delivery, HTTP 200/204, 400/401/403/404/429/5xx, duplicate commands, no-response, delayed response, stale previous receipt, and conflicting relationship state. Document direct change in semantics. Prefer a source-level, nonmutating observation of **relationship state before/after** only when independently justified and approved.

## Prioritized repair pathway: don't start from scratch

1. **Inventory old working pipeline vs Release160:** in the canonical private repo read previous known-good Control Bot cleanup/count contracts and latest Release160 upstream source. Create an exact matrix: component, old input/output, new input/output, breakage evidence, keep/adapter/rewrite decision. Baseline known-good old behavior through archived mocks, not through production rollback to an old Minecraft binary.
2. **Fix friend counts FIRST** as an independent non-destructive integration: reuse existing scheduler/history/safety gates; finish already-created Release160 `friendcountv2` and observer source, reconcile earlier CI fixture issues, prove bounded count/source completeness and console framing, then a supervised one-bot observational test only after separate approval. Do not activate authoritative capacity writes without DB backup and assignment delta checks.
3. **Repair removal adapter separately:** retain existing cleanup queue/selection/rate limits/protections; map old `friends remove` command onto Release160's actual command/remote API. Mock the exact success receipt and failure/uncertainty cases without any live DELETE. Design a trustworthy read-only postcondition independent of the broken PeopleHub list API, if possible. Never mistake command delivery/HTTP code for proof a specific account's relationship was removed.
4. **Minimize code changes:** a new narrowly scoped compatibility interface or parser is preferable to porting old Release154 runtime wholesale. Keep modern Release160 relay/transfer fixes, current Xbox SDK/auth data and existing Dell services. No broad refactor.
5. **Stage, verify, roll back:** source diff/CI on GitHub; immutable candidate and exact original image fallback; Bot0-only observational verification; explicit owner approval for any real membership mutation with backup, quarantine review and ability to restore/re-add; hard caps on trial.
6. **Only then consider cleanup resume:** explicit owner authorization after correct counts, relationship semantics, receipt/identity proof, worker gating, recent activity, uncertainty/quarantine, and rollback are all verified. Never unpause simply because GET/PersonSummary succeeds.

## Key technical nuance and honest conclusion

- **Confirmed:** Release160 changed `accounts list` display/console capture, and old Control Bot's count interface did not adapt; original Release160 Java still contains a friend removal DELETE method; the current production compatibility overlay intentionally disables its execution; HTTP400 read-only probe uses a different endpoint from removal and different HTTP client policies.
- **Unverified:** whether the old DELETE endpoint or console `friends remove` would still succeed unchanged on a real account, why PeopleHub GET returned HTTP 400, whether the full old/new relationship semantics are the same, and whether existing stale/uncertain cleanup rows can ever safely be retried.
- **Recommendation:** explicitly change the project's default approach to **"port old working MCGateway business logic to Release160 with narrow adapters, not rebuild it or spend repeated trials on indirect endpoints"**. Use diagnostics only to unblock a precise compatibility question.

**Owner-requested production boundary:** Source research, Git documentation and mocked tests are safe; no fifth live Bot0 trial, any friend mutation, cleanup resume, or production deployment is authorized.
