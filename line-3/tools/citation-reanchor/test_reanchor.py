import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('reanchor', Path(__file__).with_name('reanchor.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReanchorTests(unittest.TestCase):
    def anchor(self, raw=b'intro\nZTO\n18 decimals\nend\n', start=2, end=3):
        return r.capture_bytes(raw, 'zto.md', start, end)

    def test_unchanged_and_relocated(self):
        raw = b'intro\nZTO\n18 decimals\nend\n'
        anchor = self.anchor(raw)
        before = copy.deepcopy(anchor)
        same = r.check_bytes(anchor, raw)
        self.assertEqual(same['status'], 'unchanged')
        self.assertTrue(same['source_hash_matches'])
        moved = r.check_bytes(anchor, b'new\n' + raw)
        self.assertEqual(moved['status'], 'relocated')
        self.assertEqual(moved['unique_current_citation']['citation'], 'zto.md:3-4')
        self.assertFalse(moved['source_hash_matches'])
        self.assertFalse(moved['source_verified'])
        self.assertEqual(anchor, before)

    def test_changed_elsewhere_same_span(self):
        result = r.check_bytes(self.anchor(), b'intro\nZTO\n18 decimals\nnew ending')
        self.assertEqual(result['status'], 'same_lines_changed_source')
        self.assertFalse(result['source_hash_matches'])

    def test_ambiguous_even_if_original_span_survives(self):
        result = r.check_bytes(self.anchor(), b'intro\nZTO\n18 decimals\nZTO\n18 decimals')
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual(result['match_count'], 2)
        self.assertIsNone(result['unique_current_citation'])

    def test_missing_exact_not_fuzzy(self):
        for raw in [b'ZTO\n19 decimals', b'ZTO 18 decimals', b'ZTO\n18  decimals', b'zto\n18 decimals', b'']:
            result = r.check_bytes(self.anchor(), raw)
            self.assertEqual(result['status'], 'missing')
            self.assertEqual(result['match_count'], 0)

    def test_crlf_and_blank_final_selected_line(self):
        raw = b'intro\r\nZTO\r\n\r\nend\r\n'
        anchor = self.anchor(raw)
        self.assertEqual(anchor['text'], 'ZTO\n')
        result = r.check_bytes(anchor, raw.replace(b'\r\n', b'\n'))
        self.assertEqual(result['status'], 'same_lines_changed_source')
        self.assertEqual(result['unique_current_citation']['line_end'], 3)

    def test_no_unicode_or_whitespace_folding(self):
        anchor = self.anchor('é\n\tZTO'.encode(), 1, 2)
        for text in ['e\u0301\n\tZTO', 'é\n ZTO', 'É\n\tZTO']:
            self.assertEqual(r.check_bytes(anchor, text.encode())['status'], 'missing')

    def test_forged_anchor_same_hash_refused(self):
        anchor = self.anchor()
        anchor['text'] = 'wrong\nexcerpt'
        with self.assertRaises(r.engine.SearchError):
            r.check_bytes(anchor, b'intro\nZTO\n18 decimals\nend\n')

    def test_unchanged_duplicate_scope_is_saved_range(self):
        raw = b'ZTO\nZTO\n'
        anchor = self.anchor(raw, 2, 2)
        result = r.check_bytes(anchor, raw)
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['scope'], 'saved line range')
        self.assertEqual(result['unique_current_citation']['line_start'], 2)

    def test_overlapping_matches_and_output_cap(self):
        anchor = self.anchor(b'a\na\n', 1, 2)
        result = r.check_bytes(anchor, b'a\n' * 102)
        self.assertEqual(result['match_count'], 101)
        self.assertTrue(result['candidates_truncated'])
        self.assertEqual(len(result['candidates']), 50)
        self.assertEqual(result['candidates'][-1]['line_end'], 51)

    def test_matcher_against_exhaustive_oracle(self):
        rng = random.Random(30)
        for _ in range(500):
            lines = [rng.choice(['a', 'b', '']) for _ in range(rng.randrange(40))]
            needle = [rng.choice(['a', 'b', '']) for _ in range(rng.randrange(1, 7))]
            expected = [i + 1 for i in range(len(lines) - len(needle) + 1)
                        if lines[i:i + len(needle)] == needle]
            self.assertEqual(list(r.occurrences(lines, needle)), expected)

    def test_validation_and_bounds(self):
        anchor = self.anchor()
        for key, value in [('path', '../a.md'), ('path', '/a.md'), ('path', 'a.py'),
                           ('path', '.a.md'), ('sha256', 'A' * 64), ('sha256', None),
                           ('line_start', True), ('line_end', 1), ('line_end', 1000),
                           ('text', '\x00\nx'), ('text', '\n'), ('text', '\ud800\nx')]:
            bad = dict(anchor, **{key: value})
            with self.assertRaises(r.engine.SearchError, msg=(key, repr(value))):
                r.validate(bad)
        for raw in [b'\xff', b'\x00', b'x' * (r.engine.MAX_FILE_BYTES + 1),
                    b'x' * (r.engine.MAX_LINE_CHARS + 1)]:
            with self.assertRaises(r.engine.SearchError):
                r.check_bytes(anchor, raw)
        with patch.object(r, 'MAX_ANCHOR_BYTES', 3):
            with self.assertRaises(r.engine.SearchError):
                r.validate(anchor)
        for start, end in [(0, 1), (1, 20), (True, 2), (2, 1)]:
            with self.assertRaises(r.engine.SearchError):
                self.anchor(start=start, end=end)
        with self.assertRaises(r.engine.SearchError):
            self.anchor(b'x\n' * 201, 1, 201)

    def test_live_paths_missing_links_and_concurrent_edit(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as temp:
            root = Path(temp)
            src = root / 'zto.md'
            src.write_bytes(b'intro\nZTO\n18 decimals\nend\n')
            anchor = r.capture(root, 'zto.md', 2, 3)
            self.assertTrue(r.check(root, anchor)['source_verified'])
            with patch.object(r, 'read_source', side_effect=[src.read_bytes(), b'changed']):
                with self.assertRaises(r.engine.SearchError):
                    r.check(root, anchor)
            src.unlink()
            with self.assertRaises(r.engine.SearchError):
                r.check(root, anchor)
            src.symlink_to('absent.md')
            with self.assertRaises(r.engine.SearchError):
                r.check(root, anchor)
            src.unlink()
            with self.assertRaises(r.engine.SearchError):
                r.capture(root, '../zto.md', 1, 1)
            for path in ['/outside-workspace', '../outside-workspace']:
                with self.assertRaises(r.engine.SearchError):
                    r.capture(path, 'zto.md', 1, 1)

    def test_json_and_cli_statuses(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as temp:
            root = Path(temp)
            source = root / 'zto.md'
            source.write_bytes(b'intro\nZTO\n18 decimals\nend\n')
            script = str(Path(r.__file__))
            def run(*args):
                return subprocess.run([sys.executable, '-B', script, *map(str, args)],
                                      capture_output=True, text=True)
            captured = run('capture', root, 'zto.md', 2, 3)
            self.assertEqual(captured.returncode, 0, captured.stderr)
            saved = root / 'anchor.json'
            saved.write_text(captured.stdout)
            original_anchor = saved.read_bytes()
            for raw, code, status in [(source.read_bytes(), 0, 'unchanged'),
                                      (b'moved\n' + source.read_bytes(), 0, 'relocated'),
                                      (b'ZTO\n18 decimals\n' * 2, 1, 'ambiguous'),
                                      (b'gone', 1, 'missing')]:
                source.write_bytes(raw)
                result = run('check', root, saved)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'], status)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(saved.read_bytes(), original_anchor)
            for data in [b'{"format":1,"format":2}', b'{"format":NaN}', b'\xff', b'[]']:
                saved.write_bytes(data)
                failed = run('check', root, saved)
                self.assertEqual(failed.returncode, 2)
                self.assertEqual(failed.stdout, '')
                self.assertIn('error', json.loads(failed.stderr))

    def test_real_historical_demo(self):
        result = r.demo()
        self.assertEqual(result['original']['status'], 'unchanged')
        self.assertEqual(result['layout_edit_in_memory']['status'], 'relocated')
        self.assertIn('0xd782bdea4ef02a0bd391eb9089470c8080f0a68e', result['anchor']['text'])
        self.assertEqual(result['layout_edit_in_memory']['unique_current_citation']['citation'], 'zto.md:5-8')


if __name__ == '__main__':
    unittest.main()
