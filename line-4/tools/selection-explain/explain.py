#!/usr/bin/env python3
"""Explain a finite catalog selection and trace every requirement to its roots."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

CHECKER = Path(__file__).resolve().parent.parent / 'exhaustive-audit/audit.py'
if not CHECKER.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('selection_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
fmt = checker.fmt


def selection(value):
    """Normalize names but require exact catalog release spellings."""
    if not isinstance(value, dict) or len(value) > 1000:
        raise fmt.Invalid('selection must be an object of at most 1000 packages')
    result = {}
    for raw, release in value.items():
        package = fmt.name(raw)
        if package in result:
            raise fmt.Invalid('duplicate canonical selected package: ' + package)
        fmt.version(release)
        result[package] = release
    return dict(sorted(result.items()))


def explain(data, chosen, why=None):
    packages, roots = fmt.validate(data)
    chosen = selection(chosen)
    nodes, edges, violations = {}, [], []
    todo = deque()

    def require(source, package, constraint):
        release = chosen.get(package)
        issue = ('missing-selection' if release is None else
                 'unknown-release' if release not in packages.get(package, {}) else
                 'constraint-mismatch' if not checker.matches(release, constraint) else None)
        index = len(edges)
        edges.append({'source': source, 'package': package, 'constraint': constraint,
                      'selected_version': release, 'satisfied': issue is None,
                      'issue': issue})
        if issue is not None:
            violations.append(index)
        if package not in nodes:
            nodes[package] = {'selected_version': release, 'via': index, 'incoming': []}
            todo.append(package)
        nodes[package]['incoming'].append(index)

    # Seed all roots before expanding dependencies: first discovery is a
    # deterministic shortest root-to-node path, including when roots overlap.
    for package, constraint in sorted(roots.items()):
        require(None, package, constraint)
    expanded, unexpanded = [], []
    while todo:
        package = todo.popleft()
        release = chosen.get(package)
        if release not in packages.get(package, {}):
            unexpanded.append(package)
            continue
        expanded.append(package)
        # Continue through a known release even if one incoming constraint
        # failed. These edges explain this supplied choice, not a valid lock.
        for dep, constraint in sorted(packages[package][release].items()):
            require(package, dep, constraint)
    unreachable = sorted(chosen.keys() - nodes.keys())
    unknown_selected = sorted(p for p, v in chosen.items() if v not in packages.get(p, {}))
    payload = {'packages': packages, 'roots': roots, 'selected': chosen}
    out = {'method': 'selection-explain-v1',
           'status': 'valid' if not violations and not unreachable else 'rejected',
           'input_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True,
               separators=(',', ':')).encode()).hexdigest(),
           'selected': chosen, 'nodes': dict(sorted(nodes.items())),
           'requirements': edges, 'violations': violations,
           'unreachable_selected': unreachable, 'unknown_selected': unknown_selected,
           'expanded': sorted(expanded), 'unexpanded': sorted(unexpanded),
           'scope': 'Only dependencies of known selected releases reachable from roots are traced. '
                    'A path may include failed constraints; it describes the supplied selection. '
                    'Unexpanded nodes have missing or unknown releases; no dependencies are inferred.'}
    if why is not None:
        target = fmt.name(why)
        if target not in nodes:
            out['why'] = {'package': target, 'status': 'unreachable' if target in chosen else 'not-required',
                          'path': []}
        else:
            path, cursor = [], target
            while cursor is not None:
                edge = nodes[cursor]['via']
                path.append(edge)
                cursor = edges[edge]['source']
            path.reverse()
            out['why'] = {'package': target, 'status': 'traced', 'path': path,
                          'all_path_requirements_satisfied': all(edges[i]['satisfied'] for i in path)}
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace-local JSON catalog, or demo')
    parser.add_argument('--selection', help='workspace JSON object mapping packages to exact release strings')
    parser.add_argument('--why', help='include a shortest root-to-package path as requirement indexes')
    args = parser.parse_args(argv)
    try:
        if args.catalog == 'demo':
            if args.selection:
                raise fmt.Invalid('demo uses its own historical selection; omit --selection')
            data = fmt.load(CHECKER.parent.parent / 'offline-resolver/examples/requests.json')
            chosen = fmt.load(CHECKER.parent.parent / 'lock-plan/examples/baseline.json')
            # This is an explicit illustrative choice, not an installed environment.
            chosen['requests'] = '2.32.5'
        else:
            if not args.selection:
                raise fmt.Invalid('--selection is required outside demo')
            data, chosen = fmt.load(args.catalog), fmt.load(args.selection)
        result = explain(data, chosen, args.why)
        code = 0 if result['status'] == 'valid' else 1
    except (fmt.Invalid, OSError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
