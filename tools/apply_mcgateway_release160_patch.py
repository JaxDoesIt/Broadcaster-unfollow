#!/usr/bin/env python3
"""Exact Release160 overlay.  V2 removal is default-denied and source-only."""
import argparse, hashlib, sys
from pathlib import Path

# Installed only into a disposable upstream build tree.  V2 intentionally does
# not touch the cached list, player history, normal queue or friend count.
V2_FRIEND_MANAGER = r'''
    // MCGATEWAY_RELEASE160_FRIEND_REMOVE_V2: strict, target-scoped proof.
    private static final int MCGATEWAY_V2_MAX_BODY_BYTES = 16 * 1024;
    private static final int MCGATEWAY_V2_MAX_NONCES = 4_096;
    private static final long MCGATEWAY_V2_NONCE_TTL_MS = 15L * 60L * 1_000L;
    private final java.util.concurrent.locks.ReentrantReadWriteLock mcgatewayV2Lock = new java.util.concurrent.locks.ReentrantReadWriteLock();
    static final class McgatewayV2NonceWindow {
        private final java.util.LinkedHashMap<String, Long> consumed = new java.util.LinkedHashMap<>();
        synchronized boolean consume(String nonce) { return consume(nonce, System.currentTimeMillis()); }
        synchronized boolean consume(String nonce, long nowMs) {
            if (!mcgatewayV2Nonce(nonce)) return false;
            consumed.entrySet().removeIf(entry -> nowMs - entry.getValue() >= MCGATEWAY_V2_NONCE_TTL_MS);
            if (consumed.containsKey(nonce)) return false;
            while (consumed.size() >= MCGATEWAY_V2_MAX_NONCES) {
                java.util.Iterator<String> oldest = consumed.keySet().iterator();
                if (!oldest.hasNext()) break;
                oldest.next();
                oldest.remove();
            }
            consumed.put(nonce, nowMs);
            return true;
        }
        synchronized int size() { return consumed.size(); }
    }
    private final McgatewayV2NonceWindow mcgatewayV2Nonces = new McgatewayV2NonceWindow();
    private final HttpClient mcgatewayV2HttpClient = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).connectTimeout(java.time.Duration.ofSeconds(8)).build();
    private record McgatewayV2State(String state, boolean removable) { }
    private enum McgatewayV2ReadPhase { OBSERVE, BEFORE_DELETE, AFTER_DELETE, BEFORE_RESTORE }
    private enum McgatewayV2StateDiagnostic {
        INVALID_REQUEST("input", "invalid-request"), NONCE_REJECTED("input", "nonce-rejected"),
        NORMAL_FRIEND_WORK_BUSY("lock", "normal-friend-work-busy"), SESSION_UNAVAILABLE("identity", "session-unavailable"),
        IDENTITY_CHANGED("identity", "identity-changed"), TARGET_QUEUED("queue", "target-queued"),
        TIMEOUT("transport", "timeout"), TRANSPORT("transport", "transport"), REDIRECT("response", "redirect"),
        HTTP_400("response", "http-400"), HTTP_401("response", "http-401"), HTTP_403("response", "http-403"), HTTP_404("response", "http-404"),
        HTTP_408("response", "http-408"), HTTP_409("response", "http-409"), HTTP_429("response", "http-429"), HTTP_500("response", "http-500"),
        HTTP_502("response", "http-502"), HTTP_503("response", "http-503"), HTTP_504("response", "http-504"), HTTP_OTHER("response", "http-other"),
        CONTENT_TYPE("response", "content-type"), HEADERS("response", "headers"), DATE("response", "date"), AGE("response", "age"),
        BODY_LIMIT("body", "body-limit"), UTF8("body", "utf8"), JSON("parse", "json"), SCHEMA("parse", "schema"), INTERNAL("internal", "internal");
        private final String stage, category;
        McgatewayV2StateDiagnostic(String stage, String category) { this.stage = stage; this.category = category; }
    }
    private static final class McgatewayV2StateException extends Exception {
        private final McgatewayV2StateDiagnostic diagnostic;
        private McgatewayV2StateException(McgatewayV2StateDiagnostic diagnostic) { this.diagnostic = diagnostic; }
    }
    private static McgatewayV2StateException mcgatewayV2StateFail(McgatewayV2StateDiagnostic diagnostic) { return new McgatewayV2StateException(diagnostic); }
    private static McgatewayV2StateDiagnostic mcgatewayV2StateDiagnostic(Throwable error) {
        if (error instanceof McgatewayV2StateException typed) return typed.diagnostic;
        if (error instanceof java.util.concurrent.TimeoutException) return McgatewayV2StateDiagnostic.TIMEOUT;
        return McgatewayV2StateDiagnostic.INTERNAL;
    }
    private static McgatewayV2StateDiagnostic mcgatewayV2HttpDiagnostic(int status) {
        return switch (status) {
            case 400 -> McgatewayV2StateDiagnostic.HTTP_400; case 401 -> McgatewayV2StateDiagnostic.HTTP_401;
            case 403 -> McgatewayV2StateDiagnostic.HTTP_403; case 404 -> McgatewayV2StateDiagnostic.HTTP_404;
            case 408 -> McgatewayV2StateDiagnostic.HTTP_408; case 409 -> McgatewayV2StateDiagnostic.HTTP_409;
            case 429 -> McgatewayV2StateDiagnostic.HTTP_429; case 500 -> McgatewayV2StateDiagnostic.HTTP_500;
            case 502 -> McgatewayV2StateDiagnostic.HTTP_502; case 503 -> McgatewayV2StateDiagnostic.HTTP_503;
            case 504 -> McgatewayV2StateDiagnostic.HTTP_504; default -> McgatewayV2StateDiagnostic.HTTP_OTHER;
        };
    }
    private static String mcgatewayV2StateUnknown(String nonce, String target, String account, String session, McgatewayV2StateDiagnostic diagnostic) {
        return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " state=unknown verified=false stage=" + diagnostic.stage + " category=" + diagnostic.category;
    }
    private static boolean mcgatewayV2Nonce(String value) { return value != null && value.matches("[0-9a-f]{32}"); }
    private static boolean mcgatewayV2Xuid(String value) { return value != null && value.matches("[1-9][0-9]{0,19}"); }
    private boolean mcgatewayV2Consume(String nonce) {
        // The controller owns the durable replay fence. This process-local
        // window only rejects recent duplicate console requests; expiry keeps
        // a long-lived bot from permanently exhausting command capacity.
        return mcgatewayV2Nonces.consume(nonce);
    }
    private static String mcgatewayV2Hash(String value) throws Exception {
        byte[] bytes = java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder(64); for (byte b : bytes) out.append(String.format("%02x", b & 0xff)); return out.toString();
    }
    private static String mcgatewayV2Utf8(byte[] bytes) throws Exception {
        if (bytes == null || bytes.length == 0 || bytes.length > MCGATEWAY_V2_MAX_BODY_BYTES) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.BODY_LIMIT);
        try {
            return java.nio.charset.StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(bytes)).toString();
        } catch (java.nio.charset.CharacterCodingException error) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.UTF8); }
    }
    private static long mcgatewayV2Remaining(long deadline) throws Exception {
        long remaining = java.util.concurrent.TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime());
        if (remaining < 1L) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TIMEOUT);
        return remaining;
    }
    private static HttpResponse.BodyHandler<byte[]> mcgatewayV2BodyHandler() {
        return info -> new HttpResponse.BodySubscriber<>() {
            private final java.util.concurrent.CompletableFuture<byte[]> result = new java.util.concurrent.CompletableFuture<>();
            private final java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            private java.util.concurrent.Flow.Subscription subscription;
            public java.util.concurrent.CompletionStage<byte[]> getBody() { return result; }
            public void onSubscribe(java.util.concurrent.Flow.Subscription value) { subscription = value; value.request(Long.MAX_VALUE); }
            public void onNext(java.util.List<java.nio.ByteBuffer> chunks) {
                if (result.isDone()) return;
                try { for (java.nio.ByteBuffer chunk : chunks) { int count = chunk.remaining(); if (count > MCGATEWAY_V2_MAX_BODY_BYTES - bytes.size()) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.BODY_LIMIT); byte[] part = new byte[count]; chunk.get(part); bytes.write(part); } }
                catch (Exception error) { subscription.cancel(); result.completeExceptionally(error); }
            }
            public void onError(Throwable error) { result.completeExceptionally(mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT)); }
            public void onComplete() { if (!result.isDone()) result.complete(bytes.toByteArray()); }
        };
    }
    private HttpResponse<byte[]> mcgatewayV2Send(HttpRequest request, long deadline) throws Exception {
        java.util.concurrent.CompletableFuture<HttpResponse<byte[]>> future;
        try { future = mcgatewayV2HttpClient.sendAsync(request, mcgatewayV2BodyHandler()); }
        catch (Exception error) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT); }
        try { return future.get(mcgatewayV2Remaining(deadline), java.util.concurrent.TimeUnit.MILLISECONDS); }
        catch (java.util.concurrent.TimeoutException error) { future.cancel(true); throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TIMEOUT); }
        catch (java.util.concurrent.ExecutionException error) {
            Throwable cause = error.getCause();
            if (cause instanceof McgatewayV2StateException typed) throw typed;
            throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT);
        } catch (java.util.concurrent.CancellationException error) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT); }
        catch (InterruptedException error) { Thread.currentThread().interrupt(); throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT); }
    }
    private static void mcgatewayV2Skip(com.google.gson.stream.JsonReader r, int depth) throws Exception {
        if (depth > 8) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON);
        switch (r.peek()) {
            case BEGIN_OBJECT -> { java.util.Set<String> names = new java.util.HashSet<>(); r.beginObject(); while (r.hasNext()) { if (!names.add(r.nextName())) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON); mcgatewayV2Skip(r, depth + 1); } r.endObject(); }
            case BEGIN_ARRAY -> { int count = 0; r.beginArray(); while (r.hasNext()) { if (++count > 64) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON); mcgatewayV2Skip(r, depth + 1); } r.endArray(); }
            case STRING -> { if (r.nextString().length() > 256) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON); }
            case NUMBER -> { if (r.nextString().length() > 64) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON); }
            case BOOLEAN -> r.nextBoolean();
            case NULL -> r.nextNull();
            default -> throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON);
        }
    }
    private static McgatewayV2State mcgatewayV2Parse(String body, String target) throws Exception {
        try {
            com.google.gson.stream.JsonReader r = new com.google.gson.stream.JsonReader(new java.io.StringReader(body)); r.setLenient(false);
            if (r.peek() != com.google.gson.stream.JsonToken.BEGIN_OBJECT) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA);
            java.util.Set<String> names = new java.util.HashSet<>(); String xuid = null; Boolean friend = null, sent = null, received = null;
            r.beginObject(); while (r.hasNext()) { String name = r.nextName(); if (!names.add(name)) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA);
                if (name.equals("xuid")) { if (r.peek() != com.google.gson.stream.JsonToken.STRING) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA); xuid = r.nextString(); }
                else if (name.equals("isFriend") || name.equals("friendRequestSent") || name.equals("friendRequestReceived")) {
                    if (r.peek() != com.google.gson.stream.JsonToken.BOOLEAN) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA); Boolean v = r.nextBoolean();
                    if (name.equals("isFriend")) friend = v; else if (name.equals("friendRequestSent")) sent = v; else received = v;
                } else mcgatewayV2Skip(r, 0);
            } r.endObject();
            if (r.peek() != com.google.gson.stream.JsonToken.END_DOCUMENT || !target.equals(xuid) || friend == null || sent == null || received == null) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.SCHEMA);
            return new McgatewayV2State(friend || sent || received ? "present" : "absent", friend && !sent && !received);
        } catch (McgatewayV2StateException error) { throw error; }
        catch (Exception error) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.JSON); }
    }
    private McgatewayV2State mcgatewayV2Read(String target, String account, String session, long deadline, McgatewayV2ReadPhase phase) throws Exception {
        if (toAdd.containsKey(target) || toRemove.containsKey(target)) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TARGET_QUEUED);
        if (!account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.IDENTITY_CHANGED);
        URI uri = URI.create(Constants.PEOPLE.formatted(target));
        HttpRequest request;
        try { request = HttpRequest.newBuilder().uri(uri).timeout(java.time.Duration.ofMillis(Math.min(8_000L, mcgatewayV2Remaining(deadline)))).header("Authorization", sessionManager.getTokenHeader())
            .header("x-xbl-contract-version", "3").header("Cache-Control", "no-cache").header("Pragma", "no-cache").GET().build(); }
        catch (McgatewayV2StateException error) { throw error; }
        catch (Exception error) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.TRANSPORT); }
        HttpResponse<byte[]> response = mcgatewayV2Send(request, deadline);
        if (!uri.equals(response.uri()) || (response.statusCode() >= 300 && response.statusCode() < 400)) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.REDIRECT);
        // A 404 NEVER supplies observation or mutation admission. Only an exact
        // post-read following strict pre-state + successful DELETE may use it.
        boolean postDelete404 = (phase == McgatewayV2ReadPhase.AFTER_DELETE || phase == McgatewayV2ReadPhase.BEFORE_RESTORE) && response.statusCode() == 404;
        // Xbox's post-delete target GET may be a header-light 404. The exact URI,
        // phase and stable session identity are the bounded absence evidence;
        // body freshness headers are not present to parse on this response.
        if (postDelete404) {
            if (!account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.IDENTITY_CHANGED);
            return new McgatewayV2State("friendship-absent", false);
        }
        if (response.statusCode() != 200) throw mcgatewayV2StateFail(mcgatewayV2HttpDiagnostic(response.statusCode()));
        java.util.List<String> types = response.headers().allValues("Content-Type"), ages = response.headers().allValues("Age"), dates = response.headers().allValues("Date");
        if (types.size() != 1 || ages.size() > 1 || dates.size() != 1) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.HEADERS);
        String type = types.get(0).split(";", 2)[0].trim().toLowerCase(java.util.Locale.ROOT); long age;
        try { age = ages.isEmpty() ? 0L : Long.parseLong(ages.get(0)); } catch (Exception e) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.AGE); }
        String date = dates.get(0); long dateMs;
        try { dateMs = java.time.ZonedDateTime.parse(date, java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME).toInstant().toEpochMilli(); } catch (Exception e) { throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.DATE); }
        if (!type.equals("application/json")) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.CONTENT_TYPE);
        if (age != 0) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.AGE);
        if (Math.abs(System.currentTimeMillis() - dateMs) > 60_000L) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.DATE);
        if (!account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())) throw mcgatewayV2StateFail(McgatewayV2StateDiagnostic.IDENTITY_CHANGED);
        return mcgatewayV2Parse(mcgatewayV2Utf8(response.body()), target);
    }
    private String mcgatewayV2Failure(String marker, String nonce, String target, String account, String session, String pre) {
        return marker + " nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " result=uncertain pre=" + pre + " post=unknown verified=false";
    }
    public String mcgatewayFriendStateV2(String nonce, String target) {
        String shownNonce = mcgatewayV2Nonce(nonce) ? nonce : "invalid", shownTarget = mcgatewayV2Xuid(target) ? target : "invalid";
        if (!mcgatewayV2Nonce(nonce) || !mcgatewayV2Xuid(target)) return mcgatewayV2StateUnknown(shownNonce, shownTarget, "unavailable", "unavailable", McgatewayV2StateDiagnostic.INVALID_REQUEST);
        if (!mcgatewayV2Consume(nonce)) return mcgatewayV2StateUnknown(nonce, target, "unavailable", "unavailable", McgatewayV2StateDiagnostic.NONCE_REJECTED);
        if (!mcgatewayV2Lock.writeLock().tryLock()) return mcgatewayV2StateUnknown(nonce, target, "unavailable", "unavailable", McgatewayV2StateDiagnostic.NORMAL_FRIEND_WORK_BUSY);
        String hash = "unavailable", session = "unavailable";
        try {
            long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(20); String account, rawSession;
            try { account = sessionManager.getXuid(); rawSession = sessionManager.mcgatewayV2SessionIdentity(); hash = mcgatewayV2Hash(account); session = mcgatewayV2Hash(rawSession); }
            catch (Exception error) { return mcgatewayV2StateUnknown(nonce, target, hash, session, McgatewayV2StateDiagnostic.SESSION_UNAVAILABLE); }
            McgatewayV2State state = mcgatewayV2Read(target, account, rawSession, deadline, McgatewayV2ReadPhase.OBSERVE); return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + hash + " session=" + session + " state=" + state.state() + " verified=true";
        } catch (Exception error) { return mcgatewayV2StateUnknown(nonce, target, hash, session, mcgatewayV2StateDiagnostic(error)); }
        finally { mcgatewayV2Lock.writeLock().unlock(); }
    }
    public String mcgatewayFriendRemoveV2(String nonce, String target) {
        if (!mcgatewayV2Xuid(target) || !mcgatewayV2Consume(nonce)) return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=" + (mcgatewayV2Nonce(nonce) ? nonce : "invalid") + " xuid=" + (mcgatewayV2Xuid(target) ? target : "invalid") + " account=unavailable session=unavailable result=uncertain pre=unknown post=unknown verified=false";
        if (!mcgatewayV2Lock.writeLock().tryLock()) return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=unavailable session=unavailable result=uncertain pre=unknown post=unknown verified=false";
        String account = "unavailable", session = "unavailable", pre = "unknown";
        try { long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(20); String raw = sessionManager.getXuid(), rawSession = sessionManager.mcgatewayV2SessionIdentity(); account = mcgatewayV2Hash(raw); session = mcgatewayV2Hash(rawSession);
            McgatewayV2State before = mcgatewayV2Read(target, raw, rawSession, deadline, McgatewayV2ReadPhase.BEFORE_DELETE); pre = before.state();
            if (!before.removable()) throw new IllegalStateException("pending");
            if (toAdd.containsKey(target) || toRemove.containsKey(target) || !raw.equals(sessionManager.getXuid()) || !rawSession.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("identity-before-delete");
            URI uri = URI.create(Constants.FRIEND.formatted(target)); HttpRequest request = HttpRequest.newBuilder().uri(uri).timeout(java.time.Duration.ofMillis(Math.min(8_000L, mcgatewayV2Remaining(deadline)))).header("Authorization", sessionManager.getTokenHeader()).DELETE().build();
            HttpResponse<byte[]> deleted = mcgatewayV2Send(request, deadline);
            if ((deleted.statusCode() != 200 && deleted.statusCode() != 204) || !uri.equals(deleted.uri()) || !raw.equals(sessionManager.getXuid()) || !rawSession.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("delete");
            McgatewayV2State after;
            // Xbox may briefly keep serving the pre-remove relationship after
            // an accepted DELETE. Poll the same target within the existing
            // deadline; never reissue DELETE.
            do {
                after = mcgatewayV2Read(target, raw, rawSession, deadline, McgatewayV2ReadPhase.AFTER_DELETE);
                if (after.state().equals("absent") || after.state().equals("friendship-absent")) break;
                if (mcgatewayV2Remaining(deadline) < 750L) throw new IllegalStateException("post");
                try { Thread.sleep(250L); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw interrupted; }
            } while (true);
            return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " result=removed pre=present post=" + after.state() + " verified=true" + (after.state().equals("friendship-absent") ? " basis=target-404-after-delete" : "");
        } catch (Exception e) { return mcgatewayV2Failure("MCGATEWAY_FRIEND_REMOVE_V160_V2", mcgatewayV2Nonce(nonce) ? nonce : "invalid", mcgatewayV2Xuid(target) ? target : "invalid", account, session, pre); }
        finally { mcgatewayV2Lock.writeLock().unlock(); }
    }

'''

V2_FRIEND_MANAGER += (Path(__file__).parent / 'release160/recovery-fragment.java.inc').read_text()

EDITS = [
    # Upstream SessionManager schedules expiry even if MCGateway's console deletion is denied.
    # Original exact pinned GitHub git-blob SHA-1 (full file bytes, including Git blob header).
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java',
     'gitblob_sha1:3faaef8fda8e2737e7dad6e6631b53c42ea56482',
     '''        if (friendSyncConfig.expiry().enabled()) {
            scheduledThreadPool.scheduleWithFixedDelay(this::expireFriends, 10, friendSyncConfig.expiry().check(), TimeUnit.SECONDS);
        }''',
     '''        // MCGATEWAY_RELEASE160_EXPIRY_HOLD: never schedule upstream removal.
        // MCGateway owns friendship cleanup and Release160 has no reviewed
        // deletion receipt contract. Keep every legacy friend intact.
        logger.warn("MCGateway release160: upstream automatic friend expiry is disabled.");'''),
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/FriendManager.java',
     '8531633fb9ef38540d2f02923c689d3443f01fb6223938fcb4b80282fedd7de2',
     '    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {',
     r'''    // MCGATEWAY_RELEASE160_READONLY_OVERLAY: a complete, successful HTTP reply only.
    public int mcgatewayExactFriendCount() throws XboxFriendsException {
        HttpRequest request = HttpRequest.newBuilder().uri(Constants.FRIENDS)
            .timeout(java.time.Duration.ofSeconds(20))
            .header("Authorization", sessionManager.getTokenHeader())
            .header("x-xbl-contract-version", "7").GET().build();
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) throw new IllegalStateException("friend snapshot HTTP " + response.statusCode());
            var body = com.google.gson.JsonParser.parseString(response.body()).getAsJsonObject();
            if (!body.has("people") || !body.get("people").isJsonArray()) throw new IllegalStateException("missing people snapshot");
            for (String continuation : new String[]{"continuationToken", "nextLink", "next"}) {
                if (body.has(continuation) && !body.get(continuation).isJsonNull() && !body.get(continuation).getAsString().isBlank())
                    throw new IllegalStateException("incomplete paginated friend snapshot");
            }
            java.util.Set<String> seen = new java.util.HashSet<>();
            int count = 0;
            for (var element : body.getAsJsonArray("people")) {
                var person = element.getAsJsonObject();
                if (!person.has("xuid") || !person.get("xuid").isJsonPrimitive() || !person.get("xuid").getAsJsonPrimitive().isString()
                    || !person.get("xuid").getAsString().matches("[0-9]{1,20}")
                    || !seen.add(person.get("xuid").getAsString()) || !person.has("isFriend")
                    || !person.get("isFriend").isJsonPrimitive() || !person.get("isFriend").getAsJsonPrimitive().isBoolean())
                    throw new IllegalStateException("invalid/duplicate friend identity or relationship");
                if (person.get("isFriend").getAsBoolean()) count++;
            }
            return count;
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new XboxFriendsException("friend count interrupted");
        } catch (Exception error) {
            throw new XboxFriendsException("unavailable exact friend count: " + error.getMessage());
        }
    }

    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {'''),
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManagerCore.java',
     'bbf8812477decc41e2008a520e7f5ec13c0071ede6fa8a960199cf1b1c886a29',
     '    public Logger logger() {\n        return logger;\n    }',
     r'''    public Logger logger() {
        return logger;
    }

    public String mcgatewayHealthLine() {
        boolean rta = rtaWebsocket != null && rtaWebsocket.isOpen();
        boolean httpSignaling = signaling != null && signaling.isActive();
        boolean published = sessionInfo != null && sessionInfo.getHandleId() != null && !sessionInfo.getHandleId().isBlank();
        return "MCGATEWAY_HEALTH_V160 initialized=" + initialized + " rta=" + rta + " httpSignaling=" + httpSignaling + " published=" + published;
    }

    /** Stable, non-secret binding for one authenticated published session. */
    public String mcgatewayV2SessionIdentity() {
        String handle = sessionInfo == null ? null : sessionInfo.getHandleId();
        if (handle == null || handle.isBlank()) throw new IllegalStateException("session handle unavailable");
        return getXuid() + "|" + handle;
    }'''),
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/nethernet/HttpRelaySignaling.java',
     'b2a2327227f21549b2bb229e708899be638ef5ffcb2cb9ca95c7822703d2be85',
     '            logger.info("Relayed bedrock client " + gamertag + " (" + xuid + ") to target server.");',
     r'''            logger.info("Relayed bedrock client " + gamertag + " (" + xuid + ") to target server.");
            logger.info("MCGATEWAY_RELAY_IDENTITY_V1 xuid=" + xuid);
            logger.info("MCGATEWAY_RELAY_SIGNALLED_V1 xuid=" + xuid);'''),
    ('bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java',
     '26e97e2c8cd54b4df8b1177258db70d8148c04c7d6c4ba1231e73302d21a0c7a',
     '                case "version" -> info("MCXboxBroadcast Standalone " + BuildData.VERSION);',
     r'''                case "health" -> info(StandaloneMain.sessionManager.mcgatewayHealthLine());
                case "friendcount" -> {
                    try { info("MCGATEWAY_FRIEND_COUNT_V160 count=" + StandaloneMain.sessionManager.friendManager().mcgatewayExactFriendCount()); }
                    catch (Exception error) { warn("MCGATEWAY_FRIEND_COUNT_V160 ERROR unavailable"); }
                }
                case "friends" -> warn("friends remove is DENIED: release160 removal contract requires a separate review.");
                case "version" -> info("MCXboxBroadcast Standalone " + BuildData.VERSION);'''),
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java',
     '34fc61332904d73ea38c75cf551215d987b5d4e77badcf7807cf6005de01533f',
     '        if (originallyEmpty || currentVersion != newVersion) {',
     r'''        // Existing config remains byte-identical for exact release154 image rollback.
        // All version transformations still apply to the in-memory config above.
        if (originallyEmpty) {'''),
]

# The only source change is inserted beside the existing exact-count helper.
_friend_edit = list(EDITS[1])
_friend_edit[3] = _friend_edit[3].replace(
    '    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {',
    V2_FRIEND_MANAGER + '    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {'
)
EDITS[1] = tuple(_friend_edit)

# The legacy command remains denied; a V2 mutation requires its own explicit
# feature mode and can never be reached through `friends remove`.
_logger_edit = list(EDITS[4])
_logger_edit[3] = _logger_edit[3].replace(
    '                case "friends" -> warn("friends remove is DENIED: release160 removal contract requires a separate review.");',
    r'''                case "friendstatev160" -> {
                    if (args.length != 2) warn("MCGATEWAY_FRIEND_STATE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable state=unknown verified=false stage=input category=invalid-request");
                    else info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendStateV2(args[0], args[1]));
                }
                case "friendrehearsev160", "friendrestorev160" -> {
                    if (args.length != 3) warn("MCGATEWAY_FRIEND_RECOVERY_V160_V1 invalid-request");
                    else info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendRecoveryV1(args[0], args[1], args[2], commandNode.equals("friendrehearsev160")));
                }
                case "friendremovev160" -> {
                    if (!"owner-reviewed-v2".equals(System.getenv("MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE")) || args.length != 2)
                        warn("MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable result=uncertain pre=unknown post=unknown verified=false");
                    else info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendRemoveV2(args[0], args[1]));
                }
                case "friends" -> warn("friends remove is DENIED: release160 removal contract requires a separate review.");'''
)
EDITS[4] = tuple(_logger_edit)

V2_SERIALIZED_METHODS = (
    ('    public void add(String xuid, String gamertag) {', 'ADD_LOCK'),
    ('    public boolean addIfRequired(String xuid, String gamertag) {', 'ADD_IF_REQUIRED_LOCK'),
    ('    public void remove(String xuid, String gamertag) {', 'REMOVE_LOCK'),
    ('    private void internalProcess() {', 'INTERNAL_LOCK'),
)

def wrap_v2_method(text, signature, marker):
    """Serialize every normal mutation decision with V2's target proof.

    The V2 command uses writeLock.tryLock and never waits. Normal mutations
    retain their original parallelism under the shared read lock; only V2 is
    exclusive for its fixed 20-second overall request budget. In particular,
    addIfRequired's target-state GET cannot race V2's DELETE.
    """
    marker_line = 'MCGATEWAY_RELEASE160_V2_' + marker
    if marker_line in text:
        return text
    start = text.find(signature)
    if start < 0:
        raise ValueError('missing internal process anchor')
    open_brace = start + len(signature) - 1
    depth = 0
    end = None
    for index in range(open_brace, len(text)):
        if text[index] == '{': depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise ValueError('unclosed internal process')
    prefix = signature + '\n' + '''        // ''' + marker_line + ''': normal friend decisions never run
        // concurrently with a V2 proof; V2 itself never waits here.
        mcgatewayV2Lock.readLock().lock();
        try {'''
    return text[:start] + prefix + text[open_brace + 1:end] + '''        } finally {
            mcgatewayV2Lock.readLock().unlock();
        }
''' + text[end:]

def wrap_v2_serialized_methods(text):
    for signature, marker in V2_SERIALIZED_METHODS:
        text = wrap_v2_method(text, signature, marker)
    return text

def unwrap_v2_serialized_methods(text):
    suffix = '''        } finally {
            mcgatewayV2Lock.readLock().unlock();
        }
'''
    for signature, marker in reversed(V2_SERIALIZED_METHODS):
        marker_line = 'MCGATEWAY_RELEASE160_V2_' + marker
        if marker_line not in text:
            continue
        prefix = signature + '\n' + '''        // ''' + marker_line + ''': normal friend decisions never run
        // concurrently with a V2 proof; V2 itself never waits here.
        mcgatewayV2Lock.readLock().lock();
        try {'''
        start = text.index(prefix)
        close = text.index(suffix, start + len(prefix))
        text = text[:start] + signature + text[start + len(prefix):close] + text[close + len(suffix):]
    return text

def matches_original_hash(text, source_hash):
    raw = text.encode('utf-8')
    # The additional file uses its exact upstream Git blob identity; all
    # other pinned original files retain their SHA-256 preflight hashes.
    if source_hash.startswith('gitblob_sha1:'):
        identity = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
        return identity == source_hash.split(':', 1)[1]
    return hashlib.sha256(raw).hexdigest() == source_hash


def apply(root):
    prepared = []
    for relative, original_hash, anchor, replacement in EDITS:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError('missing/unsafe source: ' + relative)
        current = path.read_text(encoding='utf-8')
        comparable = unwrap_v2_serialized_methods(current) if relative.endswith('/FriendManager.java') else current
        if matches_original_hash(current, original_hash):
            original = current
        elif comparable.count(replacement) == 1:
            original = comparable.replace(replacement, anchor, 1)
            if not matches_original_hash(original, original_hash):
                raise ValueError('source hash mismatch: ' + relative)
        else:
            raise ValueError('source hash mismatch: ' + relative)
        if original.count(anchor) != 1:
            raise ValueError('ambiguous source anchor: ' + relative)
        expected = original.replace(anchor, replacement, 1)
        if relative.endswith('/FriendManager.java'):
            expected = wrap_v2_serialized_methods(expected)
        if current not in (original, expected):
            raise ValueError('unexpected patched source: ' + relative)
        prepared.append((path, current, expected))
    # Preflight every byte of every input before writing any file.
    changed = False
    for path, current, expected in prepared:
        if current != expected:
            path.write_text(expected, encoding='utf-8'); changed = True
    return changed

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('root'); args = parser.parse_args()
    changed = apply(Path(args.root).resolve())
    print('Changed files.' if changed else 'No changes were required.')
    print('PASS: exact160 read-only candidate; relay signaling is not transfer success.')
if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('ERROR: ' + str(error), file=sys.stderr); sys.exit(1)
