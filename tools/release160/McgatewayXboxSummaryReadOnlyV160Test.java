package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;

public final class McgatewayXboxSummaryReadOnlyV160Test {
    static int assertions;
    static final String ACCOUNT="2533270000000011", TARGET="2533270000000022", NONCE="ab".repeat(16);
    static final String SESSION="session:160";
    static final McgatewayFriendRemoveV160.Permit PERMIT = new McgatewayFriendRemoveV160.Permit(
        ACCOUNT,SESSION,TARGET,NONCE,true,true,false,true);

    static void eq(Object expected,Object actual,String label) {
        if(!Objects.equals(expected,actual)) throw new AssertionError(label+" expected="+expected+" actual="+actual);
        assertions++;
    }
    static void yes(boolean value,String label) { eq(true,value,label); }
    static Map<String,List<String>> headers() {return Map.of("Content-Type",List.of("application/json"),"Age",List.of("0"));}
    static Map<String,Object> directions(Object caller,Object target) {
        Map<String,Object> m=new HashMap<>();
        m.put("isCallerFollowingTarget",caller);m.put("isTargetFollowingCaller",target);
        return m;
    }
    static McgatewayXboxRelationshipEnvelopeV160.Request request() {
        return new McgatewayXboxRelationshipEnvelopeV160.Request("GET",
            McgatewayXboxSummaryReadOnlyV160.summaryUri(TARGET),ACCOUNT,SESSION,Duration.ofSeconds(5),true,true,16*1024);
    }
    static McgatewayXboxRelationshipEnvelopeV160.Reply reply(McgatewayXboxRelationshipEnvelopeV160.Request request,
                                                             int status,Map<String,Object> body,Map<String,List<String>> hs) {
        return new McgatewayXboxRelationshipEnvelopeV160.Reply(status,request.uri(),request.account(),request.session(),
            true,true,false,120,hs,body);
    }
    static void rejected(McgatewayXboxRelationshipEnvelopeV160.Request r,
                         McgatewayXboxRelationshipEnvelopeV160.Reply p,String reason) {
        var result=McgatewayXboxSummaryReadOnlyV160.inspect(r,p,PERMIT);
        eq(false,result.observed(),reason);
    }
    static class Wire implements McgatewayXboxRelationshipEnvelopeV160.Wire {
        Deque<Function<McgatewayXboxRelationshipEnvelopeV160.Request,
            McgatewayXboxRelationshipEnvelopeV160.Reply>> queue=new ArrayDeque<>();
        int calls;
        Wire add(Function<McgatewayXboxRelationshipEnvelopeV160.Request,
            McgatewayXboxRelationshipEnvelopeV160.Reply> f){queue.addLast(f);return this;}
        public McgatewayXboxRelationshipEnvelopeV160.Reply exchange(McgatewayXboxRelationshipEnvelopeV160.Request req) {
            calls++;
            yes(req.requestNoStore(),"read no-store flag");
            yes(req.redirectsForbidden(),"read never redirect");
            yes(req.timeout().compareTo(Duration.ofSeconds(8))<=0,"bounded time");
            if(queue.isEmpty()) throw new AssertionError("unexpected fake operation");
            return queue.removeFirst().apply(req);
        }
    }
    public static void main(String[] args) {
        var r=request();
        var uri=McgatewayXboxSummaryReadOnlyV160.summaryUri(TARGET);
        eq("https://social.xboxlive.com/users/xuid("+TARGET+")/summary",uri.toString(),"exact documented summary URL");
        for(String invalid:new String[]{"0","-1","18446744073709551616","1%29"," 1","A",""}) {
            boolean denied=false;
            try {McgatewayXboxSummaryReadOnlyV160.summaryUri(invalid);}catch(IllegalArgumentException e){denied=true;}
            yes(denied,"unsafe XUID rejected");
        }
        for(boolean incoming:new boolean[]{false,true})for(boolean outgoing:new boolean[]{false,true}) {
            var evidence=McgatewayXboxSummaryReadOnlyV160.inspect(r,reply(r,200,directions(outgoing,incoming),headers()),PERMIT);
            yes(evidence.observed(),"explicit pair accepted");
            eq(incoming,evidence.snapshot().incoming(),"summary target-follows-caller => incoming");
            eq(outgoing,evidence.snapshot().outgoing(),"summary caller-follows-target => outgoing");
            eq(TARGET,evidence.snapshot().target(),"target derived from exact pinned URI");
        }
        for(Map<String,Object> bad:new Map[]{directions(null,false),directions(false,null),directions("false",false),
            directions(0,false),Map.of("isFollowingCaller",false),Map.of("isFriend",false),
            Map.of("isCallerFollowingTarget",false),Map.of("isTargetFollowingCaller",true),
            Map.of("isCallerFollowingTarget",false,"isTargetFollowingCaller",false,"nextLink","page")}) {
            rejected(r,reply(r,200,bad,headers()),"optional/invalid summary direction");
        }
        for(int status:new int[]{0,201,204,301,302,400,401,403,404,429,500,503})
            rejected(r,reply(r,status,directions(false,false),headers()),"untrusted summary HTTP status");
        for(Map<String,List<String>> h:new Map[]{
            Map.of("Content-Type",List.of("text/plain")),
            Map.of("Content-Type",List.of("application/json","application/json")),
            Map.of("content-type",List.of("application/json"),"Content-Type",List.of("application/json")),
            Map.of("Content-Type",List.of("application/json"),"Age",List.of("42")),
            Map.of("Content-Type",List.of("application/json"),"X-Cache",List.of("HIT")),
            Map.of("Content-Type",List.of("application/json"),"Location",List.of("https://example.com")),
            Map.of("Content-Type",List.of("application/json"),"Content-Length",List.of("65536")),
            Map.of("Content-Type",List.of("application/json"),"Content-Length",List.of("119")),
            Map.of("Content-Type",List.of("application/json"),"age",List.of("0"),"Age",List.of("0"))
        }) rejected(r,reply(r,200,directions(false,false),h),"malformed headers");
        rejected(r,new McgatewayXboxRelationshipEnvelopeV160.Reply(200,URI.create("https://elsewhere.invalid"),
            ACCOUNT,SESSION,true,true,false,120,headers(),directions(false,false)),"redirected host");
        rejected(r,new McgatewayXboxRelationshipEnvelopeV160.Reply(200,r.uri(),ACCOUNT,SESSION,
            true,false,false,120,headers(),directions(false,false)),"stale summary");
        rejected(r,new McgatewayXboxRelationshipEnvelopeV160.Reply(200,r.uri(),"2533270000009999",SESSION,
            true,true,false,120,headers(),directions(false,false)),"account mismatch");
        rejected(r,new McgatewayXboxRelationshipEnvelopeV160.Reply(200,r.uri(),ACCOUNT,"wrong",
            true,true,false,120,headers(),directions(false,false)),"session mismatch");
        rejected(r,new McgatewayXboxRelationshipEnvelopeV160.Reply(200,r.uri(),ACCOUNT,SESSION,
            true,true,true,120,headers(),directions(false,false)),"redirect forbidden");
        {
            Wire fake=new Wire()
                .add(req->{eq(uri,req.uri(),"summary pre GET");eq("GET",req.method(),"GET only read");
                    return reply(req,200,directions(true,true),headers());})
                .add(req->{eq("DELETE",req.method(),"first DELETE fake");return reply(req,204,null,Map.of());})
                .add(req->{eq("DELETE",req.method(),"second DELETE fake");return reply(req,204,null,Map.of());})
                .add(req->{eq(uri,req.uri(),"summary post GET");return reply(req,200,directions(false,false),headers());});
            var policy=new McgatewayFriendRemoveV160(new McgatewayXboxSummaryReadOnlyV160.FakeSummaryTransport(fake),()->0);
            var outcome=policy.attempt(PERMIT);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_REMOVED,outcome.state(),"fake summary post-read succeeds");
            eq(4,fake.calls,"exactly four fake calls");
        }
        {
            Wire fake=new Wire().add(req->reply(req,200,directions(false,null),headers()));
            var policy=new McgatewayFriendRemoveV160(new McgatewayXboxSummaryReadOnlyV160.FakeSummaryTransport(fake),()->0);
            eq(McgatewayFriendRemoveV160.State.UNVERIFIED,policy.attempt(PERMIT).state(),"optional field fail closed");
            eq(1,fake.calls,"no deletion after invalid summary");
        }
        {
            Wire fake=new Wire()
                .add(req->reply(req,200,directions(true,true),headers()))
                .add(req->reply(req,204,null,Map.of()))
                .add(req->reply(req,204,null,Map.of()))
                .add(req->reply(req,200,directions(false,null),headers()));
            var policy=new McgatewayFriendRemoveV160(new McgatewayXboxSummaryReadOnlyV160.FakeSummaryTransport(fake),()->0);
            eq(McgatewayFriendRemoveV160.State.UNCERTAIN,policy.attempt(PERMIT).state(),"no success without both post-flags");
            eq(4,fake.calls,"no second attempt after uncertainty");
        }
        System.out.println("M...XboxSummaryReadOnlyV160Test: PASS "+assertions+" fake-only assertions");
    }
}
