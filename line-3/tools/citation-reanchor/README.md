# Citation Reanchor

Check whether an exact cited passage still exists after its source document
changes, and suggest a new line citation only when its complete saved lines have
one match in that same file. This helps a worker maintain evidence in a report
without silently reusing stale line numbers. Python 3.9+ and standard library
only; keep the sibling `evidence-search/` folder with this tool.

From the repository root, one read-only command shows it working:

```sh
python3 -B line-3/tools/citation-reanchor/reanchor.py demo
```

When tried, the historical real ZTO evidence at `zto.md:3-6` checked as
`unchanged`, with its live source bytes verified. Adding a two-line reading-copy
heading **in memory** yielded `relocated` at `zto.md:5-8`. The second result has
`source_verified: false` because those edited bytes were never a live file.
No document, anchor, index or report is written by this demo. The inherited
ZTO/IMD observations are historical; this is not a fresh Ethereum read or quote.

## Save and check a citation

Choose the exact path and inclusive line range from a search result. Capture an
anchor before editing the document; shell redirection saves the printed JSON.
Use a new filename outside the source corpus to avoid overwriting evidence:

```sh
python3 -B line-3/tools/citation-reanchor/reanchor.py capture line-3/tools/evidence-search/examples/docs zto.md 3 6 > line-3/zto-anchor.json
python3 -B line-3/tools/citation-reanchor/reanchor.py check line-3/tools/evidence-search/examples/docs line-3/zto-anchor.json
```

The anchor contains the relative path, original whole-file SHA-256, original
line range and exact excerpt. It is deliberately a small standalone format,
not a search-result envelope. This command captures the **current** source;
check any old search result's hash separately before treating it as that result's
original evidence. Keep anchors private if their excerpts contain private data.
The tool itself reads only explicitly selected workspace files and prints JSON.

| Status | What the worker can infer |
| --- | --- |
| `unchanged` | Whole-file bytes match the saved hash and the saved range contains the excerpt. Duplicate text elsewhere does not invalidate the original range. |
| `same_lines_changed_source` | File bytes changed, but the sole exact occurrence occupies the original range. Review surrounding changes. |
| `relocated` | File bytes changed and the sole exact occurrence occupies a different range. Review it before updating a citation. |
| `ambiguous` | The changed source has multiple exact occurrences, even if one is at the original range. No unique citation is suggested. |
| `missing` | No exact full-line occurrence remains in this file. The tool does not guess a replacement. |

For changed files, `match_count` counts **all** overlapping occurrences, while
`candidates` contains at most the first 50 in line order and
`candidates_truncated` says whether any were omitted. On unchanged files the
scope is just the saved range; the count is one, not a document-wide census.
`unique_current_citation` is null for missing or ambiguous results. Other results
include the current source hash, path and new line range. The anchor is never
rewritten. A missing source file is an I/O error, distinct from a present file
with no matching passage.

Exit codes: **0** for capture, demo, or a unique intact passage; **1** for missing
or ambiguous passages; **2** for invalid input, source inconsistency or I/O
failure. Errors are JSON on stderr with no partial report on stdout. Code 0 for
a changed source is a suggested location, not automatic approval of new evidence.

## Matching and trust limits

Matching is exact across complete lines, including tabs, blank lines,
capitalization and Unicode code points. Only LF/CRLF line endings normalize to
LF, following Evidence Search. Thus an LF/CRLF conversion changes the file hash
but can preserve an excerpt. No whitespace folding, stemming, fuzzy matching,
file rename discovery, cross-file search or semantic equivalence is attempted.
The matching algorithm uses linear-time prefix matching and detects overlaps.

An anchor and a hash do not authenticate authorship or establish factual truth.
If an untrusted anchor's claimed hash matches current source bytes but its saved
range contradicts them, the tool refuses it. For a changed source, the old hash
cannot establish that the anchor's text ever appeared in the old document;
retain the old document or a trusted receipt when that provenance is needed.
Even an unchanged excerpt can acquire a different meaning from altered context.
Nothing establishes current token state, consensus finality or authority to pay.

Live `check` reads the selected source again after matching and refuses an
observed concurrent change. Keep files static: this is not an atomic snapshot,
OS sandbox or defense against concurrent path replacement. Static symlinks,
parent traversal, paths outside the current workspace, hidden source names and
non-document suffixes are refused by the inherited engine.

Bounds: one UTF-8 `.md`, `.txt` or `.rst` file, 1,000,000 source bytes, 16,000
characters per source line; anchors contain 1–200 lines with nonblank text,
at most 131,072 excerpt bytes and 1,000,000 serialized input bytes. NULs,
malformed Unicode, duplicate JSON keys and non-finite numbers fail. Empty files
may be checked and produce `missing`, but cannot supply a nonblank anchor.
No dependencies are installed; no network, environment lookup, document
execution, secret access, wallet, transaction or payment is involved.

## Checks actually run

```sh
python3 -B line-3/tools/citation-reanchor/test_reanchor.py -v
```

All 14 behavioral tests passed. They cover the five statuses, unchanged duplicate
scope, changed-source ambiguity, overlapping and capped candidates, exact CRLF
and blank-line handling, Unicode distinctions, forged same-hash excerpts,
malformed inputs, source/anchor limits, missing files, symlinks, workspace bounds,
concurrent edits, immutable inputs, CLI exit codes and the real ZTO demo.
Five hundred deterministic random cases compare the matcher with exhaustive
line-slice matching. Test files live only in `test/scratch/`.
