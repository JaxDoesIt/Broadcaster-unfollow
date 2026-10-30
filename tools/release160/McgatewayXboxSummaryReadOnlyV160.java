package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Source-only Xbox PersonSummary evidence alternative, with FAKE wire only.
 * Not wired into any broadcaster console command or real HTTP client.
 * PersonSummary's caller/target directions are distinct from the optional
 * legacy Person.isFollowingCaller field. Live semantics remain unverified.
 */
public final class McgatewayXboxSummaryReadOnlyV160 {
    private McgatewayXboxSummaryReadOnlyV160() { }
    private static final Pattern XUID = Pattern.compile("[1-9][0-9]{0,19}");
    private static final Pattern SESSION = Pattern.compile("[A-Za-z0-9._:-]{1,128}");
    private static final Pattern NONCE = Pattern.compile("[0-9a-f]{32}");
    private static final int MAX_BYTES = 16 * 1024;

    static boolean validXuid(String xuid) {
        if (xuid == null || !XUID.matcher(xuid).matches()) return false;
        try { Long.parseUnsignedLong(xuid); return true; }
        catch (NumberFormatException error) { return false; }
    }

    public static URI summaryUri(String targetXuid) {
        if (!validXuid(targetXuid)) throw new IllegalArgumentException("invalid target");
        return URI.create("https://social.xboxlive.com/users/xuid(" + targetXuid + ")/summary");
    }

    public record Evidence(McgatewayFriendRemoveV160.Snapshot snapshot, String classification) {
        public boolean observed() { return snapshot != null; }
    }

    private static boolean safeHeaders(Map<String,List<String>> headers) {
        if (headers == null) return false;
        String contentType = null;
        String length = null;
        java.util.Set<String> seen = new java.util.HashSet<>();
        for (var entry : headers.entrySet()) {
            String name = entry.getKey();
            List<String> values = entry.getValue();
            if (name == null || values == null || values.size() != 1 || values.get(0) == null
                || values.get(0).indexOf('\r') >= 0 || values.get(0).indexOf('\n') >= 0) return false;
            String key = name.toLowerCase(Locale.ROOT);
            if (!seen.add(key)) return false;
            String value = values.get(0);
            if (key.equals("content-type")) {
                if (contentType != null) return false;
                contentType = value;
            } else if (key.equals("content-length")) {
                if (length != null || !value.matches("[0-9]{1,5}")) return false;
                length = value;
            } else if (key.equals("age")) {
                if (!value.equals("0")) return false;
            } else if (key.equals("x-cache")) {
                if (value.toLowerCase(Locale.ROOT).contains("hit")) return false;
            } else if (key.equals("location") || key.equals("link") || key.equals("continuation")
                || key.equals("next") || key.equals("nextlink")) return false;
        }
        return contentType != null && contentType.matches("(?i)application/json(?:;\\s*charset=utf-8)?")
            && (length == null || Integer.parseInt(length) <= MAX_BYTES);
    }

    /**
     * Accepts an already strictly decoded JSON object, never a raw JSON string.
     * The future decoder must reject duplicate keys, invalid UTF-8, excessive
     * nesting, trailing text, and pagination before creating this map.
     */
    public static Evidence inspect(McgatewayXboxRelationshipEnvelopeV160.Request request,
                                   McgatewayXboxRelationshipEnvelopeV160.Reply response,
                                   McgatewayFriendRemoveV160.Permit permit) {
        if (permit == null || !validXuid(permit.xuid()) || !validXuid(permit.account())
            || permit.account().equals(permit.xuid()) || permit.nonce() == null
            || !NONCE.matcher(permit.nonce()).matches() || permit.session() == null
            || !SESSION.matcher(permit.session()).matches()) return new Evidence(null, "invalid-permit-identity");
        URI expected = summaryUri(permit.xuid());
        if (request == null || !"GET".equals(request.method()) || !expected.equals(request.uri())
            || !permit.account().equals(request.account()) || !permit.session().equals(request.session())
            || request.timeout() == null || request.timeout().isZero() || request.timeout().isNegative()
            || request.timeout().compareTo(Duration.ofSeconds(8)) > 0 || !request.requestNoStore()
            || !request.redirectsForbidden() || request.maximumResponseBytes() > MAX_BYTES
            || request.maximumResponseBytes() <= 0) return new Evidence(null, "invalid-request");
        if (response == null || response.status() != 200 || !expected.equals(response.finalUri())
            || !permit.account().equals(response.boundAccount())
            || !permit.session().equals(response.boundSession())
            || !response.complete() || !response.networkFresh() || response.redirected()
            || response.rawBodyBytes() < 2 || response.rawBodyBytes() > MAX_BYTES
            || !safeHeaders(response.headers()) || response.decodedObject() == null)
            return new Evidence(null, "untrusted-response-envelope");
        if (response.headers().entrySet().stream().anyMatch(e -> e.getKey().equalsIgnoreCase("Content-Length")
                && !e.getValue().get(0).equals(Integer.toString(response.rawBodyBytes()))))
            return new Evidence(null, "content-length-mismatch");
        Map<String,Object> json = response.decodedObject();
        if (json.containsKey("people") || json.containsKey("pagination") || json.containsKey("nextLink")
            || json.containsKey("continuationToken")) return new Evidence(null, "unexpected-pagination");
        Object caller = json.get("isCallerFollowingTarget");
        Object target = json.get("isTargetFollowingCaller");
        if (!(caller instanceof Boolean outgoing) || !(target instanceof Boolean incoming))
            return new Evidence(null, "missing-or-untyped-directions");
        // Summary has no signed target XUID in its JSON. Identity depends on
        // the HTTPS URL, caller authentication, and audited response provenance.
        return new Evidence(new McgatewayFriendRemoveV160.Snapshot(permit.account(),permit.session(),
            permit.xuid(),200,incoming,outgoing,true,true,false),"typed-summary-fields-observed-not-live-attested");
    }

    /** FAKE wire adapter only. No credentials, HttpClient or filesystem. */
    public static final class FakeSummaryTransport implements McgatewayFriendRemoveV160.Transport {
        private final McgatewayXboxRelationshipEnvelopeV160.Wire wire;
        private final McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter deleteAdapter;

        public FakeSummaryTransport(McgatewayXboxRelationshipEnvelopeV160.Wire wire) {
            if (wire == null) throw new IllegalArgumentException("missing fake wire");
            this.wire = wire;
            this.deleteAdapter = new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire);
        }
        public McgatewayFriendRemoveV160.Snapshot readRelationship(McgatewayFriendRemoveV160.Permit p,
                Duration budget) throws Exception {
            if (p == null || !validXuid(p.xuid()) || budget == null || budget.isZero()
                || budget.isNegative() || budget.compareTo(Duration.ofSeconds(8)) > 0)
                throw new IllegalArgumentException("invalid fake read budget");
            var request = new McgatewayXboxRelationshipEnvelopeV160.Request("GET",summaryUri(p.xuid()),
                p.account(),p.session(),budget,true,true,MAX_BYTES);
            return inspect(request, wire.exchange(request), p).snapshot();
        }
        public McgatewayFriendRemoveV160.DeleteReply deleteFollower(McgatewayFriendRemoveV160.Permit p,
                Duration budget) throws Exception { return deleteAdapter.deleteFollower(p,budget); }
        public McgatewayFriendRemoveV160.DeleteReply deleteOutgoing(McgatewayFriendRemoveV160.Permit p,
                Duration budget) throws Exception { return deleteAdapter.deleteOutgoing(p,budget); }
    }
}
