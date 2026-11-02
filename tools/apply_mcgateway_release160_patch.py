#!/usr/bin/env python3
"""Exact release160 read-only compatibility candidate; no live channel mutation.
Relay evidence is signaling only. Existing config is transformed in RAM, never rewritten.
"""
import argparse, hashlib, sys
from pathlib import Path

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

    // Lazy dedicated client: never inherit redirect-following from the general API client.
    private static final class McgatewayCountClient {
        static final HttpClient CLIENT = HttpClient.newBuilder()
            .connectTimeout(java.time.Duration.ofSeconds(4))
            .version(HttpClient.Version.HTTP_1_1)
            .followRedirects(HttpClient.Redirect.NEVER).build();
    }

    public String mcgatewayFriendCountProof(String nonce) throws Exception {
        return McgatewayFriendCountProof.capture(McgatewayCountClient.CLIENT, sessionManager.getTokenHeader(), nonce);
    }

    // Reviewed Release160 console compatibility. Never use upstream's
    // retrying toRemove queue for Control Bot's durable single-attempt cleanup.
    // This capability is unreachable through the console unless the operator
    // explicitly enables the exact reviewed mode in the container environment.
    private final java.util.concurrent.atomic.AtomicBoolean mcgatewayRemovalInFlight =
        new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final class McgatewayReviewedRemovalClient {
        static final HttpClient CLIENT = HttpClient.newBuilder()
            .connectTimeout(java.time.Duration.ofSeconds(4))
            .version(HttpClient.Version.HTTP_1_1)
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();
    }
    public void mcgatewayReviewedRemoveOnce(String xuid) {
        if (!McgatewayReviewedFriendRemove.validXuid(xuid))
            throw new IllegalArgumentException("invalid reviewed removal identifier");
        if (!mcgatewayRemovalInFlight.compareAndSet(false, true))
            throw new IllegalStateException("reviewed removal already in progress");
        try {
            HttpRequest request = McgatewayReviewedFriendRemove.buildRequest(xuid, sessionManager.getTokenHeader());
            McgatewayReviewedRemovalClient.CLIENT.sendAsync(request, HttpResponse.BodyHandlers.discarding())
                .whenComplete((response, failure) -> {
                    try {
                        if (failure != null || response == null) {
                            logger.warn("Failed to remove all friend relationships for XUID " + xuid + " (request unavailable)");
                        } else if (!McgatewayReviewedFriendRemove.successStatus(response.statusCode())) {
                            logger.warn("Failed to remove all friend relationships for XUID " + xuid
                                + " (HTTP " + response.statusCode() + ")");
                        } else {
                            // Only a confirmed HTTP 200/204 may produce the
                            // existing Control Bot's strict success receipt.
                            // Do not make a second request, retry, or infer
                            // success from command acceptance.
                            logger.info("Removed Unknown (" + xuid + ") as a friend");
                        }
                    } catch (RuntimeException unexpected) {
                        // Do not expose HTTP bodies, authorization or raw exception text.
                        logger.warn("Failed to remove all friend relationships for XUID " + xuid + " (result unavailable)");
                    } finally {
                        mcgatewayRemovalInFlight.set(false);
                    }
                });
        } catch (RuntimeException error) {
            mcgatewayRemovalInFlight.set(false);
            throw new IllegalStateException("reviewed removal request unavailable");
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
                case "friendcountv2" -> {
                    if (args.length != 1 || !args[0].matches("[0-9a-f]{32}")) {
                        warn("MCGATEWAY_FRIEND_COUNT_V160_V2 nonce=invalid ERROR unavailable");
                    } else {
                        try { info(StandaloneMain.sessionManager.friendManager().mcgatewayFriendCountProof(args[0])); }
                        catch (Exception error) {
                            warn("MCGATEWAY_FRIEND_COUNT_V160_V2 nonce=" + args[0] + " ERROR unavailable"
                                + com.rtm516.mcxboxbroadcast.core.McgatewayFriendCountProof.safeFailureFields(error));
                        }
                    }
                }
                case "friends" -> {
                    String reviewMode = System.getenv("MCGATEWAY_RELEASE160_FRIEND_REMOVAL_MODE");
                    if (com.rtm516.mcxboxbroadcast.core.McgatewayReviewedFriendRemove.permitted(args, reviewMode)) {
                        StandaloneMain.sessionManager.friendManager().mcgatewayReviewedRemoveOnce(args[1]);
                        // Enqueue/transport acceptance is NOT the remote success receipt.
                        info("MCGATEWAY_RELEASE160_FRIEND_REMOVE queued");
                    } else {
                        warn("friends remove is DENIED: release160 removal contract requires a separate review.");
                    }
                }
                case "version" -> info("MCXboxBroadcast Standalone " + BuildData.VERSION);'''),
    ('core/src/main/java/com/rtm516/mcxboxbroadcast/core/configs/ConfigLoader.java',
     '34fc61332904d73ea38c75cf551215d987b5d4e77badcf7807cf6005de01533f',
     '        if (originallyEmpty || currentVersion != newVersion) {',
     r'''        // Existing config remains byte-identical for exact release154 image rollback.
        // All version transformations still apply to the in-memory config above.
        if (originallyEmpty) {'''),
]

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
        if matches_original_hash(current, original_hash):
            original = current
        elif current.count(replacement) == 1:
            original = current.replace(replacement, anchor, 1)
            if not matches_original_hash(original, original_hash):
                raise ValueError('source hash mismatch: ' + relative)
        else:
            raise ValueError('source hash mismatch: ' + relative)
        if original.count(anchor) != 1:
            raise ValueError('ambiguous source anchor: ' + relative)
        expected = original.replace(anchor, replacement, 1)
        if current not in (original, expected):
            raise ValueError('unexpected patched source: ' + relative)
        prepared.append((path, current, expected))
    # Both helper files are preflighted before any file is written.
    for helper_name in ('McgatewayFriendCountProof.java', 'McgatewayReviewedFriendRemove.java'):
        helper_source = Path(__file__).parent / 'release160' / helper_name
        helper_target = root / 'core/src/main/java/com/rtm516/mcxboxbroadcast/core' / helper_name
        if helper_source.is_symlink() or not helper_source.is_file():
            raise ValueError('missing/unsafe reviewed helper template: ' + helper_name)
        expected_helper = helper_source.read_text(encoding='utf-8')
        if helper_target.is_symlink() or helper_target.exists() and not helper_target.is_file():
            raise ValueError('unsafe reviewed helper target: ' + helper_name)
        current_helper = helper_target.read_text(encoding='utf-8') if helper_target.exists() else ''
        if current_helper and current_helper != expected_helper:
            raise ValueError('source hash mismatch: reviewed helper ' + helper_name)
        prepared.append((helper_target, current_helper, expected_helper))
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
