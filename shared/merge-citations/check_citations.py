#!/usr/bin/env python3
"""Review an exact saved citation against both edits and their merged candidate."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).absolute().parent


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


tree = module('citation_merge_tree', 'tools/tree-review/tree_review.py')
anchor_tool = module('citation_merge_anchor', 'tools/citation-reanchor/reanchor.py')
LIMITS = [
    'Suggestions refer to a recomputed in-memory candidate, never an applied file.',
    'An intact excerpt may have a changed meaning in its new context; review it.',
    'The saved anchor must match the supplied base bytes and original line range.',
    'No author authentication, factual verification, semantic merge or approval.',
    'Exact complete-line matching; only LF/CRLF endings normalize.',
    'Stable bounded UTF-8 trees only; no atomic snapshot or race protection.',
    'No files are written, no documents executed, and no network is used.'
]


def inspect(sources, anchor):
    if len(sources) != 3:
        raise ValueError('provide exactly three source trees')
    anchor_tool.validate(anchor)
    name = anchor['path']
    original = sources[0]['files'].get(name)
    if original is None:
        raise ValueError('anchor source is absent from the base tree')
    # A changed-source search alone cannot prove the anchor ever existed.
    # Bind both the excerpt and its coordinates to the actual supplied base.
    raw = original.encode('utf-8')
    if anchor_tool.engine.digest(raw) != anchor['sha256']:
        raise ValueError('anchor hash does not match the base source')
    anchor_tool.check_bytes(anchor, raw)
    for source in sources:
        for text in source['files'].values():
            tree.validate_text(text)
    packet = tree.combine(sources)
    entry = next(item for item in packet['files'] if item['path'] == name)

    def check(text):
        return ({'status': 'deleted', 'unique_current_citation': None,
                 'source_verified': False} if text is None else
                anchor_tool.check_bytes(anchor, text.encode('utf-8')))

    branches = {side: check(source['files'].get(name))
                for side, source in zip(tree.SIDES, sources)}
    conflicts = [item['path'] for item in packet['files']
                 if item['status'].endswith('conflict')]
    if entry['status'].endswith('conflict'):
        candidate = None
        status = 'blocked'
    else:
        candidate = check(entry['candidate'])
        status = ('blocked' if conflicts else 'deleted' if entry['candidate'] is None
                  else 'ready-for-review' if candidate['unique_current_citation']
                  else 'needs-review')
    return {'format': 'merge-citations/v1', 'status': status,
            'path': name, 'base_anchor_verified': True,
            'text_merge_clean': packet['clean'], 'inputs': packet['inputs'],
            'conflicted_paths': conflicts, 'merge_status': entry['status'],
            'candidate_sha256': entry['candidate_sha256'],
            'branches': branches, 'candidate': candidate,
            'candidate_diff_from_base': None if entry['candidate'] is None else
                tree.review.unified(original, entry['candidate'], 'BASE', 'CANDIDATE'),
            'limits': LIMITS}


def from_directories(paths, anchor):
    if len(paths) != 3:
        raise ValueError('provide exactly three source directories')
    budget = [0]
    sources = [tree.snapshot(path, budget) for path in paths]
    result = inspect(sources, anchor)
    # Detect ordinary edits during review without claiming an atomic snapshot.
    budget = [0]
    after = [tree.snapshot(path, budget) for path in paths]
    if any(tree.manifest(a) != tree.manifest(b) for a, b in zip(sources, after)):
        raise ValueError('source tree changed during review; retry with static inputs')
    result['source_trees_rechecked'] = True
    return result


def demo():
    raw = anchor_tool.engine.read_bytes(
        anchor_tool.engine.workspace_path(HERE / 'examples/zto.md'), 1_000_000)
    text = raw.decode('utf-8')
    anchor = anchor_tool.capture_bytes(raw, 'zto.md', 3, 6)
    versions = (text, '# Reading copy\n\n' + text,
                text + '\nReview historical observations before relying on them.\n')
    result = inspect([{'files': {'zto.md': version}, 'directories': set()}
                      for version in versions], anchor)
    result['demo'] = ('Real historical ZTO document with two illustrative edits in memory. '
                      'No new chain observation and no files applied.')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    p = sub.add_parser('review')
    for name in ('base', 'ours', 'theirs', 'anchor'):
        p.add_argument(name)
    args = parser.parse_args(argv)
    try:
        result = demo() if args.command == 'demo' else from_directories(
            [args.base, args.ours, args.theirs], anchor_tool.load_anchor(args.anchor))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['status'] == 'ready-for-review' else 1
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}, ensure_ascii=True),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
