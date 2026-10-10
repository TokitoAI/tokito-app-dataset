import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_nxp_video_review import BASE, SOURCE, validate


class NXPVideoReview(unittest.TestCase):
    def setUp(self):
        self.review=json.loads((BASE/'nxp-component-body-review.json').read_text())
        self.revision=json.loads((SOURCE/'revision-compatibility-review.json').read_text())

    def test_saved_review(self):
        self.assertEqual(validate(self.review,self.revision),4)

    def test_uncertain_body_cannot_inherit_neighbor_identity(self):
        row=next(row for row in self.review['masks'] if row['observed_reference_designator'] is None)
        row['source_candidate_part_number']='XC6227C331PR-G'
        with self.assertRaisesRegex(ValueError,'Ambiguous identity'):
            validate(self.review,self.revision)

    def test_wrong_reference_join_rejected(self):
        self.review['masks'][0]['source_candidate_component_id']='nxp-frdm-mcxn236:C:U2'
        with self.assertRaisesRegex(ValueError,'Wrong reference-to-source'):
            validate(self.review,self.revision)

    def test_revision_conflict_cannot_be_silently_cleared(self):
        self.revision['revision_equivalence_verified']=True
        with self.assertRaisesRegex(ValueError,'B/C equivalence'):
            validate(self.review,self.revision)

    def test_copyright_suffix_cannot_be_promoted_to_hardware_revision(self):
        self.revision['photographed_marking']='B'
        with self.assertRaisesRegex(ValueError,'Incorrect revision identities'):
            validate(self.review,self.revision)
