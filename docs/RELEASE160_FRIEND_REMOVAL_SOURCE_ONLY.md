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



## Oct30: Official PersonSummary two-direction alternative, 455 offline assertions

Microsoft's GDK docs for **GET /users/{ownerId}/summary** state the owner can be `xuid(target)` while the authenticated caller is a separate account. The returned **PersonSummary** JSON documents both `isCallerFollowingTarget` and `isTargetFollowingCaller` as Boolean values:
- <https://learn.microsoft.com/en-us/xbox/gdk/docs/reference/live/rest/uri/people/uri-usersowneridsummaryget?view=gdk-2604>
- <https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/live/rest/json/json-personsummary?view=gdk-2604>

Unlike a legacy Person GET whose `isFollowingCaller` field is optional and does not guarantee the outgoing direction, PersonSummary offers a plausible exact target relation observation. It is **not yet real Xbox-tested** on MCGateway accounts and may have authorization/response differences. The summary body does **not** contain a signed target XUID; target association needs a strict HTTPS requested/final URI and actual authenticated account binding. A social SDK's `isFollowingCaller` value can be a backward-compatibility alias of `isFriend`, which is a further reason not to conflate Person and PersonSummary fields. Read the actual response and fail closed if either explicit field is missing, untyped, contradictory or unverifiable.

Committed exact locally compiled Git blobs:
- `tools/release160/McgatewayXboxSummaryReadOnlyV160.java` = `0917a726b25e9e58be54b58a82db4745576d8b3e`
- `tools/release160/McgatewayXboxSummaryReadOnlyV160Test.java` = `3ddf22a12baf723febe2d2ed74726ab790907a9c`

The **fake only** Java summary adapter consumes an injected `Wire` and never uses `HttpClient`, tokens, real Xbox requests or production code. It rejects wrong caller/target/session URI, malformed/missing/duplicated headers, stale/redirected/incomplete results, 404/401/403/429/503, missing/null/non-Boolean directions, ambiguous pagination, and mismatched Content-Length. It supports two-direction fake pre/post observations and intentional simulated DELETEs in its deterministic fixture harness; the live Xbox friend-removal command remains explicitly DENIED.

Actual local Java21 compilation of all **six** test/source files: previous **167 + 191** assertions, plus **97** summary assertions, **455 total PASS**, exact fetched source hashes match `git hash-object`. CI workflow updated to run all three suites, **run conclusion not independently verified**. Do NOT present the existence of an artificial `Reply.boundAccount` field or `networkFresh` test flag as proof of real HTTP binding or freshness. The source still needs a strict raw JSON decoder and a verified real authenticated **GET-only** probe before any production command integration or canary. Never expose tokens, XUIDs, profile data, raw JSON bodies or Discord names in probe output.

The next realistic deployment-independent step is to prepare a strictly bounded, source-only authenticated read probe design with exact request allowlist, no credentials in command args/logs, transport TLS/no-redirect enforcement and response-shape-only output. A live GET on any production bot would require separate owner approval. No auto-unpause.


## Oct30: offline-only schema probe committed with sanitized field-shape output

Files:
- `tools/release160/xbox_summary_schema_probe.py` Git blob `ba983986892e6228d220f54657a6ac0a5b35e552`.
- `tools/release160/test_xbox_summary_schema_probe.py` Git blob `aa7549576f57367b2ab7a48eea3310ccf44bf237`.

These exact committed bytes were compared against local `git hash-object` and validated with `python3 -B test_xbox_summary_schema_probe.py`: **6 unittest groups PASS**. They supplement, but do not replace, the previous **455 Java fake-HTTP assertions**. The GitHub workflow `release160-friend-removal-source-only-ci.yml` was expanded to run the Python suite; its Actions run status has NOT been independently verified.

The offline-only Python module imports **no socket, HTTP, subprocess or credential libraries**, provides NO real network client or token loader, and cannot issue a real Xbox GET/DELETE by itself. `offline_probe` accepts an externally injected fake callback solely for synthetic tests. The request is fixed to one GET `https://social.xboxlive.com/users/xuid(target)/summary`, with narrow identity/session/timeout/redirect/cache attributes. It rejects invalid IDs, unsafe method/URI settings, untrusted HTTP status/redirect/account/session metadata, cached/incomplete responses, oversized or non-UTF8 payloads, missing/mismatched content-length, duplicate and malformed headers, duplicate JSON keys (including nested keys), NaN, excessive JSON depth/node counts, and missing/untyped relationship flags. It reports **only** the HTTP status class, schema outcome and two field **types**, not values, targets, account XUIDs, tokens, full JSON or exception text. Even `typed_both_fields` returns `can_authorize_removal: false` and `real_xbox_provenance: false`, because the injected metadata cannot attest a real Xbox session.

Important current limitation: official GDK People URI documentation describes an older service context, including platform applicability restrictions; the existence of the documented PersonSummary field names is NOT proof that a modern MCXboxBroadcast Release160 authenticated account can call this endpoint with the same semantics. Do not treat API documentation or fake response flags as live validation. A future real transport must pin TLS endpoint and authenticated Xbox account, disable redirects, bound raw response and wall time, prevent any non-GET egress and log only sanitized report. Obtain **separate owner approval before any real authenticated request**. The current `friends remove` DENIED patch and Control Bot cleanup gate remain intact. No Docker/build/publish/DB mutation and no cleanup resume.
