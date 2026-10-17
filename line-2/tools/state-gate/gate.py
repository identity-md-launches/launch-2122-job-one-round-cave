#!/usr/bin/env python3
"""Check caller-authored conditions on proven Ethereum state, offline."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('witness_for_state_gate',
                                           HERE.parent / 'state-witness/witness.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
MAX_POLICY = 65536


def keys(value, required, optional=()):
    w.require(type(value) is dict and set(required) <= set(value) <= set(required) | set(optional),
              'missing or unknown policy field')


def decimal(value):
    w.require(isinstance(value, str) and len(value) <= 78 and
              re.fullmatch(r'0|[1-9][0-9]*', value) is not None,
              'bounds must be canonical uint256 decimal strings')
    number = int(value)
    w.require(number < 1 << 256, 'bound exceeds uint256')
    return number


def bounds(value):
    keys(value, (), ('equals', 'min', 'max'))
    w.require(bool(value), 'numeric condition must not be empty')
    w.require('equals' not in value or len(value) == 1,
              'equals cannot be combined with range bounds')
    result = {k: decimal(v) for k, v in value.items()}
    w.require(result.get('min', 0) <= result.get('max', (1 << 256)-1),
              'minimum exceeds maximum')
    return result


def validate(policy):
    keys(policy, ('format', 'address', 'account', 'storage'))
    w.require(policy['format'] == 'state-gate/1', 'unsupported policy format')
    w.hex_data(policy['address'], 20, 'policy address')
    account = policy['account']
    keys(account, (), ('exists', 'nonce', 'nativeBalanceWei', 'codeHash', 'storageRoot'))
    for key, value in account.items():
        if key == 'exists':
            w.require(type(value) is bool, 'exists must be boolean')
        elif key in ('nonce', 'nativeBalanceWei'):
            bounds(value)
        else:
            w.hex_data(value, 32, key)
    storage = policy['storage']
    w.require(type(storage) is list and len(storage) <= 64, 'at most 64 storage conditions')
    w.require(bool(account) or bool(storage), 'policy must contain a condition')
    seen = set()
    for row in storage:
        keys(row, ('slot',), ('exists', 'value'))
        slot = w.slot_number(row['slot'])
        w.require(slot not in seen, 'duplicate policy slot')
        seen.add(slot)
        w.require('exists' in row or 'value' in row, 'slot must contain a condition')
        if 'exists' in row:
            w.require(type(row['exists']) is bool, 'exists must be boolean')
        if 'value' in row:
            bounds(row['value'])
    return policy


def load_policy(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_POLICY + 1)
    w.require(len(raw) <= MAX_POLICY, 'policy exceeds 64 KiB')
    return validate(w.parse_json(raw))


def evaluate(policy, witness, trusted_root):
    """Proof failures raise; valid proofs may return accepted=False."""
    validate(policy)
    w.require(type(witness) is dict, 'witness must be an object')
    state = w.verify(witness.get('proof'), trusted_root, policy['address'],
                     [row['slot'] for row in policy['storage']])
    checks = []

    def record(field, actual, expected):
        if isinstance(expected, dict):
            limits = bounds(expected)
            number = int(actual)
            passed = (number == limits.get('equals', number) and
                      number >= limits.get('min', 0) and
                      number <= limits.get('max', (1 << 256)-1))
        else:
            passed = actual == expected
        checks.append({'field': field, 'actual': actual, 'expected': expected, 'passed': passed})

    for key, expected in policy['account'].items():
        actual = state['accountExists' if key == 'exists' else key]
        if key == 'nonce':
            actual = str(int(actual, 16))
        if key in ('codeHash', 'storageRoot'):
            expected = expected.lower()
        record('account.' + key, actual, expected)
    rows = {int(row['slot'], 16): row for row in state['storage']}
    for condition in policy['storage']:
        number = w.slot_number(condition['slot'])
        row = rows[number]
        for field in ('exists', 'value'):
            if field in condition:
                actual = row[field] if field == 'exists' else str(int(row['value'], 16))
                record('storage.' + hex(number) + '.' + field, actual, condition[field])
    canonical = json.dumps(policy, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    return {'format': 'state-gate-result/1', 'verified': True,
            'accepted': all(row['passed'] for row in checks),
            'stateRoot': state['stateRoot'], 'address': state['address'],
            'policySha256': hashlib.sha256(canonical).hexdigest(), 'checks': checks,
            'trust': 'Authenticate the root and policy independently. This checks only sampled state; '
                     'it does not verify consensus, finality, storage layout, execution or future state.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='check the historical real ZTO/IMD pool offline')
    demo.add_argument('--reject', action='store_true', help='show a valid proof failing a condition')
    check = sub.add_parser('check')
    check.add_argument('policy')
    check.add_argument('witness')
    check.add_argument('--state-root', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            policy = load_policy(HERE / 'examples/pool-policy.json')
            witness = w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')
            if args.reject:
                policy['storage'][0]['value'] = {'equals': '0'}
            result = evaluate(policy, witness, w.DEMO_ROOT)
            result['demo'] = 'Historical RPC observation; the demo root is not a consensus-authenticated checkpoint.'
        else:
            result = evaluate(load_policy(args.policy), w.load_bundle(args.witness), args.state_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result['accepted'] else 3
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'accepted': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'accepted': False, 'error': 'Unreadable or malformed input.'}),
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
