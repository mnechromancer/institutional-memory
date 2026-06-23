# KSE — Field Reports & Droid Intelligence Logs

*Filed by: K-9RX Unit (GX-8 Integration Droid, KSE Systems Division)*
*Cross-referenced by: Riya Patel, Solutions Engineering*
*Compiled: April 30, 2026*

---

## A Note On K-9RX

K-9RX — "Kurex" — is KSE's Systems Integration Lead. He is a GX-8
maintenance droid who was repurposed for software integration work after
"demonstrating an unusually adversarial approach to diagnostic questioning"
(his personnel file's words, not ours). He is extremely literal. He does
not soften feedback. He is the most reliable signal in this account.

When K-9RX is happy, the account is healthy.
When K-9RX is annoyed, something real is wrong.
When K-9RX goes quiet, something very real is wrong.

He is currently somewhere between annoyed and quiet.

---

## Active Tickets Filed by K-9RX

### NAV-3301 — Navigation Cache Desync

**Filed:** 2026-01-22
**Priority:** Medium (self-assessed by K-9RX as "unacceptable within defined parameters")
**Current status:** Patch deployed 2026-02-19. K-9RX has not confirmed resolution.

K-9RX's initial report was characteristically precise:

  "The VANGUARD route calculation module is returning cached hyperspace
   coordinates in 7.8% of queries. The correct figure should be 0.0%.
   I have attached 847 log entries. I expect a root cause analysis, not
   a workaround. Workarounds are what the previous vendor provided."

The "previous vendor" reference is to Nexus Data Works. Being compared to
Nexus Data Works is the K-9RX equivalent of a Sith distress signal.

Our engineering team patched the caching layer on Feb 19. We told K-9RX.
He replied: "Acknowledged. Logging will tell me. I will tell you."

He has not told us. That was 70 days ago.

**Action required:** Riya Patel needs to call K-9RX directly before renewal.
Not a ticket. A call. He responds to direct contact.

### TRAIN-667 — Mandalore Site Onboarding Incomplete

**Filed:** 2026-02-15
**Priority:** Medium
**Status:** Open — training session offered, not yet scheduled

K-9RX's note is short, which means he's more annoyed than usual:

  "38 of 60 Mandalore personnel are using VANGUARD v3 interface.
   v3 was deprecated in October 2025. I have reported this internally.
   I was told 'they'll catch up.' They have not caught up."

Our offer: a free remote training session with one of our specialists.
Status: Kendall Ors (Mandalore IT lead) accepted in writing. Never scheduled.

Explain this at the renewal call as: "We have offered a full remediation
session and are waiting on scheduling coordination." Do not say "the ball
was dropped." Even though it was. Partially by both sides.

### SHIELD-019 — Shield Generator Module Integration Errors

**Filed:** 2026-03-10 by Mira Jade (Head of Operations)
**Priority:** P2 (self-escalated)
**Status:** In progress — our integration team has a fix in staging

This is Mira Jade's first direct contact with our support team.
The ticket is formal and technical, but she escalated it to P2 herself,
which is unusual for a Head of Operations filing a first ticket.

K-9RX added a note to this ticket on 2026-03-18:

  "This integration was designed to interface with legacy shield inventory
   schema. The schema was updated in January 2026 when Director Callus
   restructured the operations data model. VANGUARD was not notified of
   the schema change. I flagged this internally. The response was that
   VANGUARD should have anticipated the change. I do not know how."

This is important: the data format error in SHIELD-019 is not entirely our
fault. Director Callus's team changed the underlying schema without
notifying us. K-9RX is documenting this quietly. He may be building a case.
For whom, we don't yet know.

---

## K-9RX Anomaly Logs — Unprompted Reports

K-9RX has filed four unprompted anomaly reports in the last 60 days.
These did not come through our support system. They came as direct emails
to Riya Patel. This is unusual.

### Anomaly Report KSE-AN-001 (2026-03-22)

  "I am logging this for completeness. Over the past three weeks I have
   observed 14 instances of VANGUARD API queries returning routing data
   that is 4-6 hours stale. The occurrence rate is 3.1%. This is outside
   normal cache behavior. The pattern does not match NAV-3301, which was
   resolved. I am monitoring. I will report if the rate increases."

### Anomaly Report KSE-AN-002 (2026-04-08)

  "The anomaly rate referenced in AN-001 has increased to 6.4%.
   I have identified that the affected queries all originate from
   the Corellian data relay. I have reported this to Director Callus.
   He classified it as a VANGUARD vendor issue. I am not certain of that
   classification. I am flagging here as well."

Riya Patel responded, opened an investigation. The Corellian relay was
reconfigured by our infrastructure team on April 14. Rate appeared to drop.

### Anomaly Report KSE-AN-003 (2026-04-29)

  "The rate has returned. Currently at 5.8%. The pattern is the same.
   The relay reconfiguration addressed the symptom, not the source.
   I am continuing to monitor. I want to flag that Director Callus asked
   me to route all future anomaly reports through his office rather than
   directly to vendors. I am sending this to you before I comply with
   that instruction, because I believe you should have it."

This last message arrived on April 29. It has not been escalated internally.
Riya Patel flagged it to Jordan Reeves with the note: "Something feels off.
K-9RX doesn't hedge. When he says he 'believes you should have it' that's
the closest he gets to 'something is wrong.'"

**This should be investigated before the renewal call.**
