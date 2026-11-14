# Release160 network reliability candidate

This source candidate repairs presence retry and incomplete session reconstruction
without changing friend cleanup authority, persisted account data, or fleet channels.
Upstream remains pinned to 798d8b3a6107359643b525f1c9c3303c020ae09b.

## Evidence and changes

On 2026-11-14, 51 presence failures across all18 production accounts in24hours
were HTTP connection timeouts. Most clustered during a common network incident.
Later public HTTPS probes succeeded; they cannot attribute the earlier outage.

The old presence method logged success even after exceptions and deferred the
next attempt for300seconds. The candidate requires HTTP200 for acceptance, adds
bounded connect/request timeouts and jittered exponential retries, honors429
Retry-After, and keeps authorization failures at a conservative retry interval.
A single cancellable schedule prevents accumulating retry chains. It emits closed
failure categories without account identifiers, tokens, bodies or exception text.

A failed session reconstruction can leave open replacement RTA plus old signaling
and a stale published handle. The candidate retains a pending reconstruction flag
until full publication completes. Cached sockets cannot clear that flag; subsequent
checks retry the transaction. A recursion guard handles publish/update/check calls.
Read-only health and friend-state session authority refuse stale publication while
pending. Existing account files and cleanup protections remain unchanged.

## Verification and release boundary

`tools/test_release160_patch.py` verifies exact-source preflight, idempotence and
all existing friend-state/cleanup contracts. `NetworkReliabilityProof` runs actual
patched methods with injected replies, scheduler and publication failures; no Xbox
requests, credentials, or storage writes. CI compiles pinned upstream, runs all
existing proofs plus this proof, and publishes only an immutable commit candidate.

Production rollout still requires the canonical MCGateway staged-rollout contract:
record exact image/config rollback, isolate one canary, verify real post-start
joining, then advance one bot at a time. This source change alone does not move
stable/test tags, alter live containers or establish public joinability.
