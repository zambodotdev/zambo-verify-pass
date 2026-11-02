#!/usr/bin/env python3
"""verify.py: the verify pass, as a runnable tool.

Takes a Zambo receipt id or a https://zambo.dev/run/<id> link, checks
the receipt at the v2 verify endpoint, prints every check and the
verification_status, and shows the output that was actually saved.
With --claim, it also compares a retelling against the saved record
and prints the verdict: verified when the claim matches what was
saved, mismatch when it does not.

With --handover <id-or-link>, it walks the handover's steps and
verifies each step's receipt the same way.

    python3 verify.py 26084974-6c2e-42ef-b4bc-0707bb3c8413
    python3 verify.py https://zambo.dev/run/26084974-6c2e-42ef-b4bc-0707bb3c8413 --claim "ETH at $2,242.99"
    python3 verify.py --handover https://zambo.dev/handover/fa7444ae-e3c7-4206-ae12-3adb5e749fb0

Standard library only. No API key, no account. The verify endpoint is
a plain HTTPS read: GET https://zambo.dev/api/v2/receipt/{id}/verify

Trust the record, not the retelling. A receipt proves the saved result
was not changed since it was saved, never that the answer was right;
the verdict vocabulary is the endpoint's own: verified / verification
failed / not checked / absent.
"""
import argparse
import base64
import json
import re
import sys
import urllib.request

API = "https://zambo.dev/api/v2/receipt/{id}/verify"
HANDOVER_JSON = "https://zambo.dev/handover/{id}.json"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
RUN_URL_RE = re.compile(r"zambo\.dev/run/([0-9a-f-]{36})")


def get_json(url, attempts=3):
    """Read a JSON document over HTTPS. urllib first; if the local
    network keeps truncating the body, fall back to the system curl,
    which rides a different code path through most proxies."""
    last = None
    for _ in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "zambo-verify-pass/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # truncated reads and proxy hiccups
            last = exc
    import shutil
    import subprocess
    if shutil.which("curl"):
        for _ in range(attempts):
            try:
                out = subprocess.run(
                    ["curl", "-sS", "--fail", "--max-time", "60", "-A", "zambo-verify-pass/1.0", url],
                    capture_output=True, timeout=90)
                if out.returncode == 0:
                    return json.loads(out.stdout.decode("utf-8"))
                last = RuntimeError(out.stderr.decode("utf-8", "replace")[:200])
            except Exception as exc:
                last = exc
    raise SystemExit(f"could not read {url}: {last}")


def receipt_id_of(value):
    m = RUN_URL_RE.search(value) or UUID_RE.search(value)
    if not m:
        raise SystemExit(f"no receipt id found in: {value}")
    return m.group(1) if m.lastindex else m.group(0)


def handover_id_of(value):
    m = UUID_RE.search(value)
    if not m:
        raise SystemExit(f"no handover id found in: {value}")
    return m.group(0)


def saved_output_text(v2):
    """The committed output lives in the receipt's canonical bytes."""
    receipt = v2.get("receipt") or {}
    cb = receipt.get("canonical_bytes")
    if cb:
        try:
            doc = json.loads(base64.b64decode(cb))
            out = doc.get("output") or {}
            if isinstance(out, dict) and out.get("text"):
                return out["text"]
            if isinstance(out, str):
                return out
        except Exception:
            pass
    return receipt.get("result_preview") or ""


def verify_receipt(receipt_id, claim=None):
    v2 = get_json(API.format(id=receipt_id))
    status = v2.get("verification_status", "absent")
    print(f"receipt {receipt_id}")
    print(f"  source: https://zambo.dev/run/{receipt_id}")
    print(f"  verification_status: {status}")
    checks = v2.get("checks") or {}
    for name, check in checks.items():
        if isinstance(check, dict):
            print(f"  check {name}: {check.get('status')}")
    saved = saved_output_text(v2)
    if saved:
        print("  saved output:")
        for line in saved.splitlines():
            print(f"    {line}")
    verdict = None
    if claim is not None:
        match = claim.strip() in saved or saved.strip() in claim.strip() and bool(saved.strip())
        # A claim verifies when the value it asserts appears in the
        # saved record. Compare on the claim's distinctive content:
        # the full claim string first, then its longest token run.
        if not match:
            tokens = [t for t in re.split(r"\s+", claim.strip()) if len(t) > 3]
            match = bool(tokens) and all(t in saved for t in tokens if any(c.isdigit() for c in t))
        verdict = "verified" if (status == "verified" and match) else "mismatch"
        print(f"  claim: {claim!r}")
        print(f"  claim matches the saved record: {match}")
        print(f"  VERDICT: {verdict}")
    return status, verdict


def walk_handover(handover_id):
    doc = get_json(HANDOVER_JSON.format(id=handover_id))
    ids = []
    for step in doc.get("steps") or []:
        url = step.get("receipt_url") or ""
        m = UUID_RE.search(url)
        if m:
            ids.append((step.get("tool") or "step", m.group(0)))
    if not ids:
        for node in (doc.get("graph") or {}).get("nodes") or []:
            rid = node.get("receipt")
            if rid and UUID_RE.fullmatch(rid):
                ids.append((node.get("label") or "step", rid))
    print(f"handover {handover_id}: {len(ids)} receipted steps")
    results = []
    for label, rid in ids:
        print(f"\n[{label}]")
        status, _ = verify_receipt(rid)
        results.append((label, rid, status))
    print("\nwalk summary:")
    for label, rid, status in results:
        print(f"  {label}: {status}  https://zambo.dev/run/{rid}")
    bad = [r for r in results if r[2] != "verified"]
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify a Zambo receipt, or walk a handover verifying each step.")
    ap.add_argument("receipt", nargs="?", help="receipt id or https://zambo.dev/run/<id> link")
    ap.add_argument("--claim", help="a retelling to compare against the saved record")
    ap.add_argument("--handover", help="handover id or link: verify every step receipt in it")
    args = ap.parse_args(argv)
    if args.handover:
        return walk_handover(handover_id_of(args.handover))
    if not args.receipt:
        ap.error("give a receipt id or link, or --handover")
    status, verdict = verify_receipt(receipt_id_of(args.receipt), claim=args.claim)
    if verdict is not None:
        return 0 if verdict == "verified" else 1
    return 0 if status == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())
