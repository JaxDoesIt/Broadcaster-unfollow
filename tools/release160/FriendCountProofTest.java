package com.rtm516.mcxboxbroadcast.core;

import java.time.Duration;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.util.function.LongSupplier;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Offline fixture proof; no network, token, XUID output, or mutation. */
public final class FriendCountProofTest {
    private static final String NONCE = "0123456789abcdef0123456789abcdef";
    public static void main(String[] args) throws Exception {
        positiveAndTransport(); realisticMetadata(); zero(); safeFailureCategories();
        for (String people : List.of("[{\"xuid\":\"1\",\"isFriend\":1}]", "[{\"xuid\":\"1\",\"isFriend\":true},{\"xuid\":\"1\",\"isFriend\":false}]", "[{\"xuid\":\"1\",\"isFriend\":false}]") ) fail(people, "{\"targetFriendCount\":1}");
        failWith(new McgatewayFriendCountProof.Response(200, Map.of(), "{\"people\":[],\"next\":null}"));
        failWith(new McgatewayFriendCountProof.Response(200, Map.of("x-continuation", List.of("x")), "{\"people\":[]}"));
        // The actual V4 read-only PeopleHub diagnostic observed HTTP 400.
        // The v3 producer is a different HTTP client and was NOT tested live,
        // so simulate its own friend-list failure explicitly, never as zero.
        for (int status : List.of(206, 302, 400, 404, 429, 500, 503)) {
            final int candidateStatus = status;
            expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(
                resp("{\"targetFriendCount\":1}"),
                new McgatewayFriendCountProof.Response(candidateStatus, Map.of("Content-Type", List.of("application/json")), "{\"people\":[{\"xuid\":\"7\",\"isFriend\":true}]}"),
                resp("{\"targetFriendCount\":1}")), "Bearer hidden", NONCE));
        }
        failWith(new McgatewayFriendCountProof.Response(500, Map.of(), "{}"));
        failWith(new McgatewayFriendCountProof.Response(200, Map.of("Content-Type", List.of("text/plain")), "{\"targetFriendCount\":0}"));
        failWith(resp("{"));
        for (String key : List.of("continuation", "continuationToken", "next", "nextLink", "nextPage", "nextPageLink", "nextPageToken", "paging", "pagingInfo", "pagination", "hasMore", "skipToken", "@odata.nextLink", "totalPages", "NEXT-page")) paginationBody(key);
        // Unknown window/total-count metadata might describe a partial page,
        // even if the summary and visible mutual rows happen to agree.
        for (String key : List.of("totalCount", "startIndex", "maxItems", "pageSize", "pageCount", "pageNumber", "hasNext")) paginationBody(key);
        for (String key : List.of("totalCount", "startIndex", "maxItems", "pageSize", "pageCount", "pageNumber", "hasNext")) {
            expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(
                resp("{\"targetFriendCount\":1}"),
                resp("{\"people\":[{\"xuid\":\"7\",\"isFriend\":true}],\"metadata\":{\"" + key + "\":1}}"),
                resp("{\"targetFriendCount\":1}")), "Bearer hidden", NONCE));
        }
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
        upstreamRequestParity();
        finalSummaryDeadlineRejected();
        abaAccepted();
        expectFailure(() -> McgatewayFriendCountProof.capture(new Stub(resp("{\"targetFriendCount\":1}"), resp("{\"people\":[{\"xuid\":\"7\",\"isFriend\":true}]}"), resp("{\"targetFriendCount\":2}")), "Bearer hidden", NONCE));
        System.out.println("FriendCountProofTest: PASS");
    }

    private static String failureFields(McgatewayFriendCountProof.Fetcher fetcher) {
        try {
            McgatewayFriendCountProof.capture(fetcher,"Bearer fake-test",NONCE);
            throw new AssertionError("expected fail-closed count proof");
        } catch(AssertionError assertion) { throw assertion; }
        catch(Exception error) {
            return McgatewayFriendCountProof.safeFailureFields(error);
        }
    }
    private static void safeFailureCategories() {
        check(failureFields(new Stub(new McgatewayFriendCountProof.Response(
            503,Map.of("Content-Type",List.of("application/json")),"{}")))
            .equals(" stage=summary-before category=http-rejected"));
        check(failureFields(new Stub(resp("{\"targetFriendCount\":1}"),
            new McgatewayFriendCountProof.Response(400,
                Map.of("Content-Type",List.of("application/json")),"{}")))
            .equals(" stage=friends-fetch category=http-rejected"));
        check(failureFields(new Stub(resp("{\"targetFriendCount\":1}"),
            resp("{\"people\":[],\"next\":null}")))
            .equals(" stage=friends-validate category=pagination-unproven"));
        check(failureFields(new Stub(resp("{\"targetFriendCount\":1}"),
            resp("{\"people\":[{\"xuid\":\"1\",\"isFriend\":true}]}"),
            resp("{\"targetFriendCount\":2}")))
            .equals(" stage=crosscheck category=count-mismatch"));
        check(failureFields(new Stub(resp("{\"targetFriendCount\":1}"),
            resp("{\"people\":[]}"),
            new McgatewayFriendCountProof.Response(503,
                Map.of("Content-Type",List.of("application/json")),"{}")))
            .equals(" stage=summary-after category=http-rejected"));
        check(failureFields(new Stub(resp("{\"targetFriendCount\":1}"),
            resp("{\"people\":[]}"),
            resp("{\"targetFriendCount\":1}")))
            .equals(" stage=crosscheck category=count-mismatch"));
        // Simulate the actual Java HttpClient sendAsync().get() wrapper;
        // the reporter must never output these fake sensitive exception messages.
        String fakeSensitive="SECRET_TOKEN_FAKE XUID=123 fake-response-body";
        record WrappedCase(Exception thrown,String expected) {}
        var cases=List.of(
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new java.net.http.HttpConnectTimeoutException(fakeSensitive)),"timeout"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new java.net.UnknownHostException(fakeSensitive)),"dns-unavailable"),
            new WrappedCase(new java.util.concurrent.CompletionException(
                new java.net.ConnectException(fakeSensitive)),"connection-failed"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new javax.net.ssl.SSLHandshakeException(fakeSensitive)),"tls-failed"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new java.io.IOException(fakeSensitive)),"network-io"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new java.util.concurrent.CancellationException(fakeSensitive)),"transport-cancelled"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new java.util.concurrent.RejectedExecutionException(fakeSensitive)),"transport-unavailable"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new IllegalStateException(fakeSensitive)),"unclassified"),
            new WrappedCase(new java.util.concurrent.ExecutionException(
                new IllegalStateException()) ,"unclassified")
        );
        for(var fixture : cases) {
            String report=failureFields(request -> {
                if(request.uri().equals(McgatewayFriendCountProof.FRIENDS)) throw fixture.thrown();
                return resp("{\"targetFriendCount\":1}");
            });
            check(report.equals(" stage=friends-fetch category="+fixture.expected()));
            check(!report.contains(fakeSensitive) && !report.contains("123"));
        }
        // A successful HTTP read followed by a malformed friend row is a
        // roster validation failure, NOT an untrusted transport success.
        String rosterFailure=failureFields(new Stub(
            resp("{\"targetFriendCount\":1}"),
            resp("{\"people\":[{\"xuid\":\"1\",\"isFriend\":\"yes\"}]}")));
        check(rosterFailure.equals(" stage=friends-validate category=invalid-friends"));
        String sensitive="XBL3.0 token secret-authorization response-body xuid=123";
        String unknown=McgatewayFriendCountProof.safeFailureFields(
            new IllegalStateException(sensitive));
        check(unknown.equals(" stage=other category=unclassified"));
        check(!unknown.contains(sensitive) && !unknown.contains("123")
            && !unknown.contains("secret"));
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
    private static void upstreamRequestParity() throws Exception {
        // Pure request-construction assertions. No HTTP send, token lookup,
        // Docker, Xbox, or friend mutation occurs in this test.
        var summary = McgatewayFriendCountProof.buildUpstreamCompatibleRequest(
            new McgatewayFriendCountProof.Request(
                McgatewayFriendCountProof.SUMMARY, "3", "XBL3.0 fake-test-only",
                Duration.ofSeconds(8)));
        var friends = McgatewayFriendCountProof.buildUpstreamCompatibleRequest(
            new McgatewayFriendCountProof.Request(
                McgatewayFriendCountProof.FRIENDS, "7", "XBL3.0 fake-test-only",
                Duration.ofSeconds(8)));
        check("GET".equals(summary.method()) && "GET".equals(friends.method()));
        check(summary.uri().equals(McgatewayFriendCountProof.SUMMARY));
        check(friends.uri().equals(McgatewayFriendCountProof.FRIENDS));
        check("3".equals(summary.headers().firstValue("x-xbl-contract-version").orElse("")));
        check("7".equals(friends.headers().firstValue("x-xbl-contract-version").orElse("")));
        check("en-GB".equals(friends.headers().firstValue("accept-language").orElse("")));
        check(summary.headers().firstValue("accept-language").isEmpty());
        check(summary.headers().firstValue("Authorization").orElse("").equals("XBL3.0 fake-test-only"));
        check(friends.headers().firstValue("Authorization").orElse("").equals("XBL3.0 fake-test-only"));
        check(summary.headers().map().size() == 2 && friends.headers().map().size() == 3);
        for (HttpRequest request : List.of(summary, friends)) {
            check(request.headers().firstValue("Accept").isEmpty());
            check(request.headers().firstValue("Cache-Control").isEmpty());
            check(request.timeout().isPresent()
                && request.timeout().get().equals(Duration.ofSeconds(8)));
            check(request.bodyPublisher().isEmpty());
        }
        expectFailure(() -> McgatewayFriendCountProof.buildUpstreamCompatibleRequest(
            new McgatewayFriendCountProof.Request(
                java.net.URI.create("https://example.invalid/people"),
                "7", "XBL3.0 fake-test-only", Duration.ofSeconds(8))));
        expectFailure(() -> McgatewayFriendCountProof.buildUpstreamCompatibleRequest(
            new McgatewayFriendCountProof.Request(
                McgatewayFriendCountProof.FRIENDS,
                "3", "XBL3.0 fake-test-only", Duration.ofSeconds(8))));
        expectFailure(() -> McgatewayFriendCountProof.buildUpstreamCompatibleRequest(
            new McgatewayFriendCountProof.Request(
                McgatewayFriendCountProof.SUMMARY,
                "7", "XBL3.0 fake-test-only", Duration.ofSeconds(8))));
        try (HttpClient http2 = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .followRedirects(HttpClient.Redirect.NEVER).build()) {
            expectFailure(() -> McgatewayFriendCountProof.capture(
                http2, "XBL3.0 fake-test-only", NONCE));
        }
        try (HttpClient redirecting = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .followRedirects(HttpClient.Redirect.NORMAL).build()) {
            expectFailure(() -> McgatewayFriendCountProof.capture(
                redirecting, "XBL3.0 fake-test-only", NONCE));
        }
        // A correctly configured transport with invalid token input must
        // fail before requesting anything, including a DNS lookup.
        try (HttpClient correct = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .followRedirects(HttpClient.Redirect.NEVER).build()) {
            expectFailure(() -> McgatewayFriendCountProof.capture(
                correct, "", NONCE));
        }
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
