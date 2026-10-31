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

## Safety and next gate
- No Dell access, no Bot0 restart, no fleet restart, no Xbox API request, no database access, no friend cleanup, no GHCR test/stable promotion occurred.
- Source probes never authorize deletion. Friend removal remains intentionally denied. Cleanup remains paused.
- Before any live canary: Bot0 active image and base digest verified in the operator's read-only Dell check; next inspect container reconstruction settings and prepare exact-digest recovery; verify live health and operator-only one-shot console route; require separate explicit owner approval for Bot0-only deployment and a single Xbox GET.
- After authorized Bot0-only canary: inspect only redacted `MCGATEWAY_PERSONSUMMARY_SCHEMA_V160` result and decide the next contract review; do not remove friends or roll out to the remaining 15 bots as a consequence of schema evidence alone.
