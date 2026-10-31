#!/usr/bin/env python3
"""No-network mock and adversarial tests for the result-only redactor."""
import unittest
from personsummary_console_result import summarize

N = "0123456789abcdef0123456789abcdef"
SAFE = b"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce=" + N.encode() + b" http=200 fields=two_boolean_fields can_authorize_removal=false"

class ConsoleResultTests(unittest.TestCase):
    def test_normal_marker_redacts_surrounding_secrets(self):
        raw = (b"[INFO] example-xuid=1234567890123456 token=REDACT-ME\n"
               + b"\x1b[32m[19:32:11 INFO] [Console] " + SAFE + b"\x1b[0m\r\n"
               + b"Other secret event\n")
        out = summarize(raw, N, True)
        self.assertEqual(out, "PERSONSUMMARY_DIAGNOSTIC result=OBSERVED http=200 fields=two_boolean_fields can_authorize_removal=false")
        for secret in ("1234567890123456", "REDACT-ME", N, "Other secret event"):
            self.assertNotIn(secret, out)

    def test_all_coarse_allowed_field_shapes(self):
        for http in ("200", "auth", "limited", "server", "other", "unverified"):
            for fields in ("two_boolean_fields", "missing_field", "untyped_field",
                           "unverified", "no_cached_target", "already_used"):
                record = (f"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce={N} "
                          f"http={http} fields={fields} can_authorize_removal=false").encode()
                result = summarize(record, N, True)
                self.assertIn("result=OBSERVED", result)
                self.assertIn("can_authorize_removal=false", result)

    def test_v3_friend_list_http_and_shape_labels_redacted(self):
        labels = (
            "list_auth", "list_limited", "list_server", "list_other",
            "list_empty", "list_no_valid_target", "list_invalid",
            "list_incomplete", "list_unverified"
        )
        for field in labels:
            raw = (
                b"BEFORE token=SECRET XUID=2533270000000022\n"
                + f"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce={N} "
                  f"http=unverified fields={field} can_authorize_removal=false".encode()
                + b"\nAFTER friend=PRIVATE"
            )
            output = summarize(raw, N, True)
            self.assertEqual(
                output,
                f"PERSONSUMMARY_DIAGNOSTIC result=OBSERVED "
                f"http=unverified fields={field} can_authorize_removal=false"
            )
            self.assertNotIn("SECRET", output)
            self.assertNotIn("2533270000000022", output)
            self.assertNotIn(N, output)
        for invalid in ("list_ready", "list_confirmed", "list_secret", "list_200"):
            raw = (f"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce={N} "
                   f"http=unverified fields={invalid} can_authorize_removal=false").encode()
            self.assertIn("result=UNVERIFIED", summarize(raw, N, True))
        raw = (f"MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce={N} "
               f"http=200 fields=list_auth can_authorize_removal=false").encode()
        self.assertIn("result=UNVERIFIED", summarize(raw, N, True))

    def test_reject_ambiguous_or_unproven(self):
        cases = [
            (SAFE, N, False),
            (SAFE, N, 1),
            (SAFE, "f" * 32, True),
            (SAFE + b"\n" + SAFE, N, True),
            (SAFE.replace(b"false", b"true"), N, True),
            (SAFE.replace(b"http=200", b"http=201"), N, True),
            (SAFE.replace(b"fields=two_boolean_fields", b"fields=verified"), N, True),
            (b"personsummaryprobe " + N.encode(), N, True),
            (SAFE + b"\xff", N, True),
            (SAFE * 12000, N, True),
            (SAFE + b"\nMCGATEWAY_PERSONSUMMARY_SCHEMA_V160 nonce="
             + N.encode() + b" http=200 fields=missing_field can_authorize_removal=false", N, True),
        ]
        for raw, nonce, delivered in cases:
            with self.subTest(raw=raw[:70], delivered=delivered):
                self.assertEqual(
                    summarize(raw, nonce, delivered),
                    "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false",
                )

    def test_reject_null_unicode_and_invalid_nonce(self):
        for data in (None, "string-not-bytes", {}, b""):
            self.assertEqual(
                summarize(data, N, True),
                "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false"
            )
        for nonce in (N.upper(), "a" * 31, "", None, N + "0"):
            self.assertEqual(
                summarize(SAFE, nonce, True),
                "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false",
            )

if __name__ == "__main__":
    unittest.main(verbosity=2)
