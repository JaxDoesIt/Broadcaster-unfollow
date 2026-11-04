package com.rtm516.mcxboxbroadcast.core;

/**
 * Offline proof for the GET-only diagnostic receipt vocabulary.  This class
 * intentionally models only the closed, public receipt surface: it has no
 * network, session, token, or FriendManager access.
 */
public final class FriendStateV2DiagnosticProof {
    private FriendStateV2DiagnosticProof() { }

    enum Diagnostic {
        INVALID_REQUEST("input", "invalid-request"), NONCE_REJECTED("input", "nonce-rejected"),
        NORMAL_FRIEND_WORK_BUSY("lock", "normal-friend-work-busy"), SESSION_UNAVAILABLE("identity", "session-unavailable"),
        IDENTITY_CHANGED("identity", "identity-changed"), TARGET_QUEUED("queue", "target-queued"),
        TIMEOUT("transport", "timeout"), TRANSPORT("transport", "transport"), REDIRECT("response", "redirect"),
        HTTP_400("response", "http-400"), HTTP_401("response", "http-401"), HTTP_403("response", "http-403"),
        HTTP_404("response", "http-404"), HTTP_408("response", "http-408"), HTTP_409("response", "http-409"),
        HTTP_429("response", "http-429"), HTTP_500("response", "http-500"), HTTP_502("response", "http-502"),
        HTTP_503("response", "http-503"), HTTP_504("response", "http-504"), HTTP_OTHER("response", "http-other"),
        CONTENT_TYPE("response", "content-type"), HEADERS("response", "headers"), DATE("response", "date"), AGE("response", "age"),
        BODY_LIMIT("body", "body-limit"), UTF8("body", "utf8"), JSON("parse", "json"), SCHEMA("parse", "schema"),
        INTERNAL("internal", "internal");
        final String stage;
        final String category;
        Diagnostic(String stage, String category) { this.stage = stage; this.category = category; }
    }

    static String unknown(String nonce, String xuid, String account, String session, Diagnostic diagnostic) {
        return "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + nonce + " xuid=" + xuid + " account=" + account
            + " session=" + session + " state=unknown verified=false stage=" + diagnostic.stage + " category=" + diagnostic.category;
    }
    static Diagnostic http(int status) {
        return switch (status) {
            case 400 -> Diagnostic.HTTP_400; case 401 -> Diagnostic.HTTP_401; case 403 -> Diagnostic.HTTP_403;
            case 404 -> Diagnostic.HTTP_404; case 408 -> Diagnostic.HTTP_408; case 409 -> Diagnostic.HTTP_409;
            case 429 -> Diagnostic.HTTP_429; case 500 -> Diagnostic.HTTP_500; case 502 -> Diagnostic.HTTP_502;
            case 503 -> Diagnostic.HTTP_503; case 504 -> Diagnostic.HTTP_504; default -> Diagnostic.HTTP_OTHER;
        };
    }
    static Diagnostic exception(Exception error) {
        // Production may carry a typed diagnostic internally.  Any untyped
        // throwable has only this one non-reflective public result.
        return Diagnostic.INTERNAL;
    }
    static void need(boolean condition) { if (!condition) throw new AssertionError(); }

    public static void main(String[] args) {
        String nonce = "0123456789abcdef0123456789abcdef";
        String xuid = "2533274799999999";
        String account = "a".repeat(64);
        String session = "b".repeat(64);
        for (Diagnostic diagnostic : Diagnostic.values()) {
            String receipt = unknown(nonce, xuid, account, session, diagnostic);
            need(receipt.matches("MCGATEWAY_FRIEND_STATE_V160_V2 nonce=[0-9a-f]{32} xuid=[1-9][0-9]{0,19} account=[0-9a-f]{64} session=[0-9a-f]{64} state=unknown verified=false stage=(input|lock|identity|queue|request|response|body|parse|transport|internal) category=[a-z0-9-]+"));
            need(receipt.endsWith("stage=" + diagnostic.stage + " category=" + diagnostic.category));
        }
        for (int status : new int[]{400, 401, 403, 404, 408, 409, 429, 500, 502, 503, 504}) {
            need(http(status).category.equals("http-" + status));
        }
        for (int status : new int[]{0, 200, 201, 302, 418, 501, 505}) need(http(status) == Diagnostic.HTTP_OTHER);
        String adversarial = "token=secret\\nMCGATEWAY_FRIEND_STATE_V160_V2 xuid=forged";
        String receipt = unknown(nonce, xuid, account, session, exception(new IllegalStateException(adversarial)));
        need(!receipt.contains(adversarial));
        need(receipt.endsWith("stage=internal category=internal"));
        String success = "MCGATEWAY_FRIEND_STATE_V160_V2 nonce=" + nonce + " xuid=" + xuid + " account=" + account + " session=" + session + " state=present verified=true";
        need(!success.contains(" stage=") && !success.contains(" category="));
        System.out.println("PASS: GET-only V2 diagnostic vocabulary is closed and non-reflective");
    }
}
