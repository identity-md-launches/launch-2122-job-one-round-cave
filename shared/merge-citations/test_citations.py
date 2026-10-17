"""Behavioral tests for the merge/citation handoff; workspace scratch only."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('merge_citations_test', HERE / 'check_citations.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Citations(unittest.TestCase):
    def setUp(self):
        self.text = 'intro\nZTO\n18 decimals\nend\n'
        self.anchor = m.anchor_tool.capture_bytes(self.text.encode(), 'note.md', 2, 3)

    def trees(self, ours=None, theirs=None):
        return [{'files': {'note.md': text}, 'directories': set()}
                for text in (self.text, self.text if ours is None else ours,
                             self.text if theirs is None else theirs)]

    def test_real_demo(self):
        result = m.demo()
        self.assertEqual(result['status'], 'ready-for-review')
        self.assertEqual(result['candidate']['unique_current_citation']['citation'], 'zto.md:5-8')
        self.assertEqual(result['candidate_sha256'], result['candidate']['current_sha256'])
        self.assertFalse(result['candidate']['source_verified'])

    def test_independent_edits_and_immutable_inputs(self):
        trees = self.trees('heading\n' + self.text, self.text + 'footnote\n')
        before = copy.deepcopy((trees, self.anchor))
        result = m.inspect(trees, self.anchor)
        self.assertEqual((trees, self.anchor), before)
        self.assertEqual(result['candidate']['status'], 'relocated')
        self.assertIn('+heading', result['candidate_diff_from_base'])
        self.assertIn('+footnote', result['candidate_diff_from_base'])

    def test_changed_passage_is_not_replaced(self):
        result = m.inspect(self.trees(self.text.replace('18', '19')), self.anchor)
        self.assertEqual(result['status'], 'needs-review')
        self.assertEqual(result['candidate']['status'], 'missing')
        self.assertIsNone(result['candidate']['unique_current_citation'])

    def test_duplicate_passage_is_ambiguous(self):
        result = m.inspect(self.trees(self.text + 'ZTO\n18 decimals\n'), self.anchor)
        self.assertEqual(result['candidate']['status'], 'ambiguous')
        self.assertEqual(result['candidate']['match_count'], 2)
        self.assertEqual(result['status'], 'needs-review')

    def test_conflict_has_no_candidate_citation(self):
        result = m.inspect(self.trees(self.text.replace('18', '17'),
                                      self.text.replace('18', '19')), self.anchor)
        self.assertEqual(result['status'], 'blocked')
        self.assertIsNone(result['candidate'])
        self.assertIsNone(result['candidate_sha256'])

    def test_unrelated_conflict_blocks_overall_review(self):
        trees = self.trees()
        for tree, text in zip(trees, ('base\n', 'ours\n', 'theirs\n')):
            tree['files']['other.md'] = text
        result = m.inspect(trees, self.anchor)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['conflicted_paths'], ['other.md'])
        self.assertEqual(result['candidate']['status'], 'unchanged')

    def test_deletion_is_distinct_from_missing_excerpt(self):
        trees = self.trees()
        trees[2]['files'].pop('note.md')
        result = m.inspect(trees, self.anchor)
        self.assertEqual(result['status'], 'deleted')
        self.assertEqual(result['candidate']['status'], 'deleted')
        self.assertIsNone(result['candidate_sha256'])

    def test_delete_modify_conflict(self):
        trees = self.trees('heading\n' + self.text)
        trees[2]['files'].clear()
        result = m.inspect(trees, self.anchor)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['merge_status'], 'delete-modify-conflict')

    def test_path_collision(self):
        trees = self.trees()
        trees[2] = {'files': {'note.md/child.txt': 'child'}, 'directories': {'note.md'}}
        result = m.inspect(trees, self.anchor)
        self.assertEqual(result['merge_status'], 'path-conflict')
        self.assertIsNone(result['candidate'])

    def test_stale_and_forged_anchors(self):
        for change in ({'sha256': 'a' * 64}, {'text': 'OTHER\n18 decimals'},
                       {'line_start': 1, 'line_end': 2}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.inspect(self.trees(), dict(self.anchor, **change))
        trees = self.trees()
        trees[0]['files'].clear()
        with self.assertRaises(ValueError):
            m.inspect(trees, self.anchor)

    def test_crlf_and_unicode_are_exact(self):
        result = m.inspect(self.trees(self.text.replace('\n', '\r\n')), self.anchor)
        self.assertEqual(result['candidate']['status'], 'same_lines_changed_source')
        result = m.inspect(self.trees(self.text.replace('ZTO', 'ＺＴＯ')), self.anchor)
        self.assertEqual(result['candidate']['status'], 'missing')

    def test_workspace_cli_and_portability(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as temp:
            root = Path(temp)
            paths = [root / side for side in m.tree.SIDES]
            for path, text in zip(paths, (self.text, 'heading\n' + self.text, self.text)):
                path.mkdir()
                (path / 'note.md').write_bytes(text.encode())
            anchor = root / 'anchor.json'
            anchor.write_text(json.dumps(self.anchor))
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            command = [sys.executable, '-B', str(HERE / 'check_citations.py'),
                       'review', *map(str, paths), str(anchor)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['source_trees_rechecked'])
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            (paths[1] / 'note.md').write_text(self.text.replace('ZTO', 'changed'))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            anchor.write_text('{"format":1,"format":2}')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            copied = root / 'standalone'
            shutil.copytree(HERE, copied)
            result = subprocess.run([sys.executable, '-B', str(copied / 'check_citations.py'),
                                     'demo'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'ready-for-review')

    def test_concurrent_change_rejected(self):
        snapshots = self.trees() + self.trees('later\n' + self.text)
        with patch.object(m.tree, 'snapshot', side_effect=snapshots):
            with self.assertRaisesRegex(ValueError, 'changed during review'):
                m.from_directories(['base', 'ours', 'theirs'], self.anchor)

    def test_symlink_and_parent_traversal_rejected(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as temp:
            root = Path(temp)
            (root / 'note.md').symlink_to('missing')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                m.from_directories([root] * 3, self.anchor)
            with self.assertRaises(ValueError):
                m.from_directories([root / '..'] * 3, self.anchor)


if __name__ == '__main__':
    unittest.main()
