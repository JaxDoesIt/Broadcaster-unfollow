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
env_boundary = 'private String mcgatewayRecoveryEnv(String key) { return System.getenv(key); }'
assert source.count(env_boundary) == 1
source = source.replace(env_boundary, 'private String mcgatewayRecoveryEnv(String key) { return recoveryEnv.get(key); }')
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
    private final FakeLogger logger = new FakeLogger();
    final class FakeLogger { final List<String> lines=new ArrayList<>(); final List<List<String>> calls=new ArrayList<>(); void info(String line){lines.add(line);calls.add(List.copyOf(((ScriptedClient)mcgatewayV2HttpClient).methods));} }
    private final Map<String,String> recoveryEnv = new HashMap<>();
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
    static final String PLAN = "12".repeat(16), PLAN_HASH = "e".repeat(64);
    static FriendStateV2ActualProof recovery(Answer... replies) throws Exception {
        var f=fixture(replies);String prefix="MCGATEWAY_RELEASE160_RECOVERY_";
        f.recoveryEnv.put(prefix+"MODE","owner-reviewed-recovery-v1");
        f.recoveryEnv.put(prefix+"PLAN_ID",PLAN);f.recoveryEnv.put(prefix+"PLAN_SHA256",PLAN_HASH);
        f.recoveryEnv.put(prefix+"TARGET_SHA256",mcgatewayV2Hash(TARGET));
        f.recoveryEnv.put(prefix+"ACCOUNT_SHA256",mcgatewayV2Hash(f.sessionManager.account));
        f.recoveryEnv.put(prefix+"ISSUED_MS",Long.toString(System.currentTimeMillis()-1000));
        f.recoveryEnv.put(prefix+"EXPIRES_MS",Long.toString(System.currentTimeMillis()+600000));
        return f;
    }
    static void recoveryProofs() throws Exception {
        Answer present=answer(200,flags(true,false,false)), missing=answer(404,"{}");
        var denied=fixture(present);
        need(denied.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false stage=binding"));
        need(((ScriptedClient)denied.mcgatewayV2HttpClient).methods.isEmpty());
        for(String key:List.of("MODE","PLAN_ID","PLAN_SHA256","TARGET_SHA256","ACCOUNT_SHA256","EXPIRES_MS")){
            var f=recovery(present);f.recoveryEnv.put("MCGATEWAY_RELEASE160_RECOVERY_"+key,"bad");
            need(f.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false"));
            need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.isEmpty());
        }
        for(long[] dates:List.of(new long[]{1,2},new long[]{System.currentTimeMillis()+60000,System.currentTimeMillis()+120000},new long[]{System.currentTimeMillis()-1000,System.currentTimeMillis()+1000000})){
            var expired=recovery(present);
            expired.recoveryEnv.put("MCGATEWAY_RELEASE160_RECOVERY_ISSUED_MS",Long.toString(dates[0]));
            expired.recoveryEnv.put("MCGATEWAY_RELEASE160_RECOVERY_EXPIRES_MS",Long.toString(dates[1]));
            need(expired.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false"));
            need(((ScriptedClient)expired.mcgatewayV2HttpClient).methods.isEmpty());
        }
        for(boolean rehearsal:List.of(true,false)){
            var near=recovery(present);
            near.recoveryEnv.put("MCGATEWAY_RELEASE160_RECOVERY_EXPIRES_MS",Long.toString(System.currentTimeMillis()+1000));
            need(near.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,rehearsal).contains("verified=false"));
            need(((ScriptedClient)near.mcgatewayV2HttpClient).methods.isEmpty());
        }
        for(Answer refused:List.of(missing,answer(200,flags(false,true,false)),answer(200,flags(true,false,true)))){
            var noMarker=recovery(refused);
            need(noMarker.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("deleteAttempted=false post=unknown verified=false"));
            need(noMarker.logger.lines.isEmpty());
            need(!((ScriptedClient)noMarker.mcgatewayV2HttpClient).methods.contains("DELETE"));
        }
        var wrong=recovery(present);
        need(wrong.mcgatewayFriendRecoveryV1(nonce(),PLAN,"2533270000000001",true).contains("verified=false"));
        need(((ScriptedClient)wrong.mcgatewayV2HttpClient).methods.isEmpty());
        var f=recovery(present,answer(204,"{}"),missing,answer(204,"{}"),present);
        String n=nonce(),receipt=f.mcgatewayFriendRecoveryV1(n,PLAN,TARGET,true);
        need(receipt.contains("action=rehearse result=restored pre=present deleteAttempted=true post=present verified=true stage=complete"));
        need(f.logger.lines.size()==2 && f.logger.lines.get(0).contains("MCGATEWAY_FRIEND_RECOVERY_ARMED_V1 nonce="+n));
        need(f.logger.lines.get(0).endsWith("pre=present isFriend=true friendRequestSent=false friendRequestReceived=false deleteNext=true verified=true stage=pre-delete"));
        need(f.logger.lines.get(1).contains("MCGATEWAY_FRIEND_RECOVERY_SETTLED_V1 nonce="+n));
        need(f.logger.calls.equals(List.of(List.of("GET"),List.of("GET","DELETE","GET"))));
        var delayed=recovery(present,answer(204,"{}"),present,missing,answer(204,"{}"),present);
        need(delayed.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("action=rehearse result=restored pre=present deleteAttempted=true post=present verified=true stage=complete"));
        need(((ScriptedClient)delayed.mcgatewayV2HttpClient).methods.equals(List.of("GET","DELETE","GET","GET","PUT","GET")));

        need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.equals(List.of("GET","DELETE","GET","PUT","GET")));
        need(f.mcgatewayFriendRecoveryV1(n,PLAN,TARGET,true).contains("verified=false"));
        ((ScriptedClient)f.mcgatewayV2HttpClient).answers.add(present);
        need(f.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false"));
        need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.stream().filter("DELETE"::equals).count()==1);

        for(int deleteStatus:new int[]{200,204})for(int putStatus:new int[]{200,204}){
            var explicitRecovery=recovery(present,answer(deleteStatus,"{}"),answer(200,flags(false,false,false)),answer(putStatus,"{}"),present);
            need(explicitRecovery.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("post=present verified=true stage=complete"));
            need(explicitRecovery.logger.lines.size()==2 && explicitRecovery.logger.lines.get(1).contains("post=absent basis=explicit-flags"));
        }
        var queuedDelete=recovery(present,answer(202,"{}"));
        need(queuedDelete.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false stage=delete"));
        need(queuedDelete.logger.lines.size()==1);
        var pending=recovery(answer(200,flags(false,true,false)));
        need(pending.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,false).contains("verified=false stage=pre"));
        need(((ScriptedClient)pending.mcgatewayV2HttpClient).methods.equals(List.of("GET")));
        for(Answer post:List.of(answer(200,flags(false,true,false)),missing,answer(200,"{}"),answer(500,"{}"))){
            var bad=recovery(missing,answer(204,"{}"),post);
            need(bad.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,false).contains("verified=false"));
        }
        // Exhausting scripted replies models transport loss after deletion.
        // No settled witness exists; the independent root journal must retain
        // MANUAL_REQUIRED. A separate restore test uses the SAME sealed target.
        var lost=recovery(present,answer(204,"{}"));
        need(lost.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("deleteAttempted=true post=unknown verified=false"));
        need(lost.logger.lines.size()==1);
        // An unknown DELETE/absence outcome supplies only the first witness.
        var deleteLost=recovery(present);
        need(deleteLost.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false"));
        need(deleteLost.logger.lines.size()==1);
        // Once DELETE+absence are proven, a failed PUT retains BOTH witnesses.
        var putLost=recovery(present,answer(204,"{}"),missing);
        need(putLost.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,true).contains("verified=false stage=put"));
        need(putLost.logger.lines.size()==2);

        var restarted=recovery(missing,answer(204,"{}"),present);restarted.sessionManager.session="new-session";
        need(restarted.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,false).contains("action=restore result=restored pre=unknown deleteAttempted=false post=present verified=true"));
        var already=recovery(present);
        need(already.mcgatewayFriendRecoveryV1(nonce(),PLAN,TARGET,false).contains("result=already-restored"));
        need(((ScriptedClient)already.mcgatewayV2HttpClient).methods.equals(List.of("GET")));
        System.out.println("PASS: actual exact-target recovery methods; disabled/binding/replay/pending/loss/restart/strict post-GET gates");
    }
    public static void main(String[] args) throws Exception {
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
        for(Answer postDelete404:List.of(
            new Answer(404,"","","","",false,false),
            new Answer(404,"{}","text/html","0",missing.date(),false,false),
            new Answer(404,"{}","application/json","1",missing.date(),false,false),
            new Answer(404,"{}","application/json","0","Mon, 1 Jan 2001 00:00:00 GMT",false,false))){
            var f=fixture(present,answer(204,"{}"),postDelete404);
            need(f.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("result=removed pre=present post=friendship-absent verified=true basis=target-404-after-delete"));
            need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.equals(List.of("GET","DELETE","GET")));
        }
        for(Answer bad:List.of(answer(200,flags(true,false,false)),answer(200,flags(false,true,false)),answer(200,flags(false,false,true)),answer(200,"{}"),answer(403,"{}"),answer(429,"{}"),answer(500,"{}"),
            new Answer(404,"{}","application/json","0",missing.date(),true,false),
            new Answer(404,"{}","application/json","0",missing.date(),false,true))){
            var f=fixture(present,answer(204,"{}"),bad);
            need(f.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("result=uncertain"));
        }
        for(int status:new int[]{201,429,500}){
            var f=fixture(present,answer(status,"{}"));
            need(f.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("result=uncertain"));
            need(((ScriptedClient)f.mcgatewayV2HttpClient).methods.size()==2);
        }
        var explicit=fixture(present,answer(204,"{}"),answer(200,flags(false,false,false)));
        need(explicit.mcgatewayFriendRemoveV2(nonce(),TARGET).contains("post=absent verified=true"));
        recoveryProofs();
        System.out.println("PASS: actual overlay methods, scripted HTTP only; asymmetric404/pending/freshness/identity/URI gates");
    }
}
'''
Path(sys.argv[1]).write_text(header + source + footer)
