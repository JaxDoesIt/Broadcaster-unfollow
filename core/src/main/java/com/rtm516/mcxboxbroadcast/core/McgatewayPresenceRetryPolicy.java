package com.rtm516.mcxboxbroadcast.core;

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Pure, deterministic Xbox presence pacing. No IO or player identity is used.
 * A 200 acknowledgement is NOT evidence that players can join a world.
 */
public final class McgatewayPresenceRetryPolicy {
    public static final int DEFAULT_HEARTBEAT_SECONDS = 300;
    private static final int MAX_HEARTBEAT_SECONDS = 3600;
    private static final int MAX_SERVER_RETRY_SECONDS = 3600;

    private McgatewayPresenceRetryPolicy() { }

    public static int acceptedDelaySeconds(String header) {
        try {
            long value = Long.parseLong(header == null ? "" : header.trim());
            if (value >= 30 && value <= MAX_HEARTBEAT_SECONDS) {
                return (int) value;
            }
        } catch (NumberFormatException ignored) {
            // Malformed or oversized heartbeat headers must not force a hot loop.
        }
        return DEFAULT_HEARTBEAT_SECONDS;
    }

    /**
     * status 0 indicates an IOException/timeout before an HTTP response.
     * failureCount is consecutive, beginning at 1. jitterSample is injected
     * to make offline tests deterministic; production passes random entropy.
     */
    public static int failureDelaySeconds(int status, int failureCount,
                                          String retryAfter, long nowEpochSeconds,
                                          int jitterSample) {
        final int attempt = Math.max(1, failureCount);
        final boolean transientFailure = status == 0 || status >= 500;
        final int base;
        if (transientFailure) {
            base = attempt == 1 ? 60 : attempt == 2 ? 120 : attempt == 3 ? 240 : 300;
        } else {
            // 429 and authentication/other 4xx must NOT be aggressively retried.
            base = DEFAULT_HEARTBEAT_SECONDS;
        }
        // Up to 20% positive per-bot jitter, with 300s cap absent server hold.
        final int jitterSpan = Math.min(30, base / 5);
        final int jitter = Math.floorMod(jitterSample, jitterSpan + 1);
        final int localDelay = Math.min(DEFAULT_HEARTBEAT_SECONDS, base + jitter);
        // Honor server Retry-After on 429/503 (and other 5xx), even if longer
        // than local backoff, bounded at one hour for recoverability.
        if (status == 429 || transientFailure) {
            return Math.max(localDelay, parsedRetryAfterSeconds(retryAfter, nowEpochSeconds));
        }
        return localDelay;
    }

    static int parsedRetryAfterSeconds(String header, long nowEpochSeconds) {
        if (header == null || header.isBlank()) return 0;
        final String value = header.trim();
        try {
            // Bound before parsing, including huge but otherwise numeric values.
            if (value.matches("[0-9]+")) {
                if (value.length() > 6) return MAX_SERVER_RETRY_SECONDS;
                return (int) Math.min(MAX_SERVER_RETRY_SECONDS, Long.parseLong(value));
            }
            final long deadline = ZonedDateTime.parse(
                value, DateTimeFormatter.RFC_1123_DATE_TIME).toEpochSecond();
            final long delay = Math.max(0L, deadline - nowEpochSeconds);
            return (int) Math.min(MAX_SERVER_RETRY_SECONDS, delay);
        } catch (RuntimeException ignored) {
            return 0;
        }
    }
}
