# Selection Explain

Explain **why a package is in a proposed selection** and diagnose every broken
requirement, without searching for a replacement or installing anything. Uses
Python 3.10+ and the standard library only; run from the repository root.

```sh
python3 -B line-4/tools/selection-explain/explain.py demo --why idna
```

Tried against the inherited historical Requests metadata projection: the demo
validated five selected packages and six requirements with no violations.
`why.path` was `[0, 4]`: the root requires Requests 2.32.5, which requires
`idna <4,>=2.5`; selected idna 3.10 satisfies that constraint. urllib3 has two
incoming requirements, from the root and Requests; both are checked. The demo
explicitly updates the illustrative Lock Plan baseline to Requests 2.32.5;
it does not inspect an installed environment. Leaving the older baseline's
Requests 2.31.0 instead reports a root constraint mismatch.

For your own finite catalog and a JSON object mapping package names to exact
release strings:

```sh
python3 -B line-4/tools/selection-explain/explain.py path/to/catalog.json --selection path/to/selection.json --why package-name
```

Catalog syntax is inherited from [Offline Resolver](../offline-resolver/README.md):
exactly `packages` and `roots`, numeric versions with up to four components,
`*` or comma-separated comparisons. Names canonicalize case and `._-` aliases;
ambiguous aliases are rejected. Release strings must match catalog keys exactly:
selection `1` does not guess the catalog key `1.0`. All inputs must resolve inside
the current workspace and be at most 1 MB; duplicate JSON keys are rejected.
Selection objects have at most 1,000 packages. No network, environment lookup,
package execution, signing, payments or writes occur at tool runtime.

The JSON report contains:

- `requirements`: every root edge and every dependency edge of each known,
  reachable selected release; `source: null` denotes a root. Other sources are
  package names whose release is in `selected`. An edge states its constraint,
  selected version, satisfaction and issue: `missing-selection`, `unknown-release`
  or `constraint-mismatch`.
- `violations`: indexes into that list, preserving **all** failed incoming edges,
  including those on cycles or shared dependencies.
- `nodes`: every traced package, with all incoming edge indexes and a `via`
  predecessor chosen by deterministic breadth-first traversal. This is a compact
  explanation forest, avoiding a copy of every path in the output.
- `why`: optional shortest root-to-target path as edge indexes. Ties use sorted
  roots/dependencies. A target outside the graph is `unreachable` if selected or
  `not-required` otherwise. A shortest path can pass even if another incoming
  edge fails: always inspect global `status` and `violations`.
- `unreachable_selected`: extra choices with no selected-release path from a
  root. `unknown_selected` lists selected releases absent from the catalog.
  `unexpanded` lists traced missing/unknown selections whose dependency metadata
  cannot be inferred. Their possible descendants are **unknown**, not proven
  unnecessary. A known but mismatched release is still expanded so its further
  problems can be seen; a path describes the supplied choice, not a valid lock.
- `input_sha256`: digest of the normalized catalog plus selection. It binds this
  report to those inputs; it is not a signature or independent certification.

Exit **0**: valid reachable selection; **1**: rejected selection; **2**: malformed
input or workspace read failure. `valid` requires every root/edge satisfied and
no extra selections. A valid selection may have other compatible alternatives;
this tool makes no optimality, uniqueness or unsatisfiability claim. Breadth-first
traversal terminates on cycles, visits each reachable package once and checks
every incoming requirement. It has no combinatorial search budget. Graph work
is linear in the selected reachable graph after sorting input names; the one
optional path is iterative, including long dependency chains.

Tests:

```sh
python3 -B -m unittest discover -s line-4/tools/selection-explain -p 'test_*.py' -v
```

All 16 initial tests passed, including 6,400 candidate selections over 100 seeded
catalogs checked against Exhaustive Audit's separate compatibility predicate.
Cases cover diamonds, multiple causes, mismatches, missing roots/dependencies,
unknown versions/packages, unreachable extras, alias collisions, exact release
spellings, self-dependencies, cycles and a 500-package chain. Tests write no
files and contact no services. Grammar and the edge-comparison implementation
remain inherited trust dependencies, not independent proofs.

This finite projection does not model full PyPI syntax, interpreter/platform
markers, artifacts, availability, publisher trust, vulnerabilities or actual
installability. Stored metadata is historical, not a current recommendation.
No coin is needed for dependency tracing.
