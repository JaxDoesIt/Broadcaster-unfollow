#!/usr/bin/env python3
"""Source-only repair of Release160 accounts-list status, after the exact original overlay.

Does not connect to Xbox, modify live Docker, enable friendship mutations, or publish images.
All targets are preflighted before writing. Idempotent for exact reviewed changes only.
"""
from pathlib import Path
import argparse
import hashlib

SESSION = "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java"
CORE = "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManagerCore.java"
HELPER_TARGET = "core/src/main/java/com/rtm516/mcxboxbroadcast/core/McgatewaySocialCountV160.java"
CONSOLE = "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
PINNED_CORE_BLOB = "4b4e7f201dfbfc8e1ed9dfbf765abefd498126bf"
HELPER_ID = "public final class McgatewaySocialCountV160"
PINNED_SESSION_BLOB = "3faaef8fda8e2737e7dad6e6631b53c42ea56482"
EXPIRY_UPSTREAM = '''        if (friendSyncConfig.expiry().enabled()) {
            scheduledThreadPool.scheduleWithFixedDelay(this::expireFriends, 10, friendSyncConfig.expiry().check(), TimeUnit.SECONDS);
        }'''
EXPIRY_OVERLAY = '''        // MCGATEWAY_RELEASE160_EXPIRY_HOLD: never schedule upstream removal.
        // MCGateway owns friendship cleanup and Release160 has no reviewed
        // deletion receipt contract. Keep every legacy friend intact.
        logger.warn("MCGateway release160: upstream automatic friend expiry is disabled.");'''
HEALTH_UPSTREAM = '''    public Logger logger() {
        return logger;
    }'''
HEALTH_OVERLAY = '''    public Logger logger() {
        return logger;
    }

    public String mcgatewayHealthLine() {
        boolean rta = rtaWebsocket != null && rtaWebsocket.isOpen();
        boolean httpSignaling = signaling != null && signaling.isActive();
        boolean published = sessionInfo != null && sessionInfo.getHandleId() != null && !sessionInfo.getHandleId().isBlank();
        return "MCGATEWAY_HEALTH_V160 initialized=" + initialized + " rta=" + rta + " httpSignaling=" + httpSignaling + " published=" + published;
    }'''

LIST_OLD = '''    public void listSessions() {
        coreLogger.info("Loading status of sessions...");

        // Run off the calling thread as this makes web requests
        scheduledThreadPool.execute(() -> {
            List<String> messages = new ArrayList<>();

            messages.add("Primary Session:");
            messages.add(" - Gamertag: " + getGamertag());
            messages.add("   Friends: " + socialSummary().targetFriendCount() + "/" + Constants.MAX_FRIENDS);

            if (!subSessionManagers.isEmpty()) {
                messages.add("Sub-sessions: (" + subSessionManagers.size() + ")");
                for (Map.Entry<String, SubSessionManager> subSession : subSessionManagers.entrySet()) {
                    messages.add(" - ID: " + subSession.getKey());
                    messages.add("   Gamertag: " + subSession.getValue().getGamertag());
                    messages.add("   Friends: " + subSession.getValue().socialSummary().targetFriendCount() + "/" + Constants.MAX_FRIENDS);
                }
            } else {
                messages.add("No sub-sessions");
            }

            for (String message : messages) {
                coreLogger.info(message);
            }
        });
    }'''

LIST_NEW = '''    public void listSessions() {
        coreLogger.info("Loading status of sessions...");

        // MCGATEWAY_ACCOUNTS_LIST_PRODUCER_V160: use the existing async worker,
        // but ALWAYS report a sanitized unavailable receipt instead of silently
        // dropping the result when the Xbox summary is absent or malformed.
        // This output is provisional only; never a capacity or removal proof.
        try {
            scheduledThreadPool.execute(() -> {
                try {
                    List<String> messages = new ArrayList<>();
                    McgatewaySocialCountV160.Observation primary = mcgatewaySocialCountV160();
                    messages.add("Primary Session:");
                    messages.add(" - Gamertag: " + getGamertag());
                    messages.add("   Friends: " + primary.display() + "/" + Constants.MAX_FRIENDS);

                    if (!subSessionManagers.isEmpty()) {
                        messages.add("Sub-sessions: (" + subSessionManagers.size() + ")");
                        for (Map.Entry<String, SubSessionManager> subSession : subSessionManagers.entrySet()) {
                            messages.add(" - ID: " + subSession.getKey());
                            messages.add("   Gamertag: " + subSession.getValue().getGamertag());
                            McgatewaySocialCountV160.Observation child = subSession.getValue().mcgatewaySocialCountV160();
                            messages.add("   Friends: " + child.display() + "/" + Constants.MAX_FRIENDS);
                        }
                    } else {
                        messages.add("No sub-sessions");
                    }

                    for (String message : messages) coreLogger.info(message);
                    coreLogger.info("MCGATEWAY_ACCOUNTS_LIST_V160 result="
                        + (primary.observed() ? "provisional" : "unavailable")
                        + " reason=" + primary.reason());
                } catch (RuntimeException ignored) {
                    coreLogger.warn("MCGATEWAY_ACCOUNTS_LIST_V160 result=unavailable reason=worker-exception");
                }
            });
        } catch (java.util.concurrent.RejectedExecutionException ignored) {
            coreLogger.warn("MCGATEWAY_ACCOUNTS_LIST_V160 result=unavailable reason=executor-rejected");
        }
    }'''

CORE_ANCHOR = '    /**\n     * Get the social summary for the current user\n     * @return The current social summary\n     */\n    public SocialSummaryResponse socialSummary() {'
CORE_INSERT = '''    // MCGATEWAY_ACCOUNTS_LIST_PRODUCER_V160: read only the summary that
    // accounts list already requested, but validate its status and field.
    // Nothing from this request is authoritative for admission or cleanup.
    public McgatewaySocialCountV160.Observation mcgatewaySocialCountV160() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(Constants.SOCIAL_SUMMARY)
                .timeout(Duration.ofSeconds(8))
                .header("Authorization", getTokenHeader())
                .header("x-xbl-contract-version", "3")
                .GET()
                .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            return McgatewaySocialCountV160.parse(response.statusCode(), response.body());
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
            return McgatewaySocialCountV160.unavailable("interrupted");
        } catch (Exception ignored) {
            return McgatewaySocialCountV160.unavailable("request-failed");
        }
    }

'''


def read_target(path, required):
    if path.is_symlink() or (required and not path.is_file()) or (path.exists() and not path.is_file()):
        raise ValueError("missing or unsafe source: " + path.name)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def git_blob_sha1(text):
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def patch(root: Path, helper_file: Path) -> bool:
    root = root.resolve()
    if not root.is_dir() or helper_file.is_symlink() or not helper_file.is_file():
        raise ValueError("unsafe or missing upstream/helper")
    s, c, h = (root / x for x in (SESSION, CORE, HELPER_TARGET))
    session = read_target(s, True)
    core = read_target(c, True)
    old_helper = read_target(h, False)
    console = read_target(root / CONSOLE, True)
    helper = helper_file.read_text(encoding="utf-8")
    if HELPER_ID not in helper or helper.count(HELPER_ID) != 1:
        raise ValueError("unexpected reviewed helper identity")
    if "MCGATEWAY_RELEASE160_EXPIRY_HOLD" not in session or "friends remove is DENIED" not in console:
        raise ValueError("Release160 original expiry/removal hold not proven")
    if "MCGATEWAY_XBOX_PRESENCE_POST_ACCEPTED" in core or "friendcountv2" in console:
        raise ValueError("not original production-baseline overlay")

    if session.count(LIST_OLD) == 1 and LIST_NEW not in session:
        new_session = session.replace(LIST_OLD, LIST_NEW, 1)
    elif session.count(LIST_NEW) == 1 and LIST_OLD not in session:
        new_session = session
    else:
        raise ValueError("unreviewed SessionManager listSessions() source")

    if core.count(CORE_ANCHOR) != 1:
        raise ValueError("unexpected SessionManagerCore source")
    if CORE_INSERT in core and core.count(CORE_INSERT) == 1:
        new_core = core
        original_core = core.replace(CORE_INSERT, "", 1)
    elif "MCGATEWAY_ACCOUNTS_LIST_PRODUCER_V160" not in core:
        new_core = core.replace(CORE_ANCHOR, CORE_INSERT + CORE_ANCHOR, 1)
        original_core = core
    else:
        raise ValueError("tampered SessionManagerCore producer hook")
    # The original baseline overlay changes SessionManagerCore.mcgatewayHealthLine
    # only; it must still have the documented exact health marker.
    if "MCGATEWAY_HEALTH_V160 initialized=" not in original_core:
        raise ValueError("original health guard missing")
    # Reconstruct both exact pinned upstream source blobs by reverting only
    # the original production overlay and our own known additive blocks.
    session_before_us = new_session.replace(LIST_NEW, LIST_OLD, 1)
    if session_before_us.count(EXPIRY_OVERLAY) != 1:
        raise ValueError("unexpected baseline expiry patch")
    raw_session = session_before_us.replace(EXPIRY_OVERLAY, EXPIRY_UPSTREAM, 1)
    if git_blob_sha1(raw_session) != PINNED_SESSION_BLOB:
        raise ValueError("upstream SessionManager Git blob mismatch")

    if original_core.count(HEALTH_OVERLAY) != 1:
        raise ValueError("unexpected baseline health patch")
    raw_core = original_core.replace(HEALTH_OVERLAY, HEALTH_UPSTREAM, 1)
    if git_blob_sha1(raw_core) != PINNED_CORE_BLOB:
        raise ValueError("upstream SessionManagerCore Git blob mismatch")
    if old_helper not in ("", helper):
        raise ValueError("different helper already exists")

    changes = [(s, session, new_session), (c, core, new_core), (h, old_helper, helper)]
    changed = any(old != new for _, old, new in changes)
    for target, old, new in changes:
        if old != new:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new, encoding="utf-8")
    return changed


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("upstream_root")
    p.add_argument("helper_file")
    args = p.parse_args()
    result = patch(Path(args.upstream_root), Path(args.helper_file))
    print("CHANGED" if result else "UNCHANGED")
