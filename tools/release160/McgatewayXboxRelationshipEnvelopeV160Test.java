package com.rtm516.mcxboxbroadcast.core;

import java.net.URI;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** No real network: all HTTP replies and decoded Person objects are fakes. */
public final class McgatewayXboxRelationshipEnvelopeV160Test {
    private static int assertions;
    private static final String ACCOUNT="2533270000000011", XUID="2533270000000022", NONCE="ab".repeat(16);
    private static final String SESSION="session:160";
    private static final McgatewayFriendRemoveV160.Permit PERMIT=new McgatewayFriendRemoveV160.Permit(
        ACCOUNT, SESSION, XUID, NONCE, true, true, false, true);
    private static final URI GET=McgatewayXboxRelationshipEnvelopeV160.relationshipUri(XUID);
    private static final URI DELETE_FOLLOWER=McgatewayXboxRelationshipEnvelopeV160.followerDeleteUri(XUID);
    private static final Map<String,Object> PRESENT=Map.of(
        "xuid",XUID,"isFollowingCaller",Boolean.TRUE,"isFollowedByCaller",Boolean.TRUE);
    private static final Map<String,Object> ABSENT=Map.of(
        "xuid",XUID,"isFollowingCaller",Boolean.FALSE,"isFollowedByCaller",Boolean.FALSE);

    private static void eq(Object expected,Object actual,String message) {
        if(!Objects.equals(expected,actual)) throw new AssertionError(message+" expected="+expected+" actual="+actual);
        assertions++;
    }
    private static void yes(boolean value,String message) { eq(true,value,message); }
    private static Map<String,List<String>> headers(){return Map.of("Content-Type",List.of("application/json"),"Cache-Control",List.of("no-store"));}
    private static McgatewayXboxRelationshipEnvelopeV160.Reply reply(McgatewayXboxRelationshipEnvelopeV160.Request request,
            int status,Map<String,Object> json,Map<String,List<String>> headers) {
        return new McgatewayXboxRelationshipEnvelopeV160.Reply(status,request.uri(),request.account(),request.session(),
            true,true,false,json == null ? 0 : 200,headers,json);
    }
    private static Map<String,Object> person(Object xuid,Object incoming,Object outgoing) {
        var map=new HashMap<String,Object>();
        map.put("xuid",xuid);map.put("isFollowingCaller",incoming);map.put("isFollowedByCaller",outgoing);
        return map;
    }
    private static final class Wire implements McgatewayXboxRelationshipEnvelopeV160.Wire {
        final Deque<java.util.function.Function<McgatewayXboxRelationshipEnvelopeV160.Request,
                McgatewayXboxRelationshipEnvelopeV160.Reply>> actions=new ArrayDeque<>();
        int invoked;
        Wire add(java.util.function.Function<McgatewayXboxRelationshipEnvelopeV160.Request,
                McgatewayXboxRelationshipEnvelopeV160.Reply> action){actions.add(action);return this;}
        @Override public McgatewayXboxRelationshipEnvelopeV160.Reply exchange(McgatewayXboxRelationshipEnvelopeV160.Request req) {
            invoked++;
            eq(true,req.redirectsForbidden(),"no redirects requested");
            eq(true,req.requestNoStore(),"no cache requested");
            eq(true,req.timeout().compareTo(Duration.ofSeconds(8))<=0,"bounded request timeout");
            eq(16*1024,req.maximumResponseBytes(),"response cap");
            eq(ACCOUNT,req.account(),"expected account");
            eq(SESSION,req.session(),"expected session");
            if(actions.isEmpty())throw new AssertionError("extra HTTP operation");
            return actions.removeFirst().apply(req);
        }
    }
    private static McgatewayXboxRelationshipEnvelopeV160.Request getRequest() {
        return new McgatewayXboxRelationshipEnvelopeV160.Request("GET",GET,ACCOUNT,SESSION,
            Duration.ofSeconds(5),true,true,16*1024);
    }
    private static void rejected(McgatewayXboxRelationshipEnvelopeV160.Reply bad,String label) {
        var result=McgatewayXboxRelationshipEnvelopeV160.validatePersonReply(bad,getRequest());
        eq(false,result.verified(),label);
        eq(null,result.snapshot(),label+" no proof snapshot");
    }
    private static McgatewayXboxRelationshipEnvelopeV160.Reply modified(
            McgatewayXboxRelationshipEnvelopeV160.Reply base,int status,URI uri,String acct,
            String session,boolean complete,boolean fresh,boolean redirected,int size,
            Map<String,List<String>> headers,Map<String,Object> person) {
        return new McgatewayXboxRelationshipEnvelopeV160.Reply(status,uri,acct,session,complete,fresh,redirected,size,headers,person);
    }
    public static void main(String[] ignored) throws Exception {
        eq("https://social.xboxlive.com/users/me/people/xuid("+XUID+")",GET.toString(),"exact GET path");
        eq("https://social.xboxlive.com/users/me/people/follower/xuid("+XUID+")",DELETE_FOLLOWER.toString(),"exact follower DELETE path");
        eq(GET,McgatewayXboxRelationshipEnvelopeV160.outgoingDeleteUri(XUID),"exact outgoing DELETE path");
        for(String invalid:new String[]{"0","-1","A","abc","18446744073709551616"," 2","2%29",""}) {
            boolean threw=false;
            try{McgatewayXboxRelationshipEnvelopeV160.relationshipUri(invalid);}catch(IllegalArgumentException e){threw=true;}
            yes(threw,"reject unsafe XUID path");
        }
        var req=getRequest();
        var ok=reply(req,200,PRESENT,headers());
        var result=McgatewayXboxRelationshipEnvelopeV160.validatePersonReply(ok,req);
        yes(result.verified(),"two explicit typed flags recognized");
        eq(true,result.snapshot().incoming(),"incoming true");
        eq(true,result.snapshot().outgoing(),"outgoing true");
        eq(ACCOUNT,result.snapshot().account(),"account bound");
        eq(SESSION,result.snapshot().session(),"session bound");
        eq(XUID,result.snapshot().target(),"XUID bound");
        yes(McgatewayXboxRelationshipEnvelopeV160.validatePersonReply(reply(req,200,ABSENT,headers()),req).verified(),
            "two explicit false booleans accepted as syntactic response");
        for(Map<String,Object> bad:new Map[]{
            person(XUID,null,false),person(XUID,false,null),person(XUID,"false",false),
            person(XUID,false,0),person(42,false,false),person("2533270000000023",false,false),
            Map.of("xuid",XUID,"isFollowingCaller",Boolean.FALSE),
            Map.of("xuid",XUID,"isFollowedByCaller",Boolean.FALSE),
            Map.of("xuid",XUID,"isFriend",Boolean.FALSE),
            Map.of("xuid",XUID,"isFollowingCaller",Boolean.FALSE,"isFollowedByCaller",Boolean.FALSE,"nextLink","continuation")
        }) rejected(reply(req,200,bad,headers()),"invalid/missing/optional direction");
        rejected(reply(req,404,null,headers()),"404 is NOT verified absence");
        for(int status:new int[]{0,201,204,301,302,400,401,403,429,500,503})
            rejected(reply(req,status,ABSENT,headers()),"bad GET status");
        for(var h:new Map[]{
            Map.of("Content-Type",List.of("text/plain")),
            Map.of("Content-Type",List.of("application/json; charset=latin1")),
            Map.of("Content-Type",List.of("application/json","application/json")),
            Map.of("Content-Type",List.of("application/json"),"Age",List.of("30")),
            Map.of("Content-Type",List.of("application/json"),"X-Cache",List.of("HIT")),
            Map.of("Content-Type",List.of("application/json"),"Content-Length",List.of("42")),
            Map.of("Content-Type",List.of("application/json"),"Content-Length",List.of("200","200")),
            Map.of("Content-Type",List.of("application/json"),"content-type",List.of("application/json")),
            Map.of("Content-Type",List.of("application/json"),"Age",List.of("0","1"))
        }) rejected(reply(req,200,ABSENT,h),"untrusted headers");
        rejected(modified(ok,200,URI.create("https://attacker.invalid/path"),ACCOUNT,SESSION,true,true,false,200,headers(),ABSENT),"different host");
        rejected(modified(ok,200,GET,ACCOUNT,"different",true,true,false,200,headers(),ABSENT),"session mismatch");
        rejected(modified(ok,200,GET,"2533270000000033",SESSION,true,true,false,200,headers(),ABSENT),"account mismatch");
        rejected(modified(ok,200,GET,ACCOUNT,SESSION,false,true,false,200,headers(),ABSENT),"incomplete body");
        rejected(modified(ok,200,GET,ACCOUNT,SESSION,true,false,false,200,headers(),ABSENT),"possibly cached body");
        rejected(modified(ok,200,GET,ACCOUNT,SESSION,true,true,true,200,headers(),ABSENT),"redirected response");
        rejected(modified(ok,200,GET,ACCOUNT,SESSION,true,true,false,17*1024,headers(),ABSENT),"oversized body");
        rejected(modified(ok,200,GET,ACCOUNT,SESSION,true,true,false,0,headers(),ABSENT),"zero-byte JSON");
        {
            Wire wire=new Wire().add(r->{eq("GET",r.method(),"read method");eq(GET,r.uri(),"read URI");return reply(r,200,PRESENT,headers());})
                .add(r->{eq("DELETE",r.method(),"follower method");eq(DELETE_FOLLOWER,r.uri(),"follower URI");return reply(r,204,null,Map.of());})
                .add(r->{eq("DELETE",r.method(),"outgoing method");eq(GET,r.uri(),"outgoing URI");return reply(r,404,null,Map.of());})
                .add(r->{eq("GET",r.method(),"post-read method");return reply(r,200,ABSENT,headers());});
            var remove=new McgatewayFriendRemoveV160(
                new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire),()->0);
            var outcome=remove.attempt(PERMIT);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_REMOVED,outcome.state(),"fake HTTP full protocol");
            eq(4,wire.invoked,"two GET and two DELETE calls");
        }
        {
            Wire wire=new Wire().add(r->reply(r,200,person(XUID,false,null),headers()));
            var remove=new McgatewayFriendRemoveV160(
                new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire),()->0);
            eq(McgatewayFriendRemoveV160.State.UNVERIFIED,remove.attempt(PERMIT).state(),"missing optional flag never permits deletion");
            eq(1,wire.invoked,"no DELETE with missing flag");
        }
        {
            Wire wire=new Wire().add(r->reply(r,200,PRESENT,headers()))
                .add(r->reply(r,204,null,Map.of()))
                .add(r->reply(r,204,null,Map.of()))
                .add(r->reply(r,200,person(XUID,false,null),headers()));
            var remove=new McgatewayFriendRemoveV160(
                new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire),()->0);
            eq(McgatewayFriendRemoveV160.State.UNCERTAIN,remove.attempt(PERMIT).state(),"no false success after missing post flag");
            eq(4,wire.invoked,"GET-DELETE-DELETE-GET only once");
        }
        {
            Wire wire=new Wire().add(r->reply(r,200,ABSENT,headers()))
                .add(r->reply(r,200,ABSENT,headers()));
            var remove=new McgatewayFriendRemoveV160(
                new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire),()->0);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_ALREADY_ABSENT,remove.attempt(PERMIT).state(),"two independent absent reads");
            eq(2,wire.invoked,"no DELETE for verified absent pre-state");
        }
        {
            Wire wire=new Wire().add(r->reply(r,200,PRESENT,headers()))
                .add(r->modified(reply(r,204,null,Map.of()),204,URI.create("https://elsewhere.invalid"),ACCOUNT,SESSION,true,true,true,0,Map.of(),null));
            var remove=new McgatewayFriendRemoveV160(
                new McgatewayXboxRelationshipEnvelopeV160.UnconnectedWireAdapter(wire),()->0);
            eq(McgatewayFriendRemoveV160.State.UNCERTAIN,remove.attempt(PERMIT).state(),"redirected DELETE may have applied, refuse success");
            eq(2,wire.invoked,"stop after unsafe DELETE");
        }
        System.out.println("M...XboxRelationshipEnvelopeV160Test PASS " + assertions + " fake-envelope assertions, zero network");
    }
}
