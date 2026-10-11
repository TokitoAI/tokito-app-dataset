import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NxpPhotoIdentityTest(unittest.TestCase):
    def test_observed_crystal_identity_correction_is_preserved(self):
        masks = json.loads((ROOT / 'annotations/nxp-dense-component-review.json').read_text())['masks']
        corrected = [row for row in masks if row.get('identity_correction_evidence')]
        self.assertEqual(3, len(corrected))
        for row in corrected:
            self.assertEqual('Y3', row['observed_reference_designator'])
            self.assertTrue(row['instance_id'].endswith(':Y3'))
            if 'source_annotation_instance_id' in row:
                self.assertTrue(row['source_annotation_instance_id'].endswith(':Y3'))

    def test_corrected_crosswalk_remains_source_candidate_not_physical_proof(self):
        document = json.loads((ROOT / 'data/ar-alignment/nxp-mask-to-glb-candidates.json').read_text())
        self.assertFalse(document['production_ar_eligible'])
        self.assertFalse(document['physical_camera_pose_verified'])
        corrected = [row for row in document['instances'] if row.get('identity_correction_evidence')]
        self.assertEqual(3, len(corrected))
        for row in corrected:
            self.assertEqual('ref:Y3', row['source_glb_selector'])
            self.assertTrue(row['candidate_only'])
            self.assertEqual('nxp-frdm-mcxn236:C:Y3', row['source_candidate_component_id'])


if __name__ == '__main__':
    unittest.main()
