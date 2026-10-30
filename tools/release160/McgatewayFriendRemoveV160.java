package com.rtm516.mcxboxbroadcast.core;

import java.time.Duration;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Pure-Java, unconnected Release160 friend-removal protocol candidate.
 * NO production console command imports this class. A future integration must
 * provide authenticated, redirect-free, bounded Xbox HTTP adapters, plus an
 * independently durable controller dispatch-intent and a cross-worker friend
 * sync/assignment fence. Never infer an exact friend-count delta from removal.
 */
public final class McgatewayFriendRemoveV160 {
    private static final Pattern NONCE = Pattern.compile("[0-9a-f]{32}");
    private static final Pattern XUID = Pattern.compile("[1-9][0-9]{0,19}");
    private static final int MAX_NONCES = 4096;
    private static final long MAX_OPERATION_NANOS = Duration.ofSeconds(30).toNanos();
    private static final long MAX_CALL_NANOS = Duration.ofSeconds(8).toNanos();

    /** A wire-independent, complete remote relationship observation. */
    public record Snapshot(String account, String session, String target, int status,
                           Boolean incoming, Boolean outgoing, boolean complete,
                           boolean fresh, boolean redirected) { }

    /** HTTP status 2xx/404 is a tentative DELETE result, never postcondition proof. */
    public record DeleteReply(int status, boolean redirected, boolean complete) { }

    /** The controller must provide durable and owner-authorized admission. */
    public record Permit(String account, String session, String xuid, String nonce,
                         boolean ownerAuthorized, boolean durableIntentCommitted,
                         boolean priorUncertain, boolean externalFriendSyncFenced) { }

    public enum State { DENIED, BUSY, UNVERIFIED, UNCERTAIN, VERIFIED_REMOVED, VERIFIED_ALREADY_ABSENT }

    public record Outcome(State state, String reason, boolean remoteMutationMayHaveOccurred,
                          String verifiedFrame) {
        public boolean verified() {
            return state == State.VERIFIED_REMOVED || state == State.VERIFIED_ALREADY_ABSENT;
        }
    }

    /** All production HTTP/identity behavior must be implemented in an audited adapter. */
    public interface Transport {
        Snapshot readRelationship(Permit permit, Duration timeout) throws Exception;
        DeleteReply deleteFollower(Permit permit, Duration timeout) throws Exception;
        DeleteReply deleteOutgoing(Permit permit, Duration timeout) throws Exception;
    }

    public interface Clock { long nanoTime(); }

    private final Transport transport;
    private final Clock clock;
    private final AtomicBoolean inFlight = new AtomicBoolean();
    private final Set<String> consumedNonces = new HashSet<>();

    public McgatewayFriendRemoveV160(Transport transport, Clock clock) {
        if (transport == null || clock == null) throw new IllegalArgumentException("missing dependency");
        this.transport = transport;
        this.clock = clock;
    }

    private static boolean validXuid(String xuid) {
        if (xuid == null || !XUID.matcher(xuid).matches()) return false;
        try { Long.parseUnsignedLong(xuid); return true; }
        catch (NumberFormatException e) { return false; }
    }

    private static Outcome stop(State state, String reason, boolean touched) {
        return new Outcome(state, reason, touched, null);
    }

    private static boolean trusted(Snapshot snapshot, Permit permit) {
        return snapshot != null && snapshot.status == 200 && snapshot.complete
            && snapshot.fresh && !snapshot.redirected
            && permit.account.equals(snapshot.account) && permit.session.equals(snapshot.session)
            && permit.xuid.equals(snapshot.target)
            && snapshot.incoming != null && snapshot.outgoing != null;
    }

    private static boolean acceptedDelete(DeleteReply reply) {
        if (reply == null || reply.redirected || !reply.complete) return false;
        return reply.status == 404 || reply.status >= 200 && reply.status <= 299;
    }

    private Duration remaining(long start) {
        final long elapsed = clock.nanoTime() - start;
        if (elapsed < 0 || elapsed >= MAX_OPERATION_NANOS) throw new IllegalStateException("expired window");
        return Duration.ofNanos(Math.min(MAX_CALL_NANOS, MAX_OPERATION_NANOS - elapsed));
    }

    /**
     * This is one NO-RETRY operation. A failure after an attempted DELETE is
     * UNCERTAIN, not a negative relationship proof. The consumed nonce persists
     * ONLY in this instance: durable replay prevention remains the controller's
     * responsibility, and this prototype MUST NOT be wired into production.
     */
    public Outcome attempt(Permit permit) {
        if (permit == null || !permit.ownerAuthorized || !permit.durableIntentCommitted
            || permit.priorUncertain || !permit.externalFriendSyncFenced
            || !validXuid(permit.account) || !validXuid(permit.xuid)
            || permit.account.equals(permit.xuid)
            || permit.session == null || !permit.session.matches("[A-Za-z0-9._:-]{1,128}")
            || permit.nonce == null || !NONCE.matcher(permit.nonce).matches()) {
            return stop(State.DENIED, "unapproved-or-invalid-permit", false);
        }
        if (!inFlight.compareAndSet(false, true)) return stop(State.BUSY, "account-busy", false);
        try {
            String nonceKey = permit.account + ":" + permit.nonce;
            if (consumedNonces.contains(nonceKey)) return stop(State.DENIED, "replayed-nonce", false);
            if (consumedNonces.size() >= MAX_NONCES) return stop(State.DENIED, "nonce-ledger-capacity", false);
            consumedNonces.add(nonceKey); // consume even on pre-read failure
            long start = clock.nanoTime();
            boolean touched = false;
            try {
                Snapshot before = transport.readRelationship(permit, remaining(start));
                if (!trusted(before, permit)) return stop(State.UNVERIFIED, "untrusted-pre-state", false);
                boolean wasPresent = before.incoming || before.outgoing;
                if (wasPresent) {
                    // A DELETE attempt may succeed remotely even if the client
                    // times out or throws. Mark touched BEFORE invoking it.
                    Duration followerBudget = remaining(start);
                    touched = true;
                    if (!acceptedDelete(transport.deleteFollower(permit, followerBudget)))
                        return stop(State.UNCERTAIN, "follower-delete-unverified", true);
                    Duration outgoingBudget = remaining(start);
                    if (!acceptedDelete(transport.deleteOutgoing(permit, outgoingBudget)))
                        return stop(State.UNCERTAIN, "outgoing-delete-unverified", true);
                }
                Snapshot after = transport.readRelationship(permit, remaining(start));
                if (!trusted(after, permit) || after.incoming || after.outgoing)
                    return stop(touched ? State.UNCERTAIN : State.UNVERIFIED,
                                "post-state-not-proven-absent", touched);
                String result = wasPresent ? "removed" : "already-absent";
                // This frame is only an in-memory result. A separately tested
                // producer console adapter must decide trusted log emission.
                String frame = "MCGATEWAY_FRIEND_REMOVE_V160_V1 nonce=" + permit.nonce
                    + " xuid=" + permit.xuid + " result=" + result
                    + " pre=" + (wasPresent ? "present" : "absent")
                    + " post=absent verified=true";
                return new Outcome(wasPresent ? State.VERIFIED_REMOVED : State.VERIFIED_ALREADY_ABSENT,
                                   "fresh-post-read-proved-absent", touched, frame);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return stop(touched ? State.UNCERTAIN : State.UNVERIFIED, "interrupted", touched);
            } catch (Exception e) {
                return stop(touched ? State.UNCERTAIN : State.UNVERIFIED,
                            touched ? "post-dispatch-error" : "pre-dispatch-error", touched);
            }
        } finally {
            inFlight.set(false);
        }
    }
}
