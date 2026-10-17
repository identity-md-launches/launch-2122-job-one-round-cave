"""Real-chain evidence and adversarial policy tests; no network."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gate_tested', HERE / 'gate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.p = g.load_policy(HERE / 'examples/pool-policy.json')
        self.b = g.w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')

    def check(self):
        return g.evaluate(self.p, self.b, g.w.DEMO_ROOT)

    def test_real_pool(self):
        result = self.check()
        self.assertTrue(result['verified'])
        self.assertTrue(result['accepted'])
        self.assertEqual(len(result['checks']), 4)
        self.assertEqual(result['checks'][-1]['actual'],
                         str(int(self.b['proof']['storageProof'][0]['value'], 16)))

    def test_valid_proof_failed_policy(self):
        self.p['storage'][0]['value'] = {'equals': '0'}
        result = self.check()
        self.assertTrue(result['verified'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['checks'][-1]['passed'])

    def test_ranges_inclusive_and_exact_uint256(self):
        value = int(self.p['storage'][0]['value']['equals'])
        for condition, accepted in (({'min':str(value),'max':str(value)},True),
                                    ({'min':str(value+1)},False),
                                    ({'max':str(value-1)},False)):
            self.p['storage'][0]['value'] = condition
            self.assertEqual(self.check()['accepted'], accepted)

    def test_account_numeric_conditions(self):
        self.p['account']['nonce'] = {'equals': str(int(self.b['proof']['nonce'],16))}
        self.p['account']['nativeBalanceWei'] = {'min': '0', 'max': str((1<<256)-1)}
        self.assertTrue(self.check()['accepted'])
        self.p['account']['nativeBalanceWei'] = {'equals': str(int(self.b['proof']['balance'],16)+1)}
        self.assertFalse(self.check()['accepted'])

    def test_hashes_and_existence(self):
        self.p['account']['codeHash'] = '0x' + self.p['account']['codeHash'][2:].upper()
        self.p['account']['storageRoot'] = self.b['proof']['storageHash']
        self.assertTrue(self.check()['accepted'])
        self.p['account']['exists'] = False
        self.assertFalse(self.check()['accepted'])
        self.p['account']['exists'] = True
        self.p['storage'][0]['exists'] = False
        self.assertFalse(self.check()['accepted'])

    def test_proven_absence_is_zero_not_missing_evidence(self):
        self.b = g.w.load_bundle(HERE.parent / 'state-witness/examples/zto-mainnet.json')
        self.p = {'format':'state-gate/1','address':g.w.ZTO,'account':{},
                  'storage':[{'slot':s,'exists':False,'value':{'equals':'0'}} for s in ('0x0','0x1')]}
        self.assertTrue(self.check()['accepted'])
        self.b['proof']['storageProof'][0]['proof'] = []
        with self.assertRaises(g.w.Invalid):
            self.check()

    def test_wrong_root_and_address_reject(self):
        with self.assertRaises(g.w.Invalid):
            g.evaluate(self.p, self.b, '0x'+'00'*32)
        self.p['address'] = g.w.ZTO
        with self.assertRaises(g.w.Invalid):
            self.check()

    def test_corrupt_proof_cannot_pass_even_false_condition(self):
        self.p['storage'][0]['value'] = {'equals':'0'}
        for field, value in (('value','0x0'), ('proof', [])):
            b = copy.deepcopy(self.b)
            b['proof']['storageProof'][0][field] = value
            with self.subTest(field=field), self.assertRaises(g.w.Invalid):
                g.evaluate(self.p, b, g.w.DEMO_ROOT)

    def test_exact_slot_set_required(self):
        self.p['storage'] = []
        with self.assertRaises(g.w.Invalid):
            self.check()
        self.b['proof']['storageProof'] = []
        self.assertTrue(self.check()['accepted'])

    def test_metadata_cannot_choose_root_address_or_slots(self):
        before = self.check()
        self.b.update(block={'stateRoot':'0x'+'00'*32},address=g.w.ZTO,slots=[],chainId=999)
        self.assertEqual(before, self.check())

    def test_inputs_unchanged_and_fingerprint_stable(self):
        before = copy.deepcopy((self.p,self.b))
        result = self.check()
        self.assertEqual(before,(self.p,self.b))
        self.p = dict(reversed(list(self.p.items())))
        self.assertEqual(result,self.check())
        self.p['account']['exists'] = False
        self.assertNotEqual(result['policySha256'],self.check()['policySha256'])

    def test_bad_numeric_conditions(self):
        for value in ({}, {'equals':True}, {'min':1}, {'max':'01'}, {'equals':'-1'},
                      {'equals':str(1<<256)}, {'min':'2','max':'1'},
                      {'equals':'1','min':'0'}, {'other':'1'}, {'min':'9'*1000}):
            self.p['storage'][0]['value'] = value
            with self.subTest(value=str(value)[:80]), self.assertRaises(g.w.Invalid):
                self.check()

    def test_unknown_fields_empty_policy_and_types(self):
        for change in (lambda p:p.update(root='ignored'),
                       lambda p:p['account'].update(balance={'min':'0'}),
                       lambda p:p['storage'][0].update(extra=True),
                       lambda p:p['account'].update(exists=1),
                       lambda p:p['storage'][0].update(exists='true'),
                       lambda p:p.update(account={}, storage=[]),
                       lambda p:p.update(storage=[{'slot':'0x1'}]),
                       lambda p:p.update(format='wrong')):
            p = copy.deepcopy(self.p)
            change(p)
            with self.assertRaises(g.w.Invalid):
                g.evaluate(p,self.b,g.w.DEMO_ROOT)

    def test_duplicates_and_limits(self):
        for rows in ([self.p['storage'][0]]*2, [self.p['storage'][0]]*65):
            self.p['storage'] = rows
            with self.assertRaises(g.w.Invalid):
                self.check()
        with self.assertRaises(g.w.Invalid):
            g.w.parse_json('{"format":1,"format":2}')
        with self.assertRaises(g.w.Invalid):
            g.w.parse_json('{"x":NaN}')
        with self.assertRaises(g.w.Invalid):
            g.load_policy(Path.cwd().parent/'outside.json')

    def test_cli_exit_status_and_atomic_failure(self):
        for args, expected in ((['demo'],0),(['demo','--reject'],3),
                               (['check',str(HERE/'examples/pool-policy.json'),
                                 str(HERE.parent/'state-witness/examples/zto-pool-mainnet.json'),
                                 '--state-root','0x'+'00'*32],1)):
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(g.main(args),expected)
            if expected == 1:
                self.assertEqual(out.getvalue(),'')
                self.assertFalse(json.loads(err.getvalue())['verified'])
            else:
                self.assertEqual(err.getvalue(),'')
                result=json.loads(out.getvalue())
                self.assertTrue(result['verified'])
                self.assertEqual(result['accepted'],expected==0)


if __name__ == '__main__':
    unittest.main()
