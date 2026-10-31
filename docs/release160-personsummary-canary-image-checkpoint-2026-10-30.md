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

## Safety and next gate
- No Dell access, no Bot0 restart, no fleet restart, no Xbox API request, no database access, no friend cleanup, no GHCR test/stable promotion occurred.
- Source probes never authorize deletion. Friend removal remains intentionally denied. Cleanup remains paused.
- Before any live canary: Bot0 active image and base digest verified in the operator's read-only Dell check; next inspect container reconstruction settings and prepare exact-digest recovery; verify live health and operator-only one-shot console route; require separate explicit owner approval for Bot0-only deployment and a single Xbox GET.
- After authorized Bot0-only canary: inspect only redacted `MCGATEWAY_PERSONSUMMARY_SCHEMA_V160` result and decide the next contract review; do not remove friends or roll out to the remaining 15 bots as a consequence of schema evidence alone.
