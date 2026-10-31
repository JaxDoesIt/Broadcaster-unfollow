"""Source-only fixed-upstream patch fixture checks; no Xbox account or network."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from apply_personsummary_canary import (
    patch, FRIEND_ANCHOR, CONSOLE_ANCHOR, FRIEND_PATH, CONSOLE_PATH, CORE_TARGET,
)

HELPER = Path(__file__).resolve().parent / 'McgatewayXboxPersonSummaryProbeV160.java'


def fixture(root: Path) -> dict[Path, bytes]:
    base = {
        FRIEND_PATH: 'class FriendManager {\n' + FRIEND_ANCHOR + '\n}\n',
        CONSOLE_PATH: 'class StandaloneLoggerImpl {\n' + CONSOLE_ANCHOR + '\n}\n',
        'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java':
            '// MCGATEWAY_RELEASE160_EXPIRY_HOLD\n',
    }
    for path, contents in base.items():
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contents)
    return {root / path: contents.encode() for path, contents in base.items()}


class PatchTests(unittest.TestCase):
    def test_applicable_idempotent_pinned(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = fixture(root)
            self.assertTrue(patch(root, HELPER))
            friend = (root / FRIEND_PATH).read_text()
            console = (root / CONSOLE_PATH).read_text()
            self.assertEqual(1, friend.count('mcgatewayOneShotPersonSummaryProbe('))
            self.assertEqual(1, console.count('case "personsummaryprobe" ->'))
            self.assertIn(CONSOLE_ANCHOR, console)
            self.assertNotIn('friends remove is DENIED', friend)
            self.assertIn('can_authorize_removal=false', console)
            self.assertIn('lastFriendCache == null', friend)
            self.assertIn('compareAndSet(false, true)', friend)
            self.assertIn('getTokenHeader()', friend)
            self.assertIn('getXuid()', friend)
            self.assertEqual((root / CORE_TARGET).read_bytes(), HELPER.read_bytes())
            snapshot = {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in root.rglob('*') if p.is_file()}
            self.assertFalse(patch(root, HELPER))
            self.assertEqual(snapshot, {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in root.rglob('*') if p.is_file()})
            self.assertEqual(baseline[root / 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java'],
                             (root / 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java').read_bytes())

    def test_missing_guard_no_changes(self):
        for guard in ('deny', 'expiry', 'friend'):
            with self.subTest(guard=guard), TemporaryDirectory() as tmp:
                root = Path(tmp)
                fixture(root)
                if guard == 'deny':
                    (root / CONSOLE_PATH).write_text('class Fake {}')
                elif guard == 'expiry':
                    (root / 'core/src/main/java/com/rtm516/mcxboxbroadcast/core/SessionManager.java').write_text('')
                else:
                    (root / FRIEND_PATH).write_text('class Fake {}')
                snapshot = {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.assertRaises(ValueError):
                    patch(root, HELPER)
                self.assertEqual(snapshot, {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()})
                self.assertFalse((root / CORE_TARGET).exists())

    def test_existing_mismatched_helper_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            p = root / CORE_TARGET
            p.write_text('other content')
            with self.assertRaises(ValueError):
                patch(root, HELPER)
            self.assertNotIn('personsummaryprobe', (root / CONSOLE_PATH).read_text())

    def test_symlink_target_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            original = root / FRIEND_PATH
            original.unlink()
            original.symlink_to(root / CONSOLE_PATH)
            with self.assertRaises(ValueError):
                patch(root, HELPER)
            self.assertNotIn('personsummaryprobe', (root / CONSOLE_PATH).read_text())

    def test_preexisting_tampered_hook_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            with (root / CONSOLE_PATH).open('a') as handle:
                handle.write('case "personsummaryprobe" -> runAnything();')
            with self.assertRaises(ValueError):
                patch(root, HELPER)

if __name__ == '__main__':
    unittest.main(verbosity=2)
