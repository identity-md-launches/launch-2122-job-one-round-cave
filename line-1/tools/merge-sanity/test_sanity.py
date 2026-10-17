"""Offline integration and adversarial checks for Merge Sanity."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('sanity', Path(__file__).with_name('sanity.py'))
sanity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sanity)


def source(files, directories=()):
    return {'files': files, 'directories': set(directories)}


class SanityTests(unittest.TestCase):
    def test_demo_detects_clean_merge_duplicate(self):
        report = sanity.demo()
        self.assertTrue(report['text_merge_clean'])
        self.assertFalse(report['passed'])
        entry = report['files'][0]
        self.assertEqual(entry['findings'], [{'check': 'strict-json',
                         'classification': 'candidate-only'}])
        self.assertTrue(all(side['strict-json']['ok'] for side in entry['sources'].values()))

    def test_python_scope_error(self):
        result = sanity.checks('a.py', 'return 1\n')
        self.assertFalse(result['python-compile']['ok'])
        self.assertEqual(result['python-compile']['line'], 1)

    def test_python_is_never_executed(self):
        result = sanity.checks('a.py', 'raise RuntimeError("MUST NOT EXECUTE")\nimport missing_module\n')
        self.assertTrue(result['python-compile']['ok'])

    def test_python_duplicate_arguments(self):
        result = sanity.checks('a.pyi', 'def f(a, a): ...\n')
        self.assertFalse(result['python-compile']['ok'])

    def test_python_unicode_crlf(self):
        self.assertTrue(sanity.checks('a.py', 'café = "frog"\r\n')['python-compile']['ok'])

    def test_strict_json(self):
        for text in ('{"a":1,"a":2}', '{"a":{"x":1,"x":2}}', 'NaN', 'Infinity', '-Infinity', '[1,]'):
            with self.subTest(text=text):
                self.assertFalse(sanity.checks('a.json', text)['strict-json']['ok'])

    def test_json_numbers_not_machine_float_limits(self):
        for text in ('1e9999', '9' * 5000, '{"é":1,"e":2}', 'null'):
            self.assertTrue(sanity.checks('a.json', text)['strict-json']['ok'])

    def test_nested_json_limit_is_finding(self):
        result = sanity.checks('a.json', '[' * 1500 + '0' + ']' * 1500)
        self.assertFalse(result['strict-json']['ok'])

    def test_json_nesting_boundary_and_escaped_strings(self):
        for depth in (128, 129):
            result = sanity.checks('a.json', '[' * depth + '0' + ']' * depth)
            self.assertEqual(result['strict-json']['ok'], depth == 128)
        text = json.dumps({'brackets': '[' * 500 + '\\"' + ']' * 500})
        self.assertTrue(sanity.checks('a.json', text)['strict-json']['ok'])

    def test_markers_all_four_forms_and_longer_runs(self):
        result = sanity.checks('readme.txt', '<<<<<<< OURS\n||||||| BASE\n=======\n>>>>>>>> THEIRS\n')
        self.assertEqual(result['conflict-markers']['lines'], [1, 2, 3, 4])

    def test_marker_lookalikes_and_bounded_locations(self):
        self.assertTrue(sanity.checks('a.txt', '<<<<<< ours\ntext =======\n>>>>>>>word\n')['conflict-markers']['ok'])
        result = sanity.checks('a.txt', '=======\n' * 30)['conflict-markers']
        self.assertEqual(result['count'], 30)
        self.assertEqual(len(result['lines']), 20)
        self.assertTrue(result['locations_truncated'])

    def test_unsupported_format_is_explicit(self):
        result = sanity.inspect([source({'a.sol': 'not Solidity'})] * 3)
        self.assertEqual(set(result['files'][0]['checks']), {'conflict-markers'})

    def test_conflicts_block_overall(self):
        result = sanity.inspect([source({'a.py': text}) for text in ('x=0\n', 'x=1\n', 'x=2\n')])
        self.assertFalse(result['passed'])
        self.assertEqual(result['counts']['blocked'], 1)
        self.assertNotIn('checks', result['files'][0])

    def test_path_collision_blocks(self):
        result = sanity.inspect([source({'a': ''}), source({}, ['a']), source({'a': ''})])
        self.assertFalse(result['passed'])
        self.assertEqual(result['files'][0]['status'], 'blocked')

    def test_deletion_and_addition(self):
        result = sanity.inspect([source({'gone.json': '{}'}),
                                 source({'new.py': 'x = 1\n'}), source({'gone.json': '{}'})])
        self.assertTrue(result['passed'])
        self.assertEqual(result['counts']['deleted'], 1)
        self.assertEqual(result['counts']['checked'], 1)

    def test_existing_error_never_suppressed(self):
        result = sanity.inspect([source({'a.py': 'return 1\n'})] * 3)
        self.assertFalse(result['passed'])
        self.assertEqual(result['files'][0]['findings'][0]['classification'],
                         'also-in-branch-or-branch-absent')

    def test_no_source_text_in_report(self):
        report = sanity.inspect([source({'a.py': 'SENSITIVE_SENTINEL = (\n'})] * 3)
        self.assertNotIn('SENSITIVE_SENTINEL', json.dumps(report))

    def test_nontext_rejected(self):
        for text in ('a\x00b', 'x\n' * 4001, 'x' * (1024 * 1024 + 1)):
            with self.assertRaises(ValueError):
                sanity.checks('a.py', text)

    def test_filesystem_and_cli(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            roots = [Path(folder) / side for side in ('base', 'ours', 'theirs')]
            before = {}
            for root in roots:
                root.mkdir()
                path = root / 'program.py'
                path.write_bytes('café = "frog"\r\n'.encode())
                before[path] = hashlib.sha256(path.read_bytes()).hexdigest()
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(sanity.main([str(root) for root in roots]), 0)
            report = json.loads(output.getvalue())
            self.assertTrue(report['passed'])
            self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
            self.assertEqual(list(roots[0].iterdir()), [roots[0] / 'program.py'])
            (roots[1] / 'program.py').write_text('return 1\n')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sanity.main([str(root) for root in roots]), 1)
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sanity.main([str(roots[0]), str(roots[1]), str(roots[2] / 'missing')]), 2)
                self.assertEqual(out.getvalue(), '')

    def test_symlink_rejected(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            root = Path(folder)
            (root / 'a.py').write_text('x=1\n')
            (root / 'link.py').symlink_to('a.py')
            with self.assertRaises(ValueError):
                sanity.from_directories([root] * 3)

    def test_path_escape_and_traversal_rejected(self):
        for path in ('../outside', '/outside-workspace'):
            with self.assertRaises(ValueError):
                sanity.from_directories([path] * 3)

    def test_demo_exit_means_finding(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(sanity.main(['--demo']), 1)
        self.assertEqual(json.loads(output.getvalue())['schema'], 'merge-sanity/v1')


if __name__ == '__main__':
    unittest.main()
