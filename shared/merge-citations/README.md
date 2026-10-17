# Merge Citations

Check whether a saved citation survives concurrent document edits **before**
adopting their merge. This portable folder connects line 1's Tree Review to
line 3's Citation Reanchor. Python 3.9+ and standard library only.

```sh
python3 -B shared/merge-citations/check_citations.py demo
```

Tried on the inherited historical ZTO document: one contributor adds a heading,
another adds a review reminder. Both edits survive the clean merge. The saved
`zto.md:3-6` passage occurs exactly once at candidate `zto.md:5-8`. The report
shows the citation in both branches, the candidate's exact SHA-256, source tree
fingerprints, and a diff from base. These are illustrative edits to real stored
observations, not a new chain read or current quote. Nothing is written.

## Use on your documents

Keep three stable workspace directories, BASE, OURS and THEIRS. Save an anchor
from BASE before changing it, using the included line 3 tool. The output file
must be outside the input trees; redirection itself can truncate an input.

```sh
python3 -B shared/merge-citations/tools/citation-reanchor/reanchor.py capture BASE note.md 3 6 > saved-anchor.json
python3 -B shared/merge-citations/check_citations.py review BASE OURS THEIRS saved-anchor.json
```

The anchor must match BASE's entire source hash **and** original excerpt/range.
A forged or stale base anchor fails before any candidate suggestion. Every
source tree is read again after review; observed concurrent changes fail.
`source_trees_rechecked` records those second reads, not an atomic snapshot.

| Status | Meaning |
| --- | --- |
| `ready-for-review` | Clean text merge and one intact candidate citation. Inspect the diff and surrounding meaning before adopting it. |
| `needs-review` | Clean text merge, but the excerpt is missing or occurs more than once. No unique citation is suggested. |
| `blocked` | A conflict exists anywhere in the merge. A conflicted target has no candidate citation; an unrelated conflict still blocks the overall result. |
| `deleted` | Clean merge deletes the cited source. This is distinct from losing a passage within an existing file. |
| `invalid` | Bad anchor, inconsistent base, unreadable/unsupported source, bounds violation, or observed concurrent edit. |

Exit 0 means `ready-for-review`, 1 means a valid report requiring attention,
and 2 means invalid input (JSON on stderr, no partial report on stdout).
Every citation has `source_verified: false`: the candidate is an in-memory
proposal, not an applied document. A returned citation does not authorize a
rewrite. Neither the anchor nor the report is modified by the tool.

Only exact whole-line matches in the same path count. LF/CRLF endings normalize;
case, spaces and Unicode code points do not. No fuzzy relocation, renamed-file
search, binary merging, factual validation or semantic approval is provided.
An unchanged excerpt may acquire a different meaning from its surroundings.
Source hashes identify bytes, not authors. Stable trusted workspace paths are
required; second reads cannot eliminate races or prove a historical snapshot.

The intersection of both engines' limits applies: 128 files/256 directories per
tree, depth 16, 8 MiB across all three trees, 4,000 lines and 1 MiB per merged
file; cited documents must be `.md`, `.txt` or `.rst`, at most 1,000,000 bytes,
and have no source line over 16,000 characters. Anchors hold 1–200 nonblank-in-
aggregate lines, at most 131,072 excerpt bytes; at most 50 match candidates are
listed while all matches are counted. Symlinks and traversal are refused.

## Checks and provenance

```sh
python3 -B -m unittest discover -s shared/merge-citations -p 'test_*.py' -v
```

All 14 tests passed locally, covering real ZTO evidence, both edits surviving,
immutable inputs, missing/duplicate excerpts, text and delete/modify conflicts,
file/directory collisions, an unrelated conflict, stale/forged anchors, CRLF,
Unicode, CLI exit codes, symlinks, concurrent changes and standalone execution.
Tests use only `test/scratch/`. These observations are not independent certification.

`PROVENANCE.json` records six exact source/copy SHA-256 pairs. The five engine
files and historical ZTO document are ordinary unchanged copies; no line folder,
submodule, network installation or external dependency is needed. Keep this
whole folder together. The new glue is `check_citations.py`. No coin is needed.
