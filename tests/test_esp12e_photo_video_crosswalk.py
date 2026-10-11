import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_esp12e_photo_video_crosswalk import build


class ESP12EPhotoVideoCrosswalk(unittest.TestCase):
    def test_crosswalk_is_current_one_to_one_and_release_gated(self):
        saved = json.loads((ROOT / 'data/ar-alignment/esp12e-photo-video-instance-crosswalk.json').read_text())
        self.assertEqual(saved, build())
        joins = saved['joins']
        self.assertEqual(len(joins), 20)
        for key in ('canonical_local_instance_id', 'photo_mask_instance_id', 'video_mask_instance_id'):
            self.assertEqual(len({row[key] for row in joins}), len(joins))
        self.assertEqual(len(saved['unjoined_photo_instance_ids']), 3)
        self.assertFalse(saved['training_export_eligible'])
        self.assertFalse(saved['evaluation_valid'])
        self.assertFalse(saved['ar_activation_eligible'])
        self.assertEqual({Path(row['video_image_path']).name for row in joins}, {
            'video_20261010_122211_n000000_pts00000000ms.jpg',
            'video_20261010_122211_n000523_pts00017497ms.jpg',
        })


if __name__ == '__main__':
    unittest.main()
