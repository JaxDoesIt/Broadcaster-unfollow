"""Offline-only regression tests for Compose labels after Bot0 rollback."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import owner_bot0_friendlist_status_v3_trial as trial

class StaleComposeMetadataTests(unittest.TestCase):
    def context(self, base, paths):
        bot = {"Config": {"Labels": {
            "com.docker.compose.project": "mcgateway",
            "com.docker.compose.service": trial.BOT,
            "com.docker.compose.project.working_dir": str(base),
            "com.docker.compose.project.config_files": ",".join(str(p) for p in paths),
        }}}
        return trial.compose_context(bot)

    def test_single_original_file_valid(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            primary = base / "compose.yml"
            primary.write_text("services: {}\n")
            result = self.context(base, [primary])
            self.assertEqual(result[3], str(primary.resolve()))

    def test_stale_private_recovery_override_label_accepted_only_if_absent(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            primary = base / "compose.yml"
            primary.write_text("services: {}\n")
            stale = base / "mcgateway-bot0-canary-abc" / "recovery.yml"
            result = self.context(base, [primary, stale])
            self.assertEqual(result[3], str(primary.resolve()))
            stale.parent.mkdir()
            stale.write_text("services: {}\n")
            with self.assertRaises(trial.Unsafe):
                self.context(base, [primary, stale])

    def test_other_override_paths_denied(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            primary = base / "compose.yml"
            primary.write_text("services: {}\n")
            for alternative in [
                base / "other" / "recovery.yml",
                base / "mcgateway-bot0-canary-abc" / "canary.yml",
                base / "mcgateway-bot0-canary-abc" / "other.yml",
            ]:
                with self.subTest(alternative=alternative.name):
                    with self.assertRaises(trial.Unsafe):
                        self.context(base, [primary, alternative])

    def test_multiple_overrides_denied(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            primary = base / "compose.yml"
            primary.write_text("services: {}\n")
            historical = base / "mcgateway-bot0-canary-abc" / "recovery.yml"
            with self.assertRaises(trial.Unsafe):
                self.context(base, [primary, historical, historical])

if __name__ == "__main__":
    unittest.main(verbosity=2)
