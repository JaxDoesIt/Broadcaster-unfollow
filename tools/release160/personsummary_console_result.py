#!/usr/bin/env python3
"""Pure, offline sanitizer for a future owner-authorized Bot0 PersonSummary probe.

This module does not import Docker, access Xbox, or send console commands.
It only interprets the raw output *after* a separately approved PTY capture.
Never show the original PTY capture or exception text to the operator.
"""
import re

_NONCE = re.compile(r"[0-9a-f]{32}\Z")
_HTTP = frozenset({"200", "auth", "limited", "server", "other", "unverified"})
_FIELDS = frozenset({
    "two_boolean_fields", "missing_field", "untyped_field",
    "unverified", "no_cached_target", "already_used",
    "list_auth", "list_limited", "list_server", "list_other",
    "list_empty", "list_no_valid_target", "list_invalid",
    "list_incomplete", "list_unverified"
})
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PROOF = re.compile(
    r"(?<![A-Za-z0-9_])MCGATEWAY_PERSONSUMMARY_SCHEMA_V160 "
    r"nonce=(?P<nonce>[0-9a-f]{32}) "
    r"http=(?P<http>[a-z0-9]+) "
    r"fields=(?P<fields>[a-z_]+) "
    r"can_authorize_removal=false(?![A-Za-z0-9_])"
)

def summarize(raw, nonce, delivered):
    """Return a fixed-allowlist record, never raw output.

    A transport success is necessary but NOT proof the application ran.
    Only a single matching schema marker is accepted. Even a two-boolean-field
    result is *not* authorization for friendship removal.
    """
    fail = "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false"
    if not isinstance(nonce, str) or _NONCE.fullmatch(nonce) is None:
        return fail
    if delivered is not True or not isinstance(raw, (bytes, bytearray)):
        return fail
    if len(raw) > 512 * 1024:
        return fail
    try:
        data = bytes(raw).decode("utf-8", "strict")
    except UnicodeError:
        return fail
    data = _ANSI.sub("", data)
    matches = list(_PROOF.finditer(data))
    if len(matches) != 1:
        return fail
    match = matches[0]
    if match.group("nonce") != nonce:
        return fail
    http, fields = match.group("http"), match.group("fields")
    if http not in _HTTP or fields not in _FIELDS:
        return fail
    # List outcomes are not PersonSummary HTTP responses.
    if fields.startswith("list_") and http != "unverified":
        return fail
    return (
        f"PERSONSUMMARY_DIAGNOSTIC result=OBSERVED "
        f"http={http} fields={fields} can_authorize_removal=false"
    )

if __name__ == "__main__":
    raise SystemExit("Pure sanitizer only: execute its unit tests, not a live console operation.")
