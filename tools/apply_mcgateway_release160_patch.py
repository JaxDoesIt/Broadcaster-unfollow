#!/usr/bin/env python3
"""Exact Release160 overlay.  V2 removal is default-denied and source-only."""
import argparse, hashlib, sys
from pathlib import Path

# Installed only into a disposable upstream build tree.  V2 intentionally does
# not touch the cached list, player history, normal queue or friend count.
V2_FRIEND_MANAGER = r'''
    // MCGATEWAY_RELEASE160_FRIEND_REMOVE_V2: strict, target-scoped proof.
    private static final int MCGATEWAY_V2_MAX_BODY_BYTES = 16 * 1024;
    private static final int MCGATEWAY_V2_MAX_NONCES = 256;
    private final java.util.concurrent.locks.ReentrantLock mcgatewayV2Lock = new java.util.concurrent.locks.ReentrantLock();
    private final java.util.Set<String> mcgatewayV2Nonces = new java.util.HashSet<>();
    private record McgatewayV2State(String state, boolean removable) { }
    private static boolean mcgatewayV2Nonce(String value) { return value != null && value.matches("[0-9a-f]{32}"); }
    private static boolean mcgatewayV2Xuid(String value) { return value != null && value.matches("[1-9][0-9]{0,19}"); }
    private boolean mcgatewayV2Consume(String nonce) {
        if (!mcgatewayV2Nonce(nonce) || mcgatewayV2Nonces.contains(nonce) || mcgatewayV2Nonces.size() >= MCGATEWAY_V2_MAX_NONCES) return false;
        mcgatewayV2Nonces.add(nonce); return true;
    }
    private static String mcgatewayV2Hash(String value) throws Exception {
        byte[] bytes = java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder(64); for (byte b : bytes) out.append(String.format("%02x", b & 0xff)); return out.toString();
    }
    private static String mcgatewayV2Utf8(byte[] bytes) throws Exception {
        if (bytes == null || bytes.length == 0 || bytes.length > MCGATEWAY_V2_MAX_BODY_BYTES) throw new IllegalStateException("body");
        return java.nio.charset.StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
            .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(bytes)).toString();
    }
    private static long mcgatewayV2Remaining(long deadline) throws Exception {
        long remaining = java.util.concurrent.TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime());
        if (remaining < 1L) throw new java.util.concurrent.TimeoutException("deadline");
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
                try { for (java.nio.ByteBuffer chunk : chunks) { int count = chunk.remaining(); if (count > MCGATEWAY_V2_MAX_BODY_BYTES - bytes.size()) throw new IllegalStateException("body"); byte[] part = new byte[count]; chunk.get(part); bytes.write(part); } }
                catch (Exception error) { subscription.cancel(); result.completeExceptionally(error); }
            }
            public void onError(Throwable error) { result.completeExceptionally(error); }
            public void onComplete() { if (!result.isDone()) result.complete(bytes.toByteArray()); }
        };
    }
    private HttpResponse<byte[]> mcgatewayV2Send(HttpRequest request, long deadline) throws Exception {
        java.util.concurrent.CompletableFuture<HttpResponse<byte[]>> future = httpClient.sendAsync(request, mcgatewayV2BodyHandler());
        try { return future.get(mcgatewayV2Remaining(deadline), java.util.concurrent.TimeUnit.MILLISECONDS); }
        catch (java.util.concurrent.TimeoutException error) { future.cancel(true); throw error; }
    }
    private static void mcgatewayV2Skip(com.google.gson.stream.JsonReader r, int depth) throws Exception {
        if (depth > 8) throw new IllegalStateException("depth");
        switch (r.peek()) {
            case BEGIN_OBJECT -> { java.util.Set<String> names = new java.util.HashSet<>(); r.beginObject(); while (r.hasNext()) { if (!names.add(r.nextName())) throw new IllegalStateException("duplicate"); mcgatewayV2Skip(r, depth + 1); } r.endObject(); }
            case BEGIN_ARRAY -> { int count = 0; r.beginArray(); while (r.hasNext()) { if (++count > 64) throw new IllegalStateException("array"); mcgatewayV2Skip(r, depth + 1); } r.endArray(); }
            case STRING -> { if (r.nextString().length() > 256) throw new IllegalStateException("string"); }
            case NUMBER -> { if (r.nextString().length() > 64) throw new IllegalStateException("number"); }
            case BOOLEAN -> r.nextBoolean();
            case NULL -> r.nextNull();
            default -> throw new IllegalStateException("token");
        }
    }
    private static McgatewayV2State mcgatewayV2Parse(String body, String target) throws Exception {
        com.google.gson.stream.JsonReader r = new com.google.gson.stream.JsonReader(new java.io.StringReader(body)); r.setLenient(false);
        if (r.peek() != com.google.gson.stream.JsonToken.BEGIN_OBJECT) throw new IllegalStateException("root");
        java.util.Set<String> names = new java.util.HashSet<>(); String xuid = null; Boolean friend = null, sent = null, received = null;
        r.beginObject(); while (r.hasNext()) { String name = r.nextName(); if (!names.add(name)) throw new IllegalStateException("duplicate");
            if (name.equals("xuid")) { if (r.peek() != com.google.gson.stream.JsonToken.STRING) throw new IllegalStateException("xuid"); xuid = r.nextString(); }
            else if (name.equals("isFriend") || name.equals("friendRequestSent") || name.equals("friendRequestReceived")) {
                if (r.peek() != com.google.gson.stream.JsonToken.BOOLEAN) throw new IllegalStateException("boolean"); Boolean v = r.nextBoolean();
                if (name.equals("isFriend")) friend = v; else if (name.equals("friendRequestSent")) sent = v; else received = v;
            } else mcgatewayV2Skip(r, 0);
        } r.endObject();
        if (r.peek() != com.google.gson.stream.JsonToken.END_DOCUMENT || !target.equals(xuid) || friend == null || sent == null || received == null) throw new IllegalStateException("incomplete");
        return new McgatewayV2State(friend || sent || received ? "present" : "absent", friend && !sent && !received);
    }
    private McgatewayV2State mcgatewayV2Read(String target, String account, String session, long deadline) throws Exception {
        if (toAdd.containsKey(target) || toRemove.containsKey(target)) throw new IllegalStateException("target-queued");
        if (!account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("identity-before");
        URI uri = URI.create(Constants.PEOPLE.formatted(target));
        HttpRequest request = HttpRequest.newBuilder().uri(uri).timeout(java.time.Duration.ofMillis(Math.min(8_000L, mcgatewayV2Remaining(deadline)))).header("Authorization", sessionManager.getTokenHeader())
            .header("x-xbl-contract-version", "3").header("Cache-Control", "no-cache").header("Pragma", "no-cache").GET().build();
        HttpResponse<byte[]> response = mcgatewayV2Send(request, deadline);
        if (response.statusCode() != 200 || !uri.equals(response.uri())) throw new IllegalStateException("http");
        String type = response.headers().firstValue("Content-Type").orElse("").toLowerCase(java.util.Locale.ROOT);
        long age = response.headers().firstValue("Age").map(v -> { try { return Long.parseLong(v); } catch (Exception e) { return -1L; } }).orElse(0L);
        String date = response.headers().firstValue("Date").orElse(""); long dateMs;
        try { dateMs = java.time.ZonedDateTime.parse(date, java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME).toInstant().toEpochMilli(); } catch (Exception e) { throw new IllegalStateException("date"); }
        if (!type.startsWith("application/json") || age != 0 || Math.abs(System.currentTimeMillis() - dateMs) > 60_000L || !account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("freshness");
        return mcgatewayV2Parse(mcgatewayV2Utf8(response.body()), target);
    }
    private String mcgatewayV2Failure(String marker, String nonce, String target, String account, String session, String pre) {
        return marker + " nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " result=uncertain pre=" + pre + " post=unknown verified=false";
    }
    public String mcgatewayFriendStateV2(String nonce, String target) {
        if (!mcgatewayV2Lock.tryLock()) return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable state=unknown verified=false";
        try { if (!mcgatewayV2Consume(nonce) || !mcgatewayV2Xuid(target)) throw new IllegalStateException("input"); long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(20); String account = sessionManager.getXuid(), rawSession = sessionManager.mcgatewayV2SessionIdentity(); String hash = mcgatewayV2Hash(account), session = mcgatewayV2Hash(rawSession);
            McgatewayV2State state = mcgatewayV2Read(target, account, rawSession, deadline); return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + hash + " session=" + session + " state=" + state.state() + " verified=true";
        } catch (Exception e) { return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + (mcgatewayV2Nonce(nonce) ? nonce : "invalid") + " xuid=" + (mcgatewayV2Xuid(target) ? target : "invalid") + " account=unavailable session=unavailable state=unknown verified=false"; }
        finally { mcgatewayV2Lock.unlock(); }
    }
    public String mcgatewayFriendRemoveV2(String nonce, String target) {
        if (!mcgatewayV2Lock.tryLock()) return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable result=uncertain pre=unknown post=unknown verified=false";
        String account = "unavailable", session = "unavailable", pre = "unknown";
        try { if (!mcgatewayV2Consume(nonce) || !mcgatewayV2Xuid(target)) throw new IllegalStateException("input"); long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(20); String raw = sessionManager.getXuid(), rawSession = sessionManager.mcgatewayV2SessionIdentity(); account = mcgatewayV2Hash(raw); session = mcgatewayV2Hash(rawSession);
            McgatewayV2State before = mcgatewayV2Read(target, raw, rawSession, deadline); pre = before.state();
            if (pre.equals("absent")) return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " result=already-absent pre=absent post=absent verified=true";
            if (!before.removable()) throw new IllegalStateException("pending");
            if (!raw.equals(sessionManager.getXuid()) || !rawSession.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("identity-before-delete");
            HttpRequest request = HttpRequest.newBuilder().uri(URI.create(Constants.FRIEND.formatted(target))).timeout(java.time.Duration.ofMillis(Math.min(8_000L, mcgatewayV2Remaining(deadline)))).header("Authorization", sessionManager.getTokenHeader()).DELETE().build();
            HttpResponse<byte[]> deleted = mcgatewayV2Send(request, deadline);
            if ((deleted.statusCode() != 200 && deleted.statusCode() != 204) || !raw.equals(sessionManager.getXuid()) || !rawSession.equals(sessionManager.mcgatewayV2SessionIdentity())) throw new IllegalStateException("delete");
            McgatewayV2State after = mcgatewayV2Read(target, raw, rawSession, deadline); if (!after.state().equals("absent")) throw new IllegalStateException("post");
            return "MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=" + nonce + " xuid=" + target + " account=" + account + " session=" + session + " result=removed pre=present post=absent verified=true";
        } catch (Exception e) { return mcgatewayV2Failure("MCGATEWAY_FRIEND_REMOVE_V160_V2", mcgatewayV2Nonce(nonce) ? nonce : "invalid", mcgatewayV2Xuid(target) ? target : "invalid", account, session, pre); }
        finally { mcgatewayV2Lock.unlock(); }
    }

'''

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
                    if (args.length != 2) warn("MCGATEWAY_FRIEND_STATE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable state=unknown verified=false");
                    else info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendStateV2(args[0], args[1]));
                }
                case "friendremovev160" -> {
                    if (!"owner-reviewed-v2".equals(System.getenv("MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE")) || args.length != 2)
                        warn("MCGATEWAY_FRIEND_REMOVE_V160_V2 nonce=invalid xuid=invalid account=unavailable session=unavailable result=uncertain pre=unknown post=unknown verified=false");
                    else info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendRemoveV2(args[0], args[1]));
                }
                case "friends" -> warn("friends remove is DENIED: release160 removal contract requires a separate review.");'''
)
EDITS[4] = tuple(_logger_edit)

def wrap_v2_internal_process(text):
    """Serialize the existing scheduled mutation worker with the V2 operation.

    V2 admission never waits for that worker: it uses tryLock and fails closed.
    The normal worker may wait at most the V2 bounded three-request budget.
    """
    signature = '    private void internalProcess() {'
    if 'MCGATEWAY_RELEASE160_V2_INTERNAL_LOCK' in text:
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
    prefix = '''    private void internalProcess() {
        // MCGATEWAY_RELEASE160_V2_INTERNAL_LOCK: queued normal mutations never
        // run concurrently with a V2 proof. This worker is allowed to wait only
        // for V2's fixed request budget; V2 itself never waits here.
        mcgatewayV2Lock.lock();
        try {'''
    return text[:start] + prefix + text[open_brace + 1:end] + '''        } finally {
            mcgatewayV2Lock.unlock();
        }
''' + text[end:]

def unwrap_v2_internal_process(text):
    prefix = '''    private void internalProcess() {
        // MCGATEWAY_RELEASE160_V2_INTERNAL_LOCK: queued normal mutations never
        // run concurrently with a V2 proof. This worker is allowed to wait only
        // for V2's fixed request budget; V2 itself never waits here.
        mcgatewayV2Lock.lock();
        try {'''
    suffix = '''        } finally {
            mcgatewayV2Lock.unlock();
        }
'''
    if prefix not in text:
        return text
    start = text.index(prefix)
    close = text.index(suffix, start + len(prefix))
    return text[:start] + '    private void internalProcess() {' + text[start + len(prefix):close] + text[close + len(suffix):]

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
        comparable = unwrap_v2_internal_process(current) if relative.endswith('/FriendManager.java') else current
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
            expected = wrap_v2_internal_process(expected)
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
