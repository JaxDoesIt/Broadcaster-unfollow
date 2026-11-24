#!/usr/bin/env python3
"""Counts-only optional patch after the exact Release160 reliability overlay."""
import hashlib, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent
BASE = 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/'
MAIN = 'bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneMain.java'

def apply(root):
    config = root / (BASE + 'configs/CoreConfig.java')
    main = root / MAIN
    original_config = config.read_text()
    original_main = main.read_text()
    c_anchor = '        boolean queryServer();'
    c_new = c_anchor + '''

        @Comment("Display-only counts; queries never block startup or session updates. Overrides query-server.")
        @ExcludePlatform(platforms = {"Extension"})
        @DefaultBoolean(false)
        boolean queryPlayerCounts();

        @Comment("Optional read-only shared count snapshot for this exact destination. Blank uses direct UDP.")
        @ExcludePlatform(platforms = {"Extension"})
        @DefaultString("")
        String playerCountFile();'''
    m_anchor = '    public static SessionManager sessionManager;'
    m_new = m_anchor + '\n    private static com.rtm516.mcxboxbroadcast.core.PlayerCountCache playerCounts;'
    start_anchor = '        // Sync the session info from the server if needed'
    start_new = '''        if (config.session().queryPlayerCounts()) {
            try {
                String source = config.session().playerCountFile();
                playerCounts = source.isBlank()
                    ? new com.rtm516.mcxboxbroadcast.core.PlayerCountCache(sessionInfo.getIp(), sessionInfo.getPort(), config.session().sessionInfo().players(), config.session().sessionInfo().maxPlayers())
                    : com.rtm516.mcxboxbroadcast.core.PlayerCountCache.shared(java.nio.file.Path.of(source), sessionInfo.getIp(), sessionInfo.getPort(), config.session().sessionInfo().players(), config.session().sessionInfo().maxPlayers());
                playerCounts.start();
                Runtime.getRuntime().addShutdownHook(new Thread(() -> playerCounts.close()));
            } catch (RuntimeException error) {
                // Optional display feature must not prevent the bot starting.
                logger.warn("MCGATEWAY_PLAYER_COUNTS_V1 source=fallback reason=initialization");
            }
        }

''' + start_anchor
    update_anchor = '    private static void updateSessionInfo(SessionInfo sessionInfo) {'
    update_new = update_anchor + '''
        if (config.session().queryPlayerCounts()) {
            if (playerCounts != null) playerCounts.apply(sessionInfo);
            return; // Never call the name/game-mode/native-query path in counts-only mode.
        }'''
    transforms = [(config, original_config, [(c_anchor,c_new)], 'aad3229e57d88caa5bbd3e142822d28e54af7b9eed8e271f8734eb6706a9bc64'),
                  (main, original_main, [(m_anchor,m_new),(start_anchor,start_new),(update_anchor,update_new)], '3603835cf740f46d67ca7991ba048560037f683f5f5d8b43a5d00d646c9920c5')]
    prepared=[]
    for file,current,edits,expected_hash in transforms:
        if file.is_symlink(): raise ValueError('Unsafe source')
        original=current
        for old,new in reversed(edits):
            if new in original: original=original.replace(new,old,1)
        if hashlib.sha256(original.encode()).hexdigest()!=expected_hash:raise ValueError('Unexpected upstream source: '+str(file))
        result=original
        for old,new in edits:
            if result.count(old)!=1:raise ValueError('Ambiguous source anchor')
            result=result.replace(old,new,1)
        if current not in (original,result):raise ValueError('Partial counts patch')
        prepared.append((file,result))
    target=root/(BASE+'PlayerCountCache.java')
    content=(ROOT/'PlayerCountCache.java').read_text()
    if target.exists() and (target.is_symlink() or target.read_text()!=content):raise ValueError('Unexpected count helper')
    for file,result in prepared:file.write_text(result)
    target.write_text(content)

if __name__=='__main__':
    apply(pathlib.Path(sys.argv[1]));print('Counts-only overlay PASS: pinned source, optional/off by default')
