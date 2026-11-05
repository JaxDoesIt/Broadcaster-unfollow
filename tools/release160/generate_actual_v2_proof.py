#!/usr/bin/env python3
"""Embed the exact overlay methods; replace only HTTP/session/queue boundaries."""
import importlib.util
import sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('overlay', Path(__file__).parents[1] / 'apply_mcgateway_release160_patch.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = module.V2_FRIEND_MANAGER
boundary = 'HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).connectTimeout(java.time.Duration.ofSeconds(8)).build()'
assert source.count(boundary) == 1
source = source.replace(boundary, 'new ScriptedClient()')
header = r'''
package com.rtm516.mcxboxbroadcast.core;
import java.net.URI;
import java.net.http.*;
import java.util.*;
import java.util.concurrent.*;
import javax.net.ssl.*;
public final class FriendStateV2ActualProof {
    private final Map<String,String> toAdd = new HashMap<>(), toRemove = new HashMap<>();
    private final FakeSession sessionManager = new FakeSession();
    static final String TARGET = "2533270000000000";
    static final class Constants {
        static final String PEOPLE = "https://example.invalid/users/me/people/xuid(%s)";
        static final String FRIEND = "https://example.invalid/users/me/people/friends/v2/xuid(%s)";
    }
    static final class FakeSession {
        String account="account", session="session";
        String getXuid() { return account; }
        String mcgatewayV2SessionIdentity() { return session; }
        String getTokenHeader() { return "synthetic-not-a-token"; }
    }
    record Answer(int status, String body, String type, String age, String date, boolean wrongUri, boolean changeIdentity) { }
    static Answer answer(int status, String body) {
        return new Answer(status, body, "application/json", "0", java.time.ZonedDateTime.now(java.time.ZoneOffset.UTC).format(java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME), false, false);
    }
    static String flags(boolean friend, boolean sent, boolean received) {
        return "{\"xuid\":\""+TARGET+"\",\"isFriend\":"+friend+",\"friendRequestSent\":"+sent+",\"friendRequestReceived\":"+received+"}";
    }
    final class ScriptedClient extends HttpClient {
        final Deque<Answer> answers = new ArrayDeque<>();
        final List<String> methods = new ArrayList<>();
        public Optional<java.net.CookieHandler> cookieHandler(){return Optional.empty();}
        public Optional<java.time.Duration> connectTimeout(){return Optional.empty();}
        public Redirect followRedirects(){return Redirect.NEVER;}
        public Optional<java.net.ProxySelector> proxy(){return Optional.empty();}
        public SSLContext sslContext(){try{return SSLContext.getDefault();}catch(Exception e){throw new RuntimeException(e);}}
        public SSLParameters sslParameters(){return new SSLParameters();}
        public Optional<java.net.Authenticator> authenticator(){return Optional.empty();}
        public Version version(){return Version.HTTP_1_1;}
        public Optional<Executor> executor(){return Optional.empty();}
        public <T> HttpResponse<T> send(HttpRequest r,HttpResponse.BodyHandler<T> h){throw new AssertionError("unexpected synchronous HTTP");}
        public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest r,HttpResponse.BodyHandler<T> h,HttpResponse.PushPromiseHandler<T> p){throw new AssertionError("unexpected push HTTP");}
        @SuppressWarnings("unchecked")
        public <T> CompletableFuture<HttpResponse<T>> sendAsync(HttpRequest request,HttpResponse.BodyHandler<T> handler){
            methods.add(request.method()); Answer a=answers.removeFirst();
            if(a.changeIdentity()) sessionManager.session="changed";
            HttpResponse<byte[]> response=new HttpResponse<>() {
                public int statusCode(){return a.status();}
                public HttpRequest request(){return request;}
                public Optional<HttpResponse<byte[]>> previousResponse(){return Optional.empty();}
                public HttpHeaders headers(){return HttpHeaders.of(Map.of("Content-Type",List.of(a.type()),"Age",List.of(a.age()),"Date",List.of(a.date())),(k,v)->true);}
                public byte[] body(){return a.body().getBytes(java.nio.charset.StandardCharsets.UTF_8);}
                public Optional<SSLSession> sslSession(){return Optional.empty();}
                public URI uri(){return a.wrongUri()?URI.create("https://wrong.invalid/"):request.uri();}
                public Version version(){return Version.HTTP_1_1;}
            };
            return CompletableFuture.completedFuture((HttpResponse<T>)response);
        }
    }
'''
footer = r'''
    static void need(boolean b){if(!b)throw new AssertionError();}
    static String nonce(){return UUID.randomUUID().toString().replace("-", "");}
    static FriendStateV2ActualProof fixture(Answer... replies){
        var f=new FriendStateV2ActualProof(); ((ScriptedClient)f.mcgatewayV2HttpClient).answers.addAll(List.of(replies)); return f;
    }
    static void noDelete(Answer before){
        var f=fixture(before); String result=f.mcgatewayFriendRemoveV2(nonce(),TARGET);
        need(result.contains("result=uncertain")); need(!((ScriptedClient)f.mcgatewayV2HttpClient).methods.contains("DELETE"));
    }
    public static void main(String[] args){
        Answer present=answer(200,flags(true,false,false)), missing=answer(404,"{}");
        var observed=fixture(missing);
        need(observed.mcgatewayFriendStateV2(nonce(),TARGET).contains("state=unknown verified=false stage=response category=http-404"));
        noDelete(missing);
        for(int bits=0;bits<8;bits++)if(bits!=1)noDelete(answer(200,flags((bits&1)!=0,(bits&2)!=0,(bits&4)!=0)));
        for(int deleteStatus:new int[]{200,204}){
            var f=fixture(present,answer(deleteStatus,"{}"),missing);
            String result=f.mcgatewayFriendRemoveV2(nonce(),TARGET);
            need(result.contains("result=removed pre=present post=friendship-absent verified=true basis=target-404-after-delete"));
            need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.equals(List.of("GET","DELETE","GET")));
            need(f.mcgatewayFriendRemoveV2("bad",TARGET).contains("verified=false"));
        }
        for(Answer bad:List.of(answer(200,flags(true,false,false)),answer(200,flags(false,true,false)),answer(200,flags(false,false,true)),answer(200,"{}"),answer(403,"{}"),answer(429,"{}"),answer(500,"{}"),
            new Answer(404,"{}","text/html","0",missing.date(),false,false),
            new Answer(404,"{}","application/json","1",missing.date(),false,false),
            new Answer(404,"{}","application/json","0","Mon, 1 Jan 2001 00:00:00 GMT",false,false),
            new Answer(404,"{}","application/json","0",missing.date(),true,false),
            new Answer(404,"{}","application/json","0",missing.date(),false,true))){
            var f=fixture(present,answer(204,"{}"),bad);
            need(f.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("result=uncertain"));
        }
        for(int status:new int[]{201,404,429,500}){
            var f=fixture(present,answer(status,"{}"));
            need(f.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("result=uncertain"));
            need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.size()==2);
        }
        var explicit=fixture(present,answer(204,"{}"),answer(200,flags(false,false,false)));
        need(explicit.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("post=absent verified=true"));
        System.out.println("PASS: actual overlay methods, scripted HTTP only; asymmetric404/pending/freshness/identity/URI gates");
    }
}
'''
Path(sys.argv[1]).write_text(header + source + footer)
