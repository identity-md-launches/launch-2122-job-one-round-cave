"""Offline behavioral checks; no temporary files, network or environment reads."""
import copy
import importlib.util
import itertools
import random
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('selection_explain', Path(__file__).with_name('explain.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def catalog(packages, roots=None):
    return {'packages': packages, 'roots': {'app': '*'} if roots is None else roots}


class ExplainTests(unittest.TestCase):
    def assert_graph(self, result):
        edges, nodes = result['requirements'], result['nodes']
        for package, node in nodes.items():
            self.assertIn(node['via'], node['incoming'])
            self.assertEqual(node['incoming'], [i for i, e in enumerate(edges) if e['package'] == package])
            seen, cursor = set(), package
            while cursor is not None:
                self.assertNotIn(cursor, seen)
                seen.add(cursor)
                edge = edges[nodes[cursor]['via']]
                self.assertEqual(edge['package'], cursor)
                cursor = edge['source']
        self.assertEqual(result['violations'], [i for i, e in enumerate(edges) if not e['satisfied']])

    def test_chain_and_shortest_path(self):
        data = catalog({'app': {'1': {'b': '*'}}, 'b': {'1': {'c': '==1'}}, 'c': {'1': {}}})
        out = m.explain(data, {'app': '1', 'b': '1', 'c': '1'}, 'c')
        self.assertEqual(out['status'], 'valid')
        self.assertEqual([out['requirements'][i]['package'] for i in out['why']['path']], ['app', 'b', 'c'])
        self.assertTrue(out['why']['all_path_requirements_satisfied'])
        self.assert_graph(out)

    def test_all_diamond_causes_checked(self):
        data = catalog({'app': {'1': {'b': '*', 'c': '*'}}, 'b': {'1': {'d': '==1'}},
                        'c': {'1': {'d': '==2'}}, 'd': {'1': {}, '2': {}}})
        out = m.explain(data, dict.fromkeys(('app', 'b', 'c', 'd'), '1'), 'd')
        self.assertEqual(out['status'], 'rejected')
        self.assertEqual(len(out['nodes']['d']['incoming']), 2)
        self.assertEqual(len(out['violations']), 1)
        edge = out['requirements'][out['violations'][0]]
        self.assertEqual((edge['source'], edge['package'], edge['issue']), ('c', 'd', 'constraint-mismatch'))
        self.assert_graph(out)

    def test_missing_dependency(self):
        out = m.explain(catalog({'app': {'1': {'missing': '*'}}}), {'app': '1'}, 'missing')
        self.assertEqual(out['unexpanded'], ['missing'])
        self.assertEqual(out['requirements'][1]['issue'], 'missing-selection')
        self.assertFalse(out['why']['all_path_requirements_satisfied'])
        self.assertEqual(out['status'], 'rejected')

    def test_missing_root_does_not_invent_edges(self):
        out = m.explain(catalog({'app': {'1': {'b': '*'}}}), {})
        self.assertEqual(out['expanded'], [])
        self.assertEqual(out['unexpanded'], ['app'])
        self.assertEqual(len(out['requirements']), 1)

    def test_unknown_release(self):
        out = m.explain(catalog({'app': {'1': {'b': '*'}}}), {'app': '99'})
        self.assertEqual(out['requirements'][0]['issue'], 'unknown-release')
        self.assertEqual(out['unknown_selected'], ['app'])
        self.assertNotIn('b', out['nodes'])

    def test_unknown_package(self):
        out = m.explain(catalog({}), {'app': '1'})
        self.assertEqual(out['status'], 'rejected')
        self.assertEqual(out['unknown_selected'], ['app'])

    def test_continue_known_but_mismatched_release(self):
        data = catalog({'app': {'1': {'b': '==2'}}, 'b': {'1': {'c': '*'}}})
        out = m.explain(data, {'app': '1', 'b': '1'}, 'c')
        self.assertEqual([out['requirements'][i]['issue'] for i in out['violations']],
                         ['constraint-mismatch', 'missing-selection'])
        self.assertEqual(out['expanded'], ['app', 'b'])
        self.assertFalse(out['why']['all_path_requirements_satisfied'])

    def test_root_constraint_and_direct_root_shortest(self):
        data = catalog({'app': {'1': {'b': '*'}}, 'b': {'1': {}}}, {'app': '*', 'b': '==2'})
        out = m.explain(data, {'app': '1', 'b': '1'}, 'b')
        self.assertEqual(len(out['why']['path']), 1)
        self.assertEqual(out['requirements'][out['why']['path'][0]]['source'], None)
        self.assertFalse(out['why']['all_path_requirements_satisfied'])
        self.assertEqual(len(out['nodes']['b']['incoming']), 2)

    def test_cycles_and_self_edges(self):
        data = catalog({'app': {'1': {'app': '*', 'b': '*'}}, 'b': {'1': {'app': '*'}}})
        out = m.explain(data, {'app': '1', 'b': '1'}, 'b')
        self.assertEqual(out['status'], 'valid')
        self.assertEqual(len(out['requirements']), 4)
        self.assertEqual(len(out['nodes']['app']['incoming']), 3)
        self.assert_graph(out)

    def test_orphans_not_expanded(self):
        data = catalog({'app': {'1': {}}, 'orphan': {'1': {'absent': '*'}}})
        out = m.explain(data, {'app': '1', 'orphan': '1'}, 'orphan')
        self.assertEqual(out['status'], 'rejected')
        self.assertEqual(out['unreachable_selected'], ['orphan'])
        self.assertNotIn('absent', out['nodes'])
        self.assertEqual(out['why']['status'], 'unreachable')
        self.assertEqual(m.explain(data, {'app': '1'}, 'absent')['why']['status'], 'not-required')

    def test_no_release_spelling_guess(self):
        out = m.explain(catalog({'app': {'1.0': {}}}), {'app': '1'})
        self.assertEqual(out['requirements'][0]['issue'], 'unknown-release')
        self.assertEqual(m.explain(catalog({'app': {'1.0': {}}}), {'app': '1.0'})['status'], 'valid')

    def test_aliases_digest_determinism_and_no_mutation(self):
        data = catalog({'My_App': {'1': {'Dep_B': '*'}}, 'dep-b': {'1': {}}}, {'my-app': '*'})
        chosen = {'MY_APP': '1', 'dep.b': '1'}
        before = copy.deepcopy((data, chosen))
        out = m.explain(data, chosen, 'DEP_B')
        other = m.explain(catalog({'dep-b': {'1': {}}, 'my-app': {'1': {'dep-b': '*'}}}, {'my-app': '*'}),
                          {'dep-b': '1', 'my-app': '1'}, 'dep-b')
        self.assertEqual(out, other)
        self.assertEqual((data, chosen), before)
        self.assert_graph(out)

    def test_invalid_inputs(self):
        data = catalog({'app': {'1': {}}})
        for chosen in ([], None, {'app': 1}, {'app': '*'}, {'A_B': '1', 'a-b': '1'},
                       {'bad/name': '1'}, {str(i): '1' for i in range(1001)}):
            with self.subTest(chosen_type=type(chosen).__name__), self.assertRaises(m.fmt.Invalid):
                m.explain(data, chosen)
        with self.assertRaises(m.fmt.Invalid):
            m.explain(catalog({'app': {'1': {}, '1.0': {}}}), {})
        with self.assertRaises(m.fmt.Invalid):
            m.explain(data, {'app': '1'}, '../outside')

    def test_deep_chain_is_iterative(self):
        packages = {f'p{i}': {'1': {f'p{i+1}': '*'} if i < 499 else {}} for i in range(500)}
        out = m.explain(catalog(packages, {'p0': '*'}), dict.fromkeys(packages, '1'), 'p499')
        self.assertEqual(out['status'], 'valid')
        self.assertEqual(len(out['why']['path']), 500)

    def test_historical_requests(self):
        data = m.fmt.load(m.CHECKER.parent.parent / 'offline-resolver/examples/requests.json')
        chosen = m.fmt.load(m.CHECKER.parent.parent / 'lock-plan/examples/baseline.json')
        rejected = m.explain(data, chosen, 'idna')
        self.assertEqual(rejected['requirements'][rejected['violations'][0]]['package'], 'requests')
        chosen['requests'] = '2.32.5'
        out = m.explain(data, chosen, 'idna')
        self.assertEqual(out['status'], 'valid')
        self.assertEqual(len(out['requirements']), 6)
        self.assertEqual(len(out['nodes']['urllib3']['incoming']), 2)
        self.assertEqual([out['requirements'][i]['package'] for i in out['why']['path']], ['requests', 'idna'])
        self.assert_graph(out)

    def test_seeded_equivalence_to_separate_checker(self):
        rng = random.Random(2804)
        # Exercise every selection of each generated three-package catalog,
        # including missing roots, orphans, cycles and unknown versions.
        for _ in range(100):
            packages = {p: {v: {q: rng.choice(('*', '==1', '==2', '>2'))
                                for q in ('app', 'b', 'c', 'missing') if rng.random() < .2}
                            for v in ('1', '2') if rng.random() < .85}
                        for p in ('app', 'b', 'c')}
            data = catalog(packages, {'app': rng.choice(('*', '==1', '==2'))})
            normalized, roots = m.fmt.validate(data)
            for values in itertools.product((None, '1', '2', '99'), repeat=3):
                chosen = {p: v for p, v in zip(('app', 'b', 'c'), values) if v is not None}
                out = m.explain(data, chosen, 'c')
                expected = m.checker.assignment(normalized, roots, chosen)
                self.assertEqual(out['status'] == 'valid', expected is not None and expected == chosen)
                self.assert_graph(out)


if __name__ == '__main__':
    unittest.main()
