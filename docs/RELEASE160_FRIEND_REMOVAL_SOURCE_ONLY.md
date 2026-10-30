# Release 160 friend-removal proof prototype

Status: **source-only, no production integration**.

The current MCGateway Release160 broadcaster explicitly denies `friends remove`; the Control Bot Release160 cleanup gate intentionally blocks removal dispatch for every upgraded bot. This work does not weaken either hold. The production cleanup queue remains paused.

## Prototype components

- `tools/release160/McgatewayFriendRemoveV160.java` is a standalone Java 21 policy with an injected `Transport`, not a real Xbox HTTP client. It models an exact-account and exact-target pre-read, follower-then-outgoing DELETE calls, and a *fresh* post-read proving both directions absent. It refuses to emit any terminal success frame when that postcondition is missing. HTTP 2xx and 404 DELETE results are tentative, **not** proof on their own.
- `tools/release160/McgatewayFriendRemoveV160Test.java` uses a fake transport. **167 assertions passed locally using Java 21**, including preexisting absent, partial delete, status 401/403/429/503, unknown/redirected/stale observations, account/session identity mismatch, interruption, deadline, consumed-nonce replay and same-thread re-entry.
- `.github/workflows/release160-friend-removal-source-only-ci.yml` is a source-only CI check; workflow status must be confirmed separately. Compiling this module does **not** make it available to the running standalone console.
- A matching controller-side, non-imported receipt-parser proposal exists at `JaxDoesIt/MCGateway` branch `fix/release160-cleanup-receipts-2026-10-30` in `tools/release160/remove-receipt-contract-v1.js`. Its 17 adversarial fixtures passed in an offline in-memory harness; GitHub Actions run status needs separate verification.

## Safety contract

The **controller** must independently authorize any future single-bot dispatch, hold an exact account/target membership fence under console lease, commit a durable intent, deny prior uncertain same-pair attempts, and include a unique nonce. The Java `Permit` is a *test input* and not authorization proof: a caller could construct it. No runtime code may treat its booleans as a credential or durable proof.

The **producer adapter**, which is NOT implemented yet, must prove that an authenticated and redirect-free Xbox read returns complete, current, specifically identified `incoming` and `outgoing` relationship booleans for the requested target and exact account. The adapter must enforce real elapsed timeouts, no cache, no unexpected pagination, a pinned account/session identity, and correct API field semantics. The pure prototype only consumes a `Snapshot` supplied by that future adapter and cannot vouch for real response semantics.

The **producer mutation fence** must stop upstream automatic following/re-following and other mutation actors across the whole authenticated session for the removal's full duration. The in-instance `AtomicBoolean` only prevents re-entry into this one Java object, not cross-process or cross-instance races. Its in-memory nonce ledger is strictly additive and fails closed at 4096 entries, but does not survive restart. Restart-resistant nonces/intents and uncertain reconciliation remain controller responsibilities.

The **removal result** can be `VERIFIED_REMOVED`, `VERIFIED_ALREADY_ABSENT`, `UNCERTAIN`, `UNVERIFIED`, `BUSY`, or `DENIED`. A remote request error after a DELETE might represent a partial Xbox mutation, so any post-dispatch failure is UNCERTAIN. Even a verified deletion does not authorize decrementing the exact friend count: incoming/outgoing states can differ from Xbox `isFriend`; a separate fresh authoritative recount is required.

## What remains before a live canary

1. Confirm Node and Java CI on their exact committed branches, retain complete immutable hashes.
2. Create a tested real Xbox HTTP adapter after validating the live Release160 read schema **without altering Xbox friends**. Test JSON shape, 200/404 distinction, two relationship directions, redirect absence, pagination, stale caches, auth/429/5xx and deadline handling.
3. Establish a real primary-session and cross-worker friend-sync fence and durable one-time nonce admission. Add executable rollback/protective kill switch, without disabling the legacy 160 block for general cleanup.
4. Integrate the separate controller receipt parser and producer logger with strict Docker log framing, dispatch intent and uncertain replay handling; prove the exact produced receipt matches the controller grammar end to end. Test crashes at every dispatch/receipt/commit boundary.
5. Only then request explicit owner approval for **one protected one-bot, one-target supervised removal** with independent proof of Xbox state, no effect on protected player access, and a rollback/reconciliation plan. Never start with the entire pending backlog or three parallel workers.

Nothing in this work updates stable/test tags, creates a production image, modifies the Control Bot service, touches Docker, accesses the live database or resumes friend cleanup.

## Oct 30: strict HTTP envelope validator and Microsoft schema discrepancy

New source-only files (NOT wired to the standalone logger, no real `HttpClient`):
- `tools/release160/McgatewayXboxRelationshipEnvelopeV160.java`, exact Git blob `03eaeb492723f45b4c8fc5f1c209d001cb6c255b`.
- `tools/release160/McgatewayXboxRelationshipEnvelopeV160Test.java`, exact Git blob `0ee6276e2166e068f30b184574eb004c10da5c05`.

JDK21 `javac` compiled the exact Git-identical files locally and the fake HTTP envelope suite PASSED **191** assertions; the earlier policy suite separately PASSED **167** assertions (**358** total). These do not make real Xbox HTTP calls. The existing GitHub Actions workflow now compiles/runs both sets; **CI status is not independently verified**.

The source-only `UnconnectedWireAdapter` receives fake typed response envelopes with explicit status, exact URI, account/session binding, no redirect, bounded body size, Content-Type, Content-Length consistency and cache indicators. Only a 200 Person object with exact target XUID AND **both actual Boolean** `isFollowingCaller` and `isFollowedByCaller` values is eligible for a syntactic snapshot. A missing or null flag, a 404, inconsistent type/identity, redirected response, ambiguous duplicate headers, stale/cache-hit or failed request yields no verified snapshot. DELETE 2xx/404 replies remain tentative and require a subsequent independently verified GET. This is structural validation over a **pre-decoded Map**, not a real strict JSON decoder or a provenance claim about the wire. The future real decoder must reject duplicate JSON keys, invalid encoding and unbounded JSON nesting; the real network adapter must enforce timeouts, redirection disabling, exact account credentials and body cap itself, not merely set Boolean flags.

**Important external schema blocker**: Microsoft Learn's GET `/users/{ownerId}/people/{targetid}` documentation describes a single Person response and 404 as target not found in owner's People list:
<https://learn.microsoft.com/en-us/xbox/gdk/docs/reference/live/rest/uri/people/uri-usersowneridpeopletargetidget?view=gdk-2604>.
Its Person JSON reference lists `isFollowingCaller` as **optional**, and does not guarantee an `isFollowedByCaller` field:
<https://learn.microsoft.com/fr-fr/xbox/gdk/docs/reference/live/rest/json/json-person?view=gdk-2510>.
Existing upstream `FriendStatusResponse` uses Java **primitive booleans**, which can collapse missing JSON booleans into false on model deserialization. Therefore a GET200 Person without both independently interpreted, explicitly present fields is **NOT proof of two-direction absence**. A GET404 is also NOT sufficient proof of both relationship directions. Other Xbox-related schemas sometimes carry both flags, but this does not establish they remain authoritative for Release160 on real accounts.

**NEXT SAFETY GATE**: design a separately owner-approved **read-only authenticated schema probe** that reports only field presence/type, response status, non-secret correlation and elapsed times, never raw tokens, gamer tags, XUIDs or response bodies. It must not issue DELETE or change the friend list. Before implementing live deletion, independently verify on the authenticated account whether both relationship directions can be observed with trustworthy semantics and fresh post-read behavior; if not, develop a different verified read-only postcondition, not a guessed false default. No one-bot deletion canary or auto-cleanup until this is proven.

