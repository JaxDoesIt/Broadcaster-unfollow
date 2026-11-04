package com.rtm516.mcxboxbroadcast.core;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Offline interleaving proof for the same lock placement injected into
 * FriendManager. It models the only dangerous race: addIfRequired's GET saying
 * friend=true while another actor deletes that target. The shared lock makes
 * that result linearizable: either delete is denied while the GET is active or
 * the add happens after a completed delete. No queue entry is discarded.
 */
public final class FriendRemovalV2InterleavingProof {
    private FriendRemovalV2InterleavingProof() { }
    static void need(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) throws Exception {
        ReentrantLock lock = new ReentrantLock();
        AtomicBoolean remoteFriend = new AtomicBoolean(true), queuedAdd = new AtomicBoolean(false);
        CountDownLatch checked = new CountDownLatch(1), releaseRead = new CountDownLatch(1), normalDone = new CountDownLatch(1);
        Thread normal = new Thread(() -> {
            lock.lock();
            try {
                boolean alreadyFriend = remoteFriend.get(); // addIfRequired target GET
                checked.countDown();
                try { if (!releaseRead.await(2, TimeUnit.SECONDS)) throw new AssertionError(); }
                catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new AssertionError(error); }
                if (!alreadyFriend) queuedAdd.set(true);
            } finally { lock.unlock(); normalDone.countDown(); }
        });
        normal.start(); need(checked.await(2, TimeUnit.SECONDS));
        // V2 is nonblocking, so it cannot delete during the normal GET/decision.
        need(!lock.tryLock()); releaseRead.countDown(); need(normalDone.await(2, TimeUnit.SECONDS)); normal.join();
        need(remoteFriend.get()); need(!queuedAdd.get());

        // Conversely a normal add waits behind V2, observes the post-delete
        // result, and queues the target instead of being silently lost.
        lock.lock(); remoteFriend.set(true); queuedAdd.set(false);
        CountDownLatch attempted = new CountDownLatch(1), added = new CountDownLatch(1);
        Thread afterDelete = new Thread(() -> {
            attempted.countDown(); lock.lock();
            try { if (!remoteFriend.get()) queuedAdd.set(true); }
            finally { lock.unlock(); added.countDown(); }
        });
        afterDelete.start(); need(attempted.await(2, TimeUnit.SECONDS)); Thread.sleep(20);
        need(!queuedAdd.get()); remoteFriend.set(false); lock.unlock(); need(added.await(2, TimeUnit.SECONDS)); afterDelete.join();
        need(queuedAdd.get());
        System.out.println("PASS: V2/addIfRequired interleaving is serialized and preserves queued add");
    }
}
