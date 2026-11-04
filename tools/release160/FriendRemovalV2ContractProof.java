package com.rtm516.mcxboxbroadcast.core;

/** Offline proof of the terminal V2 policy; it has no HTTP or token access. */
public final class FriendRemovalV2ContractProof {
    private FriendRemovalV2ContractProof() { }
    record State(String value, boolean removable) { }
    static State state(boolean friend, boolean sent, boolean received) {
        return new State(friend || sent || received ? "present" : "absent", friend && !sent && !received);
    }
    static String terminal(String before, int deleteStatus, String after, boolean accountStable, boolean sessionStable) {
        if (before.equals("absent")) return "already-absent";
        if (!before.equals("present") || !accountStable || !sessionStable) return "uncertain";
        if (deleteStatus != 200 && deleteStatus != 204) return "uncertain";
        return after.equals("absent") ? "removed" : "uncertain";
    }
    static void need(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) {
        need(state(false, false, false).value().equals("absent"));
        need(state(true, false, false).removable());
        need(!state(false, true, false).removable());
        need(!state(false, false, true).removable());
        need(terminal("absent", 0, "absent", true, true).equals("already-absent"));
        need(terminal("present", 200, "absent", true, true).equals("removed"));
        need(terminal("present", 204, "absent", true, true).equals("removed"));
        for (int status : new int[]{0, 199, 201, 404, 429, 500}) need(terminal("present", status, "absent", true, true).equals("uncertain"));
        need(terminal("present", 204, "present", true, true).equals("uncertain"));
        need(terminal("present", 204, "unknown", true, true).equals("uncertain"));
        need(terminal("present", 204, "absent", false, true).equals("uncertain"));
        need(terminal("present", 204, "absent", true, false).equals("uncertain"));
        System.out.println("PASS: V2 relationship policy only; no HTTP or mutation");
    }
}
