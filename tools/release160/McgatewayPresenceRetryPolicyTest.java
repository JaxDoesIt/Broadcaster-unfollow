package com.rtm516.mcxboxbroadcast.core;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public final class McgatewayPresenceRetryPolicyTest {
    private static int passed = 0;
    private static void eq(int actual, int expected, String label) {
        if (actual != expected) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
        passed++;
    }
    private static void between(int actual, int lo, int hi, String label) {
        if (actual < lo || actual > hi) {
            throw new AssertionError(label + ": " + actual + " not in " + lo + ".." + hi);
        }
        passed++;
    }
    public static void main(String[] args) {
        final long now = 1_800_000_000L;
        eq(McgatewayPresenceRetryPolicy.acceptedDelaySeconds("300"),300,"normal heartbeat");
        eq(McgatewayPresenceRetryPolicy.acceptedDelaySeconds("45"),45,"supported heartbeat");
        for (String header : new String[]{"0","-1","99999999","NaN","",null,"29"}) {
            eq(McgatewayPresenceRetryPolicy.acceptedDelaySeconds(header),300,"bad heartbeat");
        }
        eq(McgatewayPresenceRetryPolicy.acceptedDelaySeconds("3600"),3600,"max heartbeat");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,1,"",now,0),60,"first 503");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,2,"",now,0),120,"second 503");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,3,"",now,0),240,"third 503");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,4,"",now,0),300,"fourth 503");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,99999,"",now,Integer.MAX_VALUE),300,"bounded streak");
        between(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,1,"",now,31),60,72,"staggered first retry");
        between(McgatewayPresenceRetryPolicy.failureDelaySeconds(0,2,"",now,1234),120,144,"timeout retried");
        between(McgatewayPresenceRetryPolicy.failureDelaySeconds(502,3,"",now,99),240,270,"bad gateway retried");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,"",now,0),300,"default rate limit delay");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,"900",now,0),900,"rate-limit Retry-After seconds");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,1,"180",now,0),180,"service Retry-After seconds");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,"999999999999999",now,0),3600,"huge Retry-After bounded");
        final String httpDate = DateTimeFormatter.RFC_1123_DATE_TIME.format(
            Instant.ofEpochSecond(now + 600).atZone(ZoneOffset.UTC));
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,httpDate,now,0),600,"HTTP date Retry-After");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,"nonsense",now,0),300,"invalid Retry-After");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,1,"0",now,0),60,"zero retry-after not hot loop");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(401,1,"1",now,0),300,"unauthorized not fast retried");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(403,1,"3000",now,0),300,"forbidden not fast retried");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(429,1,"-30",now,0),300,"negative Retry-After denied");
        eq(McgatewayPresenceRetryPolicy.failureDelaySeconds(503,1,"" ,now,Integer.MIN_VALUE),62,"negative entropy floor mod");
        System.out.println("McgatewayPresenceRetryPolicyTest: PASS " + passed + " deterministic assertions");
    }
}
