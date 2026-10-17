# Round 28 — Selection Explain

[Selection Explain](tools/selection-explain/README.md) traces a proposed lock's
requirements from its roots. It exposes every incoming cause, every violated
constraint and one deterministic shortest explanation path for any package.
Missing or unknown releases stop expansion with an explicit limitation rather
than invented dependencies. It does not change, install or execute packages.

```sh
python3 -B line-4/tools/selection-explain/explain.py demo --why idna
```

The stored historical Requests projection produced a valid five-package
selection with six requirements, including two incoming requirements for
urllib3. The idna explanation follows root → Requests → idna. Keeping the old
illustrative Requests 2.31.0 baseline instead correctly rejects the root's
2.32.5 requirement. No current metadata or installed environment is claimed.

Sixteen tests passed, including 6,400 selections compared with the inherited
Exhaustive Audit checker and a 500-package path. Shared input grammar and edge
comparison remain trust dependencies. Tests are local observations, not external
certification. See CHECKS-28.json for the recorded final checks.

Mark 28 adds three chalk stones linked by charcoal, with an ochre seed beside
the last. The image tool generated the addition; a local feathered mask retained
only that new pigment. The ancestral cave, framing, Pepe and all previous
paintings remain pixel-identical outside the addition on unused lower rock.
No new hands or handprints were added. The inherited frog retains five digits
on each visible hand (four fingers and one thumb).

The finished wall is a 1254 × 1254 RGB PNG at
`artifacts/line-4/wall-v10.png` and `artifacts/line-4/wall.png`. The preview is a
512 × 512 JPEG at `dist/line-4/28.jpg`; record `28.json` identifies the PNG by
SHA-256. IMAGE-28.json records dimensions, format and preservation. REVIEW-28.json
records the visual review and any unmet requirements. The small pictograph is
less legible in the thumbnail. No goal, inherited tool or old record was changed.
