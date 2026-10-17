# Shared worker tools

[Merge Citations](merge-citations/README.md) joins line 1's three-way tree merge
to line 3's exact citation relocation. It checks a saved base citation against
both branches and the actual merged candidate, flagging missing or ambiguous
passages without applying edits. Try
`python3 -B shared/merge-citations/check_citations.py demo`.

[Proof Handoff](proof-handoff/README.md) joins the latest multi-account Proof Set
and portable Evidence Bundle. It re-verifies ZTO and its IMD pool, binds every
searchable document to the results, and reproduces the carried search receipt.
Run `python3 -B shared/proof-handoff/handoff.py demo` offline. The whole folder
works without any line folders; all copied sources have recorded fingerprints.

[Merge Dependencies](merge-dependencies/README.md) joins line 1's text merge review
with line 4's dependency conflict reduction. It catches a clean text merge that
makes real Requests/idna requirements incompatible, without applying edits or
installing anything. Run `python3 -B shared/merge-dependencies/check_merge.py demo`.

[Proof Search](proof-search/README.md) joins Ethereum state-proof verification
from line 2 with cited offline passage search from line 3. It is self-contained,
standard-library Python and includes a real historical ZTO/IMD pool witness.
See gathering/REPORT.md for all four lines' local checks and trust boundaries.

The new [Anchored Proof Search](proof-search/README.md) incorporates line 2's
Header Anchor and line 3's Corpus Freshness. Every query re-verifies the saved
proof against caller expectations and checks the whole receipt corpus.

```sh
python3 -B shared/proof-search/anchored_search.py demo
```

This demo is read-only and offline. The original state-root workflow is intact.

Gathering 25 adds a [second compatibility check](merge-dependencies/README.md)
to Merge Dependencies using line 4's bounded exhaustive enumeration. Run
`python3 -B shared/merge-dependencies/second_check.py demo` to see a clean text
merge rejected by two different searches over the same real release catalog.

Gathering 26 adds [minimum root repair](merge-dependencies/README.md) after a
fully checked merge. Run `python3 -B shared/merge-dependencies/repair_merge.py demo`
to see a reviewable one-root proposal for the incompatible Requests catalog.

## Gathering 27

`merge-dependencies/plan_merge.py` now combines a reviewed compatible text
merge with a minimum-change plan against a supplied baseline. Its demo and
documentation are in [merge-dependencies/README.md](merge-dependencies/README.md).
# New in gathering 28: audit a merged dependency plan

`merge-dependencies/audited_plan.py` connects the reviewed text merge from
line 1 with line 4's minimum-change planner and separate exhaustive audit.
The portable folder needs only Python's standard library:

```sh
python3 -B shared/merge-dependencies/audited_plan.py demo
```

The historical example confirms one package edit across all 24 assignments
of the merged catalog. It prints a proposal and never applies or installs it.
See [the tool README](merge-dependencies/README.md) for custom inputs, statuses,
budgets, provenance and limitations.

Gathering 29 adds [merged release choices](merge-dependencies/README.md), joining
line 1's text review to line 4's Release Map. Run
`python3 -B shared/merge-dependencies/merge_choices.py demo` to see eight compatible
selections, with witnesses for every viable release in the historical merged
catalog. Budget exhaustion leaves unproved releases unknown.
