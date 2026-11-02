# Verify pass run: the proof record

Executed live against https://zambo.dev/mcp on November 2, 2026
(20:43 to 20:45 UTC). Job id (_session_id): `verify-pass-2026-11-02`.
Pattern: one producer identity does a real piece of work and hands it
over; one verifier identity, with its own server-issued caller handle,
picks the handover up, runs the verify pass, and records both verdicts.
Script: `run_verify_pass.py` (in the build record next to this
package). Full responses: `run-record.json` in the build record
(capability tokens in identity files, kept private).

## Identities (agent names only; handle values live in the identity files)

| Agent | Role | Identity file (build record) |
|---|---|---|
| verify-producer | Does the work, saves the finding, wraps the handover | `identity-verify-producer.json` |
| verify-verifier | Picks the handover up, runs the pass, records verdicts | `identity-verify-verifier.json` |

## What ran, in order

1. Both agents initialized separately; each was issued its own caller
   handle and saved it before making any other call.
2. The producer did one real piece of work: `live_price` ETH at
   $2,242.99, down 0.75% (24h), saved 2026-11-02 20:43:50 UTC.
   Work receipt: https://zambo.dev/run/26084974-6c2e-42ef-b4bc-0707bb3c8413
3. The producer saved the finding with `memory_remember`, with the work
   receipt inside the fact.
   Receipt: https://zambo.dev/run/802e66d0-240e-42a9-bbdf-32aca1d4b1f5
4. The producer wrapped the finding into a handover addressed to the
   verifier (summary, goal, recipient, next steps all set; both work
   receipts attached as evidence).
   Handover: https://zambo.dev/handover/fa7444ae-e3c7-4206-ae12-3adb5e749fb0
   Wrap receipt: https://zambo.dev/run/4d42b8b8-95d3-4dd5-9caa-fbf9bcbb60cc
5. The verifier picked the handover up with `handover_accept` (free).
   The pickup returned the producer's saved steps and receipts; the
   verifier read the price and the work receipt from the record, not
   from the summary.
6. The verify pass on the work receipt, over plain HTTPS (no quota):
   GET https://zambo.dev/api/v2/receipt/26084974-6c2e-42ef-b4bc-0707bb3c8413/verify
   returned verification_status **verified**, with checks:
   commitment_matches pass, canonical_payload_matches pass,
   provenance_binding pass, metadata_binding pass;
   issuer_authentication, signature, schema, chain: not_checked
   (reported as not checked, never as passed). The saved record's
   output, read from the receipt itself, says: ETH at $2,242.99.
7. Verdict on the TRUE retelling. Claim: "ETH at $2,242.99". The claim
   matches the saved record and the record verifies.
   **Verdict: verified.** Recorded as a receipted step:
   https://zambo.dev/run/5a45e50e-6591-46f0-8df1-e699a7eb88b3
8. Verdict on the WRONG retelling (the teaching case, labeled as such
   in the run and in the verdict record). Claim: "ETH at $2,354.10".
   The number was deliberately changed from $2,242.99 to $2,354.10 for
   teaching. The record itself is untouched and still verifies; the
   saved output says $2,242.99, not $2,354.10, so the claim does not
   match the saved record. **Verdict: mismatch.**
   Recorded as a receipted step:
   https://zambo.dev/run/f5209c13-7d3c-4196-a8ee-da7a970a82d5

No receipt was fabricated or altered anywhere in this run. The
mismatch lives in the retelling, not the record, which is exactly the
failure the verify pass exists to catch.

## Free-tier accounting

Each identity has its own daily allowance, keyed to its caller handle.

- Producer: 2 counted calls (live_price, memory_remember) plus its
  free daily wrap-up for the handover.
- Verifier: 2 counted calls (the two verdict records). The pickup was
  free and the verify endpoint reads cost no quota.
- Whole pass: 4 counted calls across two separate allowances, zero
  paid calls.

## Verification

Every link above was fetched on 2026-11-02 after the run: all returned
HTTP 200 (7 of 7, including the handover page and its JSON twin and
all work, wrap, and verdict receipts). The bundled `verify.py` was run
against the work receipt in all three modes before packaging: true
claim (verdict verified, exit 0), wrong claim (verdict mismatch, exit
1), and a walk of the handover (2 receipted steps, both verified,
exit 0).
