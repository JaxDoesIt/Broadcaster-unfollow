# Xbox people/PersonSummary endpoint research | PUBLIC DOCUMENTATION VS PINNED CODE

**Scope:** Offline public-documentation review only. No Xbox account token, authenticated API request, Dell access or Bot0 restart was used.

Research date: 2026-10-30 CDT / 2026-10-31 UTC. Microsoft docs show last-updated date 2025-11-06 on the cited public reference pages. Their content may require sign-in for some readers; keep public URLs as source references.

## Verified from pinned project's source (not necessarily an official Xbox contract)

1. **Pinned upstream:** `MCXboxBroadcast/Broadcaster@798d8b3a6107359643b525f1c9c3303c020ae09b`.
2. `core/.../Constants.java` declares `FRIENDS=https://peoplehub.xboxlive.com/users/me/people/friends`.
3. Original upstream `FriendManager.get()` uses a GET of `Constants.FRIENDS`, Xbox contract version `7`, plus authorization and `accept-language: en-GB`. The original code checked/parses the response body without checking HTTP status. The V3 helper uses the same URI and version 7, with a bounded body, `Accept: application/json` and disabled redirect following.
4. Third live V3 result: `fields=list_other`. V3 source's branch applies only to a returned HTTP status outside {200,401,403,429,500..599}; actual code is unknown. A different endpoint cannot be justified solely by this result.
5. The PersonSummary GET helper targets `https://social.xboxlive.com/users/xuid(<target>)/summary` with contract version 3. It has **never produced a live schema response**, because no valid friend target was selected.

## Verified from official Microsoft documentation

- [Microsoft GDK: GET (/users/{ownerId}/people)](https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/live/rest/uri/people/uri-usersowneridpeopleget?view=gdk-2604) documents the **caller people collection** at `social.xboxlive.com`, path `/users/{ownerId}/people` where owner may be `me`. The page describes GET as read-only, a returned `people` array and `totalCount`, and possible 200, 400 and 403 responses. It documents query parameters `view`, `startIndex`, `maxItems`, so a partial page must not be mistaken for a complete snapshot.
- That page lists the Xbox authorization header and an optional `X-RequestedServiceVersion` (default 1). It does **not** establish that the **different** `peoplehub.xboxlive.com/users/me/people/friends` route is retired, equivalent or supported with these same headers.
- [Microsoft GDK: GET (/users/{ownerId}/summary)](https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/live/rest/uri/people/uri-usersowneridsummaryget?view=gdk-2604) documents `isCallerFollowingTarget` and `isTargetFollowingCaller` as response fields in a `PersonSummary` example, with documented 200, 400 and 403 statuses. A public example is **not** proof of this field shape or any relationship values in the user's live account.
- [Microsoft GDK: GET (/users/{ownerId}/people/{targetid})](https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/live/rest/uri/people/uri-usersowneridpeopletargetidget?view=gdk-2604) documents an individual people-relationship resource and possible 404 when a target is not found. This is **not** a definitive 404 explanation for the different friend-list collection endpoint.
- **Unverified:** no authoritative current reference was established in this review specifically documenting the pinned `peoplehub.xboxlive.com/users/me/people/friends` request's 2026 behavior or response code. It may be supported, gated, deprecated, or other; do not assert any one.

## Recommended next diagnostic decision

1. Retain the exact current `peoplehub` URL and version-7 request for the **first exact-status diagnostic patch**, to isolate the unknown variable. Any endpoint/contract/header change becomes a distinct experiment and requires independent source/CI proof.
2. In the offline patch, map a valid returned HTTP status integer to a finite, allowlisted `fields=list_http_NNN` marker when the status is not already mapped to success/auth/rate-limit/server. It reveals only a protocol status code, not a player identity, token, response body or private header. The Python sanitizer must reject statuses outside the allowlist.
3. Fake-test `list_http_400`, `list_http_404`, `list_http_302`, `list_http_204`, etc., and all unknown/error/malformed cases. No network traffic in tests.
4. Once actual code is established, examine a **narrow** compatible read-only endpoint only if Microsoft docs and the failure mode support it. If public `social` people-list GET is proposed in the future, it is a new endpoint with distinct pagination, response-shape and XUID protections, and a separate approval. No hidden dual-GET fallback on live Bot0.
5. Preserve `can_authorize_removal=false` until a separate cleanup contract/receipt review. A PersonSummary field name alone does not authorize relationship modifications.

**Attribution:** The Git repository's pinned source supports the implementation facts; the Microsoft Learn links support the official documented endpoints/status/shape. The gap between them is a research finding, **not** an automatically validated migration.
