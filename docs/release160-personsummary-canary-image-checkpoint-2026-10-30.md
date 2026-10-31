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

## Safety and next gate
- No Dell access, no Bot0 restart, no fleet restart, no Xbox API request, no database access, no friend cleanup, no GHCR test/stable promotion occurred.
- Source probes never authorize deletion. Friend removal remains intentionally denied. Cleanup remains paused.
- Before any live canary: perform a read-only Dell verification of active Bot0 container image identity and actual base digest; prepare exact-digest recovery; verify live health and operator-only one-shot console route; require separate explicit owner approval for Bot0-only deployment and a single Xbox GET.
- After authorized Bot0-only canary: inspect only redacted `MCGATEWAY_PERSONSUMMARY_SCHEMA_V160` result and decide the next contract review; do not remove friends or roll out to the remaining 15 bots as a consequence of schema evidence alone.
