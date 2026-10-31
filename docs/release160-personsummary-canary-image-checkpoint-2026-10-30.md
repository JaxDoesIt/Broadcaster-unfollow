# Release 160 PersonSummary GET canary: image prepared, deployment held

Date: 2026-10-30 CDT / 2026-10-31 UTC

## Verified source and image proof
- Original successful source/standalone JAR run: https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41148699197
- Reviewed source-proof commit: `631dabaea778f910cb776d0b5bd01593fdf64468`
- JAR artifact: ID `13022465794`, digest `sha256:f6d6b384e8ab5cd56042bd6f5a29921bb57b810094dc83cf5e6427c1d4087c3d` (artifact ZIP digest, not JAR digest)
- Source proof: original upstream `798d8b3a6107359643b525f1c9c3303c020ae09b` plus original `relay-audit-expiry-held-v2` overlay and only the GET-only PersonSummary diagnostic
- CI: 229 fake HTTP assertions, source patch fixture tests, Gradle build, standalone JAR content and checksum checks passed

## Candidate image (registry only, NOT deployed)
- Image-build branch: `build/release160-personsummary-canary-2026-10-30`
- Image workflow commit: `f59a2531206ae04ff8f7192bd2719a36367368d1`
- Successful image run: https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41149193785
- Candidate tag: `ghcr.io/jaxdoesit/mcgateway-broadcast:release-160-personsummary-get-canary-20261031-631daba`
- Candidate exact digest: `sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1`
- Original base tag: `ghcr.io/jaxdoesit/mcgateway-broadcast:release-160-relay-audit-expiry-held-v2`
- Original base exact digest: `sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`
- Baseline image labels verified: revision `f0da506d12074d5c99666d7a8ef0f73cdb6d6f58`, upstream SHA `798d8b3a6107359643b525f1c9c3303c020ae09b`, variant `relay-audit-expiry-held-v2`
- Built from baseline digest by replacing only `/opt/app/MCXboxBroadcastStandalone.jar`; image JAR checksum matched the original tested JAR; app was never started by this CI
- The workflow only writes the unique candidate tag. Registry-wide immutability is not asserted: pin any future test or recovery by the exact digest.

## Owner-witnessed Bot0 read-only identity gate (PASSED)
- Operator's latest local `docker inspect` report: `org.opencontainers.image.revision` = MATCH; `io.mcgateway.upstream-sha` = MATCH; `io.mcgateway.overlay-variant` = MATCH.
- Local `RepoDigests` includes original base digest `sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`: MATCH.
- Bot0 container reports `running=True`, `OOMKilled=False`, `RestartCount=0` at inspection.
- Read-only inspection only. This is an operator-reported local snapshot, not a live GitHub CI test. No implication about uptime, network connectivity, or Xbox schema is made.
- Remaining before any approved Bot0-only canary: recoverable container config/runtime reconstruction, supervisor and watchtower behavior, health baseline, and a separate explicit deployment authorization. Friend cleanup must remain paused.

## Operator Bot0 Compose management preflight (PASSED; reconstruction still held)
- Operator-provided local Docker inspect: Bot0 `running=True`, restart policy `unless-stopped`, `AutoRemove=False`, user `app:app`, workdir `/opt/app/config`, network `mcgateway_default`.
- One read/write bind mount at container target `/opt/app/config`; its host-side source was deliberately not disclosed.
- Docker Compose labels present. Control Bot systemd service `active/running`; Watchtower container `running=False`.
- Read-only observation; no proof that Compose files/env are intact, no reconstruction test, and no proof Control Bot will ignore a planned Bot0-only deployment.
- Before deployment: validate the Compose project/service source-file presence, effective service identity, and isolation of a Bot0-only change, without logging environment values or mount sources; then obtain a separate explicit live-test approval.

## Operator Compose reconstruction preflight (VALIDATED; no changes)
- `com.docker.compose.project` and `com.docker.compose.service` present; Bot0 service is `mcgatewaybot-docker`.
- Compose project directory and one declared Compose file exist. `docker compose config --format json` validated and returned the expected service.
- Effective service has container name `mcgatewaybot-docker`, restart policy `unless-stopped`, one config bind mount, one network, zero `depends_on`, one environment entry, and no entrypoint/command override.
- Effective service `user` is DEFAULT, while existing runtime image user was previously shown as `app:app`: not a contradiction, since the image supplies the user when Compose omits it.
- **Risk requiring special handling:** Compose image reference is TAG_OR_VARIABLE, not a digest pin. Do not rely on resolving that tag for rollback; use exact original registry digest `sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`, and candidate digest `sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1` only.
- This was read-only; no live service was stopped/recreated, no Docker image pulled, no cleanup or Xbox requests.
- Remaining for a future separately authorized live step: inspect whether currently resolved Compose tag maps to installed image locally, validate a Bot0-only temporary image override while preserving original Compose files, ensure Control Bot and other supervisors will not interfere, and have a bounded rollback procedure. No fleet rollout implied.

## Operator Compose image resolution (PASSED)
- Read-only local verification confirms the effective Compose image is already present on the Dell and its image ID equals Bot0's running image ID.
- Bot0 remains running, restart count 0 at the observation; no image pulls, Compose changes, restarts, Xbox calls or cleanup operations.
- This closes the *current Compose tag resolution* question. It does **not** turn the tag into an immutable reference: image digests remain required for trial/rollback.

## Staged Bot0-only deployment and rollback procedure (NOT AUTHORIZED, NOT EXECUTED)
1. Immediately before any future live action, reconfirm Bot0 original image ID/digest, health, 16-bot fleet status, Control Bot's interaction with Bot0 and friend-cleanup pause. Abort on unexpected state or supervisor conflict. Do not restart the full fleet.
2. Pull and verify only the canary image by immutable digest `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1`. Original rollback image is `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`. Do not modify the `:stable`/`:test` tags.
3. Preserve the original Compose file untouched. Prepare a temporary, restricted-permissions override containing only the `mcgatewaybot-docker` service's exact candidate image reference. Validate the fully resolved merged Compose service and prove all other services unchanged, environment and bind values unprinted. Confirm all host-side mount paths remain the same privately.
4. After explicit owner approval and supervisor/cleanup guard, run a *single Bot0 service* recreation with `--no-deps`, no build, no image auto-pull, and the candidate digest via the approved temporary override; no other container recreation. This does briefly interrupt Bot0 players. Do not enable cleanup.
5. Observe startup, health, real hub connectivity, and restart/timeout signals. If failed or if independent control paths unexpectedly change the container, restore the exact original image digest via a temporary Compose override for **Bot0 only**. Reconfirm Bot0 health and all other 15 bots. Do not depend on a mutable tag for rollback.
6. A separate, explicitly approved operator invocation of console `personsummaryprobe <32-lowercase-hex-nonce>` is allowed at most once per process. The command selects an existing in-memory cached friend and performs one GET with a bounded timeout and no retries, and prints only the coarse sanitized schema verdict. Do not supply a XUID or print any Xbox authentication. No friendship removal follows automatically.
7. Restore Bot0 to the verified original image digest after the test unless the owner separately authorizes a different state. Remove temporary overrides only after restoration and verification. Keep original Compose file, database, cleanup state, other 15 bots, and release channels unchanged.

**Unverified before execution:** Control Bot maintenance/health supervision behavior for a planned Bot0 recreation; exact Xbox command delivery path; current cleanup paused state; successful rollback rehearsal. Source CI and Docker registry checks do not prove these live details. Therefore, production authorization is **NOT YET REQUESTED** until these are addressed in an executable gated procedure.

## Control Bot supervision source review (GIT ONLY, not proof of installed binary)
- Reviewed branch in `JaxDoesIt/MCGateway`: `fix/release160-presence-continuation-2026-10-29`.
- `components/control-bot/index.js` Git blob `aef6d58fc48d40892ed9a565396f9ece13a2a385`: Bot0 maintenance hold path is `<active index.js directory>/data/.release160-bot0-maintenance-hold`, and restart reservation/automatic/manual/restart-all/AI paths call `release160Bot0Held`.
- `components/control-bot/lib/release160-bot0-restart-hold.js` Git blob `bff9d6dc80bcf8fc0cc3bb9466b832de73ee711d`: owner-managed exact private-file sentinel `RELEASE160_BOT0_RESTART_HOLD_V1\n` blocks Bot0 and not other 15. Absent marker does not activate hold. Malformed present marker is held closed. Marker is NOT created/deleted by source.
- `components/control-bot/lib/release160-cleanup-gate.js` Git blob `fcf0c8c8491e112295e6297786e80581185c7b0d`: final cleanup admission guard for Release160 release/update state.
- **Critical console conflict:** hold blocks Control Bot's PTY console/friend-count dispatch to Bot0. A live `personsummaryprobe` invocation cannot use that same Control Bot route while held. Do not clear the hold merely to dispatch the diagnostic. Use a separately reviewed owner-controlled direct console route, and verify its safety beforehand.
- `components/control-bot/lib/v44-core.js` reads persisted `cleanup_paused` from its SQLite state; an environment setting or old log is not live proof. The supported read-only user-facing check is Discord `/cleanup status`, including paused, active tasks, dispatch-intents and in-flight lease fields. Do not open, back up, or mutate the database in this preflight.
- `components/control-bot/lib/update-manager.js` has a separate persisted updater paused field, and its own potential Compose paths. Its `/update status` is a useful live source; external updater/watchtower state still needs independent verification.
- **NEXT BLOCKER:** active Control Bot's installed source and actual runtime pause states have not yet been verified. No hold marker write, Bot0 replacement, restart, Xbox request or cleanup command authorized by this source review.

## Installed Control Bot safety verification (OPERATOR READ-ONLY; PASSED)
- Live Control Bot main PID resolved; the active `index.js` entrypoint was identified.
- Local Git blob comparisons match reviewed code exactly: `index.js` `aef6d58fc48d40892ed9a565396f9ece13a2a385`, `release160-bot0-restart-hold.js` `bff9d6dc80bcf8fc0cc3bb9466b832de73ee711d`, and `release160-cleanup-gate.js` `fcf0c8c8491e112295e6297786e80581185c7b0d`.
- Both Bot0 restart hold and cleanup gate are wired into installed Control Bot.
- **Bot0 maintenance marker ABSENT:** the optional Bot0 restart/console hold is not currently active; no marker was created or modified by this check.
- Updater's local JSON state is readable and `paused=True`; `migrationPaused=False` (distinct flag, not the updater-wide pause).
- Stored staged rollout reports `stage=complete`. This does not, by itself, prove all live workers quiescent or cleanup paused.
- **OUTSTANDING:** operator's live `/cleanup status` (paused flag, batch active, Bot0 active cleanup rows, open dispatch intents, console leases, count capture, restart reservation). No DB, production services, Docker images, or Xbox requests touched.
- Future authorized trial must activate verified hold *before* Bot0 service recreation and use an independently reviewed console route, because the hold blocks Control Bot PTY dispatch. Do not activate hold merely to prove it works until the end-to-end invocation/rollback protocol is ready.

## Operator live Discord cleanup status (PAUSED and drained for Bot0)
- Operator's `/cleanup status` snapshot at approximately 7:32 PM local time: Mode `auto`; `Paused=Yes`; `Cleanup batch still running=No`.
- Pending `9,322` with `9,321` ready; backlog tracking continues while cleanup is paused. Do **NOT** interpret backlog as running removal.
- Last hour: `358` newly queued, `0` attempts, `0` confirmed, `0` uncertain.
- Process-wide console lease: `No in this process`; Bot0 active cleanup row tasks `0`; Bot0 unresolved durable dispatch intents `0`; Bot0 console leases `No in this process`; exact friend-count capture `No in this process`; restart already reserved `No in this process`.
- Live status itself explicitly says `Safe to stop Bot0/Control Bot: NOT ATTESTED` and `External Watchtower/updater/supervisor holds: NOT ATTESTED`. Preserve this qualification. Earlier separate checks showed Watchtower not running and updater JSON paused; both must be reconfirmed immediately before any live operation.
- The report is an ephemeral snapshot, **not** durable permission to stop/recreate Bot0. A bounded maintenance hold, fresh recheck, safe console delivery and separately approved live deployment remain required.

## One-shot console output sanitizer: mocked CI PASSED
- Added pure, offline Python result sanitizer `tools/release160/personsummary_console_result.py`; it does not call Docker, Xbox, HTTP or the Dell. It accepts only one nonce-matched diagnostic marker, allowed coarse HTTP/schema categories and the literal `can_authorize_removal=false`. It never echoes raw console content, usernames, XUIDs or authorization material.
- Adversarial unit tests `tools/release160/test_personsummary_console_result.py` cover unrelated secret-bearing logs, color escapes, duplicate markers, nonce mismatch, unconfirmed transport, bad tokens, oversized/invalid output and redaction invariants.
- GitHub Actions run `41150811644` completed successfully: https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41150811644.
- **Not equivalent to a live transport test.** The reviewed Control Bot PTY source `components/control-bot/lib/docker-console-pty.py` Git blob is `64c2b0d1803c5e75dd80b37cca2cba99de16ecc2` and its support module `bounded_console_output.py` is `7633fe7e4a434e42cbcbefa4cc41458c18661ee5`. This owner-controlled direct transport can in principle bypass CB's held console path; do not run it before checking installed copies, Bot0 TTY and obtaining separate explicit approval.
- The future live command requires **one** schema GET only when the console one-shot command reaches the application. Ordinary broadcaster startup/rejoin will also cause its normal network traffic: do not claim the entire Bot0 trial makes only one Xbox request. Do not disclose raw PTY console output.

## Operator direct PTY console readiness (PASSED; no command sent)
- Operator's read-only Dell results: installed `components/control-bot/lib/docker-console-pty.py` Git blob `64c2b0d1803c5e75dd80b37cca2cba99de16ecc2`: EXACT MATCH.
- Installed `components/control-bot/lib/bounded_console_output.py` Git blob `7633fe7e4a434e42cbcbefa4cc41458c18661ee5`: EXACT MATCH.
- Bot0 `Tty=True`, `OpenStdin=True`, `Running=True`, `RestartCount=0`.
- Maintenance marker ABSENT as expected: protection not active yet. The direct Python PTY helper is a **future option** to submit the one-shot command while the Control Bot PTY route is intentionally blocked by the maintenance marker.
- No console request, Docker changes, image pull, restart, friend cleanup or Xbox operation performed. PTY file/TTY matching does not establish a successful live console attach or an application response.

## Explicit authorization gate
- Candidate exact reference: `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:6877f7e59118a5d48ab866f8db66bbfd156f6e336252842297f80a31665f74e1`.
- Original exact recovery reference: `ghcr.io/jaxdoesit/mcgateway-broadcast@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55`.
- When the owner explicitly approves a bounded Bot0-only trial, first perform fresh no-write runtime and fleet health checks; verify cleanup is still paused with no open Bot0 tasks, and updater/Watchtower still held. Then activate the precisely formatted Bot0-only maintenance marker using a reviewed atomic private-file operation and verify it is effective.
- Do not send a console command during the maintenance hold via Control Bot: this would be blocked. After a separately reviewed and authorized Bot0-only Compose deployment, the owner-controlled PTY helper can attach directly to the exact container and submit a fresh 32-character lowercase hexadecimal nonce once. Capture output privately; pass only the filtered result through the offline-tested allowlist sanitizer. Do not print raw console traffic or retry an uncertain send.
- Restore original exact image reference via Bot0-only Compose override, verify health/fleet and monitor, then remove the marker only after safely finishing recovery. Keep original Compose file unchanged, friend cleanup paused and all 15 other bots untouched.
- A trial causes a brief Bot0 interruption and normal broadcaster Xbox reconnect traffic. The diagnostic allows at most one additional Xbox relationship GET; there is no friend removal.
- The operator may approve deployment and the GET together only after seeing the bounded procedure and risks. **NO LIVE ACTION HAS BEEN AUTHORIZED OR EXECUTED.**

## Owner authorized Bot0-only live trial: operator runner prepared, NOT YET EXECUTED
- Owner explicitly approved Bot0-only temporary replacement, one diagnostic GET and restoration to original image.
- Runner `tools/release160/owner_bot0_personsummary_trial.py`, and allowlist-only sanitizer `tools/release160/personsummary_console_result.py`, pinned to tested source commit `668773a50f4f627d836154c4a1ed7b914a39483d`.
- Offline CI https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41152033299 **completed success**. Includes fake Docker/Compose tests, forced simulated failed canary boot and rollback, private file hold, single target scope, redaction and never-live HTTP/Docker.
- GitHub-runner SHA-256: runner `55d9ecc9eae3e66f56e1cbd3e8c90ec2b2708b71bd8ce6f0fb1f32f56620cc07`; sanitizer `c5e3256a7305ef35e746b0f9c22df926183443aa5c623b93176c5301a15cd17b`.
- Before executing, owner must retrieve both source files via full immutable commit URL and verify SHA-256. Do not execute a mutable branch version or pipe remote content into a shell.
- Runner rechecks exact active Control Bot source blobs, persistent cleanup pause (SQLite read-only), updater pause/staged rollout, stopped Watchtower, full 16-bot fleet, original image identity, Bot0 TTY, Compose service/override invariance; only then pulls exact candidate digest. Abort on uncertain evidence.
- Runner creates a private Bot0-only maintenance hold, then uses a private one-service Compose digest override for candidate, observes stable container, dispatches one PTY command outside the held CB route, redacts output, restores original image digest and confirms stable process/unchanged other 15. If recovery is not proven, leave hold active and require manual review. The original Compose file, stable/test tags and cleanup state are never modified.
- Recovery verified here means the original image is running without observed restart/OOM during the bounded local observation; it does **not** prove a real Xbox/Hub join. Operator must check actual player connectivity after execution.
- Authorization is documented, but **NO Dell COMMAND HAS BEEN EXECUTED BY THE ASSISTANT** and no live outcome has been claimed.

## FIRST LIVE BOT0-ONLY TRIAL: SAFE RESTORATION, SCHEMA UNVERIFIED
- Operator ran the checksum-pinned runner prepared from commit `668773a50f4f627d836154c4a1ed7b914a39483d`. Both downloaded Python files passed SHA-256 verification.
- Live runner reported: `PREFLIGHT PASSED`; `CANDIDATE STAGED`; `BOT0 HOLD ACTIVE`; `BOT0 CANARY BOOTED`; then the sanitized diagnostic returned `PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=unverified fields=no_cached_target can_authorize_removal=false`.
- The diagnostic successfully reached the canary's console command. It found **no usable friend in the current in-memory cache**, and returned without calling `McgatewayXboxPersonSummaryProbeV160.capture`: no relationship GET was issued by this diagnostic. It does not establish status 200, 404, an Xbox error, or relationship-field schema.
- Recovery report: `RESTORING BOT0 original immutable digest`, followed by `RECOVERY VERIFIED: Bot0 original image running; maintenance hold cleared`. Recovery gate checks original image identity, no observed OOM/restarts over local observation, updater+cleanup still paused, and unchanged identity/image/running state of the other 15 containers. Still require an independent real Hub join/transfer check.
- **Investigated cause in reviewed source:** `tools/release160/apply_personsummary_canary.py` reads the private `lastFriendCache` field directly and refuses to fetch or populate it. The source `core/.../FriendManager.java` starts `lastFriendCache` as null and fills it via `get()`. Its automatic friend-sync calls `get()` on a delay equal to `friendSync.updateInterval`, only if `autoFollow || autoUnfollow`. `CoreConfig.java` has a default friend-sync interval of **60 seconds**, whereas the operator runner observes only **14 seconds** after candidate boot before the one-shot diagnostic. This makes early timing a plausible cause; user configuration and whether an Xbox friend list could be fetched have **not** been checked.
- **Do not repeat the same trial unchanged** or assume the cache will be populated after waiting. Before another *separately authorized* production test, read only the relevant non-secret settings from Bot0's `/opt/app/config/config.yml` (friendSync autoFollow/autoUnfollow/updateInterval) and investigate a mock-tested bounded cache-readiness approach. Never permit destructive friend operations or log XUIDs. Fresh owner approval needed for any second Bot0 restart/diagnostic.
- Friend cleanup remains paused by the runner's verified end state. Original Compose file, stable/test channels and database contents were not intentionally changed by the runner.

## Bot0 live friend-sync configuration and bounded warmup repair (OFFLINE VALIDATED, NOT DEPLOYED)
- Operator's read-only Dell inspection of Bot0's original `/opt/app/config/config.yml` reports `friend-sync.auto-follow=true`, `friend-sync.auto-unfollow=true`, `friend-sync.update-interval=60 seconds`.
- `FriendManager.initAutoFriend` schedules `get()` with initial delay equal to the configured 60s interval when either automatic direction is enabled. The prior candidate script observed only 14s before trying to read `lastFriendCache`. This **supports** the early-cache hypothesis, but does not prove successful Xbox friend-list retrieval or that a usable friend exists.
- Updated Git runner `tools/release160/owner_bot0_personsummary_trial.py` on image-build branch: extend candidate stable-boot observation to 120 seconds before exactly one `personsummaryprobe`, preserving image/boot/restart identity checks throughout. Re-check the private Bot0 hold, persisted cleanup pause, updater pause, stopped Watchtower, and other 15 unchanged containers immediately before the diagnostic. Rollback's separate original-image observation remains 14 seconds.
- This adjustment is **only the Dell operator runner**. The immutable GHCR canary image, original base, Java probe, digest pins, cleanup protections, and original Compose configuration have not been changed. Waiting does not guarantee the friend cache becomes usable; `no_cached_target` may recur, and no extra Xbox list GET is added by this change.
- Additional offline mocked lifecycle assertions check that the candidate observation is exactly 120 seconds, original-image verification is still 14 seconds, and failure still triggers recovery. CI https://github.com/JaxDoesIt/Broadcaster-unfollow/actions/runs/41152679819 at source commit `d9f10814f891793862e27e5eaec047c5ee6eaffe` completed **success**.
- **No second live trial authorized or executed.** The first trial's permission is spent. A future owner-approved second trial entails two more Bot0 recreations and approximately two minutes on the candidate before the one-shot GET; verify actual hub join/transfer after restoring original.

## Safety and next gate
- No Dell access, no Bot0 restart, no fleet restart, no Xbox API request, no database access, no friend cleanup, no GHCR test/stable promotion occurred.
- Source probes never authorize deletion. Friend removal remains intentionally denied. Cleanup remains paused.
- Before any live canary: Bot0 active image and base digest verified in the operator's read-only Dell check; next inspect container reconstruction settings and prepare exact-digest recovery; verify live health and operator-only one-shot console route; require separate explicit owner approval for Bot0-only deployment and a single Xbox GET.
- After authorized Bot0-only canary: inspect only redacted `MCGATEWAY_PERSONSUMMARY_SCHEMA_V160` result and decide the next contract review; do not remove friends or roll out to the remaining 15 bots as a consequence of schema evidence alone.
