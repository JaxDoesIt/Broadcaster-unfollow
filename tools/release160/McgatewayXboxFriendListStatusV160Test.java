package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.Flow;

/** Strictly mocked one-GET status/shape test; no Docker, Xbox or auth account. */
public final class McgatewayXboxFriendListStatusV160Test {
    private static final String SELF = "2533270000000011";
    private static final String TARGET = "2533270000000022";
    private static final String SECRET = "XBL3.0 simulated NEVER_OUTPUT";
    private static final URI FRIENDS =
        URI.create("https://peoplehub.xboxlive.com/users/me/people/friends");
    private static int assertions;

    private static void eq(Object expected, Object actual, String title) {
        if (!Objects.equals(expected, actual))
            throw new AssertionError(title + ": expected expected-type and received actual-type differ");
        assertions++;
    }
    private static byte[] utf8(String s) { return s.getBytes(StandardCharsets.UTF_8); }
    private static McgatewayXboxFriendListStatusV160.Reply response(int status, byte[] body) {
        return new McgatewayXboxFriendListStatusV160.Reply(
            status, FRIENDS, Map.of("content-type", List.of("application/json")),
            body, true
        );
    }
    private static McgatewayXboxFriendListStatusV160.Selection fetch(int status, String json) {
        int[] attempts = {0};
        var selection = McgatewayXboxFriendListStatusV160.capture(request -> {
            attempts[0]++;
            eq(FRIENDS, request.uri(), "single fixed friend-list endpoint");
            eq(SECRET, request.auth(), "secret stays only inside fake request");
            eq("Friend-list request [redacted]", request.toString(), "request toString hides auth");
            return response(status, utf8(json));
        }, SECRET, SELF);
        eq(1, attempts[0], "exactly one friend-list GET per diagnostic");
        validateNoLeak(selection);
        return selection;
    }
    private static void validateNoLeak(McgatewayXboxFriendListStatusV160.Selection result) {
        eq(false, result.reason().contains(SECRET), "reason hides token");
        eq(false, result.reason().contains(TARGET), "reason hides target");
        eq(false, result.reason().contains(SELF), "reason hides caller");
        eq("Friend-list selection [redacted]", result.toString(),
            "selection toString redacted");
    }
    private static void reason(String expected, int status, String json) {
        var result = fetch(status, json);
        eq(expected, result.reason(), "coarse reason");
        eq(null, result.target(), "non-ready selection hides target");
    }
    private static McgatewayXboxFriendListStatusV160.Reply custom(
        int status, byte[] body, Map<String,List<String>> headers, URI uri, boolean complete) {
        return new McgatewayXboxFriendListStatusV160.Reply(status, uri, headers, body, complete);
    }
    private static String list(String body) { return "{\"people\":" + body + "}"; }

    public static void main(String[] ignored) {
        var happy = fetch(200, list("[{\"xuid\":\"" + TARGET + "\",\"isFriend\":true}]"));
        eq("list_ready", happy.reason(), "one valid friend target");
        eq(TARGET, happy.target(), "target retained privately, not logged");

        reason("list_empty", 200, list("[]"));
        reason("list_no_valid_target", 200, list(
            "[{\"xuid\":\"bad\"},{\"xuid\":\"" + SELF + "\"},{\"xuid\":0}]"));
        reason("list_auth", 401, "{\"error\":\"" + SECRET + "\"}");
        reason("list_auth", 403, "{\"error\":\"" + SECRET + "\"}");
        reason("list_limited", 429, "{}");
        reason("list_server", 500, "{}");
        reason("list_server", 503, "{}");
        // V4 exact status evidence: an HTTP code is safe, but never the
        // reply's body, headers, account identifiers or authentication.
        for (int code : new int[] {
            100, 199, 201, 202, 204, 206, 301, 302, 303, 304, 307, 308,
            400, 402, 404, 405, 406, 409, 410, 418, 422, 451, 499
        }) {
            reason("list_http_" + code, code, "{\"private\":\"" + SECRET + "\"}");
        }
        for (int status : new int[] {-1, 0, 99, 600, 999}) {
            reason("list_other", status, "{}");
        }
        // Successful HTTP status still requires a valid complete JSON list.
        reason("list_invalid", 200, "{\"unrelated\":\"unknown\"}");

        reason("list_invalid", 200, "");
        reason("list_invalid", 200, "{");
        reason("list_invalid", 200, "{}");
        reason("list_invalid", 200, "[]");
        reason("list_invalid", 200, "{\"people\":null}");
        reason("list_invalid", 200, "{\"people\":{}}");
        reason("list_invalid", 200, "{\"people\":[],\"people\":[]}");
        reason("list_invalid", 200, "{\"people\":[{\"xuid\":\"" + TARGET + "\",\"xuid\":\"" + SELF + "\"}]}");
        reason("list_invalid", 200, "{\"people\":[]}garbage");
        reason("list_invalid", 200, "{\"people\":[],\"metadata\":{\"x\":1,\"x\":2}}");
        reason("list_invalid", 200, list("[null]"));
        reason("list_invalid", 200, list("[1]"));
        reason("list_no_valid_target", 200,
            list("[{\"xuid\":\"18446744073709551616\"}]"));
        reason("list_no_valid_target", 200,
            list("[{\"xuid\":\"0000000000000022\"}]"));

        reason("list_incomplete", 200, "{\"people\":[],\"nextLink\":\"page2\"}");
        reason("list_incomplete", 200, "{\"people\":[],\"continuationToken\":\"next\"}");
        reason("list_incomplete", 200, "{\"people\":[],\"continuation\":3}");
        reason("list_empty", 200, "{\"people\":[],\"continuationToken\":null}");

        var malformedUtf8 = McgatewayXboxFriendListStatusV160.capture(req ->
            response(200, new byte[] {(byte)0xff, (byte)0xfe}), SECRET, SELF);
        eq("list_invalid", malformedUtf8.reason(),
            "invalid UTF8 fails without exposing data");
        validateNoLeak(malformedUtf8);

        var wrongUrl = McgatewayXboxFriendListStatusV160.capture(req ->
            custom(200, utf8(list("[]")), Map.of("Content-Type",List.of("application/json")),
                URI.create("https://evil.example/path"), true),
            SECRET, SELF);
        eq("list_unverified", wrongUrl.reason(), "redirected URL rejected");

        var wrongContentType = McgatewayXboxFriendListStatusV160.capture(req ->
            custom(200, utf8(list("[]")), Map.of("Content-Type",List.of("text/html")), FRIENDS,true),
            SECRET, SELF);
        eq("list_invalid", wrongContentType.reason(), "wrong content-type denied");

        var conflictingHeaders = McgatewayXboxFriendListStatusV160.capture(req ->
            custom(200, utf8(list("[]")), Map.of(
                "Content-Type",List.of("application/json", "text/html")), FRIENDS,true),
            SECRET, SELF);
        eq("list_invalid", conflictingHeaders.reason(), "multi-value headers rejected");

        var badLength = McgatewayXboxFriendListStatusV160.capture(req ->
            custom(200, utf8(list("[]")), Map.of(
                "Content-Type",List.of("application/json"),
                "Content-Length",List.of("999")), FRIENDS,true),
            SECRET, SELF);
        eq("list_invalid", badLength.reason(), "incorrect content length denied");

        var incomplete = McgatewayXboxFriendListStatusV160.capture(req ->
            custom(200, utf8(list("[]")), Map.of(
                "Content-Type",List.of("application/json")), FRIENDS,false),
            SECRET, SELF);
        eq("list_invalid", incomplete.reason(), "partial response denied");

        var oversized = McgatewayXboxFriendListStatusV160.capture(req ->
            response(200, new byte[2 * 1024 * 1024 + 1]), SECRET, SELF);
        eq("list_invalid", oversized.reason(), "oversized response denied");

        var networkError = McgatewayXboxFriendListStatusV160.capture(req -> {
            throw new java.io.IOException("private token=" + SECRET);
        }, SECRET, SELF);
        eq("list_unverified", networkError.reason(), "transport failure sanitized");
        validateNoLeak(networkError);

        int[] forbidden = {0};
        for (String invalidSelf : new String[]{null, "", "bad", "0", "18446744073709551616"}) {
            var result = McgatewayXboxFriendListStatusV160.capture(req -> {
                forbidden[0]++;
                return response(200, utf8(list("[]")));
            }, SECRET, invalidSelf);
            eq("list_unverified", result.reason(), "invalid self fails closed");
        }
        var badAuth = McgatewayXboxFriendListStatusV160.capture(req -> {
            forbidden[0]++;
            return response(200, utf8(list("[]")));
        }, "", SELF);
        eq("list_unverified", badAuth.reason(), "missing auth fails closed");
        eq(0, forbidden[0], "invalid inputs cause zero GET calls");

        McgatewayXboxFriendListStatusV160.LimitedSubscriber subscriber =
            new McgatewayXboxFriendListStatusV160.LimitedSubscriber();
        class Subscription implements Flow.Subscription {
            boolean cancelled;
            @Override public void request(long n) { }
            @Override public void cancel() { cancelled = true; }
        }
        Subscription subscription = new Subscription();
        subscriber.onSubscribe(subscription);
        subscriber.onNext(List.of(ByteBuffer.wrap(new byte[2 * 1024 * 1024 + 1])));
        eq(true, subscription.cancelled, "body cap cancels HTTP stream");
        eq(true, subscriber.getBody().toCompletableFuture().isCompletedExceptionally(),
            "overlong body fails without unbounded memory");
        System.out.println("PASS: " + assertions +
            " fully mocked, nonmutating Xbox list status/privacy/size assertions");
    }
}
