import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_esp12e_alignment_metadata import validate


class ESP12EIdentityContracts(unittest.TestCase):
    def setUp(self):
        self.index = json.loads((ROOT / 'data/ar-alignment/esp12e-video-instances.json').read_text())

    def test_saved_index_validates_with_raw_assets_or_lfs_pointers(self):
        self.assertEqual(validate(ROOT, self.index), 56)

    def test_swapped_module_pin_is_rejected(self):
        row = next(row for row in self.index['instances'] if row.get('source_module_pin_number') == 1)
        row['source_module_pin_number'] = 22
        with self.assertRaisesRegex(ValueError, 'Swapped contact identity'):
            validate(ROOT, self.index)

    def test_shield_cannot_silently_become_a_board_child(self):
        row = next(row for row in self.index['instances'] if row['kind'] == 'rf_shield')
        row['parent_id'] = self.index['physical_specimen_id']
        with self.assertRaisesRegex(ValueError, 'Changed body parent'):
            validate(ROOT, self.index)

    def test_partial_index_cannot_activate_training(self):
        self.index['training_export_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'cannot activate release'):
            validate(ROOT, self.index)
