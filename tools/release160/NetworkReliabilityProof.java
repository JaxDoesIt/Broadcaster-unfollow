package com.rtm516.mcxboxbroadcast.core;

import com.rtm516.mcxboxbroadcast.core.exceptions.*;
import com.rtm516.mcxboxbroadcast.core.storage.StorageManager;
import java.io.*;
import java.lang.reflect.*;
import java.net.URI;
import java.net.http.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import javax.net.ssl.SSLSession;

/** Runs the real patched methods, with no Xbox request, credentials or live files. */
public final class NetworkReliabilityProof {
    static void need(boolean value) { if (!value) throw new AssertionError(); }
    static final class Log implements Logger {
        final List<String> lines = new ArrayList<>();
        public void info(String s) { lines.add(s); }
        public void warn(String s) { lines.add(s); }
        public void error(String s) { lines.add(s); }
        public void error(String s, Throwable e) { lines.add(s); }
        public void debug(String s) { lines.add(s); }
        public Logger prefixed(String s) { return this; }
    }
    static final class Pending implements ScheduledFuture<Object> {
        boolean cancelled; final long seconds;
        Pending(long seconds) { this.seconds = seconds; }
        public boolean cancel(boolean interrupt) { cancelled = true; return true; }
        public boolean isCancelled() { return cancelled; }
        public boolean isDone() { return cancelled; }
        public Object get() { throw new AssertionError(); }
        public Object get(long t, TimeUnit u) { throw new AssertionError(); }
        public long getDelay(TimeUnit u) { return u.convert(seconds, TimeUnit.SECONDS); }
        public int compareTo(Delayed other) { return 0; }
    }
    static final class Scheduler extends ScheduledThreadPoolExecutor {
        final List<Pending> tasks = new ArrayList<>();
        Scheduler() { super(1); }
        @Override public ScheduledFuture<?> schedule(Runnable task, long delay, TimeUnit unit) {
            Pending result = new Pending(TimeUnit.SECONDS.convert(delay, unit)); tasks.add(result); return result;
        }
    }
    static final class Reply implements HttpResponse<Void> {
        final HttpRequest request; final int status; final HttpHeaders headers;
        Reply(HttpRequest request, int status, Map<String,List<String>> values) {
            this.request = request; this.status = status; this.headers = HttpHeaders.of(values, (a,b)->true);
        }
        public int statusCode() { return status; }
        public HttpRequest request() { return request; }
        public Optional<HttpResponse<Void>> previousResponse() { return Optional.empty(); }
        public HttpHeaders headers() { return headers; }
        public Void body() { return null; }
        public Optional<SSLSession> sslSession() { return Optional.empty(); }
        public URI uri() { return request.uri(); }
        public HttpClient.Version version() { return HttpClient.Version.HTTP_1_1; }
    }
    static final class Fake extends SessionManagerCore {
        final Scheduler scheduler = new Scheduler();
        int calls, status=200, publishCalls; boolean failPublish, transportReady=true;
        IOException failure; Map<String,List<String>> headers=Map.of(); HttpRequest last;
        Fake(Log log, StorageManager storage) { super(storage, null, log); }
        public ScheduledExecutorService scheduledThread() { return scheduler; }
        public String getSessionId() { return "fixture"; }
        public String getXuid() { return "123"; }
        public String getTokenHeader() { return "fixture-not-a-real-credential"; }
        protected boolean handleFriendship() { return false; }
        protected void updateSession() { checkConnection(); }
        protected void publishSession() throws SessionCreationException {
            publishCalls++; updateSession(); // Exercise the recursive call path.
            if (failPublish) throw new SessionCreationException("fixture publish failed");
        }
        protected boolean mcgatewaySessionTransportReady() { return transportReady; }
        protected HttpResponse<Void> mcgatewaySendPresence(HttpRequest request) throws IOException {
            calls++; last=request;
            if (failure!=null) throw failure;
            return new Reply(request,status,headers);
        }
    }
    public static void main(String[] args) throws Exception {
        int[] writes={0};
        StorageManager storage=(StorageManager)Proxy.newProxyInstance(StorageManager.class.getClassLoader(),new Class<?>[]{StorageManager.class},(proxy,method,values)->{
            if (method.getName().equals("screenshot")) return new File("/this-offline-proof-file-does-not-exist");
            if (method.getParameterCount()>0) writes[0]++;
            if (method.getReturnType()==String.class) return "";
            return null;
        });
        Log log=new Log(); Fake fake=new Fake(log,storage);
        try {
            fake.failure=new HttpConnectTimeoutException("fixture timeout"); fake.updatePresence();
            need(fake.calls==1 && fake.last.timeout().orElseThrow().equals(Duration.ofSeconds(20)));
            need(fake.scheduler.tasks.getLast().seconds>=5 && fake.scheduler.tasks.getLast().seconds<=10);
            need(log.lines.stream().noneMatch(s->s.contains("successful")||s.contains("POST_ACCEPTED")));
            need(log.lines.stream().anyMatch(s->s.contains("category=connect-timeout")));
            Pending previous=fake.scheduler.tasks.getLast();
            fake.failure=null; fake.status=429; fake.headers=Map.of("Retry-After",List.of("120")); fake.updatePresence();
            need(previous.cancelled && fake.scheduler.tasks.getLast().seconds>=120);
            fake.status=200; fake.headers=Map.of("X-Heartbeat-After",List.of("180")); fake.updatePresence();
            need(fake.scheduler.tasks.getLast().seconds==180);
            need(log.lines.stream().filter(s->s.equals("MCGATEWAY_XBOX_PRESENCE_POST_ACCEPTED status=200")).count()==1);
            need(SessionManagerCore.mcgatewayPresenceRetrySeconds(1,0,0,0)==5);
            need(SessionManagerCore.mcgatewayPresenceRetrySeconds(2,0,0,0)==10);
            need(SessionManagerCore.mcgatewayPresenceRetrySeconds(32,0,0,0)==300);
            need(SessionManagerCore.mcgatewayPresenceRetrySeconds(1,401,0,0)>=300);
            need(SessionManagerCore.mcgatewayRetryAfterSeconds("Tue, 17 Nov 2026 00:02:00 GMT",Instant.parse("2026-11-17T00:00:00Z"))==120);
            need(SessionManagerCore.mcgatewayRetryAfterSeconds("invalid",Instant.now())==0);
            need(SessionManagerCore.mcgatewayRetryAfterSeconds("Tue, 17 Nov 2026 00:02:00 GMT",Instant.parse("2026-11-17T00:00:00.100Z"))==120);
            Method create=SessionManagerCore.class.getDeclaredMethod("createSession");create.setAccessible(true);
            Field pending=SessionManagerCore.class.getDeclaredField("mcgatewayRebuildPending");pending.setAccessible(true);
            fake.failPublish=true;
            try { create.invoke(fake); throw new AssertionError(); }
            catch (InvocationTargetException e) { need(e.getCause() instanceof SessionCreationException); }
            need(pending.getBoolean(fake)); need(fake.publishCalls==1);
            SessionInfo info=new SessionInfo();info.setHostName("fixture");info.setWorldName("fixture");
            fake.sessionInfo=new ExpandedSessionInfo("fixture","123",info);fake.sessionInfo.setHandleId("cached-handle");
            need(fake.mcgatewayHealthLine().endsWith("published=false"));
            try { fake.mcgatewayV2SessionIdentity(); throw new AssertionError(); }
            catch (IllegalStateException expected) { }
            fake.sessionInfo=null;fake.failPublish=false;fake.transportReady=true;
            fake.checkConnection();need(fake.publishCalls==2 && !pending.getBoolean(fake));
            fake.checkConnection();need(fake.publishCalls==2); // Open sockets no longer hide a failed rebuild, nor force needless work after success.
            int calls=fake.calls;fake.shutdown();fake.updatePresence();need(fake.calls==calls);
            need(fake.scheduler.tasks.getLast().cancelled);need(writes[0]==0);
            System.out.println("PASS: real presence timeout/retry/429/ACK/shutdown and partial-rebuild recovery; no network or storage mutation");
        } finally { fake.scheduler.shutdownNow(); }
    }
}
