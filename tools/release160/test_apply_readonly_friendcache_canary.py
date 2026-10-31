"""Pure offline tests for the extra GET-only, mutation-blocked canary overlay."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from apply_readonly_friendcache_canary import patch, METHODS, FRIEND, PROBE_FROM, PROBE_TO, METHOD

FRIEND_ANCHOR = "    public void init(CoreConfig.FriendSyncConfig friendSyncConfig) {"

def prepare(root):
    main = root / FRIEND
    main.parent.mkdir(parents=True, exist_ok=True)
    signatures = list(METHODS)
    source = ("class FriendManager {\n"
              "    // MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT\n"
              "    private boolean mcgPersonSummaryProbeConsumed;\n"
              "    void diagnostic() {\n"
              "        // mcgPersonSummaryProbeConsumed.compareAndSet(false, true)\n"
              + PROBE_FROM + "\n    }\n"
              + "\n".join(s + "\n    }\n" for s in signatures)
              + "}\n")
    main.write_text(source)
    expiry = root / "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java"
    expiry.parent.mkdir(parents=True, exist_ok=True)
    expiry.write_text("// MCGATEWAY_RELEASE160_EXPIRY_HOLD\n")
    console = root / "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
    console.parent.mkdir(parents=True, exist_ok=True)
    console.write_text("// friends remove is DENIED\n")
    return main, expiry, console

class ReadOnlyCachePatchTests(unittest.TestCase):
    def test_all_mutation_entrypoints_blocked_and_get_populates_only_when_needed(self):
        with TemporaryDirectory() as tmp:
            target, _, _ = prepare(Path(tmp))
            self.assertTrue(patch(Path(tmp)))
            code = target.read_text()
            self.assertIn(PROBE_TO, code)
            self.assertIn("snapshot = get()", code)
            self.assertIn("mcgPersonSummaryReadonlyCandidate() { return true; }", code)
            self.assertIn(METHOD, code)
            for signature, guard in METHODS.items():
                self.assertEqual(1, code.count(signature), signature)
                self.assertIn(signature + "\n" + guard, code, signature)
            self.assertFalse(patch(Path(tmp)), "second application must be idempotent")

    def test_deny_missing_or_tampered_guard_no_writes(self):
        for which in ("probe", "expiry", "console", "mutation"):
            with self.subTest(which=which), TemporaryDirectory() as tmp:
                root = Path(tmp)
                target, expiry, console = prepare(root)
                if which == "probe":
                    target.write_text(target.read_text().replace(PROBE_FROM, "bad hook"))
                elif which == "expiry":
                    expiry.write_text("not the reviewed expiry guard")
                elif which == "console":
                    console.write_text("friend removal allowed")
                elif which == "mutation":
                    target.write_text(target.read_text().replace(
                        "    public void remove(String xuid, String gamertag) {",
                        "    public void remove(String target) {"))
                before = target.read_bytes()
                with self.assertRaises(ValueError):
                    patch(root)
                self.assertEqual(before, target.read_bytes())

    def test_symlink_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target, _, console = prepare(root)
            target.unlink()
            target.symlink_to(console)
            with self.assertRaises(ValueError):
                patch(root)

    def test_existing_modified_guard_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target, _, _ = prepare(root)
            self.assertTrue(patch(root))
            src = target.read_text()
            target.write_text(src.replace(METHODS[
                "    public void remove(String xuid, String gamertag) {"
            ], "// REMOVED GUARD"))
            with self.assertRaises(ValueError):
                patch(root)

if __name__ == "__main__":
    unittest.main(verbosity=2)
