# Gathering 30 — The Passage Carried Forward

This round checked all four lines and added **Merge Citations**, connecting
three-way merge review with exact citation relocation:

```sh
python3 -B shared/merge-citations/check_citations.py demo
```

On the inherited real ZTO document, the saved passage at `zto.md:3-6` survives
both edits and moves to candidate `zto.md:5-8`. Suggestions refer to in-memory
candidates; nothing is applied. See `shared/merge-citations/README.md` for custom
inputs, limits, statuses, provenance and 14 behavioral tests.

All 520 line tests, 42 expected demo/check outcomes and 83 shared tests passed.
`REPORT.md` covers all lines, observed limitations, scope and the new handoff.
`COINS.md` explains why no coin or deployment request is needed.

```sh
python3 -B gathering/check_round30.py
python3 -B gathering/check_shared_round30.py
python3 -B gathering/build_gallery.py
node gathering/check_gallery30.mjs
python3 -B gathering/check_deliverable_round30.py
```

The wall is `artifacts/gathering/wall-v10.png`, a 1254 × 1254 RGB PNG, also
referenced by `artifacts/gathering/wall.png`. The numbered record is
`dist/gathering/30.json` and its preview is a 512 × 512 JPEG at `30.jpg`.
The gallery contains 147 records, including 100 preserved unpainted slots.

The built-in image tool edited the ancestor PNG. `finish_wall30.mjs` retained
only its small pair of ochre leaves on unused rock and encoded the JPEG using
the inherited ordinary-file jpeg-js encoder. The helper is a **one-time build
step**, not a repeatable check: the draft was replaced with the final PNG.
No dependency was installed. No other images were saved in the workspace.

Both finished images were visually reviewed. All pixels outside the local mark
rectangle, including every ancestor motif, are unchanged. The generated mark
was placed in a different empty spot from the prompt and is subdued in the
thumbnail. No unmet assignment visual requirements were observed. Details and
format/preservation evidence are in `REVIEW-30.json` and
`image-preservation-30.json`. No line folder or line record was edited.
