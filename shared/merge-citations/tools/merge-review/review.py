#!/usr/bin/env python3
"""Read-only review packet for the sibling threeway merger (standard library)."""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

# Load only the explicitly named sibling implementation, never an input module.
ENGINE = Path(__file__).resolve().parents[1] / 'threeway' / 'merge.py'
spec = importlib.util.spec_from_file_location('pepe_threeway', ENGINE)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def unified(before, after, before_name, after_name):
    """Represent missing final newlines explicitly, like a unified diff."""
    result = []
    for line in difflib.unified_diff(before.splitlines(keepends=True),
                                     after.splitlines(keepends=True),
                                     fromfile=before_name, tofile=after_name, n=3):
        result.append(line)
        if not line.endswith(('\n', '\r')):
            result.append('\n\\ No newline at end of file\n')
    return ''.join(result)


def packet(base, ours, theirs):
    result = engine.merge(base, ours, theirs)
    sources = dict(base=base, ours=ours, theirs=theirs)
    conflicts = []
    lines = base.splitlines(keepends=True)
    for number, conflict in enumerate(result['conflicts'], 1):
        start, end = conflict['base_start'], conflict['base_end']
        conflicts.append(dict(
            number=number, **conflict,
            context_before=''.join(lines[max(0, start - 3):start]),
            context_after=''.join(lines[end:end + 3]),
            ours_diff=unified(conflict['base'], conflict['ours'], 'BASE region', 'OURS region'),
            theirs_diff=unified(conflict['base'], conflict['theirs'], 'BASE region', 'THEIRS region')))
    return dict(schema='merge-review/v1', clean=result['clean'],
                inputs={name: dict(sha256=digest(text), bytes=len(text.encode('utf-8')),
                                   lines=len(text.splitlines(keepends=True)))
                        for name, text in sources.items()},
                merged_sha256=digest(result['merged']), merged=result['merged'],
                diffs={name: unified(base, sources[name], 'BASE', name.upper())
                       for name in ('ours', 'theirs')}, conflicts=conflicts,
                limits=['Line-based alignment can be ambiguous on repeated text.',
                        'Clean means no textual conflict, not semantic correctness.',
                        'Hashes identify bytes; they do not authenticate an author.'])


def render(report):
    # JSON-string quote all untrusted text. Controls and terminal escapes cannot run.
    quote = lambda value: json.dumps(value, ensure_ascii=True)
    out = ['MERGE REVIEW', 'Status: ' + ('CLEAN (review still required)' if report['clean'] else 'CONFLICTS'),
           'Input fingerprints (SHA-256 of exact UTF-8 bytes):']
    for name, info in report['inputs'].items():
        out.append(f"  {name}: {info['sha256']} ({info['bytes']} bytes, {info['lines']} lines)")
    for name, diff in report['diffs'].items():
        out.extend([f'{name.upper()} change against BASE (JSON-quoted unified diff):', quote(diff)])
    for conflict in report['conflicts']:
        start, end = conflict['base_start'], conflict['base_end']
        location = f'base lines {start + 1}..{end}' if end > start else f'insertion after {start} base lines'
        out.append(f"Conflict {conflict['number']}: {location} (zero-based [{start}, {end}))")
        for name in ('context_before', 'base', 'ours', 'theirs', 'context_after'):
            out.append(f'  {name}: {quote(conflict[name])}')
    out.extend(['Merged candidate (JSON-quoted; inspect before use):', quote(report['merged']),
                'Merged SHA-256: ' + report['merged_sha256']])
    out.extend('Limit: ' + item for item in report['limits'])
    return '\n'.join(out) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='BASE OURS THEIRS, inside current workspace')
    parser.add_argument('--demo', choices=('clean', 'conflict'))
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args(argv)
    if args.demo:
        if args.paths:
            parser.error('use either --demo or three paths')
        base = 'Title: Deployment checklist\nSource: draft.txt\nReview: optional\n'
        ours = base.replace('draft.txt', 'verified-source.txt')
        theirs = base.replace('optional', 'required') if args.demo == 'clean' else base.replace('draft.txt', 'audited-source.txt')
        texts = base, ours, theirs
    else:
        if len(args.paths) != 3:
            parser.error('provide BASE OURS THEIRS or --demo clean|conflict')
        try:
            texts = tuple(engine.read_text(path) for path in args.paths)
        except (OSError, ValueError, UnicodeError) as error:
            print('merge-review: ' + ascii(str(error)), file=sys.stderr)
            return 2
    try:
        report = packet(*texts)
    except (ValueError, UnicodeError) as error:
        print('merge-review: ' + ascii(str(error)), file=sys.stderr)
        return 2
    output = json.dumps(report, ensure_ascii=True, indent=2) + '\n' if args.format == 'json' else render(report)
    sys.stdout.buffer.write(output.encode('utf-8'))
    return 0 if report['clean'] else 1


if __name__ == '__main__':
    sys.exit(main())
