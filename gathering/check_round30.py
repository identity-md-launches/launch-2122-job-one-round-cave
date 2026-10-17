"""Run documented line tool tests and demos without editing any line folder."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = {
    1: ('threeway', 'merge-review', 'tree-review', 'review-recheck',
        'candidate-export', 'conflict-finish', 'stage-audit', 'resolution-review', 'merge-sanity'),
    2: ('state-witness', 'header-anchor', 'code-witness', 'proof-set',
        'pool-state', 'header-chain', 'state-diff', 'ancestry-diff', 'proof-pack', 'state-gate'),
    3: ('evidence-search', 'corpus-freshness', 'search-receipt',
        'evidence-bundle', 'corpus-change-receipt', 'query-impact',
        'collection-guide', 'reading-list', 'phrase-finder', 'citation-reanchor'),
    4: ('offline-resolver', 'conflict-core', 'exhaustive-audit',
        'root-repair', 'lock-plan', 'plan-audit', 'release-map', 'selection-explain'),
}

DEMOS = [
    (1, 'conflict-finish/test_finish.py', []),
    (1, 'resolution-review/review.py', ['--demo']),
    (2, 'proof-pack/pack.py', ['demo']),
    (2, 'proof-pack/pack.py', ['demo', '--pool']),
    (3, 'phrase-finder/phrases.py', ['demo']),
    (4, 'release-map/release_map.py', ['demo']),
    (1, 'stage-audit/test_audit.py', []),
    (2, 'ancestry-diff/ancestry_diff.py', ['demo']),
    (3, 'reading-list/reading_list.py', ['demo']),
    (4, 'plan-audit/audit_plan.py', ['demo']),
    (1, 'threeway/merge.py', ['--demo', '--format', 'json']),
    (1, 'merge-review/review.py', ['--demo', 'clean', '--format', 'json']),
    (1, 'tree-review/tree_review.py', ['--demo', 'clean', '--format', 'json']),
    (1, 'review-recheck/recheck.py', ['--demo', 'clean']),
    (1, 'candidate-export/export.py', ['--demo']),
    (2, 'state-witness/witness.py', ['demo']),
    (2, 'header-anchor/anchor.py', ['demo']),
    (2, 'code-witness/code_witness.py', ['demo']),
    (2, 'proof-set/proof_set.py', ['demo']),
    (2, 'pool-state/pool_state.py', ['demo']),
    (2, 'header-chain/header_chain.py', ['demo']),
    (2, 'header-chain/header_chain.py', ['demo', '--pool']),
    (2, 'state-diff/state_diff.py', ['demo']),
    (2, 'state-diff/state_diff.py', ['demo', '--zto']),
    (3, 'evidence-search/search.py', ['demo']),
    (3, 'corpus-freshness/freshness.py', ['demo']),
    (3, 'search-receipt/receipt.py', ['demo']),
    (3, 'evidence-bundle/bundle.py', ['demo']),
    (3, 'corpus-change-receipt/receipt.py', ['demo']),
    (3, 'query-impact/impact.py', ['demo']),
    (3, 'collection-guide/guide.py', ['demo']),
    (4, 'offline-resolver/resolve.py', ['demo']),
    (4, 'conflict-core/core.py', ['demo']),
    (4, 'exhaustive-audit/audit.py', ['demo']),
    (4, 'root-repair/repair.py', ['demo']),
    (4, 'lock-plan/plan.py', ['demo']),
]


def fingerprints():
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for n in range(1, 5)
            for folder in (Path(f'line-{n}'), Path(f'dist/line-{n}'))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def run(args, timeout=180, expected=0):
    proc = subprocess.run([sys.executable, '-B', *args], capture_output=True,
                          text=True, timeout=timeout)
    result = {'command': 'python3 -B ' + ' '.join(args), 'exit': proc.returncode, 'expected_exit': expected,
              'stdout_tail': proc.stdout[-600:], 'stderr_tail': proc.stderr[-600:]}
    if proc.returncode != expected:
        raise AssertionError(result)
    return result


def main():
    before = fingerprints()
    suites, demos = [], []
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='gathering30-') as temp:
        copy = Path(temp) / 'offline-resolver'
        shutil.copytree('line-4/tools/offline-resolver', copy)
        for n, names in TOOLS.items():
            for name in names:
                folder = f'line-{n}/tools/{name}'
                target = str(copy) if name == 'offline-resolver' else folder
                result = run(['-m', 'unittest', 'discover', '-s', target,
                              '-p', 'test_*.py'], 180)
                match = re.search(r'Ran (\d+) tests?', result['stderr_tail'])
                result.update(tool=folder, tests=int(match[1]) if match else 0)
                if not result['tests']:
                    raise AssertionError(result)
                suites.append(result)
                print(folder, result['tests'], flush=True)
    DEMOS.extend([(1, 'merge-sanity/sanity.py', ['--demo']), (1, 'merge-sanity/trial.py', []), (2, 'state-gate/gate.py', ['demo']), (2, 'state-gate/gate.py', ['demo', '--reject']), (3, 'citation-reanchor/reanchor.py', ['demo']), (4, 'selection-explain/explain.py', ['demo', '--why', 'idna'])])
    for n, script, args in DEMOS:
        expected = 1 if script == 'merge-sanity/sanity.py' else 3 if '--reject' in args else 0
        result = run([f'line-{n}/tools/{script}', *args], 90, expected)
        result['line'] = n
        demos.append(result)
        print(result['command'], 'ok', flush=True)
    after = fingerprints()
    if before != after:
        raise AssertionError('line files or records changed')
    report = {'suites': suites, 'demos': demos,
              'total_tests': sum(item['tests'] for item in suites),
              'line_files_unchanged': True, 'protected_files': before}
    Path('gathering/checks-30.json').write_text(json.dumps(report, indent=2) + '\n')
    print('TOTAL', report['total_tests'], 'tests;', len(demos), 'demos')


if __name__ == '__main__':
    main()
