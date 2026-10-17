"""Check the shared integrations and copied-source provenance, offline."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def main():
    results = []
    for name in ('proof-search', 'merge-dependencies', 'proof-handoff', 'merge-citations'):
        command = [sys.executable, '-B', '-m', 'unittest', 'discover',
                   '-s', 'shared/' + name, '-p', 'test_*.py', '-v']
        proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
        count = re.search(r'Ran (\d+) tests?', proc.stderr)
        results.append({'tool': name, 'command': command, 'exit': proc.returncode,
                        'tests': int(count[1]) if count else 0, 'log': proc.stderr})
        print(name, results[-1]['tests'], proc.returncode)
    root = Path('shared/proof-handoff')
    provenance = json.loads((root / 'PROVENANCE.json').read_text())
    source_drift = []
    for item in provenance:
        assert hashlib.sha256((root / item['copy']).read_bytes()).hexdigest() == item['sha256']
        current = hashlib.sha256(Path(item['source']).read_bytes()).hexdigest()
        if current != item['sha256']:
            source_drift.append({'source': item['source'], 'current_sha256': current,
                                 'frozen_copy_sha256': item['sha256']})
    adapted = json.loads(Path('shared/merge-dependencies/SECOND-CHECK-PROVENANCE.json').read_text())
    for key, hash_key in [('source', 'source_sha256'), ('copy', 'copy_sha256')]:
        assert hashlib.sha256(Path(adapted[key]).read_bytes()).hexdigest() == adapted[hash_key]
    source = Path(adapted['source']).read_text().replace(
        "ENGINE = Path(__file__).resolve().parent.parent / 'offline-resolver' / 'resolve.py'",
        "ENGINE = Path(__file__).resolve().parent / 'resolve.py'")
    assert source[:source.index('\ndef main(argv=None):')] + '\n' == Path(adapted['copy']).read_text()
    root_repair = json.loads(Path('shared/merge-dependencies/REPAIR-PROVENANCE.json').read_text())
    for key, hash_key in [('source', 'source_sha256'), ('copy', 'copy_sha256')]:
        assert hashlib.sha256(Path(root_repair[key]).read_bytes()).hexdigest() == root_repair[hash_key]
    lock_plan = json.loads(Path('shared/merge-dependencies/LOCK-PLAN-PROVENANCE.json').read_text())
    for key, hash_key in [('source', 'source_sha256'), ('copy', 'copy_sha256')]:
        assert hashlib.sha256(Path(lock_plan[key]).read_bytes()).hexdigest() == lock_plan[hash_key]
    audit_provenance = json.loads(Path('shared/merge-dependencies/PLAN-AUDIT-PROVENANCE.json').read_text())
    for key, hash_key in [('source', 'source_sha256'), ('copy', 'copy_sha256')]:
        assert hashlib.sha256(Path(audit_provenance[key]).read_bytes()).hexdigest() == audit_provenance[hash_key]
    audited_command = [sys.executable, '-B', 'shared/merge-dependencies/audited_plan.py', 'demo']
    audited_proc = subprocess.run(audited_command, capture_output=True, text=True, timeout=60)
    assert audited_proc.returncode == 0, audited_proc.stderr
    audited_result = json.loads(audited_proc.stdout)
    assert audited_result['status'] == 'audited'
    plan_command = [sys.executable, '-B', 'shared/merge-dependencies/plan_merge.py', 'demo']
    plan_proc = subprocess.run(plan_command, capture_output=True, text=True, timeout=60)
    assert plan_proc.returncode == 0, plan_proc.stderr
    plan_result = json.loads(plan_proc.stdout)
    assert plan_result['status'] == 'planned'
    assert plan_result['plan']['minimum_change_count'] == 1
    second_command = [sys.executable, '-B', 'shared/merge-dependencies/second_check.py', 'demo']
    second = subprocess.run(second_command, capture_output=True, text=True, timeout=60)
    assert second.returncode == 0, second.stderr
    second_result = json.loads(second.stdout)
    assert second_result['status'] == 'unsatisfiable'
    assert second_result['enumeration']['checked_assignments'] == second_result['enumeration']['candidate_assignments']
    repair_command = [sys.executable, '-B', 'shared/merge-dependencies/repair_merge.py', 'demo']
    repair_proc = subprocess.run(repair_command, capture_output=True, text=True, timeout=60)
    assert repair_proc.returncode == 0, repair_proc.stderr
    repair_result = json.loads(repair_proc.stdout)
    assert repair_result['status'] == 'repair_proposed'
    assert repair_result['repair']['minimum_removed_count'] == 1
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='shared30-') as temp:
        copied = Path(temp) / 'merge-dependencies'
        shutil.copytree('shared/merge-dependencies', copied)
        portable = subprocess.run([sys.executable, '-B', str(copied/'repair_merge.py'), 'demo'],
                                  capture_output=True, text=True, timeout=60)
        assert portable.returncode == 0, portable.stderr
        assert json.loads(portable.stdout)['status'] == 'repair_proposed'
    command = [sys.executable, '-B', str(root / 'handoff.py'), 'check',
               str(root / 'tools/proof-set/examples/zto-and-pool.json'),
               '--block-hash', '0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc',
               '--manifest-sha256', 'a4e9d3fb56c90bf1202ac3d53b8ce7c557febe06d88581a9430a2f6a59f14e8f',
               '--bundle', str(root / 'examples/zto-proof-bundle.json'),
               '--expected-sha256', '57ba25ab26d159efaa1c07dc28c1dc0a0e0914049df9646b46374fd04621089f']
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    choices_command = [sys.executable, '-B', 'shared/merge-dependencies/merge_choices.py', 'demo']
    choices_proc = subprocess.run(choices_command, capture_output=True, text=True, timeout=60)
    assert choices_proc.returncode == 0, choices_proc.stderr
    choices = json.loads(choices_proc.stdout)
    assert choices['status'] == 'mapped'
    release_provenance = json.loads(Path('shared/merge-dependencies/RELEASE-MAP-PROVENANCE.json').read_text())
    for key, hash_key in [('source', 'source_sha256'), ('copy', 'copy_sha256')]:
        assert hashlib.sha256(Path(release_provenance[key]).read_bytes()).hexdigest() == release_provenance[hash_key]
    citation_root = Path('shared/merge-citations')
    for item in json.loads((citation_root / 'PROVENANCE.json').read_text()):
        assert hashlib.sha256((citation_root / item['copy']).read_bytes()).hexdigest() == item['sha256']
        assert hashlib.sha256(Path(item['source']).read_bytes()).hexdigest() == item['sha256']
    citation_command = [sys.executable, '-B', str(citation_root / 'check_citations.py'), 'demo']
    citation_run = subprocess.run(citation_command, capture_output=True, text=True, timeout=60)
    assert citation_run.returncode == 0, citation_run.stderr
    citation_result = json.loads(citation_run.stdout)
    assert citation_result['candidate']['unique_current_citation']['citation'] == 'zto.md:5-8'
    report = {'citation_demo': citation_result, 'citation_provenance_verified': True, 'choices_demo': choices, 'release_map_source_hashes_verified': True, 'suites': results, 'total_tests': sum(r['tests'] for r in results),
              'copied_files_match_current_sources': len(provenance) - len(source_drift),
              'frozen_copies_verified': len(provenance),
              'source_drift': source_drift,
              'adapted_exhaustive_source_verified': True,
              'root_repair_source_hashes_verified': True,
              'lock_plan_source_hashes_verified': True,
              'plan_audit_source_hashes_verified': True,
              'audited_demo': {'command': audited_command, 'exit': audited_proc.returncode, 'result': audited_result},
              'plan_demo': {'command': plan_command, 'exit': plan_proc.returncode, 'result': plan_result},
              'portable_repair_demo': {'exit': portable.returncode, 'status': 'repair_proposed'},
              'repair_demo': {'command': repair_command, 'exit': repair_proc.returncode,
                              'result': repair_result},
              'second_check_demo': {'command': second_command, 'exit': second.returncode, 'result': second_result},
              'example': {'command': command, 'exit': proc.returncode,
                          'result': json.loads(proc.stdout)}}
    Path('gathering/shared-checks-30.json').write_text(json.dumps(report, indent=2)+'\n')
    assert all(r['exit'] == 0 and r['tests'] > 0 for r in results)
    assert report['example']['result']['verified'] is True


if __name__ == '__main__':
    main()
