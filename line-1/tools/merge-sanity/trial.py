"""Try Merge Sanity on workspace copies of the six real inherited merger files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

SPEC = importlib.util.spec_from_file_location('trial_sanity', Path(__file__).with_name('sanity.py'))
sanity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sanity)


def digests(paths):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    original = Path('line-1/tools/threeway')
    names = ['merge.py', 'test_merge.py', 'README.md',
             'examples/base.txt', 'examples/ours.txt', 'examples/theirs.txt']
    before_original = digests([original / name for name in names])
    Path('test/scratch').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir='test/scratch') as folder:
        roots = [Path(folder) / side for side in sanity.tree.SIDES]
        for root in roots:
            for name in names:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((original / name).read_bytes())
        ours_readme = roots[1] / 'README.md'
        ours_readme.write_bytes(ours_readme.read_bytes() + b'\nReview both contributors before adopting a merge.\n')
        theirs_program = roots[2] / 'merge.py'
        text = theirs_program.read_bytes()
        theirs_program.write_bytes(text.replace(b'def edits(base, changed, side):',
                                                b'# Retain each contributor.\ndef edits(base, changed, side):'))
        paths = [root / name for root in roots for name in names]
        before = digests(paths)
        clean = sanity.from_directories(roots)
        assert clean['passed'] and clean['text_merge_clean']
        assert digests(paths) == before
        theirs_program.write_bytes(theirs_program.read_bytes().replace(
            b'def edits(base, changed, side):', b'def edits(base, changed, base):'))
        before = digests(paths)
        broken = sanity.from_directories(roots)
        assert broken['text_merge_clean'] and not broken['passed']
        findings = [entry for entry in broken['files'] if entry['status'] == 'findings']
        assert len(findings) == 1 and findings[0]['path'] == 'merge.py'
        assert findings[0]['checks']['python-compile']['problem'] == 'syntax-error'
        assert digests(paths) == before
    assert digests([original / name for name in names]) == before_original
    print(json.dumps({
        'source_sha256': before_original,
        'files_per_tree': len(names), 'source_bytes_unchanged': True,
        'independent_readme_and_code_comments': clean['counts'],
        'clean_text_merge_with_python_error': {
            'text_merge_clean': broken['text_merge_clean'], 'passed': broken['passed'],
            'path': findings[0]['path'], 'findings': findings[0]['findings'],
            'python_check': findings[0]['checks']['python-compile']},
        'demo_both_branches_valid_candidate_invalid': sanity.demo(),
        'authority': 'Local observations only; no independent certification.'}, indent=2))


if __name__ == '__main__':
    main()
