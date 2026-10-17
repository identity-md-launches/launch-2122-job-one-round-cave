#!/usr/bin/env python3
"""Check or conservatively relocate an exact saved citation in a changed source."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

_spec = importlib.util.spec_from_file_location(
    'reanchor_engine', Path(__file__).absolute().parents[1] / 'evidence-search/search.py')
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

FORMAT = 'citation-anchor/v1'
MAX_ANCHOR_BYTES = 131072
MAX_ANCHOR_LINES = 200
MAX_JSON_BYTES = 1_000_000
MAX_CANDIDATES = 50


def source(raw, name):
    """Apply the ancestor's source/path/UTF-8 bounds to exactly one file."""
    if not isinstance(raw, bytes):
        raise engine.SearchError('source must be bytes')
    if len(raw) > engine.MAX_FILE_BYTES:
        raise engine.SearchError('source byte limit exceeded')
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        raise engine.SearchError('source is not UTF-8') from None
    doc = {'path': name, 'sha256': engine.digest(raw), 'text': text}
    engine.validate_index({'format': engine.FORMAT, 'documents': [doc]})
    return doc, engine.source_lines(text)


def validate(anchor):
    fields = {'format', 'path', 'line_start', 'line_end', 'sha256', 'text'}
    if not isinstance(anchor, dict) or set(anchor) != fields or anchor['format'] != FORMAT:
        raise engine.SearchError('invalid citation anchor envelope')
    if not engine.valid_relative(anchor['path']):
        raise engine.SearchError('invalid anchor source path')
    start, end = anchor['line_start'], anchor['line_end']
    if (type(start) is not int or type(end) is not int
            or not 1 <= start <= end <= engine.MAX_FILE_BYTES
            or end - start + 1 > MAX_ANCHOR_LINES):
        raise engine.SearchError('invalid anchor line range')
    if not isinstance(anchor['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', anchor['sha256']):
        raise engine.SearchError('invalid anchor source SHA-256')
    text = anchor['text']
    if not isinstance(text, str) or not text.strip() or '\x00' in text:
        raise engine.SearchError('anchor must contain nonblank UTF-8 text without NUL')
    try:
        size = len(text.encode('utf-8'))
    except UnicodeError:
        raise engine.SearchError('invalid anchor Unicode') from None
    lines = text.split('\n')  # Keep final blank lines in a selected range.
    if (size > MAX_ANCHOR_BYTES or len(lines) != end - start + 1
            or any(len(line) > engine.MAX_LINE_CHARS or line.endswith('\r') for line in lines)):
        raise engine.SearchError('anchor excerpt/range or size is invalid')
    return anchor


def capture_bytes(raw, name, start, end):
    doc, lines = source(raw, name)
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise engine.SearchError('selected lines are outside source')
    return validate({'format': FORMAT, 'path': name, 'line_start': start,
                     'line_end': end, 'sha256': doc['sha256'],
                     'text': '\n'.join(lines[start - 1:end])})


def read_source(root, name):
    if not engine.valid_relative(name):
        raise engine.SearchError('invalid source path')
    root = engine.workspace_path(root)
    if not root.is_dir():
        raise engine.SearchError('corpus root must be a directory')
    return engine.read_bytes(engine.workspace_path(root / name), engine.MAX_FILE_BYTES)


def capture(root, name, start, end):
    return capture_bytes(read_source(root, name), name, start, end)


def occurrences(lines, needle):
    """Linear-time exact line matching, including overlapping occurrences."""
    prefix = [0] * len(needle)
    matched = 0
    for i in range(1, len(needle)):
        while matched and needle[i] != needle[matched]:
            matched = prefix[matched - 1]
        if needle[i] == needle[matched]:
            matched += 1
        prefix[i] = matched
    matched = 0
    for i, line in enumerate(lines):
        while matched and line != needle[matched]:
            matched = prefix[matched - 1]
        if line == needle[matched]:
            matched += 1
        if matched == len(needle):
            yield i - len(needle) + 2  # One-based inclusive start.
            matched = prefix[matched - 1]


def check_bytes(anchor, raw):
    validate(anchor)
    doc, lines = source(raw, anchor['path'])
    start, end = anchor['line_start'], anchor['line_end']
    needle = anchor['text'].split('\n')
    same_hash = doc['sha256'] == anchor['sha256']
    candidates, count = [], 0
    if same_hash:
        if lines[start - 1:end] != needle:
            raise engine.SearchError('anchor contradicts source with the same SHA-256')
        positions = [start]
    else:
        positions = occurrences(lines, needle)
    for at in positions:
        count += 1
        if len(candidates) < MAX_CANDIDATES:
            last = at + len(needle) - 1
            candidates.append({'path': anchor['path'], 'line_start': at, 'line_end': last,
                               'citation': f"{anchor['path']}:{at}-{last}",
                               'sha256': doc['sha256']})
    if same_hash:
        status = 'unchanged'
    elif not count:
        status = 'missing'
    elif count > 1:
        status = 'ambiguous'
    elif candidates[0]['line_start'] == start:
        status = 'same_lines_changed_source'
    else:
        status = 'relocated'
    return {'format': 'citation-reanchor-result/v1', 'status': status,
            'original_citation': f"{anchor['path']}:{start}-{end}",
            'original_sha256': anchor['sha256'], 'current_sha256': doc['sha256'],
            'source_hash_matches': same_hash,
            'unique_current_citation': candidates[0] if count == 1 else None,
            'match_count': count, 'candidates': candidates,
            'candidates_truncated': count > MAX_CANDIDATES,
            'scope': 'saved line range' if same_hash else 'all exact line occurrences in same path',
            'source_verified': False}


def check(root, anchor):
    validate(anchor)
    report = check_bytes(anchor, read_source(root, anchor['path']))
    # A fresh second bounded read catches ordinary edits during the scan.
    # This is not an atomic filesystem snapshot or race-resistant sandbox.
    if engine.digest(read_source(root, anchor['path'])) != report['current_sha256']:
        raise engine.SearchError('source changed during check; retry with a static source')
    report['source_verified'] = True
    return report


def load_anchor(path):
    raw = engine.read_bytes(engine.workspace_path(path), MAX_JSON_BYTES)
    def reject_constant(value):
        raise engine.SearchError('non-finite JSON number')
    try:
        anchor = json.loads(raw.decode('utf-8'), object_pairs_hook=engine.reject_duplicates,
                            parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise engine.SearchError('anchor is not valid UTF-8 JSON') from None
    return validate(anchor)


def demo():
    root = Path(__file__).absolute().parents[1] / 'evidence-search/examples/docs'
    anchor = capture(root, 'zto.md', 3, 6)
    original = check(root, anchor)
    raw = read_source(root, 'zto.md')
    # A synthetic layout-only edit to historical real evidence, in memory.
    moved = check_bytes(anchor, b'# Reading copy\n\n' + raw)
    return {'anchor': anchor, 'original': original, 'layout_edit_in_memory': moved}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('capture', help='print an anchor for a source line range')
    p.add_argument('root')
    p.add_argument('path')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p = subs.add_parser('check', help='check a saved anchor against the same source path')
    p.add_argument('root')
    p.add_argument('anchor')
    subs.add_parser('demo', help='read-only real historical ZTO example')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'capture':
            result = capture(args.root, args.path, args.start, args.end)
        else:
            result = check(args.root, load_anchor(args.anchor))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('status') in ('missing', 'ambiguous') else 0
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
