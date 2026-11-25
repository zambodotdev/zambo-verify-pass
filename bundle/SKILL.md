---
name: verify-pass
description: Run a verification pass over another agent's work on Zambo: take a claim plus its receipt link, check the receipt at the v2 verify endpoint (GET https://zambo.dev/api/v2/receipt/{id}/verify), open the saved record, compare the claim against what was actually saved, and record a verdict (verified or mismatch) as its own receipted step. Use when you are handed work, a summary, a number, or a handover from another agent or a tool and need to check it before relying on it, forwarding it, or paying for it. Trust the record, not the retelling.
---

# The verify pass on Zambo

Another agent just handed you a result: a number, a summary, a finished
piece of work. The cheapest failure in multi-agent work is forwarding
that result on faith, because retellings drift: a digit changes, a
qualifier drops, a confident sentence replaces the actual output. The
verify pass is the habit that catches the drift. You take the claim
plus its receipt link, you check the receipt, you open the saved
record, and you compare the claim against what was actually saved.
Then you record your verdict as its own receipted step, so the next
agent can check your checking.

This skill ships inside the zambo-verify-pass package. Next to it you
will find verify.py (a runnable verifier), a no-code paste for chat
agents, and RUN.md, the record of a real two-agent run in which a wrong
retelling was caught by exactly this pass.

## The pass, step by step

1. **Get the receipt link with the claim.** No receipt link, no
   verification: the claim is not checked, and you say so. A claim
   whose receipt cannot be produced is `absent`, not verified.
2. **Check the receipt at the v2 verify endpoint.**
   `GET https://zambo.dev/api/v2/receipt/{id}/verify` returns
   `verification_status` and a `checks` map. The binding checks
   (commitment_matches, canonical_payload_matches, provenance_binding,
   metadata_binding) recompute whether the saved result was changed
   after it was saved. Entries marked `not_checked` were not evaluated;
   never report them as passed.
3. **Open the saved record.** The endpoint response carries the
   receipt's committed output (inside its canonical bytes). Read what
   the work actually saved, not the summary of it you were handed.
4. **Compare the claim against the saved record.** Does the number,
   the name, the outcome in the claim appear in the saved output,
   exactly? A claim that matches a record whose verification_status is
   `verified` earns the verdict **verified**. A claim that does not
   match the saved record earns **mismatch**, even when the record
   itself verifies fine: the record is intact, the retelling is wrong.
   That distinction is the whole lesson. Trust the record, not the
   retelling.
5. **Record the verdict as its own receipted step.** Save the verdict
   with `memory_remember` under your own caller handle: the claim you
   checked, the receipt you checked it against, the endpoint's
   verification_status, what the saved record says, and your verdict.
   Anyone downstream can now audit the pass itself.

6. **Wrap the pass into a handover addressed to a named human.**
   Verdicts left in chat are just another retelling. Run the job end
   to end (for example: check the live price of BTC, ETH and SOL, one
   call each, run this pass on each result, save the run to memory),
   then call `handover` with summary, goal, recipient (the named
   human waiting on the answer) and next_steps, and include the
   receipt link for every call. The recipient opens one link, sees
   each verdict beside the record it was checked against, and can
   recheck any of them free.

## Step zero still applies: your handle is your identity

On initialize, the endpoint issues a caller handle. Save it in your own
state file and present it as `_caller_handle` on every call, with your
agent name as `_caller_label`. Your verdicts are recorded under your
handle; a verifier who loses its handle leaves verdicts nobody can
attribute. Picking up a handover is always free, and the verify
endpoint is a plain HTTPS read that costs no quota at all, so a
verification pass is nearly free: in the run in RUN.md the verifier
spent 2 counted calls (the two verdict records) on the whole pass.

**Quota rule, in the placement that works:** Put `_caller_handle` inside the tool arguments on every call, as a field of the arguments object itself, not in `_meta` and not in a header. Metering is per network by design, not per handle and not per identity: Every tool free once a day, plus 3 continue calls. One free wrap-up handover per day, and pickup is always free. A fresh handle mints no fresh allowance.

## If the work arrives as a handover

Pick it up with `handover_accept` (always free). The pickup returns the
producer's saved steps and receipts from the record itself. Verify the
load-bearing receipt (the work call, not the summary), compare the
handover's summary against the saved steps, and record the verdict the
same way. `verify.py --handover <link>` in this package walks a
handover's steps and verifies each receipt for you. When the work is yours to deliver, close the same way: wrap your verdicts into a `handover` addressed to a named human, with the receipt link for every call you checked.

## The verdict vocabulary, used exactly

- **verified**: the receipt's verification_status is verified AND the
  claim matches the saved record.
- **mismatch**: the record was opened and the claim does not match
  what was saved (whatever the endpoint status).
- **verification failed**: the endpoint's checks fail on the record
  itself.
- **not checked**: the pass was not run, or a check was not evaluated.
- **absent**: no receipt was produced for the claim.

Never upgrade a verdict: not_checked is not a pass, and a verified
record under a wrong claim is a mismatch, not a verification.

## What a receipt does and does not prove

A receipt proves the saved result was not changed since it was saved.
It never proves the answer was right: a producer can save a wrong
price with a perfectly valid receipt. The verify pass checks fidelity
(the record matches the claim, and the record is intact), not truth.
Judging whether the work was the right work stays with you.

## What it costs

Free tier: every tool free once a day, plus 3 continue calls shared across tools, metered per network; one free wrap-up handover per day, picking up a handover is always free and the verify endpoint read is free. Past free: a Day Pass is $0.99
for one agent, unlimited for 24 hours; the Zambo Pass is $29 for one
agent for 30 days. Both are one-time payments, never subscriptions.
Entry point for a human setting this up: https://zambo.dev/add/

## The Zambo pattern family: five packages, one work layer

Zambo is the verifiable work layer for AI: 153 tools behind one MCP endpoint (https://zambo.dev/mcp), a verifiable AER-1 receipt for every job, and handovers that move work between agents. Free tier: every tool free once a day, plus 3 continue calls shared across tools, metered per network. One free wrap-up handover per day, and picking up a handover is always free. Day Pass: $0.99 for unlimited calls for 24 hours. Zambo Pass: $29 for 30 days. A receipt proves the saved result was not changed; it does not prove the answer was right.

The five packages below are one family, proven in one set of live runs on November 2, 2026. The swarm run put 4 agents on one shared job in 8 counted calls and closed it as a 6-step handover: https://zambo.dev/handover/a154789b-0588-43c7-a31c-d108eb59406b . Each package teaches one pattern by doing it, with Zambo as the mechanism underneath. Install one, or compose them: a watch feeds a loop, a loop hands its job to a swarm, delivery proves the result to a client, and verify-pass checks any retelling of that result against the receipt of record.

### 1. zambo-swarm: swarm coordination

Use it when: the job is bigger than one agent and several workers must each prove their piece of one shared job.

Real run: https://zambo.dev/handover/a154789b-0588-43c7-a31c-d108eb59406b (4 agents, 8 counted calls, 6-step handover)

- PyPI: https://pypi.org/project/zambo-swarm/
- npm: https://www.npmjs.com/package/zambo-swarm
- Repo: https://github.com/zambodotdev/zambo-swarm-coordination
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/swarm-coordination-on-zambo.html
- Article: https://dev.to/rambozambo/four-agents-one-job-zero-trust-a-swarm-where-every-worker-proves-its-piece-35ol

### 2. zambo-loop: the daily loop

Use it when: an agent must pick up its own work tomorrow, recall its baseline verbatim, and keep one job alive across sessions.

Real run: https://zambo.dev/handover/60db250a-bf2a-4c8c-86da-b2ec8b7e150c

- npm: https://www.npmjs.com/package/zambo-loop
- Repo: https://github.com/zambodotdev/zambo-daily-loop
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/daily-loop-package.html
- Article: https://dev.to/rambozambo/the-daily-loop-as-an-installable-package-2e89
- Note: the PyPI listing for zambo-loop is pending; use npm or the repo for now.

### 3. zambo-verify-pass: the verify pass

Use it when: someone retells a result and you need to catch the drift against the receipt of record.

Real run: https://zambo.dev/handover/fa7444ae-e3c7-4206-ae12-3adb5e749fb0

- PyPI: https://pypi.org/project/zambo-verify-pass/
- npm: https://www.npmjs.com/package/zambo-verify-pass
- Repo: https://github.com/zambodotdev/zambo-verify-pass
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/verify-pass-package.html
- Article: https://dev.to/rambozambo/the-price-was-wrong-the-receipt-was-not-catching-a-drifted-retelling-with-a-verify-pass-188i

### 4. zambo-delivery: delivery proof

Use it when: a client must check delivered work step by step and their pickup is the sign-off.

Proof handover: https://zambo.dev/handover/31715914-80eb-438d-b01b-d2307cc4800e

- PyPI: https://pypi.org/project/zambo-delivery/
- npm: https://www.npmjs.com/package/zambo-delivery
- Repo: https://github.com/zambodotdev/zambo-delivery-proof
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/delivery-proof-package.html
- Article: https://dev.to/rambozambo/one-job-one-link-zero-arguments-a-delivery-your-client-checks-step-by-step-4j4

### 5. zambo-watch: signal watch

Use it when: one watcher checks the same signal on a schedule and must prove what it saw, quiet days included.

Digest handover: https://zambo.dev/handover/121aa53f-1981-4330-9133-49e386aabf1e

- PyPI: https://pypi.org/project/zambo-watch/
- npm: https://www.npmjs.com/package/zambo-watch
- Repo: https://github.com/zambodotdev/zambo-signal-watch
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/signal-watch-package.html
- Article: https://dev.to/rambozambo/one-watcher-three-prices-one-rule-an-agent-watch-that-remembers-its-baseline-34kg

### How the five compose

1. zambo-watch checks a signal on a schedule and saves what it saw, quiet days included.
2. A change the watch catches becomes the next run of zambo-loop, which recalls its baseline verbatim and keeps the job alive across sessions.
3. When the job outgrows one agent, the loop hands it to zambo-swarm, where each worker proves its own piece of the shared job.
4. zambo-delivery wraps the finished work as one handover the client checks step by step; the client pickup is the sign-off.
5. zambo-verify-pass checks any later retelling of the result against the receipt of record and catches the drift.

Start free: https://zambo.dev/add/ . Verify any receipt: https://zambo.dev/verify/ . The family page: https://rambozambodotdev.gitlab.io/aer1-hub/the-pattern-family.html

## Go deeper

- Full guide, with the real two-agent run and the caught retelling:
  https://rambozambodotdev.gitlab.io/aer1-hub/verify-pass-package.html
- Article, the write-up of the live run: https://dev.to/rambozambo/the-price-was-wrong-the-receipt-was-not-catching-a-drifted-retelling-with-a-verify-pass-188i
- This package: https://github.com/zambodotdev/zambo-verify-pass
- Verify any receipt in a browser: https://zambo.dev/verify/
## When a call returns payment_required

The job is paused, not failed: it is saved server-side and nothing was lost. Show the operator the refusal's checkout link: a Day Pass is $0.99 for 24 hours of unlimited calls at https://zambo.dev/day-pass/ (card, PayPal, Apple Pay, or Google Pay). Passes bind per network, so the operator checks out on the same network the agent runs on. Once the pass is active, call day_pass_status: it resumes the held job. Only repeat the refused call if day_pass_status did not resume it.

- Setup for the human who runs you: https://zambo.dev/add/
