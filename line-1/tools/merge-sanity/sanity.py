#!/usr/bin/env python3
"""Check recomputed merge candidates without executing any candidate code."""
import argparse
import decimal
import importlib.util
import json
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'tree-review' / 'tree_review.py'
SPEC = importlib.util.spec_from_file_location('sanity_tree', SOURCE)
tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tree)
MARKER = re.compile(r'^(?:<{7,}|\|{7,}|={7,}|>{7,})(?:\s|$)')
MAX_JSON_DEPTH = 128
LIMITS = [
    'Selected static checks only; passing is neither semantic correctness nor approval.',
    'Python is compiled but never executed, imported, or used to resolve imports.',
    'Python validity depends on the interpreter running this tool.',
    'JSON requires unique keys, finite numeric literals and depth <=128; no schema is checked.',
    'Marker-like lines can be intentional prose; inspect every finding.',
    'Other file formats receive only the conflict-marker check.',
    'Bounded UTF-8 stable workspace trees; no atomic snapshots or race protection.',
    'Hashes identify bytes, not authors. No files are written.']


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def reject_constant(_):
    raise ValueError('non-finite JSON literal')


def json_depth_exceeded(text):
    # Bound nesting before recursive parsing; brackets in strings do not count.
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return True
        elif char in ']}':
            depth -= 1
    return False


def checks(name, text):
    """Results contain locations, never source snippets or user exception text."""
    tree.validate_text(text)
    locations = [number for number, line in enumerate(text.splitlines(), 1)
                 if MARKER.match(line)]
    result = {'conflict-markers': {
        'ok': not locations, 'count': len(locations), 'lines': locations[:20],
        'locations_truncated': len(locations) > 20}}
    suffix = Path(name).suffix
    if suffix in ('.py', '.pyi'):
        try:
            # Compile catches scope errors missed by ast.parse, without running code.
            compile(text, '<candidate>', 'exec', dont_inherit=True, optimize=0)
            result['python-compile'] = {'ok': True}
        except SyntaxError as error:
            result['python-compile'] = {
                'ok': False, 'problem': 'syntax-error',
                'line': error.lineno, 'column': error.offset}
        except (ValueError, OverflowError, RecursionError):
            result['python-compile'] = {'ok': False, 'problem': 'compiler-limit'}
    elif suffix == '.json':
        if json_depth_exceeded(text):
            result['strict-json'] = {'ok': False, 'problem': 'nesting-limit'}
            return result
        try:
            # Avoid float overflow and Python's integer string length limit.
            json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant,
                       parse_float=decimal.Decimal, parse_int=str)
            result['strict-json'] = {'ok': True}
        except json.JSONDecodeError as error:
            result['strict-json'] = {'ok': False, 'problem': 'invalid-json',
                                     'line': error.lineno, 'column': error.colno}
        except (ValueError, decimal.InvalidOperation):
            result['strict-json'] = {'ok': False, 'problem': 'duplicate-key-or-nonfinite-literal'}
        except (RecursionError, OverflowError):
            result['strict-json'] = {'ok': False, 'problem': 'parser-limit'}
    return result


def inspect(sources):
    if len(sources) != 3:
        raise ValueError('exactly three source trees are required')
    packet = tree.combine(sources)
    entries = []
    for entry in packet['files']:
        name = entry['path']
        item = {'path': name, 'merge_status': entry['status'],
                'candidate_sha256': entry['candidate_sha256']}
        if entry['status'].endswith('conflict'):
            item['status'] = 'blocked'
        elif entry['candidate'] is None:
            item['status'] = 'deleted'
        else:
            candidate = checks(name, entry['candidate'])
            original = {side: checks(name, source['files'][name])
                        if name in source['files'] else None
                        for side, source in zip(tree.SIDES, sources)}
            findings = []
            for check, outcome in candidate.items():
                if outcome['ok']:
                    continue
                branches_pass = all(original[side] is not None and
                                    original[side][check]['ok']
                                    for side in ('ours', 'theirs'))
                findings.append({'check': check,
                                 'classification': 'candidate-only' if branches_pass
                                                   else 'also-in-branch-or-branch-absent'})
            item.update(status='findings' if findings else 'checked',
                        checks=candidate, sources=original, findings=findings)
        entries.append(item)
    counts = {key: sum(item['status'] == key for item in entries)
              for key in ('blocked', 'deleted', 'checked', 'findings')}
    return {'schema': 'merge-sanity/v1', 'passed': not (counts['blocked'] or counts['findings']),
            'text_merge_clean': packet['clean'], 'inputs': packet['inputs'],
            'counts': counts, 'files': entries, 'limits': LIMITS}


def from_directories(paths):
    if len(paths) != 3:
        raise ValueError('exactly three source directories are required')
    budget = [0]
    return inspect([tree.snapshot(path, budget) for path in paths])


def demo():
    # Both branches rename a DIFFERENT key to the same key; each is valid alone.
    base = '{\n  "left": 1,\n  "spacer": 0,\n  "right": 2\n}\n'
    versions = (base, base.replace('"left"', '"chosen"'),
                base.replace('"right"', '"chosen"'))
    return inspect([{'files': {'settings.json': text}, 'directories': set()}
                    for text in versions])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='BASE_DIR OURS_DIR THEIRS_DIR')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    if args.demo and args.paths or not args.demo and len(args.paths) != 3:
        parser.error('provide three source trees or --demo')
    try:
        report = demo() if args.demo else from_directories(args.paths)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print('merge-sanity: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
