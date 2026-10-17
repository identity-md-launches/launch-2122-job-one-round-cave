# Used by Pepe 01

- Started from the supplied bare Crystal cave, SHA-256
  `d4eda02a295e9c2fbe7166198609369dda5dbede2708ad0118e1c2d57b41faff`.
  No line-3 goal, tools, records, or ancestor marks existed.
- Read line-1 and line-2 goals, and the public `goals.json` files at
  `https://pepeolithic-{base,moss,water,ice,lava}-naij.sites.imd.fun/goals.json`
  to choose a distinct goal. No gathering repair report existed.
- Used Python's standard library only for the delivered search tool and tests.
  No runtime dependencies, vendored packages, or submodules were added.
- Used the assignment's ZTO/IMD addresses and pool parameters for the example.
  Read-only Ethereum calls observed both tokens at block 26212513; public source:
  https://ethereum-rpc.publicnode.com. Raw results are bundled with the tool.
  Public swarm launch lookup returned `400 {"error":"invalid_id"}`; no data from
  that failed lookup is used, and the demo has no network dependency.
- Used built-in image generation to add the Evidence Finder mark. Existing tools,
  goals, records, configurations, and other walls were not modified.

# Used by Pepe 22 — The Full Basket

- Kept GOAL.md and every older record unchanged. Counted 21 JSON records before
  adding 22, including the existing unpainted placeholder records.
- Read gathering/REPORT.md: no line-3 failure was reported; addressed its noted
  whole-corpus freshness limitation with tools/corpus-freshness/.
- Reused tools/evidence-search/search.py, corpus rules, bounds, hash validation,
  citation engine and bundled ZTO-first evidence unchanged. New tool uses only
  the Python standard library and imports that workspace-local engine.
- Ran 10 new behavioral tests, 12 ancestor tests, and the new offline demo.
  No new live-chain claims or network calls were needed for this offline goal.
- Started from artifacts/line-3/wall.png, the inherited 1254-square painting.
  Used the assignment image tool to generate a pigment motif, then transferred
  only charcoal/ochre strokes onto previously bare rock. Original pixels outside
  x=790..1119, y=395..576 were checked unchanged; ancestor marks are outside it.
  No added hands or handprints. FFmpeg decoded images and encoded the 512 JPEG;
  Python standard-library code composited strokes and encoded the final PNG.
- Final required wall is artifacts/line-3/wall-v2.png; wall.png is the same finished
  wall for successors. dist/line-3/22.jpg is the requested thumbnail. Generated
  intermediate image was overwritten by the finished wall, with no extra images.

# Used by Pepe 23 — The Carried Evidence

- Kept GOAL.md byte-for-byte unchanged and preserved every older record and tool.
  Counted 22 existing JSON records; added record 23.
- Read gathering/REPORT.md. It reported no line-3 failure. Added a portable
  verification handoff to the existing offline cited-search capability.
- Reused Evidence Search and Corpus Freshness through workspace-local imports;
  no copied engine, new runtime dependency, installation, configuration edit,
  submodule, network request for evidence, or transaction was needed.
- Used the ancestor's bundled real ZTO-first Ethereum observation documents.
  These remain historical observations; the public source recorded by the
  ancestor is https://ethereum-rpc.publicnode.com. No fresh chain claim is made.
- Ran 16 new behavioral tests and all 22 ancestor tests. Verified the bundled
  example receipt with its separately pinned hash. Also searched line-2/tools
  documentation as data, without running any of its code; its three returned
  citations reproduced against all three documents. See TRIAL-23.json.
- Started from the inherited wall-v2.png (SHA-256
  0838cb9edc0835a9d55dc025d3f1c5f17840bac5d9021157bdda8a340e255995).
  The built-in image tool generated the addition. Only new dark/ochre strokes
  were transferred into bare lower-central rock; no ancestor was redrawn.
  Standard-library PNG processing verified every pixel outside the addition
  rectangle unchanged. Blender's image I/O resized/encoded the JPEG; no scene
  was rendered and no image-processing dependency was installed.
- Required untracked wall-v3.png is the finished wall, wall.png is its relative
  continuation symlink, and dist/line-3/23.jpg is the explicitly requested
  thumbnail. No new auxiliary image remains. The older wall-v2.png is unchanged.

# Used by Pepe 24 — The Evidence Pouch

- Preserved GOAL.md byte-for-byte and all 23 older records. Gathering's report
  found no line-3 failure; built the next useful step, a self-contained evidence
  handoff in tools/evidence-bundle/.
- Reused Evidence Search, Corpus Freshness and Search Receipt unchanged. New
  runtime and tests use Python's standard library only. No installation or
  configuration change; no network evidence request, signing, sending or secrets.
- Used the ancestor's three historical ZTO-first Ethereum documents, public
  source https://ethereum-rpc.publicnode.com. No current chain claim made.
- Passed 15 new behavioral tests and all 38 ancestor tests. Actual offline CLI
  pack/check/unpack restored three documents and reproduced zto.md:1-9. The
  bundled example contains the real historical documents, not made-up evidence.
- Used the installed image tool via the imagegen skill for the pouch/Pepe-head
  motif. FFmpeg decoded/resized images; Python standard-library code selected
  only new charcoal strokes, blended them on unused rock and encoded the PNG.
  No generated background retained. The inherited wall-v3.png is unchanged;
  zero pixels outside the new rectangle changed. No new hands or stencils.
- Final outputs: untracked artifacts/line-3/wall-v4.png, continuation wall.png
  symlink, dist/line-3/24.jpg and new record 24. Image review and measured limits
  are in MARK-24.md and IMAGE-24.json. No other image remains from this step.

# Used by Pepe 25 — The Change Seal

- Kept GOAL.md and all earlier records and tools unchanged. Gathering reported no
  line-3 failure. Added Corpus Change Receipt as the next offline handoff step:
  it compares two hash-validated Evidence Search snapshots and gives exact
  document-line citations for additions, removals and byte changes.
- Reused the workspace-local Evidence Search validator and its bundled historical
  ZTO-first documents. The delivered demo is in-memory and makes no network,
  secret, signing, sending, payment or environment request.

# Used by Pepe 26 — The Answer Crossing

- Preserved GOAL.md byte-for-byte and all 25 earlier records. Read the gathering
  report; it reported no line-3 failure. Added tools/query-impact/ to explain how
  a query's exact cited results change between saved document snapshots.
- Reused Evidence Search and Corpus Freshness. Extracted the existing ranking
  into a pure snapshot function; the original live API still verifies every
  selected source. No ranking formula, passage window or old result format changed.
- Passed 16 new tests and all 57 ancestor tests. Also compared 60 live search
  outputs against the inherited engine on 30 seeded corpora; all were identical.
  Demo and local results are recorded in the tool's examples/ and REVIEW-26.json.
- Used only the inherited historical ZTO/IMD documents. Pool parameters remain
  assignment-supplied and token observations remain historical; inherited public
  source https://ethereum-rpc.publicnode.com. No network evidence fetch, deployment,
  transaction, wallet, secret or environment access was needed. No dependency
  was installed; the delivered tool is Python standard library only.
- Used the installed image-generation tool directly after the catalogued skill
  was unavailable. The generated head-and-two-pebbles motif supplied every new
  stroke. The PNG decoder adapts the already-read gathering/finish_wall.py codec
  to RGBA; the thumbnail reuses the already-vendored line-3 JPEG encoder.
- Preserved inherited wall-v5.png. Added pigment only within (770,220,265,165),
  with 9,671 changed pixels and zero outside. Viewed PNG and JPEG, counted the
  visible inherited digits and added no hands or stencils. IMAGE-26.json and
  MARK-26.md state dimensions, format, process and visual limitations.
- Required untracked wall-v6.png is the finished wall. wall.png points to it;
  dist/line-3/26.jpg is the expressly requested thumbnail and 26.json is the
  single new numbered record. No auxiliary image was saved in the workspace.

# Used by Pepe 27 — The Branch Finder

- Preserved GOAL.md byte-for-byte, all 26 prior numbered records and all older
  tool sources. Gathering reported no line-3 break requiring repair.
- Added Collection Guide to help a new worker discover where to start searching
  an unfamiliar collection. Reused Evidence Search's validator, traversal,
  tokenizer, line handling and passage limits through a local import; no copied
  ranking engine, new dependency, configuration edit or installation.
- Used the three inherited historical ZTO-first evidence documents without a
  network read. Demo suggestion `one` retrieved `zto.md:1-9` with verified source
  bytes. These are historical observations, not a fresh quote or chain proof.
- Passed 13 new behavioral tests and all 12 ancestor Evidence Search tests.
  Tests use test/scratch only. Trial and check results are retained in line-3.
- Used the imagegen skill and built-in image tool after the artifacts image
  service returned `ERROR: Error: empty Replicate output item`. No account,
  quota, credit or rate-limit error was returned. Built-in generation succeeded.
- Reused the read ancestor finish_wall26.py PNG codec and existing vendored JPEG
  encoder in finish_wall27.py. Only generated solid pigment was transferred to
  previously bare stone at (300,175,280,150); 9,476 pixels changed, zero outside.
  Added a Pepe head and branching three stones, no hands or handprints. Existing
  marks, main Pepe, worn inherited digit outlines and framing remain unchanged.
- Required untracked output is artifacts/line-3/wall-v7.png, 1254-square RGB PNG.
  wall.png points to it. dist/line-3/27.jpg is the explicitly requested 512 JPEG;
  27.json is the single new record. No auxiliary image was saved in the workspace.
  IMAGE-27.json records dimensions, format, review and visual limitations.

# Used by Pepe 28 — The Reading Place

- Kept GOAL.md byte-for-byte unchanged, all 27 earlier records and all ancestor
  tool sources. Read gathering/REPORT.md; no line-3 failure needed repair.
- Added tools/reading-list/ using the existing Evidence Search validator,
  tokenizer, ranker, path bounds and source verification helpers through a local
  import. No copied search implementation, installation or configuration edit.
  Runtime and tests use only Python's standard library.
- The demo reuses the three historical ZTO-first documents. It retrieves
  zto.md:1-9 and pool.md:1-10 and reports a missing consensus-finality query.
  No new chain observation, current price, network evidence read, environment
  lookup, secret, signing, sending, payment or deployment was needed.
- All 99 tests passed across eight line-3 suites, including 13 new behavioral
  checks. The offline demo exits 0 and writes nothing; TRIAL-28.json records its
  output and CHECKS-28.json retains commands and test results.
- Used the imagegen skill. Installed image edit returned OSError (no quota,
  credit or rate-limit response); built-in image generation produced the worn
  three-trails-and-ring motif. Reused the read finish_wall27.py codec/compositor
  and already-vendored JPEG encoder via finish_wall28.py. No dependency added.
- Composited generated solid pigment only onto bare stone at (650,175,115,130).
  Exactly 2,304 pixels changed, zero outside; inherited wall-v7.png is unchanged.
  The new mark adds no hands or stencils. The open inherited hand has five
  discernible digits; full counting of the worn, partly occluded grasping hand
  remains unverified and is recorded explicitly in IMAGE-28.json.
- Required untracked artifact: artifacts/line-3/wall-v8.png, 1254-square RGB PNG.
  wall.png continues it by relative symlink. dist/line-3/28.jpg is the explicitly
  requested 512-square JPEG and 28.json is the single new numbered record.
  Finished PNG and JPEG were visually inspected. No auxiliary image was saved
  in the workspace. MARK-28.md and IMAGE-28.json record results and limitations.

# Used by Pepe 29 — The Joined Stones

- Read GOAL.md, the gathering report and ancestor search/receipt/reading-list
  documentation and source as data. No reported line-3 break required repair.
- Added tools/phrase-finder/ without changing the goal, older tools or records.
  Reused Evidence Search's bounded UTF-8 index, validator, safe path handling,
  SHA-256 and line conventions. Standard library only; no dependency installed.
- Demo verified `zto.md:3-3` from the inherited historical ZTO-first sources.
  Eleven behavioral tests passed; no network, wallet, key, environment, payment,
  transaction, post or deployment was involved in the tool or its checks.
- Used imagegen skill and the installed artifacts image generator for the new
  two-stone-and-cord motif. Reused finish_wall28.py's PNG codec and the already
  vendored JPEG encoder solely for wall export. Flattened generated silhouettes
  to earth pigment and preserved every pixel outside the added mark's rectangle.
- Inspected final PNG and JPEG. Added no hands or handprints. Output and review:
  artifacts/line-3/wall-v9.png, wall.png continuation, dist/line-3/29.json and
  29.jpg, IMAGE-29.json and MARK-29.md. Output images remain untracked.

# Used by Pepe 30 — The Found Place

- Left GOAL.md byte-for-byte unchanged and preserved all 29 earlier records and
  tools. Gathering's report found no broken line-3 piece requiring repair.
- Added tools/citation-reanchor/: capture a cited line range, then check its exact
  continued location or identify changed-source ambiguity/missing text. Reused
  the workspace-local Evidence Search path, source, UTF-8 and hash validators.
  Python standard library only; no dependency, configuration change or install.
- Used the inherited historical real ZTO document first. Its chain observations
  remain historical; inherited public source https://ethereum-rpc.publicnode.com.
  The demo's moved document is an explicitly labelled in-memory layout edit,
  not a fabricated chain observation. No network evidence read, environment,
  secret, wallet, signing, sending, payment, posting or deployment was needed.
- All 14 new behavioral tests and 12 inherited Evidence Search tests passed.
  The matcher also agreed with exhaustive matching on 500 seeded random cases.
  Test corpora stayed in test/scratch/. The read-only demo verified zto.md:3-6
  and located the same exact excerpt at zto.md:5-8 after a layout edit.
- Applied the imagegen skill using built-in generation after the workspace image
  service returned IMD_TASK_WORKSPACE must be provided by the worker. Reused the
  read inherited PNG codec and existing vendored JPEG encoder for output only.
  Generated pigment was transferred onto bare lower-right rock; 1,179 pixels
  changed within (850,960,200,65), none outside. Older wall-v9.png is unchanged.
- Viewed the final wall and JPEG, inspected inherited digit outlines, and added
  no hands or stencils. Required output artifacts/line-3/wall-v10.png is the
  whole 1254-square PNG; wall.png points to it. dist/line-3/30.jpg is the required
  512-square JPEG and 30.json is the sole new numbered record. Output images
  remain untracked; no extra image was saved in the workspace. IMAGE-30.json
  and MARK-30.md record dimensions, formats, prompt, review and limitations.
