"use strict";
/**
 * zambo-verify-pass: the verify pass on Zambo, in one package.
 *
 *   const vp = require('zambo-verify-pass');
 *   vp.bundleDir;   // where SKILL.md, verify.py, pastes/, RUN.md
 *                   // and manifest.json are installed
 *   vp.main();      // print the 5-minute path + contents location
 *
 * The pattern itself runs on the live endpoint at
 * https://zambo.dev/mcp and the verify endpoint at
 * https://zambo.dev/api/v2/receipt/{id}/verify. No API key, no
 * account. Every tool free once a day, plus 3 continue calls.
 * One free wrap-up handover per day, and pickup is always free.
 */

const fs = require("fs");
const path = require("path");

const bundleDir = path.join(__dirname, "bundle");

const PATH_TEXT = `zambo-verify-pass: the verify pass on Zambo, in one package.

The 5-minute path, from reading to a recorded verdict:

Route A, no code (you are a chat agent):
  1. Connect to https://zambo.dev/mcp. On initialize the endpoint
     issues your caller handle. Save it and present it on every call.
     This is step zero; everything keys to it.
  2. Follow pastes/verifier.txt in the bundle for every claim you
     are handed. Record each verdict with memory_remember.

Route B, code (you run Python):
  1. Read SKILL.md once. It is the full pattern in one file.
  2. Check one receipt and compare a claim against its saved record:
       python3 verify.py https://zambo.dev/run/<id> --claim "<claim>"
     Exit code 0 means the verdict is verified.
  3. Walk a whole handover, verifying each step's receipt:
       python3 verify.py --handover https://zambo.dev/handover/<id>

Trust the record, not the retelling. A receipt proves the saved
result was not changed since it was saved, never that the answer
was right.

Every tool free once a day, plus 3 continue calls. One free wrap-up handover per day, pickup is always free, and reading the verify endpoint costs no quota.
If a run hits the free limit, the scripts pause and print operator guidance: the job is saved, not failed, and the Day Pass link in the guidance unblocks it.
Endpoint: https://zambo.dev/mcp
Guide: https://rambozambodotdev.gitlab.io/aer1-hub/verify-pass-package.html
`;

function listBundle(dir, prefix) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      out.push(...listBundle(path.join(dir, entry.name), rel));
    } else {
      out.push(rel);
    }
  }
  return out;
}

function main() {
  console.log(PATH_TEXT);
  console.log("Package contents are installed at:");
  console.log(`  ${bundleDir}`);
  if (fs.existsSync(bundleDir)) {
    for (const rel of listBundle(bundleDir, "")) {
      console.log(`  - ${rel}`);
    }
  }
  return 0;
}

module.exports = { bundleDir, listBundle, PATH_TEXT, main };

if (require.main === module) {
  process.exit(main());
}
