package com.rtm516.mcxboxbroadcast.core;

import java.net.http.HttpClient;
import java.util.List;

/** Pure offline request and authorization-gate tests. No HTTP or DELETE sent. */
public final class FriendRemovalCompatProofTest {
    private static void check(boolean condition) {
        if (!condition) throw new AssertionError("reviewed removal fixture failed");
    }
    public static void main(String[] args) {
        String[] valid = {"remove", "18446744073709551615"};
        check(!McgatewayReviewedFriendRemove.permitted(valid, null));
        check(!McgatewayReviewedFriendRemove.permitted(valid, ""));
        check(!McgatewayReviewedFriendRemove.permitted(valid, "true"));
        check(!McgatewayReviewedFriendRemove.permitted(valid, "owner-reviewed-v159"));
        check(McgatewayReviewedFriendRemove.permitted(valid, "owner-reviewed-v160"));
        for (String[] bad : List.of(
            new String[]{"remove"}, new String[]{"remove", "1", "extra"},
            new String[]{"add", "1"}, new String[]{"remove", "0"},
            new String[]{"remove", "01"}, new String[]{"remove", "-1"},
            new String[]{"remove", "18446744073709551616"},
            new String[]{"remove", "xuid(1)"}, new String[]{"remove", "1\n2"},
            new String[]{"REMOVE", "1"}, new String[]{"remove", " 1"}
        )) check(!McgatewayReviewedFriendRemove.permitted(bad, "owner-reviewed-v160"));
        check(!McgatewayReviewedFriendRemove.validXuid("0"));
        check(McgatewayReviewedFriendRemove.validXuid("1"));
        check(McgatewayReviewedFriendRemove.validXuid("18446744073709551615"));
        final String fakeAuth = "XBL3.0 fake-test-only";
        var req = McgatewayReviewedFriendRemove.buildRequest("1", fakeAuth);
        check(req.method().equals("DELETE"));
        check(req.uri().toString().equals("https://social.xboxlive.com/users/me/people/friends/v2/xuid(1)"));
        check(req.timeout().orElseThrow().toSeconds() == 15);
        check(req.headers().firstValue("Authorization").orElse("").equals(fakeAuth));
        check(req.headers().map().size() == 1);
        check(req.bodyPublisher().isEmpty());
        for (int status : List.of(201, 202, 206, 301, 302, 400, 401, 403, 404, 409, 429, 500, 503))
            check(!McgatewayReviewedFriendRemove.successStatus(status));
        check(McgatewayReviewedFriendRemove.successStatus(200));
        check(McgatewayReviewedFriendRemove.successStatus(204));
        try (HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .followRedirects(HttpClient.Redirect.NEVER).build()) {
            check(client.followRedirects() == HttpClient.Redirect.NEVER);
        }
        System.out.println("FriendRemovalCompatProofTest: PASS (no network calls)");
    }
}
