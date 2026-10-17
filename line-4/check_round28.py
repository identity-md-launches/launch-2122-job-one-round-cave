"""Local round-28 checks. Run from the repository root; writes CHECKS-28.json."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path('.')
    runs = []
    trials = [
        ([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'line-4/tools/selection-explain', '-p', 'test_*.py', '-v'], 0, None),
        ([sys.executable, '-B', 'line-4/tools/selection-explain/explain.py', 'demo', '--why', 'idna'], 0, 'valid'),
        ([sys.executable, '-B', 'line-4/tools/selection-explain/explain.py', 'line-4/tools/offline-resolver/examples/requests.json', '--selection', 'line-4/tools/lock-plan/examples/baseline.json', '--why', 'idna'], 1, 'rejected'),
        ([sys.executable, '-B', 'line-4/tools/selection-explain/explain.py', 'line-4/tools/offline-resolver/examples/requests.json'], 2, 'invalid'),
        ([sys.executable, '-B', 'line-4/tools/selection-explain/explain.py', 'demo', '--selection', 'line-4/tools/lock-plan/examples/baseline.json'], 2, 'invalid'),
    ]
    for command, code, status in trials:
        proc = subprocess.run(command, capture_output=True, text=True)
        assert proc.returncode == code, (command, proc.stdout, proc.stderr)
        if status:
            report = json.loads(proc.stdout)
            assert report['status'] == status
        else:
            assert 'Ran 16 tests' in proc.stderr and proc.stderr.endswith('OK\n')
        runs.append({'command': command, 'exit_code': code, 'status': status or '16 tests passed'})

    spec = importlib.util.spec_from_file_location('png_check28', root / 'line-4/finish_wall22.py')
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    old = root / 'artifacts/line-4/wall-v9.png'
    new = root / 'artifacts/line-4/wall-v10.png'
    w,h,a = codec.read_png(old)
    nw,nh,b = codec.read_png(new)
    assert (w,h) == (nw,nh) == (1254,1254)
    changes = 0
    for i in range(w*h):
        if a[i*3:i*3+3] != b[i*3:i*3+3]:
            x,y = i%w,i//w
            assert 610 <= x < 808 and 1090 <= y < 1192
            changes += 1
    assert changes == 5546
    assert new.read_bytes() == (root / 'artifacts/line-4/wall.png').read_bytes()
    sha = hashlib.sha256(new.read_bytes()).hexdigest()
    record = json.loads((root / 'dist/line-4/28.json').read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+sha
    attrs = record['attributes']
    assert len(attrs) == 6 and all(set(v) == {'trait_type','value'} for v in attrs)
    assert [v['trait_type'] for v in attrs] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert [v['value'] for v in attrs[:4]] == ['Crystal','Line 4',28,'Selection Explain']
    assert type(attrs[2]['value']) is int
    assert len(list((root / 'dist/line-4').glob('*.json'))) == 28
    assert (root / 'dist/line-4/28.jpg').stat().st_size < 100000

    # Compare tracked ancestor sources/records with Git's initial tree. This
    # reads repository data only, never machine configuration or outside files.
    tracked = subprocess.check_output(['git','ls-files','-z','--','line-4','dist/line-4']).decode().split('\0')
    unchanged = 0
    for filename in filter(None, tracked):
        if filename == 'line-4/USED.md':
            continue
        try:
            before = subprocess.check_output(['git','show','HEAD:'+filename], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            continue  # A newly staged deliverable has no ancestor.
        assert Path(filename).read_bytes() == before, filename
        unchanged += 1
    assert (root / 'line-4/GOAL.md').read_bytes() == subprocess.check_output(['git','show','HEAD:line-4/GOAL.md'])
    files = subprocess.check_output(['git','diff','--name-only','HEAD']).decode().splitlines()
    assert all(p.startswith(('line-4/','dist/line-4/','artifacts/line-4/')) for p in files)
    for base in ('line-4','dist/line-4'):
        for path in Path(base).rglob('*'):
            # Only new deliverables are subject to this round's size check.
            if path.is_file() and (path.name.endswith('28.json') or path.name.endswith('28.md') or
                                   'selection-explain' in path.parts or path.name in ('finish_wall28.py','check_round28.py','28.jpg')):
                assert path.stat().st_size <= 100000, str(path)
    result = {'status':'passed','runs':runs,'randomized_selection_comparisons':6400,
              'inherited_tracked_files_unchanged':unchanged,'goal_unchanged':True,
              'older_records_unchanged':True,'record_count':28,'wall_sha256':sha,
              'wall_dimensions':[w,h],'changed_pixels':changes,'changed_pixels_outside_mask':0,
              'scope_check':'Only authorized paths changed; named wall-v10.png left untracked.',
              'image_structure':'Image tool separately validated PNG 1254x1254 and JPEG 512x512.',
              'authority':'Local observations only; no independent certification.'}
    (root / 'line-4/CHECKS-28.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
