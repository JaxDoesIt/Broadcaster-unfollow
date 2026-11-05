package com.rtm516.mcxboxbroadcast.core;

/** Offline proof of the terminal V2 policy; it has no HTTP or token access. */
public final class FriendRemovalV2ContractProof {
    private FriendRemovalV2ContractProof() { }
    record State(String value, boolean removable) { }
    static State state(boolean friend, boolean sent, boolean received) {
        return new State(friend || sent || received ? "present" : "absent", friend && !sent && !received);
    }
    static String terminal(String before, int deleteStatus, String after, boolean accountStable, boolean sessionStable) {
        // Production requires strict positive admission even for a no-op.
        if (!before.equals("present") || !accountStable || !sessionStable) return "uncertain";
        if (deleteStatus != 200 && deleteStatus != 204) return "uncertain";
        return after.equals("absent") || after.equals("friendship-absent") ? "removed" : "uncertain";
    }
    static boolean strictTransport(int status, boolean exactUri, String contentType, int age, boolean freshDate,
                                   boolean accountBefore, boolean accountAfter, boolean sessionBefore, boolean sessionAfter) {
        return status == 200 && exactUri && contentType.equals("application/json") && age == 0 && freshDate
            && accountBefore && accountAfter && sessionBefore && sessionAfter;
    }
    static void need(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) {
        for (int bits = 0; bits < 8; bits++) {
            boolean friend = (bits & 1) != 0, sent = (bits & 2) != 0, received = (bits & 4) != 0;
            State current = state(friend, sent, received);
            need(current.value().equals(bits == 0 ? "absent" : "present"));
            need(current.removable() == (friend && !sent && !received));
        }
        need(terminal("absent", 0, "absent", true, true).equals("uncertain"));
        need(terminal("present", 200, "absent", true, true).equals("removed"));
        need(terminal("present", 204, "absent", true, true).equals("removed"));
        need(terminal("present", 204, "friendship-absent", true, true).equals("removed"));
        need(terminal("unknown", 204, "friendship-absent", true, true).equals("uncertain"));
        need(terminal("present", 404, "friendship-absent", true, true).equals("uncertain"));
        need(terminal("present", 204, "friendship-absent", false, true).equals("uncertain"));
        need(terminal("present", 204, "friendship-absent", true, false).equals("uncertain"));

        for (int status : new int[]{0, 199, 201, 404, 429, 500}) need(terminal("present", status, "absent", true, true).equals("uncertain"));
        need(terminal("present", 204, "present", true, true).equals("uncertain"));
        need(terminal("present", 204, "unknown", true, true).equals("uncertain"));
        need(terminal("present", 204, "absent", false, true).equals("uncertain"));
        need(terminal("present", 204, "absent", true, false).equals("uncertain"));
        need(strictTransport(200, true, "application/json", 0, true, true, true, true, true));
        for (int status : new int[]{199, 201, 302, 404, 429, 500}) need(!strictTransport(status, true, "application/json", 0, true, true, true, true, true));
        need(!strictTransport(200, false, "application/json", 0, true, true, true, true, true));
        need(!strictTransport(200, true, "text/html", 0, true, true, true, true, true));
        need(!strictTransport(200, true, "application/json", 1, true, true, true, true, true));
        need(!strictTransport(200, true, "application/json", 0, false, true, true, true, true));
        need(!strictTransport(200, true, "application/json", 0, true, false, true, true, true));
        need(!strictTransport(200, true, "application/json", 0, true, true, false, true, true));
        need(!strictTransport(200, true, "application/json", 0, true, true, true, false, true));
        need(!strictTransport(200, true, "application/json", 0, true, true, true, true, false));
        System.out.println("PASS: V2 relationship policy only; no HTTP or mutation");
    }
}
