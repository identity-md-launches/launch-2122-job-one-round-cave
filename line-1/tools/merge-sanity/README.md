# Merge Sanity

Find static faults that survive a clean text merge. This read-only Python 3.10+
standard-library tool recomputes the inherited three-way merge from three source
trees, then checks each available candidate for conflict-marker lines, Python
compile errors and strict JSON failures. It also checks the source versions, so
you can see when a candidate fails a check that **both branches passed**.
Keep the sibling `tree-review`, `merge-review` and `threeway` folders.

One command from the workspace root shows it working, including actual bounded
filesystem reads, unchanged-input checks and CLI status checks:

```sh
python3 -B line-1/tools/merge-sanity/test_sanity.py
```

Observed: **22 tests passed**. An explicit JSON nesting bound was added after a
test showed the interpreter could accept deeper JSON than expected. The final
tests cover the 128/129 nesting boundary, escaped brackets, duplicate nested
keys, non-finite literals, huge valid numbers, Python scope and argument errors,
CRLF/Unicode, no source execution, marker-location truncation, path collisions,
text conflicts, additions/deletions, symlinks, path escape and source immutability.

The short demo illustrates a dangerous clean merge:

```sh
python3 -B line-1/tools/merge-sanity/sanity.py --demo
```

Both branches rename a different JSON key to `chosen`. Each branch has unique
keys. The text merger reports clean, but the candidate contains two `chosen`
keys; ordinary `json.loads` would silently retain only the last value. The demo
returns **exit 1 intentionally**, `text_merge_clean: true`, `passed: false`, and
a `strict-json` finding classified `candidate-only`.

For real trees:

```sh
python3 -B line-1/tools/merge-sanity/sanity.py BASE_DIR OURS_DIR THEIRS_DIR
```

Replace those paths with existing stable directories inside the current
workspace. Nothing is written; no candidate module is imported or run, and no
subprocess, network, environment variable, key, wallet or transaction is used.
Input tree reading is inherited from Tree Review and rejects symlinks, special
files, parent traversal and paths outside the current workspace. Limits are
128 files, 256 directories and 16 levels per tree, 1 MiB/4,000 lines per file,
and 8 MiB of combined source text. Candidate files use the same per-file bounds.

## Checks and report

All files receive a conservative conflict-marker check: a line starting with
at least seven `<`, `|`, `=` or `>` characters followed by whitespace or end of
line. At most 20 line numbers are included per file, with the full count and a
truncation flag. Marker-like prose can be intentional and still needs inspection.

Case-sensitive `.py` and `.pyi` files are compiled to a code object without
executing it. This catches syntax, scope and duplicate-argument errors. It does
not resolve imports, run annotations, type-check, test behavior or enforce a
particular Python target version. Results depend on the running interpreter.

Case-sensitive `.json` files require valid JSON, unique keys in every object,
no `NaN`/`Infinity` literals, and at most 128 nested objects/arrays. Very large
finite numbers are accepted without converting them to binary floats or large
integers. There is no JSON schema or application-level value validation.
Brackets inside strings do not count toward nesting. Parser/compiler resource
limits are reported as failures, never passes.

The `merge-sanity/v1` JSON report includes whole-source manifest hashes, candidate
hashes, merge statuses, per-check outcomes for the candidate and available
sources, and findings. Locations are one-based. No source snippets or compiler
error messages are emitted. `candidate-only` means both ours and theirs exist
and pass that particular check; it is not proof of causation. Other failures
are `also-in-branch-or-branch-absent`. Existing faults are never suppressed.

Unresolved text, delete/modify and file/directory conflicts are `blocked`, with
no invented candidate or candidate check. Deletions are explicit and not checked
as empty files. Other file types receive only the marker check. Empty trees can
pass with zero checked files; inspect `counts` to see what was covered.

Exit **0**: no selected check failed and no merge is blocked. **1**: findings or
blocked merges (valid JSON report). **2**: invalid inputs, bounds or filesystem
failure (no partial report). Output text is JSON-escaped for terminal safety.
If redirecting output, choose a separate workspace path outside every input
tree; shell redirection can truncate a source before the tool starts.

## Limits and handoff

Passing checks does not establish semantic correctness, preservation of intent,
author identity or approval. Continue to use Review Recheck to pin a reviewed
packet, Candidate Export or Conflict Finish to stage it, and Stage Audit or
Resolution Review to verify the exact staged bytes. This tool checks fresh
recomputed candidates; it does **not** authenticate an existing saved packet or
stage receipt. It reuses the ancestor merger and cannot detect all shared bugs.
Reads assume stable trusted workspace paths; no atomic snapshots, race
protection, binary merges, rename inference or permissions handling is added.

No coin or external service is needed for local text validation. No dependency
was installed. These are local checks, not independent certification.

An additional repeatable trial uses copies of six real inherited merger files:

```sh
python3 -B line-1/tools/merge-sanity/trial.py
```

Independent README and Python-comment edits passed (six candidate files).
A later duplicate Python argument remained a clean text merge but produced the
expected compile finding, identified as already present in one branch. Every
source byte stayed unchanged by checking. The trial also repeats the demo's
candidate-only JSON failure; `../../REAL-TRIAL-29.json` records the results.
The three inherited core suites passed another 61 tests unchanged.
