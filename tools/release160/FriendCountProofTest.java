package com.rtm516.mcxboxbroadcast.core;

import java.time.Duration;
import java.net.http.HttpClient;
import java.util.function.LongSupplier;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Offline fixture proof; no network, token, XUID output, or mutation. */
public final class FriendCountProofTest {
    private static final String NONCE = "0123456789abcdef0123456789abcdef";
    public static void main(String[] args) throws Exception {
        positiveAndTransport(); realisticMetadata(); zero();
        for (String people : List.of("[{\"xuid\":\"1\",\"isFriend\":1}]", "[{\"xuid\":\"1\",\"isFriend\":true},{\"xuid\":\"1\",\"isFriend\":false}]", "[{\"xuid\":\"1\",\"isFriend\":false}]") ) fail(people, "{\"targetFriendCount\":1}");
        failWith(new McgatewayFriendCountProof.Response(200, Map.of(), "{\"people\":[],\"next\":null}"));
        failWith(new McgatewayFriendCountProof.Response(200, Map.of("x-continuation", List.of("x")), "{\"people\":[]}"));
        failWith(new McgatewayFriendCountProof.Response(500, Map.of(), "{}"));
        failWith(new McgatewayFriendCountProof.Response(200, Map.of("Content-Type", List.of("text/plain")), "{\"targetFriendCount\":0}"));
        failWith(resp("{"));
        for (String key : List.of("continuation", "continuationToken", "next", "nextLink", "nextPage", "nextPageLink", "nextPageToken", "paging", "pagingInfo", "pagination", "hasMore", "skipToken", "@odata.nextLink", "totalPages", "NEXT-page")) paginationBody(key);
        expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":0}"), resp("{\"people\":[]}"), resp("{\"targetFriendCount\":0}")), "Bearer hidden", NONCE.toUpperCase()));
        for (String summary : List.of("{}", "{\"targetFriendCount\":\"1\"}", "{\"targetFriendCount\":null}", "{\"targetFriendCount\":1.0}", "{\"targetFriendCount\":-1}", "{\"targetFriendCount\":1,\"targetFriendCount\":1}")) fail("[]", summary);
        for (String xuid : List.of("0", "01", "18446744073709551616")) fail("[{\"xuid\":\"" + xuid + "\",\"isFriend\":true}]", "{\"targetFriendCount\":1}");
        check(McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":1}"), resp("{\"people\":[{\"xuid\":\"18446744073709551615\",\"isFriend\":true}]}"), resp("{\"targetFriendCount\":1}")), "Bearer hidden", NONCE).contains("count=1"));
        fail("[{\"xuid\":null,\"isFriend\":true}]", "{\"targetFriendCount\":1}");
        fail("[]", deepSummary(33)); fail("[" + "{\"xuid\":\"1\",\"isFriend\":false},".repeat(10_000) + "{\"xuid\":\"10001\",\"isFriend\":false}]", "{\"targetFriendCount\":0}");
        failWith(new McgatewayFriendCountProof.Response(200, Map.of(), "x".repeat(8 * 1024 * 1024 + 1)));
        expectFailure(() -> McgatewayFriendCountProof.capture(request -> { Thread.sleep(3); return new McgatewayFriendCountProof.Response(200, Map.of(), request.uri().equals(McgatewayFriendCountProof.FRIENDS) ? "{\"people\":[]}" : "{\"targetFriendCount\":0}"); }, "Bearer hidden", NONCE, Duration.ofMillis(1)));
        boundedSubscriberCancels();
        redirectClientRejected();
        finalSummaryDeadlineRejected();
        abaAccepted();
        expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":1}"), resp("{\"people\":[{\"xuid\":\"7\",\"isFriend\":true}]}"), resp("{\"targetFriendCount\":2}")), "Bearer hidden", NONCE));
        System.out.println("FriendCountProofTest: PASS");
    }

    private static void positiveAndTransport() throws Exception {
        StringBuilder people = new StringBuilder("["); for (int i = 1; i <= 1001; i++) { if (i > 1) people.append(','); people.append("{\"xuid\":\"").append(i).append("\",\"isFriend\":true}"); } people.append(']');
        Stub stub = new Stub(new McgatewayFriendCountProof.Response(200, Map.of(), "{\"targetFriendCount\":1001}"), new McgatewayFriendCountProof.Response(200, Map.of(), "{\"people\":" + people + "}"), new McgatewayFriendCountProof.Response(200, Map.of(), "{\"targetFriendCount\":1001}"));
        String line = McgatewayFriendCountProof.capture(stub, "Bearer hidden", NONCE);
        check(line.equals("MCGATEWAY_FRIEND_COUNT_V160_V2 nonce=" + NONCE + " count=1001 before=1001 after=1001 complete=true pages=1"));
        check(stub.requests.size() == 3);
        check(stub.requests.get(0).uri().equals(McgatewayFriendCountProof.SUMMARY) && stub.requests.get(0).contractVersion().equals("3"));
        check(stub.requests.get(1).uri().equals(McgatewayFriendCountProof.FRIENDS) && stub.requests.get(1).contractVersion().equals("7"));
        check(stub.requests.get(2).uri().equals(McgatewayFriendCountProof.SUMMARY) && stub.requests.stream().allMatch(r -> r.timeout().toNanos() > 0));
    }
    private static void realisticMetadata() throws Exception {
        StringBuilder people = new StringBuilder("[");
        for (int i = 1; i <= 1001; i++) {
            if (i > 1) people.append(',');
            people.append("{\"xuid\":\"").append(i).append("\",\"isFriend\":true,\"metadata\":{\"score\":1.25}");
            for (int field = 0; field < 60; field++) people.append(",\"field").append(field).append("\":").append(field).append(".5");
            people.append('}');
        }
        people.append(']');
        String line = McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":1001,\"unrelated\":2.75}"), resp("{\"people\":" + people + "}"), resp("{\"targetFriendCount\":1001,\"unrelated\":3.5}")), "Bearer hidden", NONCE);
        check(line.equals("MCGATEWAY_FRIEND_COUNT_V160_V2 nonce=" + NONCE + " count=1001 before=1001 after=1001 complete=true pages=1"));
    }
    private static void zero() throws Exception { check(McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":0}"), resp("{\"people\":[]}"), resp("{\"targetFriendCount\":0}")), "Bearer hidden", NONCE).contains("count=0 before=0 after=0")); }
    private static void abaAccepted() throws Exception { check(McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":1}"), resp("{\"people\":[{\"xuid\":\"9\",\"isFriend\":true}]}"), resp("{\"targetFriendCount\":1}")), "Bearer hidden", NONCE).contains("complete=true")); }
    private static void fail(String people, String summary) { expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(resp(summary), resp("{\"people\":" + people + "}"), resp(summary)), "Bearer hidden", NONCE)); }
    private static void failWith(McgatewayFriendCountProof.Response bad) { expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(bad, bad, bad), "Bearer hidden", NONCE)); }
    private static void paginationBody(String key) { expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":0}"), resp("{\"people\":[],\"" + key + "\":null}"), resp("{\"targetFriendCount\":0}")), "Bearer hidden", NONCE)); }
    private static McgatewayFriendCountProof.Response resp(String body) { return new McgatewayFriendCountProof.Response(200, Map.of(), body); }
    private static String deepSummary(int depth) { String value = "0"; for (int i = 0; i < depth; i++) value = "{\"x\":" + value + "}"; return "{\"targetFriendCount\":0,\"nested\":" + value + "}"; }
    private static void expectFailure(Throwing body) { try { body.run(); throw new AssertionError("expected failure"); } catch (AssertionError error) { throw error; } catch (Exception expected) { } }
    private static void boundedSubscriberCancels() {
        McgatewayFriendCountProof.BoundedSubscriber oversized = new McgatewayFriendCountProof.BoundedSubscriber(System.nanoTime() + Duration.ofSeconds(1).toNanos());
        Subscription oversizedSubscription = new Subscription(); oversized.onSubscribe(oversizedSubscription); oversized.onNext(List.of(ByteBuffer.allocate(8 * 1024 * 1024 + 1))); check(oversizedSubscription.cancelled); expectFailure(() -> oversized.getBody().toCompletableFuture().get());
        McgatewayFriendCountProof.BoundedSubscriber expired = new McgatewayFriendCountProof.BoundedSubscriber(System.nanoTime() - 1);
        Subscription expiredSubscription = new Subscription(); expired.onSubscribe(expiredSubscription); expired.onNext(List.of(ByteBuffer.allocate(1))); check(expiredSubscription.cancelled); expectFailure(() -> expired.getBody().toCompletableFuture().get());
    }
    private static void redirectClientRejected() {
        try (HttpClient client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build()) {
            expectFailure(() -> McgatewayFriendCountProof.capture(client, "Bearer hidden", NONCE));
        }
    }
    private static void finalSummaryDeadlineRejected() {
        final boolean[] finalResponseReturned = { false };
        final int[] postFinalClockCalls = { 0 };
        LongSupplier clock = () -> finalResponseReturned[0] && postFinalClockCalls[0]++ > 0 ? 2L : 0L;
        McgatewayFriendCountProof.Fetcher fetcher = new McgatewayFriendCountProof.Fetcher() {
            int request;
            public McgatewayFriendCountProof.Response fetch(McgatewayFriendCountProof.Request ignored) {
                request++;
                if (request == 3) finalResponseReturned[0] = true;
                return request == 2 ? resp("{\"people\":[{\"xuid\":\"1\",\"isFriend\":true}]}") : resp("{\"targetFriendCount\":1}");
            }
        };
        expectFailure(() -> McgatewayFriendCountProof.capture(fetcher, "Bearer hidden", NONCE, Duration.ofNanos(1), clock));
    }
    private static void check(boolean value) { if (!value) throw new AssertionError("fixture failed"); }
    private interface Throwing { void run() throws Exception; }
    private static final class Stub implements McgatewayFriendCountProof.Fetcher {
        final List<McgatewayFriendCountProof.Response> responses; final List<McgatewayFriendCountProof.Request> requests = new ArrayList<>(); int index;
        Stub(McgatewayFriendCountProof.Response... responses) { this.responses = List.of(responses); }
        public McgatewayFriendCountProof.Response fetch(McgatewayFriendCountProof.Request request) { requests.add(request); McgatewayFriendCountProof.Response response = responses.get(index++); return response.headers().isEmpty() ? new McgatewayFriendCountProof.Response(response.statusCode(), Map.of("Content-Type", List.of("application/json; charset=utf-8")), response.body()) : response; }
    }
    private static final class Subscription implements java.util.concurrent.Flow.Subscription { boolean cancelled; public void request(long amount) { } public void cancel() { cancelled = true; } }
}
