package com.rtm516.mcxboxbroadcast.core;

import java.net.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.*;
import java.util.function.LongSupplier;

/** Optional display-only cache. No Xbox, friendship, identity or session lifecycle calls. */
public final class PlayerCountCache implements AutoCloseable {
    static final byte[] MAGIC = java.util.HexFormat.of().parseHex("00ffff00fefefefefdfdfdfd12345678");
    public record Counts(int players, int maximum) {
        public Counts {
            if (players < 0 || maximum < 1 || maximum > 1_000_000 || players > maximum)
                throw new IllegalArgumentException("Invalid player counts");
        }
    }
    record Sample(Counts counts, long at) {}
    @FunctionalInterface public interface Query { Counts read() throws Exception; }
    private final Query query;
    private final LongSupplier clock;
    private final Counts fallback;
    private final ScheduledExecutorService worker;
    private volatile Sample last;
    private volatile boolean closed;
    private final java.util.concurrent.atomic.AtomicBoolean started = new java.util.concurrent.atomic.AtomicBoolean();
    static final long TTL = TimeUnit.SECONDS.toNanos(90);

    public PlayerCountCache(String host, int port, int fallbackPlayers, int fallbackMaximum) {
        this(() -> udp(host, port, 1500), System::nanoTime,
            new Counts(fallbackPlayers, fallbackMaximum));
    }
    PlayerCountCache(Query query, LongSupplier clock, Counts fallback) {
        this.query = query; this.clock = clock; this.fallback = fallback;
        worker = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "mcgateway-player-counts"); t.setDaemon(true); return t;
        });
    }
    /** Shared, data-only snapshot: mount its directory read-only, never the bot database. */
    public static PlayerCountCache shared(java.nio.file.Path file, String host, int port, int players, int maximum) {
        return new PlayerCountCache(() -> readShared(file, host, port, System.currentTimeMillis()), System::nanoTime, new Counts(players, maximum));
    }
    record Shared(int version, String host, int port, int players, int maximum, long observedAt) {}
    static Counts readShared(java.nio.file.Path file, String host, int port, long now) throws Exception {
        if (!java.nio.file.Files.isRegularFile(file, java.nio.file.LinkOption.NOFOLLOW_LINKS)) throw new IllegalArgumentException("Invalid snapshot file");
        byte[] data;
        try (var in = java.nio.file.Files.newInputStream(file)) { data = in.readNBytes(4097); }
        if (data.length > 4096) throw new IllegalArgumentException("Oversized snapshot");
        Shared s = new com.google.gson.Gson().fromJson(new String(data, StandardCharsets.UTF_8), Shared.class);
        if (s == null || s.version != 1 || !host.equals(s.host) || port != s.port || s.observedAt <= 0
                || now < s.observedAt || now - s.observedAt > 30_000) throw new IllegalArgumentException("Stale or foreign snapshot");
        return new Counts(s.players, s.maximum);
    }
    public void start() { if (!closed && started.compareAndSet(false, true)) worker.scheduleWithFixedDelay(this::poll, 0, 30, TimeUnit.SECONDS); }
    void poll() {
        if (closed) return;
        try { Counts counts = query.read(); if (counts != null && !closed) last = new Sample(counts, clock.getAsLong()); }
        catch (Exception ignored) { /* Keep last valid sample until TTL; no session failure or restart. */ }
    }
    public Counts current() {
        Sample s = last;
        return s != null && clock.getAsLong() - s.at >= 0 && clock.getAsLong() - s.at < TTL ? s.counts : fallback;
    }
    public void apply(SessionInfo target) {
        Counts c = current(); target.setPlayers(c.players); target.setMaxPlayers(c.maximum);
    }
    public String status() {
        Sample s = last; long age = s == null ? -1 : Math.max(0, TimeUnit.NANOSECONDS.toSeconds(clock.getAsLong() - s.at));
        Counts c = current();
        return "MCGATEWAY_PLAYER_COUNTS_V1 source=" + (s != null && current() == s.counts ? "query" : "fallback")
            + " ageSeconds=" + age + " players=" + c.players + " maximum=" + c.maximum;
    }
    public void close() { closed = true; worker.shutdownNow(); }

    public static Counts udp(String host, int port, int timeoutMs) throws Exception {
        InetSocketAddress target = new InetSocketAddress(host, port);
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.connect(target); socket.setSoTimeout(timeoutMs);
            long nonce = ThreadLocalRandom.current().nextLong();
            ByteBuffer ping = ByteBuffer.allocate(33).order(ByteOrder.BIG_ENDIAN);
            ping.put((byte)1).putLong(nonce).put(MAGIC).putLong(1);
            socket.send(new DatagramPacket(ping.array(), 33));
            long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(timeoutMs);
            while (System.nanoTime() < deadline) {
                socket.setSoTimeout((int)Math.max(1, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())));
                byte[] bytes = new byte[4096]; DatagramPacket packet = new DatagramPacket(bytes, bytes.length);
                socket.receive(packet);
                try { return parse(bytes, packet.getLength(), nonce); }
                catch (IllegalArgumentException ignored) { /* Ignore unrelated/malformed replies within the same deadline. */ }
            }
            throw new SocketTimeoutException();
        }
    }
    static Counts parse(byte[] b, int length, long nonce) {
        if (length < 35 || length > b.length || length >= 4096 || b[0] != 0x1c || ByteBuffer.wrap(b,1,8).getLong() != nonce
                || !Arrays.equals(Arrays.copyOfRange(b,17,33), MAGIC)) throw new IllegalArgumentException("Invalid pong");
        int n = Short.toUnsignedInt(ByteBuffer.wrap(b,33,2).getShort());
        if (n != length - 35) throw new IllegalArgumentException("Invalid pong length");
        String[] fields = new String(b,35,n,StandardCharsets.UTF_8).split(";", -1);
        if (fields.length < 6 || !fields[0].equals("MCPE") || !fields[4].matches("0|[1-9][0-9]{0,6}")
                || !fields[5].matches("[1-9][0-9]{0,6}")) throw new IllegalArgumentException("Invalid pong fields");
        return new Counts(Integer.parseInt(fields[4]), Integer.parseInt(fields[5]));
    }
}
