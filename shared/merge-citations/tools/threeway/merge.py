#!/usr/bin/env python3
"""Bounded, offline, line-based three-way merging. No input files are modified."""

import argparse
from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import sys

MAX_BYTES = 1_048_576
MAX_LINES = 4000


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    lines: tuple
    side: str


def edits(base, changed, side):
    matcher = difflib.SequenceMatcher(None, base, changed, autojunk=False)
    return [Edit(i, j, tuple(changed[k:l]), side)
            for tag, i, j, k, l in matcher.get_opcodes() if tag != 'equal']


def apply_region(base, start, end, changes):
    result = []
    cursor = start
    for change in changes:
        result.extend(base[cursor:change.start])
        result.extend(change.lines)
        cursor = change.end
    result.extend(base[cursor:end])
    return ''.join(result)


def section(text):
    # Conflict marker lines must remain distinguishable even for an unterminated file.
    return text + ('\n' if text and not text.endswith(('\n', '\r')) else '')


def merge(base_text, ours_text, theirs_text):
    """Return JSON-compatible result; locations are zero-based half-open base lines."""
    for text in (base_text, ours_text, theirs_text):
        if not isinstance(text, str) or '\x00' in text:
            raise ValueError('inputs must be text without NUL bytes')
        if len(text.encode('utf-8')) > MAX_BYTES:
            raise ValueError('each input must be at most 1 MiB')
        if len(text.splitlines(keepends=True)) > MAX_LINES:
            raise ValueError('each input must be at most 4000 lines')
    base, ours, theirs = [t.splitlines(keepends=True)
                          for t in (base_text, ours_text, theirs_text)]
    changes = sorted(edits(base, ours, 'ours') + edits(base, theirs, 'theirs'),
                     key=lambda e: (e.start, e.end, e.side))
    groups = []
    for change in changes:
        if groups and (change.start < groups[-1][1] or change.start == groups[-1][0]):
            start, end, members = groups[-1]
            groups[-1] = (start, max(end, change.end), members + [change])
        else:
            groups.append((change.start, change.end, [change]))
    result, conflicts = [], []
    cursor = 0
    for start, end, members in groups:
        result.extend(base[cursor:start])
        original = ''.join(base[start:end])
        left = apply_region(base, start, end, [e for e in members if e.side == 'ours'])
        right = apply_region(base, start, end, [e for e in members if e.side == 'theirs'])
        if left == right:
            result.append(left)
        elif left == original:
            result.append(right)
        elif right == original:
            result.append(left)
        else:
            conflicts.append({'base_start': start, 'base_end': end,
                              'base': original, 'ours': left, 'theirs': right})
            # Add a separator if the preceding content has no final newline.
            if result and result[-1] and not result[-1].endswith(('\n', '\r')):
                result.append('\n')
            result.append('<<<<<<< OURS\n' + section(left) + '||||||| BASE\n' +
                          section(original) + '=======\n' + section(right) +
                          '>>>>>>> THEIRS\n')
        cursor = end
    result.extend(base[cursor:])
    return {'schema': 'threeway/v1', 'clean': not conflicts,
            'merged': ''.join(result), 'conflicts': conflicts}


def read_text(path):
    root = Path.cwd().resolve()
    resolved = Path(path).resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError('input must be inside the current workspace directory')
    if not resolved.is_file():
        raise ValueError('input must be a regular file')
    with resolved.open('rb') as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('each input must be at most 1 MiB')
    # Decode bytes directly to preserve CRLF instead of universal-newline conversion.
    return data.decode('utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', metavar='FILE', help='BASE OURS THEIRS')
    parser.add_argument('--demo', action='store_true', help='merge bundled examples')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args(argv)
    if args.demo:
        if args.paths:
            parser.error('--demo cannot be combined with paths')
        folder = Path(__file__).resolve().parent / 'examples'
        paths = [folder / f'{name}.txt' for name in ('base', 'ours', 'theirs')]
    else:
        if len(args.paths) != 3:
            parser.error('provide BASE OURS THEIRS or --demo')
        paths = args.paths
    try:
        result = merge(*(read_text(path) for path in paths))
    except (OSError, UnicodeError, ValueError) as error:
        print(f'threeway: {error}', file=sys.stderr)
        return 2
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n' if args.format == 'json' else result['merged']
    # Use bytes to preserve newline spelling on every platform.
    sys.stdout.buffer.write(output.encode('utf-8'))
    print(f"threeway: {len(result['conflicts'])} conflict(s)", file=sys.stderr)
    return 0 if result['clean'] else 1


if __name__ == '__main__':
    sys.exit(main())
