"""Offline-only V3 source patch tests, no Xbox credentials or real services."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from apply_friendlist_status_v3 import (
    patch, FRIEND, TARGET, V2_BODY, V3_BODY, V3_MARKER,
    METHODS, METHOD,
)

HELPER = Path(__file__).resolve().parent / "McgatewayXboxFriendListStatusV160.java"

def fixture(root: Path):
    main = root / FRIEND
    main.parent.mkdir(parents=True, exist_ok=True)
    src = (
        "class FriendManager {\n"
        "  // MCGATEWAY_PERSONSUMMARY_CANARY_ONESHOT\n"
        "  // mcgPersonSummaryProbeConsumed.compareAndSet(false, true)\n"
        "  void diagnostic() {\n"
        + V2_BODY + "\n  }\n" + METHOD + "\n"
        + "\n".join(k + "\n" + v + "\n    }\n" for k, v in METHODS.items())
        + "\n}\n"
    )
    main.write_text(src)
    expiry = root / "core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java"
    expiry.parent.mkdir(parents=True, exist_ok=True)
    expiry.write_text("// MCGATEWAY_RELEASE160_EXPIRY_HOLD\n")
    console = root / "bootstrap/standalone/src/main/java/com/rtm516/mcxboxbroadcast/bootstrap/standalone/StandaloneLoggerImpl.java"
    console.parent.mkdir(parents=True, exist_ok=True)
    console.write_text("// friends remove is DENIED\n")
    return main, expiry, console

class Version3SourceTests(unittest.TestCase):
    def test_exact_v2_to_v3_patched_and_idempotent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            main, _, _ = fixture(root)
            self.assertTrue(patch(root, HELPER))
            source = main.read_text()
            self.assertIn(V3_MARKER, source)
            self.assertIn("MGC", "MGC")
            self.assertIn(V3_BODY, source)
            self.assertNotIn(V2_BODY, source)
            for signature, guard in METHODS.items():
                self.assertIn(signature + "\n" + guard, source)
            self.assertEqual((root / TARGET).read_bytes(), HELPER.read_bytes())
            before = {str(p):p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertFalse(patch(root, HELPER))
            after = {str(p):p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after, "idempotent source remains byte-for-byte")

    def test_missing_or_drifted_guards_no_writes(self):
        for which in ("expiry", "console", "v2body", "guard", "one_shot"):
            with self.subTest(which=which), TemporaryDirectory() as tmp:
                root = Path(tmp)
                main, expiry, console = fixture(root)
                if which == "expiry":
                    expiry.write_text("removed")
                elif which == "console":
                    console.write_text("removed")
                elif which == "v2body":
                    main.write_text(main.read_text().replace(V2_BODY, "unknown body"))
                elif which == "guard":
                    signature, guard = next(iter(METHODS.items()))
                    main.write_text(main.read_text().replace(
                        signature + "\n" + guard, signature + "\n UNGUARDED"))
                else:
                    main.write_text(main.read_text().replace(
                        "mcgPersonSummaryProbeConsumed.compareAndSet(false, true)", "not_one_shot"))
                old = main.read_bytes()
                with self.assertRaises(ValueError):
                    patch(root, HELPER)
                self.assertEqual(main.read_bytes(), old)
                self.assertFalse((root / TARGET).exists())

    def test_existing_wrong_helper_fails_before_source_update(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            main, _, _ = fixture(root)
            output = root / TARGET
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("unreviewed content")
            old = main.read_bytes()
            with self.assertRaises(ValueError):
                patch(root, HELPER)
            self.assertEqual(main.read_bytes(), old)

    def test_existing_partial_v3_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            main, _, _ = fixture(root)
            main.write_text(main.read_text().replace(V2_BODY,
                "        // " + V3_MARKER + "\nunknown code\n"))
            with self.assertRaises(ValueError):
                patch(root, HELPER)

    def test_symlinked_sources_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            main, _, console = fixture(root)
            main.unlink()
            main.symlink_to(console)
            with self.assertRaises(ValueError):
                patch(root, HELPER)

if __name__ == "__main__":
    unittest.main(verbosity=2)
