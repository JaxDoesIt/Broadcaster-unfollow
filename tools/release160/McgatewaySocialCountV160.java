package com.rtm516.mcxboxbroadcast.core;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Pure, read-only Release160 social-summary response inspection.
 * The Xbox summary field is not proof of an exact/full friendship snapshot.
 * Never admit this result to capacity, cleanup or durable verified-count state.
 */
public final class McgatewaySocialCountV160 {
    private McgatewaySocialCountV160() {}

    public record Observation(int count, String reason) {
        public boolean observed() {
            return count > 0 && "ok".equals(reason);
        }
        public String display() {
            return observed() ? Integer.toString(count) : "unavailable";
        }
    }

    public static Observation unavailable(String reason) {
        return new Observation(-1, reason);
    }

    public static Observation parse(int httpStatus, String body) {
        if (httpStatus != 200) return unavailable("http-non200");
        if (body == null || body.isBlank() || body.length() > 65536) return unavailable("invalid-body");
        try {
            JsonElement document = JsonParser.parseString(body);
            if (document == null || !document.isJsonObject()) return unavailable("invalid-body");
            JsonObject obj = document.getAsJsonObject();
            JsonElement value = obj.get("targetFriendCount");
            if (value == null || value.isJsonNull()) return unavailable("missing-field");
            if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) return unavailable("invalid-field");
            String decimal = value.getAsString();
            if (!decimal.matches("(?:0|[1-9][0-9]{0,4})")) return unavailable("invalid-field");
            int count = Integer.parseInt(decimal);
            if (count == 0) return unavailable("zero-unverified");
            if (count > Constants.MAX_FRIENDS) return unavailable("out-of-range");
            return new Observation(count, "ok");
        } catch (RuntimeException ignored) {
            return unavailable("invalid-body");
        }
    }
}
