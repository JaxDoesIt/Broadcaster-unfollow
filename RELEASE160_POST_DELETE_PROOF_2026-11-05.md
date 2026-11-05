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
