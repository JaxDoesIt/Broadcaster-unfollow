# Source-only asymmetric post-delete proof

Not installed; cleanup paused. OBSERVE/BEFORE_DELETE404 remain unknown and
cannot authorize DELETE or confirm a queue row. DELETE requires strict200 with
isFriend=true and both pending flags=false. Only AFTER_DELETE, following exact
DELETE200/204, may a fresh exact-route404 establish friendship absence:
post=friendship-absent verified=true basis=target-404-after-delete. No pending
flags are inferred. All freshness/header/URI/identity/queue/nonce/lock guards stay.
Post200 requires allflagsfalse; pending flags remain uncertain. Original404
case remains held; owner positive control never a removal target. No count delta.

Microsoft documents target404 as absent from owner People list:
https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/live/rest/uri/people/uri-usersowneridpeopletargetidget?view=gdk-2604

New generated harness exercises exact overlay methods with scripted HTTP/session
boundaries, not live Xbox. Heavy tests run offhost. Required before rollout:
exact-source CI, paired consumer receipt/framing changes, immutable image, protected
installation and one vetted non-owner removal/re-add/access/rollback proof.

## Exact-target recovery/rehearsal source continuation

New recovery commands are DEFAULT DENIED. A root-authored immutable descriptor
binds plan ID/hash, exact target/account hashes and issued/expiry (max15min).
Session is checked per invocation; account must persist across a recovery restart.
The mutable root journal must be separate from the hashed descriptor.
Rehearse performs strict positive/no-pending GET, DELETE, absence GET, PUT, then
strict friend/no-pending GET. Restore cannot DELETE and never certifies a rehearsal.
Pending pre-state causes no repeated PUT. PUT status alone never proves recovery.
One rehearsal DELETE attempt per process; durable cross-restart replay fencing
MUST be supplied by the independent root journal BEFORE ANY LIVE invocation.

LIVE IS BLOCKED: no sealed plan writer, armed independent restore supervisor,
root recovery attestation, permit issuer or protected final candidate promotion
is installed. A payload parser or source/image CI is not a root attestation.
Owner control remains excluded. Actual removal's unknown state must NOT trigger
an asynchronous restore racing a late Control Bot commit.
