package com.rtm516.mcxboxbroadcast.core;

import com.google.gson.Strictness;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.Flow;
import java.util.concurrent.TimeUnit;

/**
 * In-process GET-only PersonSummary schema diagnostic candidate.
 * SOURCE ONLY: no console command, updater or live broadcaster imports this.
 * Never report authentication, XUID, booleans, response bodies or exceptions.
 * Schema evidence is NOT authorization to remove a friendship.
 */
public final class McgatewayXboxPersonSummaryProbeV160 {
    private static final int MAX_BYTES = 16_384, MAX_NODES = 512, MAX_DEPTH = 12;
    private static final Pattern XUID = Pattern.compile("[1-9][0-9]{0,19}");
    private static final Pattern NONCE = Pattern.compile("[0-9a-f]{32}");
    private static final Duration TIMEOUT = Duration.ofSeconds(7);
    private static final String URL_PREFIX = "https://social.xboxlive.com/users/xuid(";
    private static final String URL_SUFFIX = ")/summary";
    private McgatewayXboxPersonSummaryProbeV160() { }

    record Request(URI uri, String authorization, Duration timeout) {
        @Override public String toString() { return "PersonSummary GET request [redacted]"; }
    }
    record Reply(int status, URI uri, Map<String,List<String>> headers,
                 byte[] body, boolean complete) {
        @Override public String toString() { return "PersonSummary response [redacted]"; }
    }
    @FunctionalInterface interface Fetcher { Reply get(Request request) throws Exception; }
    private enum Kind { BOOLEAN, OTHER }
    private static final class Counter { int nodes; }

    private static boolean isXuid(String id) {
        if (id == null || !XUID.matcher(id).matches()) return false;
        try { Long.parseUnsignedLong(id); return true; }
        catch (NumberFormatException e) { return false; }
    }

    private static String verdict(String nonce, String status, String schema) {
        // The nonce is caller-generated, fixed-format non-secret correlation only.
        return "MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=" + nonce +
            " http=" + status + " fields=" + schema +
            " can_authorize_removal=false";
    }

    /**
     * A future in-process caller supplies its EXISTING Xbox header and a
     * preselected cached-friend target. Neither may be a console argument.
     * Exactly one GET is permitted. No automatic retry or token persistence.
     */
    public static String capture(HttpClient client, String authorization, String target, String nonce) {
        if (client == null || client.followRedirects() != HttpClient.Redirect.NEVER)
            return verdict("invalid", "unverified", "unverified");
        return capture(request -> {
            HttpRequest http = HttpRequest.newBuilder(request.uri()).GET()
                .timeout(request.timeout())
                .header("Authorization", request.authorization())
                .header("x-xbl-contract-version", "3")
                .header("Cache-Control", "no-store")
                .build();
            // The custom subscriber enforces the cap DURING reception. Waiting
            // for the completed response enforces a deadline even if HTTP
            // headers arrived but the body stream stalls indefinitely.
            LimitedSubscriber subscriber = new LimitedSubscriber();
            CompletableFuture<HttpResponse<byte[]>> future = client.sendAsync(
                http, ignored -> subscriber);
            try {
                HttpResponse<byte[]> response = future.get(8, TimeUnit.SECONDS);
                return new Reply(response.statusCode(), response.uri(),
                    response.headers().map(), response.body(), true);
            } catch (Exception error) {
                subscriber.cancel();
                future.cancel(true);
                throw error;
            }
        }, authorization, target, nonce);
    }

    static String capture(Fetcher fetcher, String authorization, String target, String nonce) {
        if (fetcher == null || authorization == null || authorization.isBlank() ||
            !isXuid(target) || nonce == null || !NONCE.matcher(nonce).matches())
            return verdict("invalid", "unverified", "unverified");
        try {
            URI uri = URI.create(URL_PREFIX + target + URL_SUFFIX);
            Reply reply = fetcher.get(new Request(uri, authorization, TIMEOUT));
            if (reply == null) return verdict(nonce, "unverified", "unverified");
            String http = reply.status() == 200 ? "200" :
                reply.status() == 401 || reply.status() == 403 ? "auth" :
                reply.status() == 429 ? "limited" :
                reply.status() >= 500 && reply.status() <= 599 ? "server" : "other";
            if (reply.status() != 200 || !uri.equals(reply.uri()) || !reply.complete() ||
                reply.body() == null || reply.body().length < 2 || reply.body().length > MAX_BYTES ||
                !validHeaders(reply.headers(), reply.body().length))
                return verdict(nonce, http, "unverified");
            String body = StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(reply.body())).toString();
            return verdict(nonce, http, fieldShape(body));
        } catch (Exception ignored) {
            return verdict(nonce, "unverified", "unverified");
        }
    }

    static final class LimitedSubscriber implements HttpResponse.BodySubscriber<byte[]> {
        private final CompletableFuture<byte[]> body = new CompletableFuture<>();
        private final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        private volatile Flow.Subscription subscription;

        @Override public CompletionStage<byte[]> getBody() { return body; }
        @Override public void onSubscribe(Flow.Subscription next) {
            subscription = next;
            next.request(1);
        }
        @Override public void onNext(List<ByteBuffer> buffers) {
            if (body.isDone()) return;
            try {
                for (ByteBuffer buffer : buffers) {
                    if (buffer.remaining() > MAX_BYTES - bytes.size())
                        throw new IOException("response budget exceeded");
                    byte[] chunk = new byte[buffer.remaining()];
                    buffer.get(chunk);
                    bytes.write(chunk);
                }
                if (subscription != null) subscription.request(1);
            } catch (Exception error) {
                cancel(); body.completeExceptionally(error);
            }
        }
        @Override public void onError(Throwable error) { body.completeExceptionally(error); }
        @Override public void onComplete() { body.complete(bytes.toByteArray()); }
        void cancel() { if (subscription != null) subscription.cancel(); }
    }

    private static boolean validHeaders(Map<String,List<String>> headers, int size) {
        if (headers == null) return false;
        String type = null, contentLength = null;
        Set<String> seen = new HashSet<>();
        for (var entry : headers.entrySet()) {
            if (entry.getKey() == null || entry.getValue() == null ||
                entry.getValue().size() != 1 || entry.getValue().get(0) == null) return false;
            String key = entry.getKey().toLowerCase(Locale.ROOT);
            if (!seen.add(key)) return false;
            String value = entry.getValue().get(0);
            if (value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0) return false;
            if (key.equals("content-type")) type = value;
            else if (key.equals("content-length")) contentLength = value;
            else if (key.equals("age") && !value.equals("0")) return false;
            else if (key.equals("x-cache") && value.toLowerCase(Locale.ROOT).contains("hit")) return false;
            else if (Set.of("location", "link", "continuation", "next", "nextlink")
                .contains(key)) return false;
        }
        if (type == null || !type.matches("(?i)application/json(?:;\\s*charset=utf-8)?")) return false;
        return contentLength == null ||
            (contentLength.matches("[0-9]{1,5}") && Integer.parseInt(contentLength) == size);
    }

    private static String fieldShape(String json) throws IOException {
        try (JsonReader reader = new JsonReader(new StringReader(json))) {
            reader.setStrictness(Strictness.STRICT);
            if (reader.peek() != JsonToken.BEGIN_OBJECT) return "unverified";
            reader.beginObject();
            Set<String> seen = new HashSet<>();
            Kind caller = null, target = null;
            Counter budget = new Counter();
            while (reader.hasNext()) {
                String name = reader.nextName();
                if (!seen.add(name)) return "unverified";
                Kind kind = consume(reader, 0, budget);
                if (name.equals("isCallerFollowingTarget")) caller = kind;
                else if (name.equals("isTargetFollowingCaller")) target = kind;
                else if (Set.of("pagination", "nextLink", "continuationToken", "people")
                    .contains(name)) return "unverified";
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT) return "unverified";
            return caller == Kind.BOOLEAN && target == Kind.BOOLEAN ? "two_boolean_fields" :
                caller == null || target == null ? "missing_field" : "untyped_field";
        }
    }

    private static Kind consume(JsonReader reader, int depth, Counter budget) throws IOException {
        if (++budget.nodes > MAX_NODES || depth > MAX_DEPTH)
            throw new IOException("JSON complexity budget exceeded");
        return switch (reader.peek()) {
            case BOOLEAN -> { reader.nextBoolean(); yield Kind.BOOLEAN; }
            case STRING -> { reader.nextString(); yield Kind.OTHER; }
            case NUMBER -> { reader.nextString(); yield Kind.OTHER; }
            case NULL -> { reader.nextNull(); yield Kind.OTHER; }
            case BEGIN_ARRAY -> {
                reader.beginArray();
                while (reader.hasNext()) consume(reader, depth+1, budget);
                reader.endArray(); yield Kind.OTHER;
            }
            case BEGIN_OBJECT -> {
                reader.beginObject(); Set<String> seen = new HashSet<>();
                while (reader.hasNext()) {
                    if (!seen.add(reader.nextName())) throw new IOException("duplicate JSON key");
                    consume(reader, depth+1, budget);
                }
                reader.endObject(); yield Kind.OTHER;
            }
            default -> throw new IOException("invalid token");
        };
    }
}
