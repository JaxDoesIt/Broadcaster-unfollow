package com.rtm516.mcxboxbroadcast.core;

import com.rtm516.mcxboxbroadcast.core.configs.*;
import java.lang.reflect.*;
import java.nio.file.*;

/** Exercise the actual shaded StandaloneMain update path without authentication or sockets. */
public final class PlayerCountStandaloneProof {
    public static void main(String[] args) throws Exception {
        Path configFile=Files.createTempFile("counts-config", ".yml");
        try {
            Files.writeString(configFile,"config-version: 7\nsession:\n  query-server: true\n  query-player-counts: true\n  session-info:\n    host-name: Custom host\n    world-name: Custom world\n    players: 0\n    max-players: 100\n");
            CoreConfig config=ConfigLoader.loadConfig(configFile.toFile(),"Standalone");
            if(!config.session().queryPlayerCounts())throw new AssertionError("counts configuration not mapped");
            Class<?> main=Class.forName("com.rtm516.mcxboxbroadcast.bootstrap.standalone.StandaloneMain");
            Field field=main.getDeclaredField("config");field.setAccessible(true);field.set(null,config);
            SessionInfo info=new SessionInfo("Custom host","Custom world",0,100,"98.142.4.197",19132);
            Method update=main.getDeclaredMethod("updateSessionInfo",SessionInfo.class);update.setAccessible(true);
            // No session manager is initialized. Native query/name fallback would fail or open a socket.
            long started=System.nanoTime();update.invoke(null,info);
            if(System.nanoTime()-started>1_000_000_000L)throw new AssertionError("startup path waited for query");
            try(PlayerCountCache cache=new PlayerCountCache(()->new PlayerCountCache.Counts(12,100),System::nanoTime,new PlayerCountCache.Counts(0,100))) {
                cache.poll();Field counts=main.getDeclaredField("playerCounts");counts.setAccessible(true);counts.set(null,cache);update.invoke(null,info);
                if(info.getPlayers()!=12||info.getMaxPlayers()!=100||!info.getHostName().equals("Custom host")||!info.getWorldName().equals("Custom world")||!info.getIp().equals("98.142.4.197")||info.getPort()!=19132)throw new AssertionError("counts path modified unrelated session information");
            }
            System.out.println("PlayerCountStandaloneProof PASS: actual shaded startup/update path, counts override native query, preserved names and destination, no authentication");
        } finally {Files.deleteIfExists(configFile);}
    }
}
