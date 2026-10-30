"""Offline-only Release160 Xbox PersonSummary response-shape probe.

Deliberately has NO network client, no token parameter, no CLI that fetches
anything, and no production imports. It evaluates injected fake HTTP responses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Callable, Mapping

XUID = re.compile(r"[1-9][0-9]{0,19}\Z")
SESSION = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")
URL_START = "https://social.xboxlive.com/users/xuid("
URL_END = ")/summary"
FIELDS = ("isCallerFollowingTarget", "isTargetFollowingCaller")
MAX_BYTES = 16_384
MAX_NODES = 256
MAX_DEPTH = 12


@dataclass(frozen=True)
class Request:
    method: str
    uri: str = field(repr=False)
    caller: str = field(repr=False)
    target: str = field(repr=False)
    session: str = field(repr=False)
    timeout_seconds: int = 5
    redirect_policy: str = "never"
    cache_policy: str = "no-store"


@dataclass(frozen=True)
class Reply:
    status: int
    final_uri: str = field(repr=False)
    bound_caller: str = field(repr=False)
    bound_session: str = field(repr=False)
    headers: Mapping[str, tuple[str, ...]] = field(repr=False)
    body: bytes = field(repr=False)
    complete: bool = False
    fresh: bool = False
    redirected: bool = False


def make_request(caller: str, target: str, session: str) -> Request:
    for value in (caller, target):
        if not isinstance(value, str) or not XUID.fullmatch(value) or int(value) > 2**64 - 1:
            raise ValueError("invalid numeric identity")
    if caller == target:
        raise ValueError("caller cannot be the target")
    if not isinstance(session, str) or not SESSION.fullmatch(session):
        raise ValueError("invalid session identity")
    return Request("GET", URL_START + target + URL_END, caller, target, session)


def _reject_duplicate(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON property")
        obj[key] = value
    return obj


def _reject_constant(_: str):
    raise ValueError("non-finite JSON number")


def _bounded_json(data: bytes) -> dict:
    if len(data) > MAX_BYTES or not data:
        raise ValueError("body size outside budget")
    obj = json.loads(data.decode("utf-8", "strict"), object_pairs_hook=_reject_duplicate,
                     parse_constant=_reject_constant)
    queue = [(obj, 0)]
    n = 0
    while queue:
        value, depth = queue.pop()
        n += 1
        if n > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("JSON shape budget exceeded")
        if isinstance(value, dict):
            queue.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            queue.extend((v, depth + 1) for v in value)
    if not isinstance(obj, dict):
        raise ValueError("unexpected JSON root")
    return obj


def _validated_headers(headers: Mapping[str, tuple[str, ...]], size: int) -> None:
    if not isinstance(headers, Mapping):
        raise ValueError("invalid header container")
    seen: dict[str, str] = {}
    for name, values in headers.items():
        if not isinstance(name, str) or not isinstance(values, (tuple, list)) or len(values) != 1:
            raise ValueError("invalid header")
        value = values[0]
        if not isinstance(value, str) or any(ord(ch) < 32 or ord(ch) == 127 for ch in name + value):
            raise ValueError("invalid header framing")
        key = name.lower()
        if key in seen:
            raise ValueError("duplicate header")
        seen[key] = value
    if not re.fullmatch(r"application/json(?:;\s*charset=utf-8)?", seen.get("content-type", ""), re.I):
        raise ValueError("invalid content-type")
    length = seen.get("content-length")
    if length is None or not length.isascii() or not length.isdecimal() or int(length) != size:
        raise ValueError("invalid content-length")
    if seen.get("age", "0") != "0" or "hit" in seen.get("x-cache", "").lower():
        raise ValueError("cached reply")
    if any(key in seen for key in ("location", "link", "continuation", "next", "nextlink")):
        raise ValueError("unexpected redirect or continuation")


def inspect(request: Request, response: Reply) -> dict[str, object]:
    """Return ONLY fixed, nonidentifying diagnostics, never values/IDs/body."""
    report: dict[str, object] = {
        "http_class": "unknown", "schema": "unverified", "field_types": {key: "unverified" for key in FIELDS},
        "can_authorize_removal": False, "real_xbox_provenance": False,
    }
    try:
        if not isinstance(request, Request) or not isinstance(response, Reply):
            raise ValueError("missing request/response")
        if request != make_request(request.caller, request.target, request.session):
            raise ValueError("unsafe request")
        report["http_class"] = "200" if response.status == 200 else (
            "auth_failure" if response.status in (401, 403) else
            "rate_limited" if response.status == 429 else
            "upstream_failure" if 500 <= response.status <= 599 else "other_non_200")
        if response.status != 200 or response.final_uri != request.uri or response.redirected:
            raise ValueError("untrusted HTTP status or final URI")
        if not response.complete or not response.fresh or response.bound_caller != request.caller:
            raise ValueError("incomplete, stale or wrong-account response")
        if response.bound_session != request.session or not isinstance(response.body, bytes):
            raise ValueError("wrong session or unsafe body")
        _validated_headers(response.headers, len(response.body))
        obj = _bounded_json(response.body)
        if any(key in obj for key in ("people", "pagination", "continuationToken", "nextLink", "next")):
            raise ValueError("unexpected list or pagination")
        for key in FIELDS:
            if key not in obj:
                report["field_types"][key] = "missing"
            else:
                report["field_types"][key] = "boolean" if type(obj[key]) is bool else "other"
        report["schema"] = "typed_both_fields" if all(
            report["field_types"][key] == "boolean" for key in FIELDS) else "missing_or_untyped_field"
    except (TypeError, ValueError, UnicodeError, OverflowError, AttributeError, RecursionError):
        pass
    return report


def offline_probe(request: Request, fake_exchange: Callable[[Request], Reply]) -> dict[str, object]:
    """Injected *fake only* transport: never import urllib, requests or HttpClient."""
    try:
        if not isinstance(request, Request) or request != make_request(request.caller, request.target, request.session):
            raise ValueError("unsafe request")
        if not callable(fake_exchange):
            raise ValueError("fake exchange required")
        reply = fake_exchange(request)
        return inspect(request, reply)
    except Exception:
        return {"http_class": "unknown", "schema": "unverified",
                "field_types": {key: "unverified" for key in FIELDS},
                "can_authorize_removal": False, "real_xbox_provenance": False}


if __name__ == "__main__":
    print("SOURCE-ONLY: no network client, no live Xbox requests or removals")
