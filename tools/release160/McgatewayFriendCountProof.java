package com.rtm516.mcxboxbroadcast.core;

import com.google.gson.Strictness;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.*; import java.net.URI; import java.net.http.*; import java.nio.ByteBuffer; import java.nio.charset.*; import java.time.Duration; import java.util.*; import java.util.concurrent.*; import java.util.concurrent.Flow; import java.util.function.LongSupplier; import java.util.regex.Pattern;

/** Read-only, nonce-bound proof of one complete PeopleHub friend snapshot. */
public final class McgatewayFriendCountProof {
    static final URI SUMMARY=URI.create("https://social.xboxlive.com/users/me/summary"), FRIENDS=URI.create("https://peoplehub.xboxlive.com/users/me/people/friends");
    private static final Duration BUDGET=Duration.ofSeconds(20); private static final int MAX_BODY=8*1024*1024, MAX_ROWS=10_000, MAX_DEPTH=32, MAX_NODES=500_000;
    private static final Pattern NONCE=Pattern.compile("[0-9a-f]{32}"), XUID=Pattern.compile("[1-9][0-9]{0,19}"), COUNT=Pattern.compile("(?:0|[1-9][0-9]{0,9})");
    private McgatewayFriendCountProof() { }
    public static String capture(HttpClient client,String auth,String nonce) throws Exception {
        if(client==null||client.followRedirects()!=HttpClient.Redirect.NEVER||client.version()!=HttpClient.Version.HTTP_1_1) throw new IllegalArgumentException("HTTP1.1, redirects-disabled client required");
        return capture(req -> {
            HttpRequest http = buildUpstreamCompatibleRequest(req);
            long deadline = System.nanoTime() + req.timeout().toNanos();
            BoundedSubscriber sub = new BoundedSubscriber(deadline);
            // Inspect the HTTP status BEFORE choosing whether to decode bytes.
            // Reject non-200 responses without retaining or UTF-8-decoding error bodies.
            CompletableFuture<HttpResponse<String>> future = client.sendAsync(http, statusFirstBodyHandler(sub));
            try {
                HttpResponse<String> response = future.get(Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
                if (!response.uri().equals(req.uri())) { sub.cancel(); future.cancel(true); throw new IllegalStateException("redirected request"); }
                return new Response(response.statusCode(), response.headers().map(), response.body());
            } catch (TimeoutException error) {
                sub.cancel(); future.cancel(true); throw new IllegalStateException("request timeout", error);
            } catch (InterruptedException error) {
                sub.cancel(); future.cancel(true); Thread.currentThread().interrupt(); throw error;
            }
        }, auth, nonce, BUDGET);
    }
    // The body handler runs once headers are available. A failed HTTP status
    // must not be masked by malformed/untrusted response bytes.
    // replacing("") consumes and discards those bytes without buffering them.
    // Only HTTP 200 invokes the existing size- and deadline-bounded strict decoder.
    static HttpResponse.BodyHandler<String> statusFirstBodyHandler(BoundedSubscriber success) {
        if (success == null) throw new IllegalArgumentException("missing bounded subscriber");
        return info -> info.statusCode() == 200
            ? success : HttpResponse.BodySubscribers.replacing("");
    }
    // Release160 FriendManager.get() uses contract v7 and accept-language
    // on PeopleHub, while SessionManagerCore.socialSummary() uses contract v3
    // without that header. Build a deterministic request before transport.
    // Redirects remain disabled even though the upstream shared client follows
    // them, because one diagnostic command must never silently make extra GETs.
    static HttpRequest buildUpstreamCompatibleRequest(Request request) {
        if (request == null || request.uri() == null || request.authorization() == null
            || request.authorization().isBlank() || request.timeout() == null
            || request.timeout().isZero() || request.timeout().isNegative())
            throw new IllegalArgumentException("invalid count request");
        boolean friendList = FRIENDS.equals(request.uri());
        if (!friendList && !SUMMARY.equals(request.uri()))
            throw new IllegalArgumentException("unexpected count source URI");
        if (!request.contractVersion().equals(friendList ? "7" : "3"))
            throw new IllegalArgumentException("wrong count service contract");
        var builder = HttpRequest.newBuilder(request.uri()).GET().timeout(request.timeout())
            .header("Authorization", request.authorization())
            .header("x-xbl-contract-version", request.contractVersion());
        if (friendList) builder.header("accept-language", "en-GB");
        // Do not add Accept or Cache-Control. Original upstream does not.
        return builder.build();
    }
    static String capture(Fetcher fetcher,String auth,String nonce) throws Exception { return capture(fetcher,auth,nonce,BUDGET,System::nanoTime); }
    static String capture(Fetcher fetcher,String auth,String nonce,Duration budget) throws Exception { return capture(fetcher,auth,nonce,budget,System::nanoTime); }
    // Operator-safe diagnostic. The only permitted output values are fixed
    // stage/category tokens, never Exception.getMessage(), HTTP body, XUID,
    // authorization header, username or service URL.
    private static final class StageFailure extends Exception {
        final String stage, category;
        StageFailure(String stage, String category) {
            super("unavailable"); this.stage=stage; this.category=category;
        }
    }
    // Only fixed HTTP status classes may leave the diagnostic. Never emit
    // response bytes, headers, request URLs, authorization or error messages.
    private static final class SafeHttpStatusFailure extends IllegalStateException {
        final int code;
        SafeHttpStatusFailure(int code) { super("HTTP failure"); this.code=code; }
    }
    public static String safeFailureFields(Exception error) {
        if(error instanceof StageFailure failure)
            return " stage="+failure.stage+" category="+failure.category;
        return " stage=other category=unclassified";
    }
    private static String failureCategory(Exception error) {
        // sendAsync(...).get(...) wraps IO/timeout failures in ExecutionException.
        // Traverse ONLY a short chain of known, typed wrappers, never serialize
        // or log an exception, message, HTTP response, XUID or authorization.
        Exception reason=error;
        for(int depth=0;depth<4;depth++) {
            if(!(reason instanceof ExecutionException || reason instanceof CompletionException
                 || reason instanceof UncheckedIOException)) break;
            Throwable next=reason.getCause();
            if(!(next instanceof Exception e) || next==reason) break;
            reason=e;
        }
        String message=reason.getMessage()==null?"":reason.getMessage();
        if(reason instanceof InterruptedException) return "interrupted";
        if(reason instanceof java.net.http.HttpTimeoutException || reason instanceof TimeoutException
           || "capture timeout".equals(message) || "request timeout".equals(message)) return "timeout";
        if(reason instanceof java.net.UnknownHostException) return "dns-unavailable";
        if(reason instanceof javax.net.ssl.SSLException) return "tls-failed";
        if(reason instanceof java.net.ConnectException) return "connection-failed";
        if(reason instanceof java.nio.charset.CharacterCodingException) return "invalid-utf8";
        if(reason instanceof java.net.ProtocolException) return "http-protocol-unavailable";
        if(reason instanceof IOException) return "network-io";
        if(reason instanceof CancellationException) return "transport-cancelled";
        if(reason instanceof RejectedExecutionException) return "transport-unavailable";
        if(reason instanceof SafeHttpStatusFailure http) return switch(http.code) {
            case 400 -> "http-400";
            case 401 -> "http-401";
            case 403 -> "http-403";
            case 404 -> "http-404";
            case 408 -> "http-408";
            case 409 -> "http-409";
            case 429 -> "http-429";
            case 500 -> "http-500";
            case 502 -> "http-502";
            case 503 -> "http-503";
            case 504 -> "http-504";
            default -> "http-rejected";
        };
        if("HTTP failure".equals(message)) return "http-rejected";
        if(Set.of("pagination header","pagination body","unverified collection window metadata").contains(message))
            return "pagination-unproven";
        if("invalid targetFriendCount".equals(message)) return "invalid-summary";
        if(Set.of("invalid people snapshot","invalid friend row").contains(message))
            return "invalid-friends";
        if(Set.of("invalid JSON","invalid JSON token","trailing JSON","duplicate JSON key").contains(message))
            return "invalid-json";
        if(Set.of("oversize body","JSON limit","JSON row limit").contains(message))
            return "response-limits";
        if("missing JSON content type".equals(message)) return "invalid-content-type";
        // Only known local failure signatures and exception TYPES appear in receipts.
        // Do not inspect arbitrary exception text or report URLs, headers, tokens,
        // HTTP bodies, stack traces, identities or implementation class names.
        if("redirected request".equals(message)) return "redirect-blocked";
        if("malformed UTF-8".equals(message)) return "invalid-utf8";
        if(reason instanceof IllegalArgumentException) return "request-invalid";
        if(reason instanceof IllegalStateException) return "runtime-state-unavailable";
        if(reason instanceof RuntimeException) return "runtime-unavailable";
        return "unclassified";
    }
    private static int safeSummary(Fetcher fetcher, String auth, long deadline,
                                   LongSupplier clock, String stage) throws Exception {
        try {
            return summary(fetch(fetcher,SUMMARY,"3",auth,deadline,clock),deadline,clock);
        } catch(Exception error) {
            if(error instanceof InterruptedException) Thread.currentThread().interrupt();
            throw new StageFailure(stage,failureCategory(error));
        }
    }
    private static int safeFriends(Fetcher fetcher, String auth, long deadline,
                                   LongSupplier clock) throws Exception {
        // Distinguish transport/HTTP/header failures from validated JSON roster
        // failures, while never observing, accepting, or mutating a partial count.
        Response response;
        try {
            response=fetch(fetcher,FRIENDS,"7",auth,deadline,clock);
        } catch(Exception error) {
            if(error instanceof InterruptedException) Thread.currentThread().interrupt();
            throw new StageFailure("friends-fetch",failureCategory(error));
        }
        try {
            return friends(response,deadline,clock);
        } catch(Exception error) {
            if(error instanceof InterruptedException) Thread.currentThread().interrupt();
            throw new StageFailure("friends-validate",failureCategory(error));
        }
    }
    static String capture(Fetcher fetcher,String auth,String nonce,Duration budget,LongSupplier clock) throws Exception {
        if(fetcher==null||auth==null||auth.isBlank()||nonce==null||!NONCE.matcher(nonce).matches()
            ||budget==null||budget.isNegative()||budget.isZero()||clock==null)
            throw new IllegalArgumentException("invalid proof input");
        long deadline=clock.getAsLong()+budget.toNanos();
        int before=safeSummary(fetcher,auth,deadline,clock,"summary-before");
        int count=safeFriends(fetcher,auth,deadline,clock);
        int after=safeSummary(fetcher,auth,deadline,clock,"summary-after");
        if(before!=after||before!=count) throw new StageFailure("crosscheck","count-mismatch");
        try { checkDeadline(deadline,clock); }
        catch(Exception error) { throw new StageFailure("crosscheck",failureCategory(error)); }
        return "MCGATEWAY_FRIEND_COUNT_V160_V2 nonce="+nonce+" count="+count+" before="+before+" after="+after+" complete=true pages=1";
    }
    private static Response fetch(Fetcher f,URI uri,String contract,String auth,long deadline,LongSupplier clock) throws Exception { long remaining=deadline-clock.getAsLong(); if(remaining<=0) throw new IllegalStateException("capture timeout"); Response r=f.fetch(new Request(uri,contract,auth,Duration.ofNanos(remaining))); if(r==null) throw new IllegalStateException("HTTP failure"); if(r.statusCode()!=200) throw new SafeHttpStatusFailure(r.statusCode()); checkDeadline(deadline,clock); if(r.body()==null||r.body().getBytes(StandardCharsets.UTF_8).length>MAX_BODY) throw new IllegalStateException("oversize body"); boolean json=false; for(var h:r.headers().entrySet()){String n=normalize(h.getKey()); if(n.equals("contenttype"))for(String v:h.getValue())json|=v.matches("(?i)\\s*application/json(?:\\s*;\\s*charset=[a-z0-9._-]+)?\\s*"); if(n.equals("link")||Set.of("continuation","continuationtoken","next","nextlink","nextpage","nextpagelink","nextpagetoken","paging","paginginfo","pagination","hasmore","skiptoken","odatanextlink","totalpages").contains(n))throw new IllegalStateException("pagination header");} if(!json)throw new IllegalStateException("missing JSON content type"); return r; }
    private static int summary(Response r,long deadline,LongSupplier clock){Map<String,Object> root=object(parse(r.body(),deadline,clock),"summary object"); rejectContinuation(root,deadline,clock); Object v=root.get("targetFriendCount"); if(!(v instanceof NumberLiteral n)||!COUNT.matcher(n.text()).matches())throw new IllegalStateException("invalid targetFriendCount"); int count=Integer.parseInt(n.text()); root.clear(); checkDeadline(deadline,clock); return count;}
    private static int friends(Response r,long deadline,LongSupplier clock){Map<String,Object> root=object(parse(r.body(),deadline,clock),"friends object"); rejectContinuation(root,deadline,clock); rejectCollectionWindow(root,deadline,clock); Object raw=root.get("people"); if(!(raw instanceof List<?> people)||people.size()>MAX_ROWS)throw new IllegalStateException("invalid people snapshot"); Set<String> seen=new HashSet<>();int count=0;for(Object row:people){if((count&127)==0)checkDeadline(deadline,clock);Map<String,Object> p=object(row,"person");Object x=p.get("xuid"),fr=p.get("isFriend");if(!(x instanceof String id)||!validXuid(id)||!seen.add(id)||!(fr instanceof Boolean))throw new IllegalStateException("invalid friend row");if((Boolean)fr)count++;p.clear();}root.clear();checkDeadline(deadline,clock);return count;}
    private static boolean validXuid(String id){if(!XUID.matcher(id).matches())return false;try{Long.parseUnsignedLong(id);return true;}catch(NumberFormatException error){return false;}}
    private static Map<String,Object> object(Object v,String label){if(!(v instanceof Map<?,?>))throw new IllegalStateException("invalid "+label);@SuppressWarnings("unchecked") Map<String,Object> r=(Map<String,Object>)v;return r;}
    private static void rejectContinuation(Object v,long deadline,LongSupplier clock){checkDeadline(deadline,clock);if(v instanceof Map<?,?> m)for(var e:m.entrySet()){String k=normalize((String)e.getKey());if(Set.of("continuation","continuationtoken","next","nextlink","nextpage","nextpagelink","nextpagetoken","paging","paginginfo","pagination","hasmore","skiptoken","odatanextlink","totalpages").contains(k))throw new IllegalStateException("pagination body");rejectContinuation(e.getValue(),deadline,clock);}else if(v instanceof List<?> a)for(Object x:a)rejectContinuation(x,deadline,clock);}
    // Collection-level window metadata has not been proven complete for this
    // Xbox token/API contract. Even a 200 with a matching visible row count
    // cannot be certified as an entire mutual-friend roster if these hints
    // appear, including under a nested metadata object. Never infer zero.
    private static void rejectCollectionWindow(Object v,long deadline,LongSupplier clock){
        checkDeadline(deadline,clock);
        if(v instanceof Map<?,?> m) for(var e:m.entrySet()){
            String k=normalize((String)e.getKey());
            if(Set.of("totalcount","startindex","maxitems","pagesize","pagecount","pagenumber","hasnext").contains(k))
                throw new IllegalStateException("unverified collection window metadata");
            rejectCollectionWindow(e.getValue(),deadline,clock);
        } else if(v instanceof List<?> a) for(Object x:a) rejectCollectionWindow(x,deadline,clock);
    }
    private static String normalize(String value){return value.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]","");}
    interface Fetcher { Response fetch(Request request)throws Exception; } record Request(URI uri,String contractVersion,String authorization,Duration timeout){} record Response(int statusCode,Map<String,List<String>> headers,String body){} record NumberLiteral(String text){}
    static final class BoundedSubscriber implements HttpResponse.BodySubscriber<String> {
        private final CompletableFuture<String> body = new CompletableFuture<>();
        private final long deadline;
        private final ByteArrayOutputStream out = new ByteArrayOutputStream();
        private Flow.Subscription subscription;

        BoundedSubscriber(long deadline) { this.deadline = deadline; }
        public CompletionStage<String> getBody() { return body; }
        public void onSubscribe(Flow.Subscription subscription) { this.subscription = subscription; subscription.request(Long.MAX_VALUE); }
        public void onNext(List<ByteBuffer> buffers) {
            try {
                if (System.nanoTime() > deadline) throw new IllegalStateException("request timeout");
                for (ByteBuffer buffer : buffers) {
                    if (buffer.remaining() > MAX_BODY - out.size()) throw new IllegalStateException("oversize body");
                    byte[] bytes = new byte[buffer.remaining()]; buffer.get(bytes); out.write(bytes);
                }
            } catch (Exception error) { cancel(); body.completeExceptionally(error); }
        }
        public void onError(Throwable error) { body.completeExceptionally(error); }
        public void onComplete() {
            if (body.isDone()) return;
            try {
                body.complete(StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(out.toByteArray())).toString());
            } catch (CharacterCodingException error) { body.completeExceptionally(new IllegalStateException("malformed UTF-8", error)); }
        }
        void cancel() { if (subscription != null) subscription.cancel(); }
    }
    private static Object parse(String source,long deadline,LongSupplier clock){try(JsonReader r=new JsonReader(new StringReader(source))){r.setStrictness(Strictness.STRICT);Counter c=new Counter();Object v=read(r,0,c,deadline,clock);checkDeadline(deadline,clock);if(r.peek()!=JsonToken.END_DOCUMENT)throw new IllegalStateException("trailing JSON");return v;}catch(IOException e){throw new IllegalStateException("invalid JSON",e);}}
    private static Object read(JsonReader r,int d,Counter c,long deadline,LongSupplier clock)throws IOException{if(d>MAX_DEPTH||++c.nodes>MAX_NODES)throw new IllegalStateException("JSON limit");if((c.nodes&127)==0)checkDeadline(deadline,clock);return switch(r.peek()){case BEGIN_OBJECT->{Map<String,Object> o=new LinkedHashMap<>();r.beginObject();while(r.hasNext()){String n=r.nextName();if(o.containsKey(n))throw new IllegalStateException("duplicate JSON key");o.put(n,read(r,d+1,c,deadline,clock));}r.endObject();yield o;}case BEGIN_ARRAY->{List<Object> a=new ArrayList<>();r.beginArray();while(r.hasNext()){if(a.size()>=MAX_ROWS)throw new IllegalStateException("JSON row limit");a.add(read(r,d+1,c,deadline,clock));}r.endArray();yield a;}case STRING->r.nextString();case NUMBER->new NumberLiteral(r.nextString());case BOOLEAN->r.nextBoolean();case NULL->{r.nextNull();yield null;}default->throw new IllegalStateException("invalid JSON token");};}
    private static void checkDeadline(long deadline,LongSupplier clock){if(clock.getAsLong()>deadline)throw new IllegalStateException("capture timeout");}
    private static final class Counter{int nodes;}
}
