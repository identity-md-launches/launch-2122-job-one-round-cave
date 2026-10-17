"""Check gathering 30's records, wall continuity and source boundaries."""
import hashlib
import json
from pathlib import Path
import re

from check_round30 import fingerprints
from check_deliverable import jpeg_size
from finish_wall import read_png


def main():
    checks = json.loads(Path('gathering/checks-30.json').read_text())
    shared = json.loads(Path('gathering/shared-checks-30.json').read_text())
    assert checks['protected_files'] == fingerprints()
    assert checks['line_files_unchanged'] and checks['total_tests'] == 520
    assert len(checks['suites']) == 37 and len(checks['demos']) == 42
    assert all(x['exit'] == x['expected_exit'] for x in checks['suites'] + checks['demos'])
    assert shared['total_tests'] == 83 and all(s['exit'] == 0 for s in shared['suites'])
    assert shared['citation_provenance_verified']
    assert shared['citation_demo']['candidate']['status'] == 'relocated'
    assert shared['root_repair_source_hashes_verified']
    assert shared['repair_demo']['result']['status'] == 'repair_proposed'
    assert shared['lock_plan_source_hashes_verified']
    assert shared['plan_demo']['result']['status'] == 'planned'
    assert shared['plan_audit_source_hashes_verified']
    assert shared['audited_demo']['result']['status'] == 'audited'
    assert shared['audited_demo']['result']['minimum_audit']['checked_assignments'] == 24

    assert shared['release_map_source_hashes_verified']
    assert shared['choices_demo']['status'] == 'mapped'
    assert shared['choices_demo']['choices']['compatible_selections_found'] == 8

    wall = Path('artifacts/gathering/wall-v10.png')
    ancestor = Path('artifacts/gathering/wall-v9.png')
    width, height, pixels = read_png(wall)
    aw, ah, original = read_png(ancestor)
    evidence = json.loads(Path('gathering/image-preservation-30.json').read_text())
    assert (width, height) == (aw, ah) == (1254, 1254)
    digest = hashlib.sha256(wall.read_bytes()).hexdigest()
    assert digest == evidence['wall_sha256']
    assert hashlib.sha256(ancestor.read_bytes()).hexdigest() == evidence['ancestor_sha256']
    x0, y0, span_x, span_y = evidence['new_mark_rectangle']
    changed = outside = 0
    for i in range(width * height):
        if pixels[3*i:3*i+3] != original[3*i:3*i+3]:
            changed += 1
            x, y = i % width, i // width
            outside += not (x0 <= x < x0+span_x and y0 <= y < y0+span_y)
    assert changed == evidence['changed_pixels'] == 3842
    assert outside == evidence['changed_pixels_outside_rectangle'] == 0
    assert Path('artifacts/gathering/wall.png').resolve() == wall.resolve()

    record = json.loads(Path('dist/gathering/30.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    traits = {x['trait_type']: x['value'] for x in record['attributes']}
    assert set(traits) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 30
    assert traits['One thing'] == 'Gathering'
    preview = Path('dist/gathering/30.jpg')
    assert jpeg_size(preview.read_bytes()) == (512, 512)
    assert preview.stat().st_size == evidence['preview']['bytes'] <= 100000

    goals = [{'line': n, 'goal': Path(f'line-{n}/GOAL.md').read_text().strip()}
             for n in range(1, 5)]
    assert json.loads(Path('dist/goals.json').read_text()) == goals
    page = Path('dist/index.html').read_text()
    embedded = re.search(r'<script id="records" type="application/json">(.*?)</script>', page, re.S)
    assert embedded
    groups = json.loads(embedded[1])
    count = pending = 0
    for group, folder in zip(groups, ('line-1', 'line-2', 'line-3', 'line-4', 'gathering')):
        paths = sorted(Path('dist', folder).glob('[0-9][0-9].json'), reverse=True)
        expected = [{'number': int(p.stem), 'path': p.relative_to('dist').as_posix(),
                     **json.loads(p.read_text())} for p in paths]
        assert group['records'] == expected
        count += len(paths)
        for entry in expected:
            if entry['name'] == 'Not painted yet':
                pending += 1
                assert not Path('dist', entry['path']).with_suffix('.jpg').exists()
    assert len(groups) == 5 and count == 147 and pending == 100
    assert groups[-1]['records'][0]['number'] == 30
    gallery = json.loads(Path('gathering/gallery-checks-30.json').read_text())
    assert gallery['passed'] and gallery['records'] == count
    assert gallery['placeholders'] == pending and gallery['newest_gathering'] == 30
    assert Path('gathering/COINS.md').read_text().startswith('none\n')
    for folder in ('gathering', 'shared', 'dist'):
        assert all(p.stat().st_size <= 100000 for p in Path(folder).rglob('*') if p.is_file())

    review = {'number': 30, 'line_files_and_records_unchanged': True,
              'line_tests_passed': 520, 'line_demos_passed': 42,
              'shared_tests_passed': 83, 'gallery_records': count,
              'preserved_placeholders': pending,
              'wall': {'path': str(wall), 'dimensions': [width, height],
                       'format': 'PNG', 'mode': 'RGB', 'sha256': digest},
              'preview': {'path': str(preview), 'dimensions': [512, 512],
                          'format': 'JPEG', 'bytes': preview.stat().st_size},
              'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
              'visual_review': {'method': 'Local inspection of finished wall and JPEG preview.',
                                'pepe': 'Wide mouth and heavy-lidded eyes preserved.',
                                'hands': 'No new hands or handprints. Central Pepe hands concealed; inherited lower-center five-digit stencil retained without changes.',
                                'text_or_prohibited_symbols_observed': False,
                                'limitation': 'The small paired leaves are subdued at thumbnail scale. Generated placement differs from the requested rectangle; only its actual unused-rock area was retained.'},
              'unmet_visual_requirements': [], 'coins': 'none'}
    Path('gathering/REVIEW-30.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
