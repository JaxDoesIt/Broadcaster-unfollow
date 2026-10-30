"""Deterministic fake replies, no Xbox credentials, no network."""
import json
import unittest
from dataclasses import replace
from xbox_summary_schema_probe import Request, Reply, make_request, inspect, offline_probe, FIELDS

CALLER = '2533270000000011'
TARGET = '2533270000000022'
SESSION = 'session:160'
REQ = make_request(CALLER, TARGET, SESSION)


def reply(raw=None, **kwargs):
    if raw is None:
        raw = json.dumps({'isCallerFollowingTarget': True,
                          'isTargetFollowingCaller': False}).encode()
    headers = {'Content-Type': ('application/json',), 'Content-Length': (str(len(raw)),)}
    return replace(Reply(200, REQ.uri, CALLER, SESSION, headers, raw,
                         complete=True, fresh=True), **kwargs)


class ProbeTests(unittest.TestCase):
    def test_response_directions_without_values(self):
        baseline = None
        for outgoing in (False, True):
            for incoming in (False, True):
                r = reply(json.dumps({'isCallerFollowingTarget': outgoing,
                                      'isTargetFollowingCaller': incoming}).encode())
                result = inspect(REQ, r)
                self.assertEqual('typed_both_fields', result['schema'])
                self.assertEqual({'isCallerFollowingTarget': 'boolean',
                                  'isTargetFollowingCaller': 'boolean'}, result['field_types'])
                self.assertFalse(result['can_authorize_removal'])
                self.assertFalse(result['real_xbox_provenance'])
                text = str(result)
                self.assertNotIn(CALLER, text)
                self.assertNotIn(TARGET, text)
                if baseline is None:
                    baseline = text
                self.assertEqual(baseline, text, 'relationship values must not affect report output')

    def test_bad_identity_and_method(self):
        for bad in ('0', '-1', '18446744073709551616', '12%29', 'abc', ''):
            with self.assertRaises(ValueError):
                make_request(CALLER, bad, SESSION)
        with self.assertRaises(ValueError):
            make_request(CALLER, CALLER, SESSION)
        for req in (replace(REQ, method='DELETE'), replace(REQ, timeout_seconds=10),
                    replace(REQ, redirect_policy='follow'), replace(REQ, uri='https://example.com')):
            self.assertEqual('unverified', inspect(req, reply())['schema'])

    def test_bad_http_metadata(self):
        base = reply()
        for r in (replace(base, status=404), replace(base, status=401),
                  replace(base, status=403), replace(base, status=429),
                  replace(base, status=503), replace(base, redirected=True),
                  replace(base, final_uri='https://example.com'),
                  replace(base, bound_caller='2533270000000012'),
                  replace(base, bound_session='wrong'), replace(base, fresh=False),
                  replace(base, complete=False), replace(base, body=b'x' * 20000)):
            self.assertEqual('unverified', inspect(REQ, r)['schema'])

    def test_bad_headers(self):
        base = reply()
        h = base.headers
        variants = (
            {'Content-Type': ('application/json', 'application/json'), 'Content-Length': h['Content-Length']},
            {'Content-Type': ('text/html',), 'Content-Length': h['Content-Length']},
            {'Content-Type': ('application/json',), 'content-type': ('application/json',), 'Content-Length': h['Content-Length']},
            {'Content-Type': ('application/json',), 'Content-Length': ('123',)},
            {'Content-Type': ('application/json',), 'Content-Length': h['Content-Length'], 'Age': ('5',)},
            {'Content-Type': ('application/json',), 'Content-Length': h['Content-Length'], 'X-Cache': ('HIT',)},
            {'Content-Type': ('application/json',), 'Content-Length': h['Content-Length'], 'Location': ('http://bad',)},
            {'Content-Type': ('application/json',)},
        )
        for headers in variants:
            self.assertEqual('unverified', inspect(REQ, replace(base, headers=headers))['schema'])

    def test_payload_types_and_duplicates(self):
        for raw in (b'{"isCallerFollowingTarget":false}',
                    b'{"isTargetFollowingCaller":false}',
                    b'{"isCallerFollowingTarget":null,"isTargetFollowingCaller":false}',
                    b'{"isCallerFollowingTarget":0,"isTargetFollowingCaller":false}',
                    b'{"isCallerFollowingTarget":"false","isTargetFollowingCaller":false}'):
            self.assertEqual('missing_or_untyped_field', inspect(REQ, reply(raw))['schema'])
        for raw in (b'{"isCallerFollowingTarget":true,"isCallerFollowingTarget":false,"isTargetFollowingCaller":true}',
                    b'{"isCallerFollowingTarget":true,"isTargetFollowingCaller":false,"x":{"a":1,"a":2}}',
                    b'{"isCallerFollowingTarget":true,"isTargetFollowingCaller":false,"x":NaN}',
                    b'\xff', b'[]', b'{} garbage', b'{}',
                    b'{"people":[],"isCallerFollowingTarget":false,"isTargetFollowingCaller":false}',
                    b'{"pagination":true,"isCallerFollowingTarget":false,"isTargetFollowingCaller":false}',
                    b'[' * 100 + b']' * 100):
            self.assertNotEqual('typed_both_fields', inspect(REQ, reply(raw))['schema'])

    def test_bounded_and_no_leak(self):
        self.assertEqual('typed_both_fields', offline_probe(REQ, lambda req: reply())['schema'])
        self.assertEqual('unverified', offline_probe(REQ, lambda req: (_ for _ in ()).throw(
            Exception('secret token '+CALLER)))['schema'])
        self.assertEqual('unverified', offline_probe(REQ, None)['schema'])
        self.assertNotIn(CALLER, repr(REQ))
        self.assertNotIn(TARGET, repr(REQ))
        self.assertNotIn(CALLER, repr(reply()))
        self.assertNotIn(TARGET, repr(reply()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
