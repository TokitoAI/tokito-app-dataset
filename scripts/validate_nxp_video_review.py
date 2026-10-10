"""Check NXP video mask identity, provenance and revision limits with LFS support."""
import json
from pathlib import Path

from build_ar_alignment_dataset import content_sha, sha

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/video-captures/2026-10-10/nxp-keyframes'
SOURCE = ROOT / 'data/board-sources/nxp-frdm-mcxn236/ar-reference'


def validate(review, revision):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    manifest = json.loads((BASE / 'manifest.json').read_text())
    frames = {frame['image_path']:frame for frame in manifest['keyframes']}
    frame = frames[review['image_path']]
    require(content_sha(ROOT / review['image_path']) == frame['image_sha256'] == review['image_sha256'],
            'Frame source digest mismatch')
    require((review['image_width'],review['image_height']) ==
            (frame['image_width'],frame['image_height']), 'Mask coordinate dimensions mismatch')
    require(review['physical_specimen_id'] == manifest['physical_specimen_id']
            and review['capture_session_id'] == manifest['capture_session_id'], 'Wrong capture grouping')
    require(not review['training_export_eligible'] and not review['production_eligible'],
            'Partial revision-unverified masks cannot activate training')
    require(sha(SOURCE / 'component-map.json') == review['source_component_map_sha256'],
            'Source map changed')
    rows = {row['reference']:row for row in json.loads((SOURCE / 'component-map.json').read_text())['components']}
    identities = set()
    for mask in review['masks']:
        require(mask['instance_id'] not in identities, 'Duplicate instance ID')
        identities.add(mask['instance_id'])
        require(not mask['installed_order_code_confirmed'], 'Unverified ordering code activation')
        points = mask['polygon_xy_pixels']
        require(len(points)>=3 and all(0<=x<review['image_width'] and 0<=y<review['image_height']
                                      for x,y in points), 'Invalid body polygon')
        reference = mask['observed_reference_designator']
        if reference is None:
            require(mask['source_candidate_component_id'] is None
                    and mask['source_candidate_part_number'] is None, 'Ambiguous identity assigned source part')
        else:
            row = rows[reference]
            require(mask['source_candidate_component_id'] == row['component_id']
                    and mask['source_candidate_part_number'] == row['bom_part_number'], 'Wrong reference-to-source join')
    require(content_sha(ROOT / revision['source_pdf_path']) == revision['source_pdf_sha256'],
            'Revision history source digest mismatch')
    require(not revision['revision_equivalence_verified'] and not revision['production_eligible'],
            'Unverified B/C equivalence activation')
    require(revision['available_design_revision']=='C' and revision['photographed_marking'] is None
            and revision['photographed_copyright_text']=='2024 NXP B.V.'
            and revision['prior_B_revision_inference_retracted'],
            'Incorrect revision identities')
    require(revision['c_changes']['changed_header_contacts']==['J8:6','J8:8'], 'Changed-pin history mismatch')
    require(revision['c_changes']['added_testpoints']==[f'TP{i}' for i in range(10,33)],
            'C-only testpoint history mismatch')
    return len(review['masks'])


if __name__ == '__main__':
    review = json.loads((BASE / 'nxp-component-body-review.json').read_text())
    revision = json.loads((SOURCE / 'revision-compatibility-review.json').read_text())
    print(f'Validated {validate(review,revision)} NXP video masks; revision equivalence remains unverified')
