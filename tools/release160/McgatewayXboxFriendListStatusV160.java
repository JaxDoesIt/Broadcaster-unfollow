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
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.Flow;
import java.util.concurrent.TimeUnit;

/**
 * Operator-only, single GET, coarse friend-list diagnostic for a disposable
 * canary image. Does not mutate Xbox friendships or reveal any player data.
 *
 * All externally visible statuses are fixed strings. The selected target
 * stays inside the JVM and never appears in the console diagnostic marker.
 */
public final class McgatewayXboxFriendListStatusV160 {
    private static final int MAX_BYTES = 2 * 1024 * 1024;
    private static final int MAX_PEOPLE = 2000;
    private static final int MAX_FIELDS = 1000;
    private static final Duration TIMEOUT = Duration.ofSeconds(7);
    private static final URI FRIENDS =
        URI.create("https://peoplehub.xboxlive.com/users/me/people/friends");

    private McgatewayXboxFriendListStatusV160() { }

    record Request(URI uri, String auth, Duration timeout) {
        @Override public String toString() { return "Friend-list request [redacted]"; }
    }
    record Reply(int status, URI uri, Map<String,List<String>> headers,
                 byte[] body, boolean complete) {
        @Override public String toString() { return "Friend-list reply [redacted]"; }
    }
    @FunctionalInterface interface Fetcher { Reply get(Request request) throws Exception; }

    record Selection(String target, String reason) {
        @Override public String toString() { return "Friend-list selection [redacted]"; }
    }

    private static Selection fail(String reason) { return new Selection(null, reason); }
    private static boolean validXuid(String value) {
        if (value == null || !value.matches("[1-9][0-9]{0,19}")) return false;
        try { Long.parseUnsignedLong(value); return true; }
        catch (NumberFormatException ex) { return false; }
    }

    public static Selection capture(HttpClient client, String authorization, String self) {
        if (client == null || client.followRedirects() != HttpClient.Redirect.NEVER)
            return fail("list_unverified");
        return capture(request -> {
            HttpRequest http = HttpRequest.newBuilder(request.uri())
                .GET()
                .timeout(request.timeout())
                .header("Authorization", request.auth())
                .header("x-xbl-contract-version", "7")
                .header("Accept", "application/json")
                .header("Cache-Control", "no-store")
                .build();

            LimitedSubscriber body = new LimitedSubscriber();
            CompletableFuture<HttpResponse<byte[]>> pending =
                client.sendAsync(http, ignored -> body);
            try {
                HttpResponse<byte[]> response = pending.get(8, TimeUnit.SECONDS);
                return new Reply(response.statusCode(), response.uri(),
                    response.headers().map(), response.body(), true);
            } catch (Exception error) {
                body.cancel();
                pending.cancel(true);
                throw error;
            }
        }, authorization, self);
    }

    /** Offline tests supply a fake fetcher, never a network connection. */
    static Selection capture(Fetcher fetcher, String authorization, String self) {
        if (fetcher == null || authorization == null || authorization.isBlank()
                || !validXuid(self))
            return fail("list_unverified");
        try {
            Reply reply = fetcher.get(new Request(FRIENDS, authorization, TIMEOUT));
            if (reply == null || !FRIENDS.equals(reply.uri()))
                return fail("list_unverified");

            if (reply.status() != 200)
                return fail(switch (reply.status()) {
                    case 401, 403 -> "list_auth";
                    case 429 -> "list_limited";
                    default -> reply.status() >= 500 && reply.status() < 600
                        ? "list_server" : "list_other";
                });

            if (!reply.complete() || reply.body() == null
                    || reply.body().length == 0 || reply.body().length > MAX_BYTES
                    || !safeHeaders(reply.headers(), reply.body().length))
                return fail("list_invalid");

            String text = StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(reply.body())).toString();
            return inspect(text, self);
        } catch (Exception ignored) {
            return fail("list_unverified");
        }
    }

    private static boolean safeHeaders(Map<String,List<String>> headers, int bodySize) {
        if (headers == null) return false;
        String contentType = null, contentLength = null;
        Set<String> seen = new HashSet<>();
        for (var entry : headers.entrySet()) {
            if (entry.getKey() == null || entry.getValue() == null
                    || entry.getValue().size() != 1 || entry.getValue().get(0) == null)
                return false;
            String key = entry.getKey().toLowerCase(Locale.ROOT);
            if (!seen.add(key)) return false;
            String value = entry.getValue().get(0);
            if (value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0)
                return false;
            if (key.equals("content-type")) contentType = value;
            else if (key.equals("content-length")) contentLength = value;
            else if (key.equals("location") || key.equals("nextlink") || key.equals("continuationtoken"))
                return false;
            else if (key.equals("age") && !value.equals("0"))
                return false;
            else if (key.equals("x-cache") && value.toLowerCase(Locale.ROOT).contains("hit"))
                return false;
        }
        if (contentType == null ||
                !contentType.matches("(?i)application/json(?:;\\s*charset=utf-8)?"))
            return false;
        return contentLength == null ||
            (contentLength.matches("[0-9]{1,8}") &&
                Long.parseLong(contentLength) == bodySize);
    }

    private static Selection inspect(String json, String self) {
        try (JsonReader reader = new JsonReader(new StringReader(json))) {
            reader.setStrictness(Strictness.STRICT);
            if (reader.peek() != JsonToken.BEGIN_OBJECT)
                return fail("list_invalid");
            reader.beginObject();
            Set<String> rootFields = new HashSet<>();
            int fieldCount = 0, people = 0;
            boolean sawPeople = false, incomplete = false;
            String chosen = null;
            while (reader.hasNext()) {
                if (++fieldCount > MAX_FIELDS) return fail("list_invalid");
                String field = reader.nextName();
                if (!rootFields.add(field)) return fail("list_invalid");
                if (field.equals("people")) {
                    sawPeople = true;
                    if (reader.peek() != JsonToken.BEGIN_ARRAY) return fail("list_invalid");
                    reader.beginArray();
                    while (reader.hasNext()) {
                        if (++people > MAX_PEOPLE || reader.peek() != JsonToken.BEGIN_OBJECT)
                            return fail("list_invalid");
                        reader.beginObject();
                        Set<String> personFields = new HashSet<>();
                        String xuid = null;
                        int personFieldCount = 0;
                        while (reader.hasNext()) {
                            if (++personFieldCount > MAX_FIELDS) return fail("list_invalid");
                            String name = reader.nextName();
                            if (!personFields.add(name)) return fail("list_invalid");
                            if (name.equals("xuid") && reader.peek() == JsonToken.STRING)
                                xuid = reader.nextString();
                            else reader.skipValue();
                        }
                        reader.endObject();
                        if (chosen == null && validXuid(xuid) && !xuid.equals(self))
                            chosen = xuid;
                    }
                    reader.endArray();
                } else if (Set.of("continuationToken", "continuation", "next", "nextLink", "nextPage").contains(field)) {
                    if (reader.peek() == JsonToken.NULL) reader.nextNull();
                    else if (reader.peek() == JsonToken.STRING) {
                        if (!reader.nextString().isBlank()) incomplete = true;
                    } else {
                        reader.skipValue();
                        incomplete = true;
                    }
                } else reader.skipValue();
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT || !sawPeople)
                return fail("list_invalid");
            if (incomplete) return fail("list_incomplete");
            if (people == 0) return fail("list_empty");
            if (chosen == null) return fail("list_no_valid_target");
            return new Selection(chosen, "list_ready");
        } catch (Exception ignored) {
            return fail("list_invalid");
        }
    }

    static final class LimitedSubscriber implements HttpResponse.BodySubscriber<byte[]> {
        private final CompletableFuture<byte[]> result = new CompletableFuture<>();
        private final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        private volatile Flow.Subscription subscription;
        @Override public CompletionStage<byte[]> getBody() { return result; }
        @Override public void onSubscribe(Flow.Subscription next) {
            subscription = next;
            next.request(1);
        }
        @Override public void onNext(List<ByteBuffer> chunks) {
            if (result.isDone()) return;
            try {
                for (ByteBuffer chunk : chunks) {
                    if (chunk.remaining() > MAX_BYTES - bytes.size())
                        throw new IOException("bounded friend-list response exceeded");
                    byte[] next = new byte[chunk.remaining()];
                    chunk.get(next);
                    bytes.write(next);
                }
                if (subscription != null) subscription.request(1);
            } catch (Exception error) {
                cancel();
                result.completeExceptionally(error);
            }
        }
        @Override public void onError(Throwable error) { result.completeExceptionally(error); }
        @Override public void onComplete() { result.complete(bytes.toByteArray()); }
        void cancel() { if (subscription != null) subscription.cancel(); }
    }
}
