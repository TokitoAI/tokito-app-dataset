#!/usr/bin/env python3
"""Keep NXP J12 candidate evidence separate from canonical photo pin labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def checked_bytes(path, expected):
    data = (ROOT / path).read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        assert f'oid sha256:{expected}\n'.encode() in data, path
        return None
    assert hashlib.sha256(data).hexdigest() == expected, path
    return data


def main():
    review = json.loads((ROOT / 'annotations/nxp-j12-registration-review.json').read_text(encoding='utf-8'))
    assert review['status'] == 'candidate_not_training_ground_truth' and review['training_eligible'] is False
    assert review['evidence']['specimen_revision_readable'] is False
    assert review['evidence']['physical_pin1_mark_readable'] is False
    for path, digest in [('proposal_path', 'proposal_sha256'), ('photo_path', 'photo_sha256'),
                         ('source_pcb_path', 'source_pcb_sha256'), ('source_netlist_path', 'source_netlist_sha256')]:
        checked_bytes(review[path], review[digest])
    proposal = json.loads((ROOT / review['proposal_path']).read_text(encoding='utf-8'))
    assert proposal['status'] == review['status']
    assert proposal['image_path'] == review['photo_path']
    assert proposal['image_sha256'] == review['photo_sha256']
    assert proposal['parent_part_reference_designator'] == review['reference_designator'] == 'J12'
    assert len(proposal['proposals']) == review['evidence']['visible_contact_count'] == 10
    candidate = {entry['pin_number']: entry['source_net'] for entry in proposal['proposals']}
    assert set(candidate) == set(review['evidence']['source_j12_pin_numbers'])
    assert all(0 <= x0 < x1 <= proposal['image_width'] and
               0 <= y0 < y1 <= proposal['image_height']
               for x0, y0, x1, y1 in (entry['xyxy_pixels'] for entry in proposal['proposals']))
    netlist = json.loads((ROOT / review['source_netlist_path']).read_text(encoding='utf-8'))
    source = {}
    for record in netlist['records']:
        for node in record['nodes']:
            if node['refdes'] == 'J12':
                assert node['pin'] not in source
                source[node['pin']] = record['name']
    assert source == candidate
    hierarchy = json.loads((ROOT / 'data/photo-model/label-hierarchy.json').read_text(encoding='utf-8'))
    assert hierarchy['statistics']['photo_pins_located_by_family']['nxp_frdm_mcxn236_board'] == 0
    print('J12: 10 source proposals match official netlist; physical pin labels remain unregistered.')


if __name__ == '__main__':
    main()
