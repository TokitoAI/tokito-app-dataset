"""Distinguish unmodeled test features from missing populated package bodies."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def classify(index_path, output):
    index = json.loads(Path(index_path).read_text())
    source = ROOT / 'data/board-sources/ultimainboard-2.1.4/structured-source/components.json'
    records = json.loads(source.read_text())
    missing = set(index['references_without_selectable_geometry'])
    rows = []
    for record in records:
        ref = record['SOURCEDESIGNATOR']
        if ref not in missing:
            continue
        pattern = record.get('PATTERN', '')
        upper = pattern.upper()
        if 'TESTPOINT' in upper:
            category = 'test_contact; needs_source_pad_region_not_package_body'
        elif upper == 'FIDUCIAL':
            category = 'optical_landmark; needs_source_copper_region_not_package_body'
        elif upper.startswith('SPACER'):
            category = 'mechanical_spacer; fitted_population_and_body_pending'
        elif 'SOLDER' in upper:
            category = 'solder_jumper; needs_pad_and_bridge_population_review'
        else:
            category = 'component_package_body_missing'
        rows.append({'reference':ref,'source_pattern':pattern,'category':category,
                     'source_description':record.get('SOURCEDESCRIPTION'),
                     'specimen_population_verified':False})
    payload = {'schema_version':'1.0','production_eligible':False,
               'source_index_sha256':hashlib.sha256(Path(index_path).read_bytes()).hexdigest(),
               'source_inventory_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
               'independently_selectable_source_bodies':index['selectable_source_references'],
               'unmodeled_reference_classification':dict(Counter(r['category'] for r in rows)),
               'references':rows,
               'policy':'No synthetic package bodies for testpoints or fiducials; use exact source contact regions for AR highlighting. Source population does not prove specimen population.'}
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload['unmodeled_reference_classification']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index')
    parser.add_argument('output')
    args = parser.parse_args()
    classify(args.index,args.output)
