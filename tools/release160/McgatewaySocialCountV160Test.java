package com.rtm516.mcxboxbroadcast.core;

/** Offline-only fake HTTP body proof. Zero network, no real accounts. */
public final class McgatewaySocialCountV160Test {
    private static int passed = 0;
    private static void yes(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
        passed++;
    }
    private static void unavailable(int code, String body, String reason) {
        McgatewaySocialCountV160.Observation observation = McgatewaySocialCountV160.parse(code, body);
        yes(!observation.observed(), reason + "-observed");
        yes("unavailable".equals(observation.display()), reason + "-display");
        yes(observation.count() == -1, reason + "-count");
        yes(reason.equals(observation.reason()), reason + "-reason");
        yes(!observation.toString().contains("secretTEST"), reason + "-redaction");
    }
    public static void main(String[] args) {
        for(int count : new int[]{1, 100, 999, 1000}) {
            McgatewaySocialCountV160.Observation observation = McgatewaySocialCountV160.parse(
                200, "{\"targetFriendCount\":" + count + ",\"gamertag\":\"secretTEST\",\"following\":4}");
            yes(observation.observed(), "valid-observed");
            yes(observation.count() == count, "valid-count");
            yes("ok".equals(observation.reason()), "valid-status");
            yes(!observation.toString().contains("secretTEST"), "valid-redaction");
        }
        for(int code : new int[]{0, 206, 302, 400, 401, 404, 429, 500, 503}) {
            unavailable(code, "{\"targetFriendCount\":900}", "http-non200");
        }
        unavailable(200, "{}", "missing-field");
        unavailable(200, "{\"targetFriendCount\":null}", "missing-field");
        unavailable(200, "{\"targetFriendCount\":0}", "zero-unverified");
        unavailable(200, "{\"targetFriendCount\":1001}", "out-of-range");
        unavailable(200, "{\"targetFriendCount\":-1}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":1.5}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":1e2}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":\"800\"}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":true}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":[]}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":{}}", "invalid-field");
        unavailable(200, "{\"targetFriendCount\":\"secretTEST\"}", "invalid-field");
        unavailable(200, "not json", "invalid-body");
        unavailable(200, "[]", "invalid-body");
        unavailable(200, "", "invalid-body");
        unavailable(200, null, "invalid-body");
        unavailable(200, " ".repeat(65537), "invalid-body");
        System.out.println("MCGATEWAY_ACCOUNT_LIST_V160_FAKE_HTTP_PASS checks=" + passed);
    }
}
