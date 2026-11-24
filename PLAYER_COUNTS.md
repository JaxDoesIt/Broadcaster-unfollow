# Optional display-only player counts candidate

Pinned Release160/reliability source is unchanged underneath the additional
`tools/release160/apply_player_counts.py` overlay. The candidate adds
`session.query-player-counts: false` and `session.player-count-file: ""`.
Enabling counts overrides native query-server, preserving names, game mode and
relay destination. No auth, friendship, capacity, restart or health authority is
added. Defaults keep existing installations unchanged.

A separate daemon queries standard Bedrock UDP every 30 seconds, with a bounded
1.5-second receive deadline and validation of sender, nonce, magic, length and
numeric range. Session updates never wait for it. A successful sample survives
transient failures for at most 90 seconds, then returns configured fallback
numbers. Native SessionInfo minimum-player/full-card compatibility guards remain.
Thus raw zero/full values can display as 1 or max+1 to preserve Minecraft joining;
this display is not occupancy/capacity authority.

For a fleet sharing a Hub, prefer a common read-only snapshot directory rather
than asking 25 bots to query independently. `player-count-file` accepts a bounded
JSON object: version=1, host, port, players, maximum, observedAt (UTC epoch ms).
Endpoint must match, timestamp cannot be future or older than 30 seconds, maximum
must be 1–1,000,000, and players must be 0..maximum. Invalid/missing snapshots
follow the same cache/fallback policy. Including source age plus cache TTL, a
previous count can remain displayed up to 120 seconds after its observation.
Publish with atomic rename, mounting the directory read-only; never expose a
runtime database, credentials, player lists or Xbox tokens to this reader.

At the first local test the actual Hub UDP endpoint did not respond to three
strict queries or an independent existing dashboard query. Its authenticated
behavior-pack heartbeat did supply a fresh player count. A production shared
publisher and supervised canary remain necessary; this candidate alone neither
publishes that feed nor enables counts on the fleet or customer panels.

Proofs exercise actual deployed SessionInfo semantics, malformed/timeout/runtime
failures, stale fallback/recovery, blocked-query isolation, UDP datagrams and
shared snapshot boundaries. CI builds exact upstream plus reviewed overlays and
checks the actual shaded StandaloneMain counts path without authenticating.
No production tags/channels, containers, configs or customer accounts are changed
by the candidate build. Follow the canonical MCGateway rollout contract before
any canary/promotion; a real post-start join remains required.
