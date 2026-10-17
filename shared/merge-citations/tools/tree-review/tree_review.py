#!/usr/bin/env python3
"""Read-only, bounded three-directory text merge review; Python standard library."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

REVIEW_PATH = Path(__file__).resolve().parents[1] / 'merge-review' / 'review.py'
spec = importlib.util.spec_from_file_location('tree_review_packet', REVIEW_PATH)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

MAX_FILES = 128
MAX_DIRS = 256
MAX_DEPTH = 16
MAX_TOTAL_BYTES = 8 * 1024 * 1024
SIDES = ('base', 'ours', 'theirs')


def fingerprint(text):
    data = text.encode('utf-8')
    return {'kind': 'file', 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data)}


def validate_text(text):
    if not isinstance(text, str) or '\x00' in text:
        raise ValueError('only UTF-8 text without NUL is supported')
    if len(text.encode('utf-8')) > review.engine.MAX_BYTES:
        raise ValueError('each file must be at most 1 MiB')
    if len(text.splitlines(keepends=True)) > review.engine.MAX_LINES:
        raise ValueError('each file must have at most 4000 lines')


def workspace_directory(path):
    """Reject escape and symlink traversal before opening any supplied content."""
    root = Path.cwd().resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    # Do not normalize '..' through a potentially symlinked path component.
    if '..' in candidate.parts:
        raise ValueError('directory paths must not contain parent traversal')
    if not candidate.is_relative_to(root):
        raise ValueError('directories must be inside the current workspace')
    cursor = root
    for part in candidate.relative_to(root).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('symlink directories are not supported')
    if not candidate.is_dir():
        raise ValueError('all three inputs must be existing directories')
    return candidate


def snapshot(folder, budget):
    """Read a stable directory; no links, special files, or implicit exclusions."""
    root = workspace_directory(folder)
    files, directories = {}, set()

    def children(directory):
        with os.scandir(directory) as entries:
            for entry in entries:
                yield Path(entry.path)

    def walk(directory, depth):
        if depth > MAX_DEPTH:
            raise ValueError('directory nesting exceeds 16 levels')
        # Streaming enumeration bounds work even for a directory with many entries.
        for child in children(directory):
            relative = child.relative_to(root).as_posix()
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError('symlinks are not supported: ' + relative)
            if stat.S_ISDIR(mode):
                directories.add(relative)
                if len(directories) > MAX_DIRS:
                    raise ValueError('each tree may contain at most 256 directories')
                walk(child, depth + 1)
            elif stat.S_ISREG(mode):
                if len(files) >= MAX_FILES:
                    raise ValueError('each tree may contain at most 128 files')
                with child.open('rb') as handle:
                    data = handle.read(review.engine.MAX_BYTES + 1)
                budget[0] += len(data)
                if budget[0] > MAX_TOTAL_BYTES:
                    raise ValueError('three trees together may contain at most 8 MiB')
                if len(data) > review.engine.MAX_BYTES:
                    raise ValueError('each file must be at most 1 MiB: ' + relative)
                text = data.decode('utf-8')
                validate_text(text)
                files[relative] = text
            else:
                raise ValueError('only regular files and directories are supported: ' + relative)
    walk(root, 0)
    return {'files': files, 'directories': directories}


def manifest(tree):
    entries = {name: fingerprint(value) for name, value in tree['files'].items()}
    entries.update({name: {'kind': 'directory'} for name in tree['directories']})
    encoded = json.dumps(entries, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':')).encode('utf-8')
    return {'sha256': hashlib.sha256(encoded).hexdigest(),
            'files': len(tree['files']), 'directories': len(tree['directories']),
            'bytes': sum(len(t.encode('utf-8')) for t in tree['files'].values())}


def combine(trees):
    """Build a review plan, never a write/apply operation. Missing != empty."""
    all_files = set().union(*(set(t['files']) for t in trees))
    all_dirs = set().union(*(t['directories'] for t in trees))
    collisions = sorted(all_files & all_dirs)
    entries = []
    for name in sorted(all_files):
        texts = [tree['files'].get(name) for tree in trees]
        base, ours, theirs = texts
        inputs = {side: fingerprint(text) if text is not None else
                  {'kind': 'directory' if name in tree['directories'] else 'missing'}
                  for side, text, tree in zip(SIDES, texts, trees)}
        blocked = [p for p in collisions if name == p or name.startswith(p + '/')]
        entry = {'path': name, 'inputs': inputs, 'status': None,
                 'candidate': None, 'candidate_sha256': None, 'review': None,
                 'diffs': {side: review.unified(base or '', text or '', 'BASE', side.upper())
                           for side, text in zip(('ours', 'theirs'), (ours, theirs))}}
        if blocked:
            entry.update(status='path-conflict', blocked_by=blocked,
                         versions=dict(zip(SIDES, texts)))
        elif ours == theirs:
            entry.update(status='deleted' if ours is None else
                         'unchanged' if ours == base else 'agreed', candidate=ours)
        elif ours == base:
            entry.update(status='deleted' if theirs is None else 'theirs', candidate=theirs)
        elif theirs == base:
            entry.update(status='deleted' if ours is None else 'ours', candidate=ours)
        elif ours is None or theirs is None:
            entry.update(status='delete-modify-conflict', versions=dict(zip(SIDES, texts)))
        else:
            packet = review.packet(base if base is not None else '', ours, theirs)
            entry.update(status='merged' if packet['clean'] else 'text-conflict', review=packet)
            if packet['clean']:
                entry['candidate'] = packet['merged']
        if entry['candidate'] is not None:
            entry['candidate_sha256'] = review.digest(entry['candidate'])
        entries.append(entry)
    counts = {}
    for entry in entries:
        counts[entry['status']] = counts.get(entry['status'], 0) + 1
    return {'schema': 'tree-review/v1',
            'clean': not any(e['status'].endswith('conflict') for e in entries),
            'inputs': {side: manifest(tree) for side, tree in zip(SIDES, trees)},
            'counts': counts, 'path_conflicts': collisions, 'files': entries,
            'limits': [
                'Review only: no files are written or deleted.',
                'Empty directories, permissions and renames are not merged.',
                'Any file/directory type collision is conservatively a conflict.',
                'Line alignment can be ambiguous; clean is not semantic correctness.',
                'Hashes identify bytes, not authors; reads require stable trusted trees.',
                'No filesystem snapshot or protection against concurrent path replacement.']}


def from_directories(paths):
    budget = [0]
    return combine([snapshot(path, budget) for path in paths])


def demo(conflict=False):
    # All contents are a small text-edit example, not external identities or chain data.
    base = {'guide.md': 'Source: draft.txt\nReview: optional\n',
            'obsolete.txt': 'superseded note\n'}
    ours = {**base, 'guide.md': base['guide.md'].replace('draft.txt', 'verified-source.txt'),
            'notes.txt': 'Keep the source receipt.\n'}
    theirs = {'guide.md': base['guide.md'].replace('optional', 'required')}
    if conflict:
        ours['obsolete.txt'] = 'Keep this corrected note.\n'
    return combine([{'files': files, 'directories': set()} for files in (base, ours, theirs)])


def render(report):
    quote = lambda value: json.dumps(value, ensure_ascii=True)
    lines = ['TREE REVIEW: ' + ('CLEAN (review required)' if report['clean'] else 'CONFLICTS')]
    for side, info in report['inputs'].items():
        lines.append(f"{side}: {info['files']} files, {info['bytes']} bytes, manifest {info['sha256']}")
    for entry in report['files']:
        lines.append(entry['status'] + ' ' + quote(entry['path']))
        if entry['candidate'] is not None:
            lines.append('  candidate: ' + quote(entry['candidate']))
        if 'versions' in entry:
            lines.append('  versions: ' + quote(entry['versions']))
        if entry['review'] and not entry['review']['clean']:
            lines.append('  conflicts: ' + quote(entry['review']['conflicts']))
    lines.extend('Limit: ' + limit for limit in report['limits'])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='BASE_DIR OURS_DIR THEIRS_DIR')
    parser.add_argument('--demo', choices=('clean', 'conflict'))
    parser.add_argument('--format', choices=('json', 'text'), default='text')
    args = parser.parse_args(argv)
    if args.demo and args.paths or not args.demo and len(args.paths) != 3:
        parser.error('provide three directories or --demo clean|conflict')
    try:
        report = demo(args.demo == 'conflict') if args.demo else from_directories(args.paths)
    except (OSError, ValueError, UnicodeError) as error:
        print('tree-review: ' + ascii(str(error)), file=sys.stderr)
        return 2
    result = json.dumps(report, ensure_ascii=True, indent=2) + '\n' if args.format == 'json' else render(report)
    sys.stdout.buffer.write(result.encode('utf-8'))
    return 0 if report['clean'] else 1


if __name__ == '__main__':
    sys.exit(main())
