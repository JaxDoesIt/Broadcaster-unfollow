    // Exact-target recovery only. The root-owned descriptor and independent
    // recovery journal must be armed before invoking the rehearsal command.
    private boolean mcgatewayRecoveryRehearsalUsed = false;
    private String mcgatewayRecoveryEnv(String key) { return System.getenv(key); }
    private enum McgatewayRecoveryStage { binding, lock, identity, pre, delete, absence, put, post, complete }
    private void mcgatewayRecoveryBinding(String plan, String target, String account, long minimumRemainingMs) throws Exception {
        String prefix = "MCGATEWAY_RELEASE160_RECOVERY_";
        if (!"owner-reviewed-recovery-v1".equals(mcgatewayRecoveryEnv(prefix + "MODE"))
            || !mcgatewayV2Nonce(plan) || !plan.equals(mcgatewayRecoveryEnv(prefix + "PLAN_ID"))
            || !String.valueOf(mcgatewayRecoveryEnv(prefix + "PLAN_SHA256")).matches("[0-9a-f]{64}")
            || !mcgatewayV2Hash(target).equals(mcgatewayRecoveryEnv(prefix + "TARGET_SHA256"))
            || !mcgatewayV2Hash(account).equals(mcgatewayRecoveryEnv(prefix + "ACCOUNT_SHA256"))) throw new IllegalStateException("binding");
        long issued = Long.parseLong(mcgatewayRecoveryEnv(prefix + "ISSUED_MS"));
        long expires = Long.parseLong(mcgatewayRecoveryEnv(prefix + "EXPIRES_MS"));
        long now = System.currentTimeMillis();
        if (issued < 0 || expires <= issued || expires - issued > 900_000L || now < issued || now >= expires || expires - now < minimumRemainingMs) throw new IllegalStateException("expired");
    }
    private void mcgatewayRecoveryStable(String plan, String target, String account, String session) throws Exception {
        mcgatewayRecoveryBinding(plan, target, account, 0L);
        if (!account.equals(sessionManager.getXuid()) || !session.equals(sessionManager.mcgatewayV2SessionIdentity())
            || toAdd.containsKey(target) || toRemove.containsKey(target)) throw new IllegalStateException("identity-or-queue");
    }
    private void mcgatewayRecoveryMutation(String method, String plan, String target, String account, String session, long deadline) throws Exception {
        mcgatewayRecoveryStable(plan, target, account, session);
        URI uri = URI.create(Constants.FRIEND.formatted(target));
        HttpRequest request = HttpRequest.newBuilder().uri(uri)
            .timeout(java.time.Duration.ofMillis(Math.min(8_000L, mcgatewayV2Remaining(deadline))))
            .header("Authorization", sessionManager.getTokenHeader())
            .method(method, HttpRequest.BodyPublishers.noBody()).build();
        HttpResponse<byte[]> response = mcgatewayV2Send(request, deadline);
        if (!uri.equals(response.uri()) || (response.statusCode() != 200 && response.statusCode() != 204)) throw new IllegalStateException("mutation");
        mcgatewayRecoveryStable(plan, target, account, session);
    }
    public String mcgatewayFriendRecoveryV1(String nonce, String plan, String target, boolean rehearse) {
        String accountHash = "unavailable", sessionHash = "unavailable", planHash = "unavailable";
        String result = "uncertain", pre = "unknown", post = "unknown";
        boolean deleteAttempted = false, locked = false, verified = false;
        McgatewayRecoveryStage stage = McgatewayRecoveryStage.binding;
        try {
            if (!mcgatewayV2Nonce(nonce) || !mcgatewayV2Nonce(plan) || !mcgatewayV2Xuid(target) || !mcgatewayV2Consume(nonce)) throw new IllegalStateException("input");
            String rawAccount = sessionManager.getXuid(), rawSession = sessionManager.mcgatewayV2SessionIdentity();
            accountHash = mcgatewayV2Hash(rawAccount); sessionHash = mcgatewayV2Hash(rawSession);
            mcgatewayRecoveryBinding(plan, target, rawAccount, rehearse ? 300_000L : 60_000L);
            planHash = mcgatewayRecoveryEnv("MCGATEWAY_RELEASE160_RECOVERY_PLAN_SHA256");
            stage = McgatewayRecoveryStage.lock;
            locked = mcgatewayV2Lock.writeLock().tryLock();
            if (!locked) throw new IllegalStateException("busy");
            long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(rehearse ? 30 : 20);
            stage = McgatewayRecoveryStage.identity;
            mcgatewayRecoveryStable(plan, target, rawAccount, rawSession);
            stage = McgatewayRecoveryStage.pre;
            McgatewayV2State before = mcgatewayV2Read(target, rawAccount, rawSession, deadline,
                rehearse ? McgatewayV2ReadPhase.BEFORE_DELETE : McgatewayV2ReadPhase.BEFORE_RESTORE);
            pre = before.state().equals("friendship-absent") ? "unknown" : before.state();
            if (rehearse) {
                if (mcgatewayRecoveryRehearsalUsed) throw new IllegalStateException("rehearsal-already-attempted");
                if (!before.removable()) throw new IllegalStateException("pre-not-removable");
                mcgatewayRecoveryBinding(plan, target, rawAccount, 300_000L);
                mcgatewayRecoveryStable(plan, target, rawAccount, rawSession);
                logger.info("MCGATEWAY_FRIEND_RECOVERY_ARMED_V1 nonce=" + nonce + " plan=" + plan + " planHash=" + planHash
                    + " xuid=" + target + " account=" + accountHash + " session=" + sessionHash
                    + " action=rehearse pre=present isFriend=true friendRequestSent=false friendRequestReceived=false deleteNext=true verified=true stage=pre-delete");
                stage = McgatewayRecoveryStage.delete;
                // Conservative: this says dispatch was attempted, not that
                // a successful remote deletion has already been established.
                mcgatewayRecoveryRehearsalUsed = true;
                deleteAttempted = true;
                mcgatewayRecoveryMutation("DELETE", plan, target, rawAccount, rawSession, deadline);
                stage = McgatewayRecoveryStage.absence;
                McgatewayV2State absent;
                // Xbox may briefly continue serving the pre-remove flags after
                // the accepted DELETE. Poll the same exact target within the
                // existing recovery deadline; never reissue DELETE.
                do {
                    absent = mcgatewayV2Read(target, rawAccount, rawSession, deadline, McgatewayV2ReadPhase.AFTER_DELETE);
                    if (absent.state().equals("absent") || absent.state().equals("friendship-absent")) break;
                    if (mcgatewayV2Remaining(deadline) < 750L) throw new IllegalStateException("absence");
                    Thread.sleep(250L);
                } while (true);
                if (!absent.state().equals("absent") && !absent.state().equals("friendship-absent")) throw new IllegalStateException("absence");
                mcgatewayRecoveryStable(plan, target, rawAccount, rawSession);
                logger.info("MCGATEWAY_FRIEND_RECOVERY_SETTLED_V1 nonce=" + nonce + " plan=" + plan + " planHash=" + planHash
                    + " xuid=" + target + " account=" + accountHash + " session=" + sessionHash
                    + " action=rehearse deleteCompleted=true post=" + absent.state()
                    + " basis=" + (absent.state().equals("friendship-absent") ? "target-404-after-delete" : "explicit-flags")
                    + " verified=true stage=delete-settled");
            } else if (before.removable()) {
                mcgatewayRecoveryStable(plan, target, rawAccount, rawSession);
                result = "already-restored"; post = "present"; verified = true;
            } else if (before.state().equals("present")) {
                // A pending request needs acceptance, not repeated PUTs.
                throw new IllegalStateException("pending");
            }
            if (!verified) {
                stage = McgatewayRecoveryStage.put;
                mcgatewayRecoveryMutation("PUT", plan, target, rawAccount, rawSession, deadline);
                stage = McgatewayRecoveryStage.post;
                McgatewayV2State restored = mcgatewayV2Read(target, rawAccount, rawSession, deadline, McgatewayV2ReadPhase.OBSERVE);
                if (!restored.removable()) throw new IllegalStateException("not-restored");
                mcgatewayRecoveryStable(plan, target, rawAccount, rawSession);
                result = "restored"; post = "present"; verified = true;
            }
            stage = McgatewayRecoveryStage.complete;
        } catch (Exception error) {
            // Never leak auth/response bodies; a failure after DELETE remains
            // manual unless BOTH admission and settled-delete evidence were
            // authenticated by the independent root collector.
        } finally {
            if (locked) mcgatewayV2Lock.writeLock().unlock();
        }
        return "MCGATEWAY_FRIEND_RECOVERY_V160_V1 nonce=" + (mcgatewayV2Nonce(nonce) ? nonce : "invalid")
            + " plan=" + (mcgatewayV2Nonce(plan) ? plan : "invalid") + " planHash=" + planHash
            + " xuid=" + (mcgatewayV2Xuid(target) ? target : "invalid") + " account=" + accountHash + " session=" + sessionHash
            + " action=" + (rehearse ? "rehearse" : "restore") + " result=" + result + " pre=" + pre
            + " deleteAttempted=" + deleteAttempted + " post=" + post + " verified=" + verified + " stage=" + stage;
    }

