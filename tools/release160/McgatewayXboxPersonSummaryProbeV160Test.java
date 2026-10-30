package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.nio.ByteBuffer;
import java.util.concurrent.Flow;
import java.util.concurrent.CompletionException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Fake HTTP only. Never supplies a live Xbox token or uses a network client. */
public final class McgatewayXboxPersonSummaryProbeV160Test {
    private static final String NONCE = "ab".repeat(16);
    private static final String XUID = "2533270000000022";
    private static final String SECRET = "XBL3.0 simulated secret never print";
    private static int assertions;

    private static void eq(Object expected, Object actual, String title) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(title + ": " + actual);
        assertions++;
    }
    private static void matches(String text, String prefix) {
        eq(true, text.startsWith(prefix), "fixed output prefix");
        eq(true, text.endsWith("can_authorize_removal=false"), "never grants removal");
        eq(false, text.contains(XUID), "no XUID leak");
        eq(false, text.contains(SECRET), "no token leak");
        eq(false, text.contains("true"), "no actual relation value leak");
        eq(false, text.contains("exception"), "no exception leak");
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static McgatewayXboxPersonSummaryProbeV160.Reply reply(
            McgatewayXboxPersonSummaryProbeV160.Request req, String json, int status) {
        return new McgatewayXboxPersonSummaryProbeV160.Reply(status, req.uri(),
            Map.of("Content-Type",List.of("application/json")), utf8(json), true);
    }
    private static String run(String json) {
        return McgatewayXboxPersonSummaryProbeV160.capture(req -> {
            eq("GET", "GET", "fixed read method");
            eq(URI.create("https://social.xboxlive.com/users/xuid(" + XUID + ")/summary"),
                req.uri(), "exact target URI");
            return reply(req,json,200);
        },SECRET,XUID,NONCE);
    }
    public static void main(String[] ignored) {
        String prefix = "MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=" + NONCE + " http=200 fields=";
        String base = null;
        for (boolean a : new boolean[]{false,true}) for(boolean b : new boolean[]{false,true}) {
            String json = "{\"isCallerFollowingTarget\":" + a +
                ",\"isTargetFollowingCaller\":" + b + "}";
            String outcome = run(json);
            matches(outcome,prefix);
            eq(true,outcome.contains("fields=two_boolean_fields"),"two explicit typed flags");
            if(base==null) base=outcome;
            eq(base,outcome,"relationship values never alter report");
        }
        for (String json : new String[]{
            "{\"isCallerFollowingTarget\":false}",
            "{\"isTargetFollowingCaller\":false}",
            "{\"isCallerFollowingTarget\":\"false\",\"isTargetFollowingCaller\":false}",
            "{\"isCallerFollowingTarget\":null,\"isTargetFollowingCaller\":false}",
            "{\"isCallerFollowingTarget\":1,\"isTargetFollowingCaller\":false}",
        }) {
            matches(run(json),prefix);
            eq(false,run(json).contains("fields=two_boolean_fields"),"no missing/nonboolean proof");
        }
        for (String json : new String[]{
            "{\"isCallerFollowingTarget\":true,\"isCallerFollowingTarget\":false,\"isTargetFollowingCaller\":true}",
            "{\"isCallerFollowingTarget\":true,\"isTargetFollowingCaller\":false,\"nested\":{\"x\":1,\"x\":2}}",
            "{\"isCallerFollowingTarget\":true,\"isTargetFollowingCaller\":false} trailing",
            "{\"isCallerFollowingTarget\":true,\"isTargetFollowingCaller\":false,\"nextLink\":\"page\"}",
            "[]",
            "{}",
        }) {
            matches(run(json),prefix);
            eq(true,run(json).contains("fields=unverified") ||
                run(json).contains("fields=missing_field"),"malformed data fails closed");
        }
        for (int status : new int[]{401,403,404,429,500,503}) {
            String report = McgatewayXboxPersonSummaryProbeV160.capture(req ->
                reply(req,"{}",status),SECRET,XUID,NONCE);
            matches(report,"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=" + NONCE);
            eq(true,report.contains("fields=unverified"),"error status never verifies schema");
        }
        String badUri = McgatewayXboxPersonSummaryProbeV160.capture(req ->
            new McgatewayXboxPersonSummaryProbeV160.Reply(200, URI.create("https://elsewhere.invalid"),
                Map.of("Content-Type",List.of("application/json")),utf8("{}"),true),
            SECRET,XUID,NONCE);
        eq(true,badUri.contains("fields=unverified"),"wrong final URL denied");
        String oversized = McgatewayXboxPersonSummaryProbeV160.capture(req ->
            new McgatewayXboxPersonSummaryProbeV160.Reply(200,req.uri(),
                Map.of("Content-Type",List.of("application/json")), new byte[16385],false),
            SECRET,XUID,NONCE);
        eq(true,oversized.contains("fields=unverified"),"oversized payload denied");
        String badHeaders = McgatewayXboxPersonSummaryProbeV160.capture(req ->
            new McgatewayXboxPersonSummaryProbeV160.Reply(200,req.uri(),
                Map.of("Content-Type",List.of("application/json","application/json")),utf8("{}"),true),
            SECRET,XUID,NONCE);
        eq(true,badHeaders.contains("fields=unverified"),"duplicate content-type denied");
        String failure = McgatewayXboxPersonSummaryProbeV160.capture(req -> {
            throw new IllegalStateException("secret body "+SECRET+XUID);
        },SECRET,XUID,NONCE);
        matches(failure,"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=" + NONCE);
        eq(true,failure.contains("http=unverified fields=unverified"),"exceptions sanitized");
        {
            var bounded = new McgatewayXboxPersonSummaryProbeV160.LimitedSubscriber();
            class Subscription implements Flow.Subscription {
                boolean cancelled;
                @Override public void request(long n) { }
                @Override public void cancel() { cancelled = true; }
            }
            Subscription subscription = new Subscription();
            bounded.onSubscribe(subscription);
            bounded.onNext(List.of(ByteBuffer.wrap(new byte[16_384])));
            bounded.onNext(List.of(ByteBuffer.wrap(new byte[1])));
            eq(true,subscription.cancelled,"body-overflow cancels subscription");
            boolean failed = false;
            try { bounded.getBody().toCompletableFuture().join(); }
            catch (CompletionException expected) { failed = true; }
            eq(true,failed,"body-overflow never yields a response");
        }
        var safeReq=new McgatewayXboxPersonSummaryProbeV160.Request(
            URI.create("https://social.xboxlive.com"),SECRET,java.time.Duration.ofSeconds(7));
        eq(false,safeReq.toString().contains(SECRET),"request string redacts authentication");
        var safeReply=new McgatewayXboxPersonSummaryProbeV160.Reply(200,
            URI.create("https://social.xboxlive.com"),Map.of("Secret",List.of(SECRET)),utf8(SECRET),true);
        eq(false,safeReply.toString().contains(SECRET),"reply string redacts content");
        System.out.println("PersonSummary in-process GET probe: " + assertions + " fake HTTP assertions PASS");
    }
}
