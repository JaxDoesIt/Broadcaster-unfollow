package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Source-only Xbox relationship HTTP envelope and decoded-object validator.
 * No real HTTP client or JSON parser is connected. A future decoder must reject
 * duplicate JSON keys and must not coerce missing booleans to false.
 */
public final class McgatewayXboxRelationshipEnvelopeV160 {
    private McgatewayXboxRelationshipEnvelopeV160() { }
    private static final Pattern XUID = Pattern.compile("[1-9][0-9]{0,19}");
    private static final Pattern NONCE = Pattern.compile("[0-9a-f]{32}");
    private static final Pattern SESSION = Pattern.compile("[A-Za-z0-9._:-]{1,128}");
    private static final int MAX_BODY_BYTES = 16 * 1024;

    /** Immutable request is an instruction for a separately audited network client. */
    public record Request(String method, URI uri, String account, String session,
                          Duration timeout, boolean requestNoStore, boolean redirectsForbidden,
                          int maximumResponseBytes) { }
    /** Body is a decoded JSON object, NOT a Java model with default-false booleans. */
    public record Reply(int status, URI finalUri, String boundAccount, String boundSession,
                        boolean complete, boolean networkFresh, boolean redirected,
                        int rawBodyBytes, Map<String,List<String>> headers,
                        Map<String,Object> decodedObject) { }
    /** Never implement in production without independent auth/session provenance. */
    public interface Wire { Reply exchange(Request request) throws Exception; }

    public record ReadResult(McgatewayFriendRemoveV160.Snapshot snapshot, String reason) {
        public boolean verified() { return snapshot != null; }
    }

    private static boolean validXuid(String value) {
        if(value == null || !XUID.matcher(value).matches()) return false;
        try { Long.parseUnsignedLong(value); return true; }
        catch(NumberFormatException error) { return false; }
    }

    public static URI relationshipUri(String xuid) {
        if(!validXuid(xuid)) throw new IllegalArgumentException("invalid xuid");
        return URI.create("https://social.xboxlive.com/users/me/people/xuid(" + xuid + ")");
    }
    public static URI followerDeleteUri(String xuid) {
        if(!validXuid(xuid)) throw new IllegalArgumentException("invalid xuid");
        return URI.create("https://social.xboxlive.com/users/me/people/follower/xuid(" + xuid + ")");
    }
    public static URI outgoingDeleteUri(String xuid) { return relationshipUri(xuid); }

    private static boolean validPermit(McgatewayFriendRemoveV160.Permit permit) {
        return permit != null && validXuid(permit.account()) && validXuid(permit.xuid())
            && !permit.account().equals(permit.xuid())
            && permit.session() != null && SESSION.matcher(permit.session()).matches()
            && permit.nonce() != null && NONCE.matcher(permit.nonce()).matches();
    }

    private static String header(Map<String,List<String>> headers, String key) {
        if(headers == null) return null;
        String found = null;
        for(var entry:headers.entrySet()) {
            if(entry.getKey() == null || !entry.getKey().equalsIgnoreCase(key)) continue;
            List<String> values = entry.getValue();
            if(found != null || values == null || values.size() != 1 || values.get(0) == null) return null;
            found = values.get(0);
        }
        return found;
    }
    private static boolean duplicateOrMalformedSensitiveHeaders(Map<String,List<String>> headers) {
        if(headers == null) return true;
        for(String key:new String[]{"Content-Type","Content-Length","Age","X-Cache"}) {
            int occurrences=0;
            for(var entry:headers.entrySet()) {
                if(entry.getKey() == null || !entry.getKey().equalsIgnoreCase(key)) continue;
                occurrences++;
                List<String> values=entry.getValue();
                if(values == null || values.size() != 1 || values.get(0) == null
                    || values.get(0).indexOf('\r') >= 0 || values.get(0).indexOf('\n') >= 0) return true;
            }
            if(occurrences > 1) return true;
        }
        return false;
    }
    private static boolean noCacheEvidence(Reply reply) {
        String age = header(reply.headers(), "Age");
        if(age != null && !age.equals("0")) return false;
        String cached = header(reply.headers(), "X-Cache");
        if(cached != null && cached.toLowerCase(Locale.ROOT).contains("hit")) return false;
        return true;
    }
    private static boolean trustedEnvelope(Reply reply, Request request, boolean requireJson) {
        if(reply == null || !reply.complete() || !reply.networkFresh() || reply.redirected()
            || reply.finalUri() == null || !request.uri().equals(reply.finalUri())
            || !request.account().equals(reply.boundAccount())
            || !request.session().equals(reply.boundSession())
            || reply.rawBodyBytes() < 0 || reply.rawBodyBytes() > MAX_BODY_BYTES
            || duplicateOrMalformedSensitiveHeaders(reply.headers())
            || !noCacheEvidence(reply)) return false;
        String sizeHeader=header(reply.headers(),"Content-Length");
        if(sizeHeader != null) {
            if(!sizeHeader.matches("[0-9]{1,5}")) return false;
            if(Integer.parseInt(sizeHeader) != reply.rawBodyBytes()) return false;
        }
        if(requireJson) {
            if(reply.status() != 200 || reply.rawBodyBytes() == 0 || reply.decodedObject() == null) return false;
            String type = header(reply.headers(), "Content-Type");
            if(type == null || !type.matches("(?i)^application/json(?:;\\s*charset=utf-8)?$")) return false;
        }
        return true;
    }

    /** The documented Person response may omit relationship flags: omit means unknown. */
    public static ReadResult validatePersonReply(Reply reply, Request request) {
        if(request == null || !request.method().equals("GET") || !trustedEnvelope(reply,request,true))
            return new ReadResult(null,"untrusted-http-envelope");
        Map<String,Object> person = reply.decodedObject();
        Object rawTarget=person.get("xuid");
        if(!(rawTarget instanceof String target) || !validXuid(target)
            || !request.uri().equals(relationshipUri(target)))
            return new ReadResult(null,"untrusted-target");
        if(person.containsKey("people") || person.containsKey("continuationToken")
            || person.containsKey("nextLink") || person.containsKey("next")
            || person.containsKey("pagination")) return new ReadResult(null,"unexpected-collection-or-pagination");
        // NEVER use Gson's primitive-boolean defaults: both keys must exist as actual Boolean.
        if(!(person.get("isFollowingCaller") instanceof Boolean incoming)
            || !(person.get("isFollowedByCaller") instanceof Boolean outgoing))
            return new ReadResult(null,"missing-or-untyped-directions");
        // External semantics of these two properties are not yet live-attested.
        var snapshot = new McgatewayFriendRemoveV160.Snapshot(request.account(),request.session(),
            target,200,incoming,outgoing,true,true,false);
        return new ReadResult(snapshot,"typed-directions-present-but-live-semantics-unverified");
    }

    /** This test-only adapter can exchange fake replies, NEVER a live Xbox client. */
    public static final class UnconnectedWireAdapter implements McgatewayFriendRemoveV160.Transport {
        private final Wire fake;
        public UnconnectedWireAdapter(Wire fake) {
            if(fake == null) throw new IllegalArgumentException("missing fake wire");
            this.fake = fake;
        }
        private static Request request(McgatewayFriendRemoveV160.Permit p, Duration timeout,
                                       String method, URI uri) {
            if(!validPermit(p) || timeout == null || timeout.isZero() || timeout.isNegative()
                || timeout.compareTo(Duration.ofSeconds(8)) > 0)
                throw new IllegalArgumentException("invalid fake HTTP request");
            return new Request(method,uri,p.account(),p.session(),timeout,true,true,MAX_BODY_BYTES);
        }
        public McgatewayFriendRemoveV160.Snapshot readRelationship(McgatewayFriendRemoveV160.Permit p, Duration budget) throws Exception {
            Request r=request(p,budget,"GET",relationshipUri(p.xuid()));
            Reply reply=fake.exchange(r);
            return validatePersonReply(reply,r).snapshot();
        }
        private McgatewayFriendRemoveV160.DeleteReply delete(McgatewayFriendRemoveV160.Permit p,
                                                               Duration budget, URI uri) throws Exception {
            Request r=request(p,budget,"DELETE",uri);
            Reply reply=fake.exchange(r);
            if(!trustedEnvelope(reply,r,false)) return new McgatewayFriendRemoveV160.DeleteReply(0,true,false);
            return new McgatewayFriendRemoveV160.DeleteReply(reply.status(),false,true);
        }
        public McgatewayFriendRemoveV160.DeleteReply deleteFollower(McgatewayFriendRemoveV160.Permit p, Duration budget) throws Exception {
            return delete(p,budget,followerDeleteUri(p.xuid()));
        }
        public McgatewayFriendRemoveV160.DeleteReply deleteOutgoing(McgatewayFriendRemoveV160.Permit p, Duration budget) throws Exception {
            return delete(p,budget,outgoingDeleteUri(p.xuid()));
        }
    }
}
