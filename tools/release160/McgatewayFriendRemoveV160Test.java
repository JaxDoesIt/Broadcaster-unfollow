package com.rtm516.mcxboxbroadcast.core;

import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;

public final class McgatewayFriendRemoveV160Test {
    private static int passed;
    private static final String ACCOUNT = "2533270000000011";
    private static final String TARGET = "2533270000000022";
    private static final String NONCE = "ab".repeat(16);
    private static final McgatewayFriendRemoveV160.Permit PERMIT = new McgatewayFriendRemoveV160.Permit(
        ACCOUNT, "session:160", TARGET, NONCE, true, true, false, true);
    private static final McgatewayFriendRemoveV160.Snapshot PRESENT =
        new McgatewayFriendRemoveV160.Snapshot(ACCOUNT, "session:160", TARGET, 200, true, true, true, true, false);
    private static final McgatewayFriendRemoveV160.Snapshot ABSENT =
        new McgatewayFriendRemoveV160.Snapshot(ACCOUNT, "session:160", TARGET, 200, false, false, true, true, false);

    private static final class Fake implements McgatewayFriendRemoveV160.Transport {
        final Deque<Object> observations = new ArrayDeque<>();
        final Deque<Object> followers = new ArrayDeque<>();
        final Deque<Object> outgoing = new ArrayDeque<>();
        int reads, followerDeletes, outgoingDeletes;
        long clock;
        Runnable duringRead;

        Fake states(Object... seq) {
            for(Object step : seq) observations.addLast(step);
            return this;
        }
        Fake follower(Object step) { followers.add(step); return this; }
        Fake outgoing(Object step) { outgoing.add(step); return this; }
        private static <T> T take(Deque<Object> q, String name) throws Exception {
            if(q.isEmpty()) throw new IllegalStateException("unexpected " + name);
            Object o = q.removeFirst();
            if(o instanceof Exception e) throw e;
            @SuppressWarnings("unchecked") T value = (T)o;
            return value;
        }
        public McgatewayFriendRemoveV160.Snapshot readRelationship(McgatewayFriendRemoveV160.Permit p, Duration timeout) throws Exception {
            if(timeout.isZero() || timeout.isNegative() || timeout.compareTo(Duration.ofSeconds(8))>0) throw new AssertionError("read deadline");
            reads++;
            if(duringRead != null) duringRead.run();
            return take(observations,"read");
        }
        public McgatewayFriendRemoveV160.DeleteReply deleteFollower(McgatewayFriendRemoveV160.Permit p, Duration timeout) throws Exception {
            if(timeout.isZero() || timeout.isNegative()) throw new AssertionError("follower deadline");
            followerDeletes++;
            return take(followers,"follower delete");
        }
        public McgatewayFriendRemoveV160.DeleteReply deleteOutgoing(McgatewayFriendRemoveV160.Permit p, Duration timeout) throws Exception {
            if(timeout.isZero() || timeout.isNegative()) throw new AssertionError("outgoing deadline");
            outgoingDeletes++;
            return take(outgoing,"outgoing delete");
        }
    }

    private static McgatewayFriendRemoveV160.DeleteReply http(int status) {
        return new McgatewayFriendRemoveV160.DeleteReply(status,false,true);
    }
    private static void eq(Object expected,Object actual,String label) {
        if(!Objects.equals(expected,actual)) throw new AssertionError(label+" expected="+expected+" actual="+actual);
        passed++;
    }
    private static McgatewayFriendRemoveV160 run(Fake f, McgatewayFriendRemoveV160.Permit p,
                                                    McgatewayFriendRemoveV160.State state) {
        McgatewayFriendRemoveV160 subject = new McgatewayFriendRemoveV160(f, () -> f.clock);
        var result = subject.attempt(p);
        eq(state, result.state(),"outcome");
        if(!result.verified()) eq(null,result.verifiedFrame(),"no false success frame");
        return subject;
    }
    private static McgatewayFriendRemoveV160.Permit permit(boolean owner, boolean durable, boolean prior, boolean sync) {
        return new McgatewayFriendRemoveV160.Permit(ACCOUNT, "session:160", TARGET, NONCE, owner, durable, prior, sync);
    }
    private static McgatewayFriendRemoveV160.Snapshot snapshot(String account,String session,String target,int status,
                                                           Boolean incoming,Boolean outgoing,boolean complete,boolean fresh,boolean redirected) {
        return new McgatewayFriendRemoveV160.Snapshot(account,session,target,status,incoming,outgoing,complete,fresh,redirected);
    }

    public static void main(String[] args) throws Exception {
        {
            Fake f = new Fake().states(PRESENT,ABSENT).follower(http(204)).outgoing(http(200));
            var subject = new McgatewayFriendRemoveV160(f, () -> f.clock);
            var result = subject.attempt(PERMIT);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_REMOVED,result.state(),"two-direction postcondition");
            eq(true,result.remoteMutationMayHaveOccurred(),"mutation sent");
            eq(true,result.verifiedFrame().contains("result=removed pre=present post=absent verified=true"),"specific terminal frame");
            eq(2,f.reads,"two fresh remote reads");
            eq(1,f.followerDeletes,"follower deleted once");
            eq(1,f.outgoingDeletes,"outgoing deleted once");
            eq(McgatewayFriendRemoveV160.State.DENIED,subject.attempt(PERMIT).state(),"nonce cannot be reused");
            eq(1,f.followerDeletes,"replay has no second remote mutation");
        }
        {
            Fake f=new Fake().states(ABSENT,ABSENT);
            var r=new McgatewayFriendRemoveV160(f, () -> f.clock).attempt(PERMIT);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_ALREADY_ABSENT,r.state(),"idempotent only on two reads");
            eq(false,r.remoteMutationMayHaveOccurred(),"no remote write if already absent");
            eq(0,f.followerDeletes,"no follower delete on absent");
            eq(0,f.outgoingDeletes,"no outgoing delete on absent");
            eq(true,r.verifiedFrame().contains("result=already-absent pre=absent"),"no bogus new removal");
        }
        for(int status:new int[]{200,201,204,299,404}) {
            Fake f=new Fake().states(PRESENT,ABSENT).follower(http(status)).outgoing(http(status));
            run(f, PERMIT, McgatewayFriendRemoveV160.State.VERIFIED_REMOVED);
        }
        for(int status:new int[]{0,301,302,400,401,403,429,500,503}) {
            Fake f=new Fake().states(PRESENT).follower(http(status));
            run(f, PERMIT, McgatewayFriendRemoveV160.State.UNCERTAIN);
            eq(1,f.followerDeletes,"first delete attempted");
            eq(0,f.outgoingDeletes,"second delete withheld");
        }
        for(int status:new int[]{0,301,401,403,429,500,503}) {
            Fake f=new Fake().states(PRESENT).follower(http(204)).outgoing(http(status));
            run(f, PERMIT, McgatewayFriendRemoveV160.State.UNCERTAIN);
            eq(1,f.outgoingDeletes,"second delete attempted only once");
        }
        for(var bad:new McgatewayFriendRemoveV160.Snapshot[]{
            snapshot(ACCOUNT,"session:160",TARGET,503,true,true,true,true,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,true,true,false,true,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,true,true,true,false,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,true,true,true,true,true),
            snapshot(ACCOUNT,"session:160",TARGET,200,null,true,true,true,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,true,null,true,true,false),
            snapshot("different","session:160",TARGET,200,true,true,true,true,false),
            snapshot(ACCOUNT,"different",TARGET,200,true,true,true,true,false),
            snapshot(ACCOUNT,"session:160","different",200,true,true,true,true,false)
        }) {
            Fake f=new Fake().states(bad);
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNVERIFIED);
            eq(0,f.followerDeletes,"invalid precondition never invokes DELETE");
        }
        for(var bad:new McgatewayFriendRemoveV160.Snapshot[]{
            PRESENT,
            snapshot(ACCOUNT,"session:160",TARGET,503,false,false,true,true,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,false,false,true,false,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,false,false,false,true,false),
            snapshot(ACCOUNT,"session:160",TARGET,200,false,false,true,true,true),
            snapshot(ACCOUNT,"wrong-session",TARGET,200,false,false,true,true,false)
        }) {
            Fake f=new Fake().states(PRESENT,bad).follower(http(204)).outgoing(http(204));
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNCERTAIN);
            eq(2,f.reads,"unverified post-state despite DELETE 2xx");
        }
        {
            Fake f = new Fake().states(ABSENT,PRESENT);
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNVERIFIED);
            eq(0,f.followerDeletes,"already absent with newer present is not deleted");
        }
        for(var invalid:new McgatewayFriendRemoveV160.Permit[]{
            permit(false,true,false,true),permit(true,false,false,true),
            permit(true,true,true,true),permit(true,true,false,false),
            new McgatewayFriendRemoveV160.Permit(ACCOUNT,"session:160",TARGET,"zz".repeat(16),true,true,false,true),
            new McgatewayFriendRemoveV160.Permit(ACCOUNT,"session:160",TARGET,"A".repeat(32),true,true,false,true),
            new McgatewayFriendRemoveV160.Permit(ACCOUNT,"session:160",ACCOUNT,NONCE,true,true,false,true),
            new McgatewayFriendRemoveV160.Permit("0","session:160",TARGET,NONCE,true,true,false,true),
            new McgatewayFriendRemoveV160.Permit(ACCOUNT,"session:160","18446744073709551616",NONCE,true,true,false,true),
            new McgatewayFriendRemoveV160.Permit(ACCOUNT,"invalid session whitespace",TARGET,NONCE,true,true,false,true)
        }) {
            Fake f=new Fake();
            run(f,invalid,McgatewayFriendRemoveV160.State.DENIED);
            eq(0,f.reads,"invalid permit no remote requests");
        }
        {
            Fake f=new Fake().states(new InterruptedException("stopped"));
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNVERIFIED);
            eq(true,Thread.interrupted(),"interrupt flag restored");
        }
        {
            Fake f=new Fake().states(PRESENT).follower(new java.net.SocketTimeoutException());
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNCERTAIN);
        }
        {
            Fake f=new Fake().states(PRESENT).follower(http(204)).outgoing(new java.io.IOException("network"));
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNCERTAIN);
        }
        {
            Fake f=new Fake().states(PRESENT,ABSENT).follower(http(204)).outgoing(http(204));
            f.duringRead=()->f.clock += Duration.ofSeconds(31).toNanos();
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNVERIFIED);
            eq(0,f.followerDeletes,"bounded pre-read window expires before DELETE");
        }
        {
            Fake f=new Fake().states(PRESENT).follower(http(204));
            f.duringRead=()->{};
            f.outgoing(http(204));
            // Later adapter may stall. A fresh post-read that cannot finish
            // must never be called successful.
            run(f,PERMIT,McgatewayFriendRemoveV160.State.UNCERTAIN);
        }
        {
            Fake f=new Fake().states(PRESENT,ABSENT).follower(http(204)).outgoing(http(204));
            var subject=new McgatewayFriendRemoveV160(f, () -> f.clock);
            AtomicReference<McgatewayFriendRemoveV160.State> inner=new AtomicReference<>();
            f.duringRead=()->inner.set(subject.attempt(new McgatewayFriendRemoveV160.Permit(
                ACCOUNT,"session:160",TARGET,"cd".repeat(16),true,true,false,true)).state());
            var result=subject.attempt(PERMIT);
            eq(McgatewayFriendRemoveV160.State.VERIFIED_REMOVED,result.state(),"outer completes");
            eq(McgatewayFriendRemoveV160.State.BUSY,inner.get(),"concurrent operation refused");
        }
        System.out.println("McgatewayFriendRemoveV160Test: PASS " + passed + " assertions, fake transport only");
    }
}
