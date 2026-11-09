package com.rtm516.mcxboxbroadcast.core;

/**
 * Offline proof that the Release160 command nonce window stays bounded while
 * continuing to reject recent duplicates.
 */
public final class FriendNonceWindowProof {
    private static final long FIFTEEN_MINUTES_MS = 15L * 60L * 1_000L;

    private FriendNonceWindowProof() { }

    private static void need(boolean value) {
        if (!value) throw new AssertionError();
    }

    private static String nonce(int value) {
        return String.format("%032x", value);
    }

    public static void main(String[] args) {
        long now = 1_800_000_000_000L;
        FriendManager.McgatewayV2NonceWindow window = new FriendManager.McgatewayV2NonceWindow();

        need(window.consume(nonce(1), now));
        need(!window.consume(nonce(1), now + 1));
        need(!window.consume("not-a-nonce", now));

        for (int index = 2; index <= 300; index++) {
            need(window.consume(nonce(index), now + 1));
        }
        need(window.size() == 300);
        need(!window.consume(nonce(300), now + 2));

        long afterTtl = now + FIFTEEN_MINUTES_MS + 2;
        need(window.consume(nonce(1), afterTtl));
        need(window.size() == 1);
        need(!window.consume(nonce(1), afterTtl + 1));

        FriendManager.McgatewayV2NonceWindow saturated = new FriendManager.McgatewayV2NonceWindow();
        for (int index = 1; index <= 4_097; index++) {
            need(saturated.consume(nonce(index), now));
        }
        need(saturated.size() == 4_096);
        need(!saturated.consume(nonce(4_097), now + 1));
        need(saturated.consume(nonce(1), now + 1));
        need(saturated.size() == 4_096);

        System.out.println("PASS: command nonce deduplication is recent-windowed, expiring, and capacity-bounded");
    }
}
