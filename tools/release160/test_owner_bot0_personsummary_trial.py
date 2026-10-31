#!/usr/bin/env python3
"""Mock-only safety assertions for owner-authorized Bot0 recovery runner."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import owner_bot0_personsummary_trial as t

class PureIsolationTests(unittest.TestCase):
    def setUp(self):
        self.context = ("mcgateway", t.BOT, "/private/compose", "/private/compose/compose.yml")
        self.source = {
            "services": {
                t.BOT: {
                    "image": "ghcr.io/test:original", "container_name": t.BOT,
                    "restart": "unless-stopped",
                    "networks": {"mcgateway_default": None},
                    "volumes": [{"type": "bind", "source": "/SECRET", "target": "/opt/app/config"}],
                    "environment": {"SECRET": "do-not-output"}
                },
                "mcgatewaybot1-docker": {"image": "ghcr.io/test:stable"},
            },
            "networks": {"mcgateway_default": {"external": False}},
            "volumes": {}
        }

    def test_only_bot0_image_is_allowed_to_change(self):
        for image in (t.CANDIDATE, t.ORIGINAL):
            proposed = copy.deepcopy(self.source)
            proposed["services"][t.BOT]["image"] = image
            t.validate_override(self.context, self.source, proposed, image)

    def test_other_bot_mutation_is_denied(self):
        proposed = copy.deepcopy(self.source)
        proposed["services"][t.BOT]["image"] = t.CANDIDATE
        proposed["services"]["mcgatewaybot1-docker"]["image"] = "oops"
        with self.assertRaises(t.Unsafe):
            t.validate_override(self.context, self.source, proposed, t.CANDIDATE)

    def test_secret_environment_and_mount_mutation_is_denied(self):
        for key in ("environment", "volumes"):
            proposed = copy.deepcopy(self.source)
            proposed["services"][t.BOT]["image"] = t.CANDIDATE
            proposed["services"][t.BOT][key] = {}
            with self.assertRaises(t.Unsafe):
                t.validate_override(self.context, self.source, proposed, t.CANDIDATE)

    def test_service_set_addition_and_missing_digest_rejected(self):
        proposed = copy.deepcopy(self.source)
        proposed["services"][t.BOT]["image"] = "ghcr.io/test:tag"
        with self.assertRaises(t.Unsafe):
            t.validate_override(self.context, self.source, proposed, t.CANDIDATE)
        proposed["services"][t.BOT]["image"] = t.CANDIDATE
        proposed["services"]["another"] = {}
        with self.assertRaises(t.Unsafe):
            t.validate_override(self.context, self.source, proposed, t.CANDIDATE)

    def test_override_files_are_private_and_bot0_only(self):
        with tempfile.TemporaryDirectory() as folder:
            p = t.write_override(Path(folder), "canary", t.CANDIDATE)
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            text = p.read_text()
            self.assertEqual(text, f"services:\n  {t.BOT}:\n    image: {t.CANDIDATE}\n")
            self.assertNotIn("stable:", text)
            self.assertNotIn("mcgatewaybot1-docker", text)

    def test_marker_private_identity_must_match_to_remove(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / ".release160-bot0-maintenance-hold"
            identity = t.make_hold(p)
            self.assertEqual(p.read_bytes(), t.MARKER_BYTES)
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(t.Unsafe):
                t.remove_own_hold(p, (-1, -1))
            self.assertTrue(p.exists())
            t.remove_own_hold(p, identity)
            self.assertFalse(p.exists())

    def test_recreate_is_single_service_and_no_pull(self):
        calls = []
        def fake_cmd(argv, timeout=40):
            calls.append((argv, timeout))
            return b""
        with patch.object(t, "cmd", fake_cmd):
            t.recreate(self.context, Path("/private/canary.yml"))
        self.assertEqual(len(calls), 1)
        args = calls[0][0]
        self.assertEqual(args[-1], t.BOT)
        for item in ("--no-deps", "--no-build", "--force-recreate", "never"):
            self.assertIn(item, args)
        self.assertNotIn("restart", args)
        self.assertNotIn("down", args)

    def test_preflight_refuses_unpaused_cleanup_without_docker_mutation(self):
        with patch.object(t.os, "geteuid", return_value=0), \
             patch.object(t.sys, "argv", ["script.py", "--execute-authorized-bot0-only"]), \
             patch.object(t, "locate_control_bot", return_value=(Path("/readonly"), 1234)), \
             patch.object(t, "paused_cleanup", return_value=False), \
             patch.object(t, "cmd") as command:
            with self.assertRaises(t.Unsafe):
                t.main()
            command.assert_not_called()

    def test_direct_output_is_sanitized_with_nonce_not_printed(self):
        nonce = "d" * 32
        marker = (
            f"garbage xuid=12345 auth=SECRET\n"
            f"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce={nonce} "
            f"http=200 fields=two_boolean_fields can_authorize_removal=false\n"
        ).encode()
        class Completed:
            returncode = 0
            stdout = marker
            stderr = b"more secrets"
        with patch.object(t.secrets, "token_hex", return_value=nonce), \
             patch.object(t, "docker_inspect", return_value={"Id": "e" * 64}), \
             patch.object(t.subprocess, "run", return_value=Completed()) as sent:
            result = t.direct_one_shot(Path("/not-used"))
            self.assertEqual(sent.call_count, 1)
            self.assertIn("result=OBSERVED", result)
            self.assertNotIn("SECRET", result)
            self.assertNotIn(nonce, result)
            self.assertNotIn("12345", result)

    def test_direct_attach_failure_is_unverified_not_retried(self):
        class Completed:
            returncode = 124
            stdout = b""
            stderr = b"private error"
        with patch.object(t.secrets, "token_hex", return_value="e" * 32), \
             patch.object(t, "docker_inspect", return_value={"Id": "f" * 64}), \
             patch.object(t.subprocess, "run", return_value=Completed()) as sent:
            result = t.direct_one_shot(Path("/not-used"))
            self.assertEqual(sent.call_count, 1)
            self.assertEqual(result, "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false")


class MockedLifecycleTests(unittest.TestCase):
    def exercise(self, candidate_boot_failure):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "control"
            (root / "data").mkdir(parents=True)
            marker = root / "data" / ".release160-bot0-maintenance-hold"
            state = {"image": "baseline-id"}
            snapshots = {name: {"id": "container-" + name, "image": "baseline-id"}
                         for name in t.FLEET}
            original = {
                "services": {
                    t.BOT: {"image": "ghcr.io/original:tag", "container_name": t.BOT,
                            "volumes": [{"type": "bind", "source": "/PRIVATE", "target": "/opt/app/config"}]},
                    "mcgatewaybot1-docker": {"image": "existing-other-image"}
                },
                "networks": {}, "volumes": {}
            }
            def inspect(kind, name):
                if kind == "image":
                    return {"Id": "baseline-id"}
                if name == "watchtower":
                    return {"State": {"Running": False}}
                if name == t.BOT:
                    return {"Image": state["image"],
                            "Config": {"Tty": True, "OpenStdin": True},
                            "State": {"Running": True, "OOMKilled": False}}
                raise AssertionError("unplanned inspect")

            def effective(_context, override=None):
                data = copy.deepcopy(original)
                if override is not None:
                    data["services"][t.BOT]["image"] = (
                        t.CANDIDATE if "canary" in str(override) else t.ORIGINAL
                    )
                return data

            def recreate(_context, override):
                state["image"] = (
                    "candidate-id" if "canary" in str(override) else "baseline-id"
                )
                transitions.append(state["image"])

            def boot(expected_id, seconds):
                self.assertEqual(state["image"], expected_id)
                if candidate_boot_failure and expected_id == "candidate-id":
                    raise t.Unsafe("simulated candidate boot failure")

            transitions = []
            with patch.object(t.os, "geteuid", return_value=0), \
                 patch.object(t.sys, "argv", ["script.py", "--execute-authorized-bot0-only"]), \
                 patch.object(t, "locate_control_bot", return_value=(root, 1234)), \
                 patch.object(t, "paused_cleanup", return_value=True), \
                 patch.object(t, "paused_updates"), \
                 patch.object(t, "docker_inspect", side_effect=inspect), \
                 patch.object(t, "fleet_snapshot", return_value=snapshots), \
                 patch.object(t, "original_identity"), \
                 patch.object(t, "compose_context", return_value=("mcgateway", t.BOT, folder, "fake-compose.yml")), \
                 patch.object(t, "compose_config", side_effect=effective), \
                 patch.object(t, "other_bots_unchanged", return_value=True), \
                 patch.object(t, "cmd", return_value=b"mocked pull"), \
                 patch.object(t, "confirm_image", side_effect=lambda ref: "candidate-id" if ref == t.CANDIDATE else "baseline-id"), \
                 patch.object(t, "recreate", side_effect=recreate), \
                 patch.object(t, "verified_boot", side_effect=boot), \
                 patch.object(t, "direct_one_shot", return_value="PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=200 fields=two_boolean_fields can_authorize_removal=false"):
                outcome = t.main()
            self.assertEqual(state["image"], "baseline-id")
            self.assertEqual(transitions, ["candidate-id", "baseline-id"])
            self.assertFalse(marker.exists(), "successful restoration clears only its own hold")
            self.assertEqual(outcome, 2 if candidate_boot_failure else 0)

    def test_successful_mock_trial_restores_exact_original(self):
        self.exercise(False)

    def test_failed_mock_canary_boot_restores_and_removes_hold(self):
        self.exercise(True)

if __name__ == "__main__":
    unittest.main(verbosity=2)
