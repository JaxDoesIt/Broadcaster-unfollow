package com.rtm516.mcxboxbroadcast.core.configs;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Runs with actual Configurate/CoreConfig implementations; never opens a network connection. */
public final class ConfigCompatibilityProof {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory("mcgateway160-config-proof");
        try {
            String[] fixtures = {
                "config-version: 2\nsession:\n  session-info:\n    ip: relay.example.invalid\n    port: 19132\n",
                "config-version: 7\nsession:\n  remote-address: relay.example.invalid\n  remote-port: '19132'\n"
            };
            for (int i = 0; i < fixtures.length; i++) {
                Path file = directory.resolve("existing-" + i + ".yml");
                byte[] original = fixtures[i].getBytes(StandardCharsets.UTF_8);
                Files.write(file, original);
                for (int run = 0; run < 2; run++) {
                    CoreConfig config = ConfigLoader.loadConfig(file.toFile(), "Standalone");
                    check("relay.example.invalid".equals(config.session().remoteAddress()), "wrong effective relay host");
                    check("19132".equals(config.session().remotePort()), "wrong effective relay port");
                    check(Arrays.equals(original, Files.readAllBytes(file)), "existing config rewritten: rollback unsafe");
                }
            }
            Path newFile = directory.resolve("new.yml");
            ConfigLoader.loadConfig(newFile.toFile(), "Standalone");
            check(Files.size(newFile) > 0, "new config was not initialized");
            Path invalid = directory.resolve("invalid.yml");
            byte[] malformed = "config-version: [broken\n".getBytes(StandardCharsets.UTF_8);
            Files.write(invalid, malformed);
            boolean failed = false;
            try { ConfigLoader.loadConfig(invalid.toFile(), "Standalone"); }
            catch (Exception expected) { failed = true; }
            check(failed && Arrays.equals(malformed, Files.readAllBytes(invalid)), "malformed input was rewritten");
            System.out.println("MCGATEWAY_160_CONFIG_PROOF_PASS effective-target/existing-byte-preservation/repeated-load/new/invalid");
        } finally {
            try (var paths = Files.walk(directory)) {
                for (Path path : paths.sorted(java.util.Comparator.reverseOrder()).toList()) Files.deleteIfExists(path);
            }
        }
    }
}
