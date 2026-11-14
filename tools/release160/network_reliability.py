"""Exact generated-core transforms; never edits auth, identities or caches."""
PRESENCE = r'''    protected void updatePresence() {
        synchronized (mcgatewayPresenceLock) {
        if (mcgatewayPresenceClosed) return;
        int status = 0;
        int delay = 300;
        String category = "transport";
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(Constants.USER_PRESENCE.formatted(getXuid())))
                .timeout(Duration.ofSeconds(20))
                .header("Content-Type", "application/json")
                .header("Authorization", getTokenHeader())
                .header("x-xbl-contract-version", "3")
                .POST(HttpRequest.BodyPublishers.ofString("{\"state\": \"active\"}"))
                .build();
            HttpResponse<Void> response = mcgatewaySendPresence(request);
            status = response.statusCode();
            if (status == 200) {
                mcgatewayPresenceFailures = 0;
                delay = mcgatewayHeartbeatSeconds(response.headers().firstValue("X-Heartbeat-After").orElse("300"));
                logger.info("MCGATEWAY_XBOX_PRESENCE_POST_ACCEPTED status=200");
                logger.debug("Presence update successful, scheduling presence update in " + delay + " seconds");
            } else {
                category = status == 429 ? "rate-limit" : status == 401 || status == 403 ? "authorization" : "http";
                mcgatewayPresenceFailures = Math.min(32, mcgatewayPresenceFailures + 1);
                int after = mcgatewayRetryAfterSeconds(response.headers().firstValue("Retry-After").orElse(""), java.time.Instant.now());
                delay = mcgatewayPresenceRetrySeconds(mcgatewayPresenceFailures, status, after,
                    java.util.concurrent.ThreadLocalRandom.current().nextInt(6));
                logger.error("Failed to update presence, got status " + status);
            }
        } catch (IOException error) {
            category = mcgatewayPresenceErrorCategory(error);
            mcgatewayPresenceFailures = Math.min(32, mcgatewayPresenceFailures + 1);
            delay = mcgatewayPresenceRetrySeconds(mcgatewayPresenceFailures, 0, 0,
                java.util.concurrent.ThreadLocalRandom.current().nextInt(6));
            logger.error("Failed to update presence");
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            logger.warn("MCGATEWAY_XBOX_PRESENCE_POST_FAILED category=interrupted status=0 retrySeconds=0");
            return;
        }
        if (status != 200) logger.warn("MCGATEWAY_XBOX_PRESENCE_POST_FAILED category=" + category
            + " status=" + status + " failures=" + mcgatewayPresenceFailures + " retrySeconds=" + delay);
        if (!mcgatewayPresenceClosed) {
            if (mcgatewayPresenceFuture != null) mcgatewayPresenceFuture.cancel(false);
            mcgatewayPresenceFuture = scheduledThread().schedule(this::updatePresence, delay, TimeUnit.SECONDS);
        }
        }
    }

    /** Separate, bounded client: friend-summary load cannot consume its request budget. */
    protected HttpResponse<Void> mcgatewaySendPresence(HttpRequest request) throws IOException, InterruptedException {
        return mcgatewayPresenceClient.send(request, HttpResponse.BodyHandlers.discarding());
    }

    static int mcgatewayHeartbeatSeconds(String value) {
        try { return Math.max(30, Math.min(3600, Integer.parseInt(value))); }
        catch (NumberFormatException error) { return 300; }
    }

    static int mcgatewayPresenceRetrySeconds(int failures, int status, int retryAfter, int jitter) {
        int base = Math.min(300, 5 * (1 << Math.min(6, Math.max(0, failures - 1))));
        if (status == 401 || status == 403) base = 300;
        return Math.max(Math.max(0, Math.min(86400, retryAfter)), base + Math.max(0, Math.min(5, jitter)));
    }

    static int mcgatewayRetryAfterSeconds(String value, java.time.Instant now) {
        try { return (int) Math.max(0L, Math.min(86400L, Long.parseLong(value.trim()))); }
        catch (NumberFormatException ignored) {
            try {
                java.time.Duration remaining = java.time.Duration.between(now, java.time.ZonedDateTime.parse(value.trim(),
                    java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME).toInstant());
                long seconds = remaining.getSeconds() + (remaining.getNano() > 0 ? 1 : 0);
                return (int) Math.max(0L, Math.min(86400L, seconds));
            } catch (java.time.DateTimeException error) { return 0; }
        }
    }

    static String mcgatewayPresenceErrorCategory(Throwable error) {
        for (int depth=0; error != null && depth<8; depth++, error=error.getCause()) {
            if (error instanceof java.net.http.HttpConnectTimeoutException) return "connect-timeout";
            if (error instanceof java.net.UnknownHostException) return "dns";
            if (error instanceof javax.net.ssl.SSLException) return "tls";
            if (error instanceof java.net.http.HttpTimeoutException) return "request-timeout";
            if (error instanceof java.net.ConnectException) return "connect";
        }
        return "transport";
    }'''

FIELDS = '''    // MCGATEWAY_NETWORK_RELIABILITY_V1: pending means the whole rebuild must retry.
    private volatile boolean mcgatewayRebuildPending = false;
    private volatile boolean mcgatewayRebuildInProgress = false;
    private volatile boolean mcgatewayPresenceClosed = false;
    private final Object mcgatewayPresenceLock = new Object();
    private int mcgatewayPresenceFailures = 0;
    private java.util.concurrent.ScheduledFuture<?> mcgatewayPresenceFuture;
    private final HttpClient mcgatewayPresenceClient = HttpClient.newBuilder()
        .version(HttpClient.Version.HTTP_1_1).followRedirects(HttpClient.Redirect.NEVER)
        .connectTimeout(Duration.ofSeconds(10)).build();
'''

# These constants are filled from the exact pinned original, not from another
# locally checked-out upstream version. The outer overlay verifies the full hash.

OLD_CREATE = r'''    private void createSession() throws SessionCreationException, SessionUpdateException {
        // We only need a websocket for the primary session manager
        if (this.sessionInfo != null) {
            // Update the current session XUID
            this.sessionInfo.setXuid(getXuid());

            // Create the RTA websocket connection
            setupRtaWebsocket();

            try {
                // Wait and get the connection ID from the websocket
                String connectionId = waitForConnectionId();

                // Update the current session connection ID
                this.sessionInfo.setConnectionId(connectionId);
            } catch (InterruptedException | ExecutionException | TimeoutException e) {
                throw new SessionCreationException("Unable to get connectionId for session: " + e.getMessage());
            }

            setupNetherNet();

            if (this.signaling == null || !this.signaling.isActive()) {
                throw new SessionCreationException("Unable to start NetherNet signaling");
            }
        }

        // Set the showcase image to the current screenshot
        File imageFile = storageManager.screenshot();
        if (imageFile.exists()) {
            logger.info("Setting showcase image");
            if (galleryManager.setShowcase(imageFile)) {
                logger.info("Successfully set showcase image");
            }
        }

        publishSession();
    }'''

NEW_CREATE = r'''    private void createSession() throws SessionCreationException, SessionUpdateException {
        synchronized (this) {
            if (mcgatewayRebuildInProgress) throw new SessionCreationException("Session reconstruction is already running");
            mcgatewayRebuildPending = true;
            mcgatewayRebuildInProgress = true;
        }
        try {
        // We only need a websocket for the primary session manager
        if (this.sessionInfo != null) {
            // Update the current session XUID
            this.sessionInfo.setXuid(getXuid());

            // Create the RTA websocket connection
            setupRtaWebsocket();

            try {
                // Wait and get the connection ID from the websocket
                String connectionId = waitForConnectionId();

                // Update the current session connection ID
                this.sessionInfo.setConnectionId(connectionId);
            } catch (InterruptedException | ExecutionException | TimeoutException e) {
                throw new SessionCreationException("Unable to get connectionId for session: " + e.getMessage());
            }

            setupNetherNet();

            if (this.signaling == null || !this.signaling.isActive()) {
                throw new SessionCreationException("Unable to start NetherNet signaling");
            }
        }

        // Set the showcase image to the current screenshot
        File imageFile = storageManager.screenshot();
        if (imageFile.exists()) {
            logger.info("Setting showcase image");
            if (galleryManager.setShowcase(imageFile)) {
                logger.info("Successfully set showcase image");
            }
        }

        publishSession();
                mcgatewayRebuildPending = false;
        } finally {
            mcgatewayRebuildInProgress = false;
        }
    }'''

OLD_CHECK = r'''    protected void checkConnection() {
        boolean rtaIsOpen = this.rtaWebsocket != null && this.rtaWebsocket.isOpen();
        boolean signalingIsOpen = this.signaling != null && this.signaling.isActive();

        // Check if the connection is Lost
        if (!rtaIsOpen || !signalingIsOpen) {
            try {
                logger.warn("Connection to websocket lost, re-creating session...");
                logger.debug("WebSocket status: RTA Open: " + rtaIsOpen + ", Signaling: " + signalingIsOpen);

                createSession();
                logger.info("WebSocket session reconnected");
            } catch (SessionCreationException | SessionUpdateException e) {
                logger.error("Session is dead and hit exception trying to re-create it", e);
            }
        }
    }'''

NEW_CHECK = r'''    protected void checkConnection() {
        if (mcgatewayRebuildInProgress) return;
        boolean rtaIsOpen = this.rtaWebsocket != null && this.rtaWebsocket.isOpen();
        boolean signalingIsOpen = this.signaling != null && this.signaling.isActive();

        // Check if the connection is Lost
        if (mcgatewayRebuildPending || !mcgatewaySessionTransportReady()) {
            try {
                logger.warn("Connection to websocket lost, re-creating session...");
                logger.debug("WebSocket status: RTA Open: " + rtaIsOpen + ", Signaling: " + signalingIsOpen);

                createSession();
                logger.info("WebSocket session reconnected");
            } catch (SessionCreationException | SessionUpdateException e) {
                logger.error("Session is dead and hit exception trying to re-create it", e);
            }
        }
    }

    protected boolean mcgatewaySessionTransportReady() {
        return rtaWebsocket != null && rtaWebsocket.isOpen() && signaling != null && signaling.isActive();
    }'''

OLD_PRESENCE = r'''    protected void updatePresence() {
        HttpRequest updatePresenceRequest = HttpRequest.newBuilder()
            .uri(URI.create(Constants.USER_PRESENCE.formatted(getXuid())))
            .header("Content-Type", "application/json")
            .header("Authorization", getTokenHeader())
            .header("x-xbl-contract-version", "3")
            .POST(HttpRequest.BodyPublishers.ofString("{\"state\": \"active\"}"))
            .build();

        int heartbeatAfter = 300;
        try {
            HttpResponse<Void> updatePresenceResponse = httpClient.send(updatePresenceRequest, HttpResponse.BodyHandlers.discarding());

            if (updatePresenceResponse.statusCode() != 200) {
                logger.error("Failed to update presence, got status " + updatePresenceResponse.statusCode());
            } else {
                // Read X-Heartbeat-After header to get the next time we should update presence
                try {
                    heartbeatAfter = Integer.parseInt(updatePresenceResponse.headers().firstValue("X-Heartbeat-After").orElse("300"));
                } catch (NumberFormatException e) {
                    logger.debug("Failed to parse heartbeat after header, using default of 300");
                }
            }
        } catch (IOException | InterruptedException e) {
            logger.error("Failed to update presence", e);
        }

        // Schedule the next presence update
        logger.debug("Presence update successful, scheduling presence update in " + heartbeatAfter + " seconds");
        scheduledThread().schedule(this::updatePresence, heartbeatAfter, TimeUnit.SECONDS);
    }'''

TRANSFORMS = [
    ('    protected boolean initialized = false;', '    protected boolean initialized = false;\n' + FIELDS),
    (OLD_CREATE, NEW_CREATE), (OLD_CHECK, NEW_CHECK), (OLD_PRESENCE, PRESENCE),
    ('    public void shutdown() {', '    public void shutdown() {\n        mcgatewayPresenceClosed = true;\n        if (mcgatewayPresenceFuture != null) mcgatewayPresenceFuture.cancel(false);'),
    ('boolean published = sessionInfo != null && sessionInfo.getHandleId() != null', 'boolean published = !mcgatewayRebuildPending && sessionInfo != null && sessionInfo.getHandleId() != null'),
    ('if (handle == null || handle.isBlank()) throw new IllegalStateException("session handle unavailable");', 'if (mcgatewayRebuildPending || handle == null || handle.isBlank()) throw new IllegalStateException("session handle unavailable");')
]

def patch_core(text):
    for before, after in TRANSFORMS:
        if text.count(before) != 1: raise ValueError('ambiguous network-reliability source anchor')
        text = text.replace(before, after, 1)
    return text

def unpatch_core(text):
    if 'MCGATEWAY_NETWORK_RELIABILITY_V1' not in text: return text
    for before, after in reversed(TRANSFORMS):
        if text.count(after) != 1: raise ValueError('invalid network-reliability patched bytes')
        text = text.replace(after, before, 1)
    return text
