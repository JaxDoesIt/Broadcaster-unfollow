package com.rtm516.mcxboxbroadcast.core;

import java.net.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PlayerCountProof {
    static void check(boolean ok, String why) { if (!ok) throw new AssertionError(why); }
    static byte[] pong(long nonce, String message) {
        byte[] text=message.getBytes(StandardCharsets.UTF_8);ByteBuffer b=ByteBuffer.allocate(35+text.length);
        b.put((byte)0x1c).putLong(nonce).putLong(42).put(PlayerCountCache.MAGIC).putShort((short)text.length).put(text);return b.array();
    }
    public static void main(String[] args) throws Exception {
        AtomicLong time=new AtomicLong(1);AtomicInteger mode=new AtomicInteger();
        try(PlayerCountCache cache=new PlayerCountCache(()->{if(mode.get()==1)throw new SocketTimeoutException();if(mode.get()==2)throw new IllegalStateException();return new PlayerCountCache.Counts(12,100);},time::get,new PlayerCountCache.Counts(0,100))) {
            check(cache.current().players()==0,"startup fallback");cache.poll();check(cache.current().players()==12,"live count");
            SessionInfo s=new SessionInfo("Custom host","Custom world",0,100,"98.142.4.197",19132);
            cache.apply(s);check(s.getPlayers()==12,"published count");check(s.getHostName().equals("Custom host")&&s.getWorldName().equals("Custom world")&&s.getIp().equals("98.142.4.197")&&s.getPort()==19132,"names/destination changed");
            mode.set(1);time.addAndGet(TimeUnit.SECONDS.toNanos(30));cache.poll();check(cache.current().players()==12,"transient timeout lost cache");
            mode.set(2);cache.poll();time.addAndGet(PlayerCountCache.TTL);cache.apply(s);check(cache.current().players()==0,"stale sample retained");check(s.getPlayers()==1,"zero joinability guard changed");
            mode.set(0);cache.poll();check(cache.current().players()==12,"failed to recover");
            s.setPlayers(100);s.setMaxPlayers(100);check(s.getMaxPlayers()==101,"full-server guard changed");
        }
        for(String fields:new String[]{"MCPE;x;1;v;-1;100;","MCPE;x;1;v;101;100;","MCPE;x;1;v;2;0;","MCPE;x;1;v;NaN;100;","x;x;1;v;2;100;"}) {
            byte[] b=pong(9,fields);boolean rejected=false;try{PlayerCountCache.parse(b,b.length,9);}catch(IllegalArgumentException e){rejected=true;}check(rejected,"accepted invalid packet");
        }
        byte[] good=pong(9,"MCPE;x;1;v;12;100;");check(PlayerCountCache.parse(good,good.length,9).players()==12,"valid packet");
        boolean nonceDenied=false;try{PlayerCountCache.parse(good,good.length,10);}catch(IllegalArgumentException e){nonceDenied=true;}check(nonceDenied,"foreign reply accepted");
        CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
        try(PlayerCountCache cache=new PlayerCountCache(()->{entered.countDown();release.await();return new PlayerCountCache.Counts(9,100);},System::nanoTime,new PlayerCountCache.Counts(0,100))) {
            cache.start();check(entered.await(2,TimeUnit.SECONDS),"worker did not start");long started=System.nanoTime();
            for(int i=0;i<10000;i++)cache.apply(new SessionInfo());
            check(System.nanoTime()-started<TimeUnit.SECONDS.toNanos(1),"session reads blocked on query");release.countDown();
        }
        // Real loopback datagrams: valid response followed by an unreachable/timeout query.
        try(DatagramSocket server=new DatagramSocket(0,InetAddress.getLoopbackAddress())) {
            Thread responder=new Thread(()->{try{byte[] b=new byte[100];DatagramPacket p=new DatagramPacket(b,b.length);server.receive(p);byte[] reply=pong(ByteBuffer.wrap(b,1,8).getLong(),"MCPE;fixture;1;v;7;40;");server.send(new DatagramPacket(reply,reply.length,p.getSocketAddress()));}catch(Exception e){throw new RuntimeException(e);}});
            responder.start();check(PlayerCountCache.udp("127.0.0.1",server.getLocalPort(),500).players()==7,"UDP integration");responder.join(1000);
            long started=System.nanoTime();try{PlayerCountCache.udp("127.0.0.1",server.getLocalPort(),100);throw new AssertionError("missing timeout");}catch(SocketTimeoutException expected){}
            check(System.nanoTime()-started<TimeUnit.SECONDS.toNanos(1),"unbounded network timeout");
        }
        java.nio.file.Path shared=java.nio.file.Files.createTempFile("counts-shared", ".json");
        try {
            java.nio.file.Files.writeString(shared,"{\"version\":1,\"host\":\"98.142.4.197\",\"port\":19132,\"players\":7,\"maximum\":100,\"observedAt\":1000000}");
            check(PlayerCountCache.readShared(shared,"98.142.4.197",19132,1000001).players()==7,"shared source");
            for(long now:new long[]{999999,1030001}){boolean rejected=false;try{PlayerCountCache.readShared(shared,"98.142.4.197",19132,now);}catch(IllegalArgumentException e){rejected=true;}check(rejected,"future/stale source accepted");}
            boolean foreign=false;try{PlayerCountCache.readShared(shared,"8.8.8.8",19132,1000001);}catch(IllegalArgumentException e){foreign=true;}check(foreign,"foreign destination accepted");
            java.nio.file.Files.writeString(shared,"{}");boolean invalid=false;try{PlayerCountCache.readShared(shared,"98.142.4.197",19132,1000001);}catch(IllegalArgumentException e){invalid=true;}check(invalid,"incomplete source accepted");
        } finally {java.nio.file.Files.deleteIfExists(shared);}
        System.out.println("PlayerCountProof PASS: background isolation, timeout/runtime failure, TTL/fallback/recovery, packet validation, UDP, preserved names/destination and native joinability guards");
    }
}
