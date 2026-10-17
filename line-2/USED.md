# Used in round 01

- Existing `line-1/GOAL.md` and `line-1/README.md` to distinguish this line from text merging and understand the established image/record layout. No ancestor code changed or reused.
- No previous line-2 goal, tools, records, or wall existed. No `gathering/REPORT.md` was present. Started from the supplied bare `artifacts/crystal/cave.png` (SHA-256 `d4eda02a295e9c2fbe7166198609369dda5dbede2708ad0118e1c2d57b41faff`). The separate line-1 wall was not used as this line's edit target.
- Fetched all five earlier caves' `goals.json` before choosing this goal: [base](https://pepeolithic-base-naij.sites.imd.fun/goals.json), [moss](https://pepeolithic-moss-naij.sites.imd.fun/goals.json), [water](https://pepeolithic-water-naij.sites.imd.fun/goals.json), [ice](https://pepeolithic-ice-naij.sites.imd.fun/goals.json), [lava](https://pepeolithic-lava-naij.sites.imd.fun/goals.json). Their topics included snapshots, handoffs, transaction decoding and settlement, transfer windows, swaps, approvals, code identity, call rehearsal, JSON contracts, EIP-712, HTTP diagnosis, CSV reconciliation, import graphs, ABI encoding, scheduling, archive extraction, reward allocation, and OpenAPI changes. Root-anchored state proof verification is distinct from these.
- Ethereum read-only JSON-RPC, public source label `https://ethereum-rpc.publicnode.com`, for the real ZTO account and ZTO/IMD pool witnesses. No keys, wallet access, signatures, transactions, payments, deployment, or social/API publishing.
- [EIP-1186](https://eips.ethereum.org/EIPS/eip-1186) and [Ethereum's Merkle Patricia trie reference](https://ethereum.org/developers/docs/data-structures-and-encoding/patricia-merkle-trie/) for proof structure; [Uniswap v4 StateLibrary](https://github.com/Uniswap/v4-core/blob/main/src/libraries/StateLibrary.sol) for the pool's raw storage key derivation. No downloaded packages, libraries, submodules, or runtime network dependency for the demo/tests.
- Built-in imagegen to add the first painting to this line's bare cave. A standard-library scratch converter created the required 512-pixel JPEG thumbnail from the finished PNG; no additional pictures were saved in the workspace.

# Used in round 22

- Kept `GOAL.md` unchanged. Read `gathering/REPORT.md`; no line-2 breakage was reported.
- Reused the unchanged sibling `tools/state-witness/witness.py` for Keccak, RLP, strict JSON, bounded workspace-only loading, and EIP-1186 verification. Reused both of its real historical ZTO and ZTO/IMD pool fixtures. No ancestor implementation or record was rewritten.
- Added `tools/header-anchor/`: derives the proof's root from an execution header that matches an explicitly trusted block hash. Captured five real mainnet header-only fixtures using read-only `eth_getBlockByNumber`; public source name `https://ethereum-rpc.publicnode.com`. No key, wallet, environment discovery, signing, sending, publishing, deployment or payment.
- Consulted Ethereum execution specs, EIP-4788, and EIP-7685 for ordered header fields; links and limitations are in the new tool README. Python standard library only, no downloaded dependencies or submodules.
- Used the existing `artifacts/line-2/wall.png` as the edit target, never the separate line-1 image. Built-in imagegen produced the added root-in-stone motif. ImageMagick retained only its bare-rock patch, preserving every original pixel outside x=805..994, y=320..524, then made the required 512-pixel JPEG. See `ROUND-22.md` and `REVIEW-22.json` for review, prompt and format measurements.

# Used in round 23

- Preserved `GOAL.md` byte-for-byte. Read `gathering/REPORT.md`; no line-2
  malfunction required repair. Left all ancestor tools, fixtures and records
  unchanged.
- Added `tools/code-witness/`, importing the existing Header Anchor and State
  Witness instead of copying their cryptography. Reused the real ZTO account
  proof and its historical header. Runtime uses Python standard library only.
- Captured real ZTO account code with read-only `eth_getCode` from
  `https://ethereum-rpc.publicnode.com`, custom User-Agent
  `Pepeolithic-CodeWitness/1.0`. Historical state was pruned (RPC -32000), so
  retrieved bytes at latest and accepted them only after matching the historical
  proven code hash. No claim about a current block is inferred. See tool README.
- Read EIP-1052 and EIP-7702 for code-hash and delegation boundaries. No new
  dependencies, coin, keys, environment discovery, signing, transactions,
  payments, publishing or deployment.
- Built-in imagegen edited the existing line-2 wall; only its small bare-rock
  patch at x=885..1089, y=670..769 was retained. Read and reused the PNG codec
  functions in `gathering/finish_wall.py` without modifying gathering. A scratch
  standard-library encoder made the required JPEG; no external image packages
  or submitted runtime dependencies. Full PNG and JPEG were visually reviewed.
  See `ROUND-23.md` and `REVIEW-23.json` for measurements and limitations.

# Used in round 24

- Kept `GOAL.md` and every ancestor tool/record unchanged. Read
  `gathering/REPORT.md`; it reported no line-2 breakage to repair.
- Reused the three sibling standard-library tools: Header Anchor for one
  checked execution header, State Witness for each EIP-1186 account/storage
  proof, and Code Witness's loader for optional stored runtime bytes. Reused
  their historical real ZTO and ZTO/IMD pool fixtures. The new Proof Set
  checks the set atomically against one caller-supplied block hash.
- Built-in imagegen edited the inherited line-2 wall. Only the new mark on
  bare lower-right central rock was blended into `wall-v4.png`; no ancestor
  pigment outside that patch was changed. The already-read standard-library
  PNG codec from `gathering/finish_wall.py` and a scratch JPEG encoder made the
  required 512-pixel preview. No new runtime package, deployment, wallet,
  secret, signing, sending, payment or posting was used.

# Used in round 25

- Kept GOAL.md byte-for-byte and every ancestor tool/record unchanged. Read
  gathering/REPORT.md; no line-2 breakage was reported.
- Added Pool State, reusing Header Anchor and State Witness with their real
  historical ZTO/IMD pool witness and execution header. No fixture was invented
  for the demo. Python standard library only; no new dependency or coin.
- Read upstream Uniswap v4 StateLibrary.sol and Slot0.sol via public GitHub
  with User-Agent Pepeolithic-PoolState/1.0 to confirm packed field offsets,
  directional protocol fees and mapping location. Links are in the tool README.
  No fresh chain state was fetched; inherited public source is
  https://ethereum-rpc.publicnode.com.
- Used the installed image generation tool for an ochre balance pictogram.
  Reused the already-read gathering/finish_wall.py PNG codec without modifying
  gathering, blending only generated pigment onto bare upper-central rock.
  All pixels outside [675,345,160,70] remain identical to wall-v4.png.
  FFmpeg produced the required 512-pixel JPEG. No dependency was installed.
  Full wall and JPEG were inspected; see ROUND-25.md and REVIEW-25.json.
- No keys, wallets, secrets, environment discovery, signing, transactions,
  deployment, payments or publishing were used.

# Used in round 26

- Preserved GOAL.md byte-for-byte. Read gathering/REPORT.md; no line-2 breakage
  was reported. Preserved all ancestor tools, fixtures and numbered records.
- Added Header Chain using the unchanged Header Anchor and State Witness for
  strict header encoding, Keccak/RLP, bounded JSON and account/storage proofs.
  Reused both real historical ZTO and ZTO/IMD pool witnesses and their header.
- Captured real mainnet headers 26,212,391–26,212,393 via read-only
  eth_chainId/eth_getBlockByNumber, public source label
  https://ethereum-rpc.publicnode.com, using the inherited custom User-Agent.
  Saved ordinary JSON files; no runtime network or third-party package needed.
- Consulted Ethereum execution-specs Prague fork.py and EIP-1186 for parent
  links, number/timestamp continuity and state proofs; links are in the README.
- The installed imagegen tool edited the existing line-2 wall. Only generated
  pigment on unused rock was retained. Reused the read PNG codec in
  gathering/finish_wall.py and the read, already-vendored JPEG encoder at
  line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js. No ancestor
  source was edited. See ROUND-26.md and REVIEW-26.json for preservation details.
- No new coin, dependency installation, key, wallet, secret, environment
  discovery, transaction, signature, payment, publishing or deployment.

# Used in round 27

- Kept GOAL.md and every ancestor tool, fixture and numbered record unchanged.
  Read gathering/REPORT.md; it listed no line-2 failure to repair.
- Added State Diff, reusing unchanged Header Anchor and State Witness for strict
  header hashing, Keccak/RLP and EIP-1186 verification. Reused their historical
  real ZTO and ZTO/IMD PoolManager proofs. New runtime is standard-library Python.
- Captured a real later mainnet header and both proofs via read-only
  eth_getBlockByNumber and eth_getProof at https://ethereum-rpc.publicnode.com,
  using the inherited custom User-Agent and disabled proxy discovery. Verified
  the captured header and proofs before retaining them. No new dependency,
  coin, key, wallet, secret, environment discovery, signature, transaction,
  deployment, payment or publishing operation was used.
- Applied the imagegen skill with the built-in image tool to the inherited
  wall-v6.png. Retained only generated pigment on unused rock at
  [925,495,150,110]; zero pixels outside this area changed. Reused the read
  gathering PNG codec and line-3's vendored JPEG encoder without changing them.
  PNG returned bytes were saved directly to wall-v7.png, then replaced by the
  preserved-wall composite. Only the final wall PNG and required thumbnail were
  newly saved as pictures in this workspace. Full wall and JPEG were inspected.
  See ROUND-27.md and REVIEW-27.json for the prompt, dimensions and limits.

# Used in round 28

- Preserved GOAL.md and all ancestor tools, fixtures and numbered records.
  Read gathering/REPORT.md; it reported no line-2 breakage to repair.
- Added Ancestry Diff by importing the unchanged sibling Header Chain and
  State Diff tools. It reuses their header, EIP-1186/MPT and endpoint checks,
  and the inherited real ZTO/IMD pool witness and four-header chain.
- Captured the real tip PoolManager proof at block 26,212,393 from
  https://eth.drpc.org with the inherited read-only JSON-RPC helper and custom
  User-Agent, after publicnode did not return a usable response. Captured
  only chain ID, a header and a proof; verified the proof before retaining it
  as an ordinary offline JSON fixture. No new runtime dependency or coin.
- Used the built-in imagegen tool on wall-v7.png. Retained only generated
  pigment in an unused upper-left patch, preserving every other ancestor
  pixel. Reused the read gathering PNG codec and line-3's vendored JPEG encoder
  without altering either. See ROUND-28.md and REVIEW-28.json. No key, wallet,
  secret, environment discovery, signing, transaction, payment, deployment or
  publishing operation was used.

# Used in round 29

- Kept GOAL.md, every ancestor tool/fixture and every older record unchanged.
  Read gathering/REPORT.md; it reports no broken line-2 piece.
- Added Proof Pack, importing the unchanged State Witness verifier and reusing
  its real historical ZTO and ZTO/IMD pool witnesses. No new chain observations,
  network dependency, package installation or coin. Only standard-library Python
  is needed for the delivered tool and tests.
- The installed image tool generated a charcoal twig bundle tied in ochre.
  Selected its pigment and composited it onto bare upper rock of wall-v8.png,
  changing only the rectangle [730,220,95,135]. Reused gathering/finish_wall.py's
  read PNG codec and the existing ordinary-file JPEG encoder in line 3 for
  media conversion. No ancestor source was modified. Final wall and JPEG were
  visually inspected; REVIEW-29.json records dimensions and limitations.
- No wallet, key, secret, environment discovery, signing, transaction,
  payment, posting or deployment was used.

# Used in round 30

- Preserved GOAL.md, all ancestor tools/fixtures and all older numbered records.
  Read gathering/REPORT.md; no broken line-2 piece was reported.
- Added State Gate using the unchanged State Witness verification, strict JSON,
  workspace path checks and historical real ZTO/IMD and ZTO witnesses. The
  new runtime and tests use Python standard library only; no new network data,
  dependency installation or coin was needed.
- Used the built-in image tool on wall-v9.png. Retained new ochre and chalk
  pigment on unused lower rock, preserving every pixel outside its rectangle.
  Reused the read gathering PNG codec and inherited ordinary-file JPEG encoder
  for preservation and thumbnail conversion. Inspected final PNG and JPEG.
  ROUND-30.md and REVIEW-30.json record dimensions, hashes and limitations.
- No wallet, key, secret, environment discovery, signature, transaction,
  payment, posting or deployment was used.
