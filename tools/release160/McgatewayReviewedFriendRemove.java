package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.net.http.HttpRequest;
import java.time.Duration;

/**
 * Reviewed Release160 friend removal contract.
 * An inert validation/request-construction helper, never a mutation by itself.
 * Runtime dispatch also requires a separately operator-enabled container mode.
 */
public final class McgatewayReviewedFriendRemove {
    private McgatewayReviewedFriendRemove() { }

    public static boolean validXuid(String xuid) {
        if (xuid == null || !xuid.matches("[1-9][0-9]{0,19}")) return false;
        try {
            Long.parseUnsignedLong(xuid);
            return true;
        } catch (NumberFormatException error) {
            return false;
        }
    }

    public static boolean permitted(String[] args, String mode) {
        return "owner-reviewed-v160".equals(mode)
            && args != null && args.length == 2
            && "remove".equals(args[0]) && validXuid(args[1]);
    }

    public static HttpRequest buildRequest(String xuid, String authorization) {
        if (!validXuid(xuid) || authorization == null || authorization.isBlank())
            throw new IllegalArgumentException("invalid reviewed removal request");
        return HttpRequest.newBuilder(
                URI.create("https://social.xboxlive.com/users/me/people/friends/v2/xuid(" + xuid + ")"))
            .timeout(Duration.ofSeconds(15))
            .header("Authorization", authorization)
            .DELETE()
            .build();
    }

    public static boolean successStatus(int code) {
        return code == 200 || code == 204;
    }
}
