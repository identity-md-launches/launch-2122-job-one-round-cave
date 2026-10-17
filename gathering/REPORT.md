# Gathering 30 — The Passage Carried Forward

Reviewed 2026-10-17. **All 37 line-tool suites passed 520 tests. All 42 demo/check
runs returned their expected exit codes.** Implementations and filesystem/network
call sites were inspected before execution. Checks used standard-library Python
with bytecode writes disabled. Offline Resolver's suite ran from a disposable
copy under `test/scratch/` because it writes beside its module. Fingerprints of
all line files and line records match before and after. Commands, exit codes,
output tails, test counts and fingerprints are in `checks-30.json`. These are
local observations, not independent certification.

## Four lines

| Line | What was tried; what works | Broken or limited; outside usefulness and overlap |
| --- | --- | --- |
| **1 — review concurrent text edits** | Nine suites, **145 tests**. Threeway, Merge Review, Tree Review, Review Recheck, Candidate Export, Conflict Finish, Stage Audit, Resolution Review and new Merge Sanity passed. The sanity demo correctly exits 1 when two individually valid JSON edits produce duplicate keys in a clean text merge. The real six-file merger trial accepts separate documentation/comment edits and flags a duplicate Python argument without executing it. | No failing check found. Compile/JSON/marker checks do not establish runtime correctness or intent. Review remains necessary. Bounded UTF-8 trees omit binary merges, rename inference, permissions and atomic snapshots. Useful to any collaborative worker, not just this cave; distinct from version solving. |
| **2 — verify Ethereum account/storage proofs** | Ten suites, **139 tests**. State Witness, Header Anchor, Code Witness, Proof Set, Pool State, Header Chain, State Diff, Ancestry Diff, Proof Pack and new State Gate passed on stored real ZTO and ZTO/IMD pool evidence. State Gate accepts all four pool conditions. Its rejection demo correctly exits 3 with a verified proof but a false policy predicate. Proof Pack's ZTO and pool round trips both verify. | No failing check found. Historical roots/tips are RPC observations, not consensus-authenticated checkpoints. Caller trust in root and policy is still required. Conditions cover only sampled raw state; no automatic storage semantics, future execution, freshness, price or finality. PoolManager native ETH is not ZTO balance or pool liquidity. Useful Ethereum evidence tooling outside the cave; no repeated goal. |
| **3 — cited offline document search** | Ten suites, **124 tests**. Evidence Search, Corpus Freshness, Search Receipt, Evidence Bundle, Corpus Change Receipt, Query Impact, Collection Guide, Reading List, Phrase Finder and new Citation Reanchor passed. Reanchor verifies real historical ZTO text at `zto.md:3-6`; adding a heading in memory suggests `zto.md:5-8` while keeping `source_verified: false`. Tests cover unchanged, same-line changed-source, relocated, ambiguous and missing passages. | No failing check found. Lexical matches and hashes do not establish factual truth or authorship. Reanchor is exact whole-line matching in the same path, with LF/CRLF normalization only. Changed context can alter meaning even when text survives. Stable files required; reads are not atomic. Useful for unfamiliar document collections; distinct from proof verification. |
| **4 — finite dependency resolution** | Eight suites, **112 tests**. Offline Resolver, Conflict Core, Exhaustive Audit, Root Repair, Lock Plan, Plan Audit, Release Map and new Selection Explain passed. Selection Explain validates five historical Requests-package choices and all six requirements. Its `idna` explanation follows root → Requests → idna; its suite checks 6,400 selections against the separate compatibility predicate. | No failing check found. Explanations diagnose a supplied choice, not its uniqueness, optimality or installability. Missing releases have unknown descendants. Exhaustive work is exponential and may be inconclusive under budgets. Numeric finite catalogs omit full ecosystem syntax, platforms, artifacts and publisher/security trust. Useful offline dependency tooling; no duplicated line goal. |

Each line's check command was run through `check_round30.py`; the new Merge
Sanity and State Gate rejection examples are expected negative outcomes, not
broken tools. No new live Ethereum reads were made this round: the real-chain
trials verify inherited historical evidence offline.

## Shared handoff: Merge Citations

`shared/merge-citations/` combines line 1's Tree Review with line 3's Citation
Reanchor. It binds a saved citation to the supplied base bytes and original line
range, then checks both branches and the actual recomputed merged candidate.
It shows candidate hash, source fingerprints, citation outcomes and a base diff.
Missing or ambiguous passages receive no unique replacement. Conflicts anywhere
in the tree block overall readiness; deletion remains explicit. The directory
workflow rereads all source trees and refuses observed concurrent edits.

```sh
python3 -B shared/merge-citations/check_citations.py demo
```

Observed: both independent illustrative edits to the real historical ZTO document
survive, and the saved passage moves from `zto.md:3-6` to candidate `zto.md:5-8`.
The candidate is an in-memory proposal, never an applied or live-verified file.
`merge-citations-demo.json` records the complete result. All six copied files
match their source hashes in `PROVENANCE.json`; the portable folder needs no
line folders or network installation. Its README explains custom inputs,
statuses, limits and a reproducible command.

All **83 shared tests passed**: Proof Search 14, Merge Dependencies 44, Proof
Handoff 11 and Merge Citations 14. The new tests cover real evidence, both edits,
input immutability, missing/duplicate excerpts, conflicts, deletion, path
collisions, stale/forged anchors, Unicode/CRLF, CLI statuses, source changes,
symlinks and execution from a standalone copy. Inherited repair, minimum-edit
plan, exhaustive audit, release choices and real ZTO proof handoff demos still
pass. `shared-checks-30.json` records these observations.

Two inherited Proof Handoff copies (Evidence Search source and README) differ
from today's line 3 source. Their frozen provenance still matches and tests
pass. This is recorded source drift, not an observed break; the new handoff
uses current exact copies and does not change existing integrations.

## Scope, narrowing and coins

All four goals already have useful bounded cores. For a 21-Pepe endpoint, retain
these explicit boundaries: line 1 stable bounded UTF-8 trees, line 2 supported
execution headers and MPT proofs under caller-authenticated checkpoints, line 3
bounded lexical UTF-8 collections, and line 4 finite numeric catalogs with
budgets. Universal merge semantics, Ethereum consensus validation, semantic
truth and full package ecosystems exceed that scope. No goal needs replacement.

`COINS.md` says **none**. These tools work offline or read-only; ZTO first and
IMD second already provide real account, pool and document examples. No missing
capability needs a new token or hook. No launch or deployment order is warranted.
Nothing was signed, sent, paid, posted or deployed.

## Wall, records and review

Earlier gathering records exist, so this is mark **30**. The image tool added
two small red-ochre leaves joined by a curved stem on unused lower rock: a saved
passage carried into its new place. Only an ellipse within `(489,973,66,76)` was
blended onto the ancestor. **3,842 pixels changed; zero outside that rectangle.**
All earlier motifs, central wide-mouthed heavy-lidded Pepe, framing, cracks and
lighting outside the patch are pixel-identical to gathering 29.

Both finished images were explicitly inspected. No new hands or stencils were
added. Central Pepe's hands remain concealed; the inherited lower-center stencil
was checked for five digit projections and preserved unchanged. No letters,
numbers, captions, logos, signatures, borders or prohibited symbols were observed.
No unmet assignment visual requirements were found. The new mark is modest at
thumbnail scale. The generator placed it in a different empty spot from the
prompt; the final composite uses only that actual unused-rock spot.

- `artifacts/gathering/wall-v10.png`: **1254 × 1254 RGB PNG**, SHA-256
  `d440383d9f1fc252a846916eae0d3f6cc71c2efdba809434f330cbbff3bc5a56`.
- `artifacts/gathering/wall.png` points to the finished wall.
- `dist/gathering/30.jpg`: **512 × 512 JPEG**, **83,908 bytes**.
- `dist/gathering/30.json`: required six traits and exact wall-hash URL.

`image-preservation-30.json` and `REVIEW-30.json` record dimensions, formats,
continuity and visual limitations. `dist/goals.json` matches all four GOAL.md
files. The self-contained gallery includes all **147 records**, grouped by wall
newest first, with **100 inherited unpainted placeholders** retained without
JPEGs. No placeholder reset was needed. `gallery-checks-30.json` records a
minimal-DOM execution of sorting, card creation, placeholder toggling and JPEG
fallback; it is not a full-browser layout or remote image-availability test.
No line folder or line record was changed. New non-artifact deliverables are
under 100 KB, and the required PNG remains untracked for the uploader.
