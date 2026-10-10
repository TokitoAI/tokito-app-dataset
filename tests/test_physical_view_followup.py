import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'physical_view_followup',
    Path(__file__).resolve().parents[1] / 'scripts/validate_physical_view_followup.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

supplemental_spec = importlib.util.spec_from_file_location(
    'additional_flip_clips',
    Path(__file__).resolve().parents[1] / 'scripts/validate_additional_flip_clips.py')
supplemental = importlib.util.module_from_spec(supplemental_spec)
supplemental_spec.loader.exec_module(supplemental)


class PhysicalViewFollowupTests(unittest.TestCase):
    def test_tracked_source_hashes_and_view_limits(self):
        result = review.validate()
        self.assertEqual(len(result), 4)
        self.assertTrue(all(row['sha256_verified'] for row in result))
        self.assertTrue(all(not row['training_export_eligible'] for row in result))

    def test_cannot_mark_new_clip_as_flip_evidence(self):
        import json
        data = json.loads(review.MANIFEST.read_text(encoding='utf-8'))
        data['recordings'][0]['continuous_rotate_flip_seen'] = True
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'manifest.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError):
                review.validate(path)

    def test_lfs_pointer_oid_and_declared_size_are_verified(self):
        digest = 'a' * 64
        with tempfile.TemporaryDirectory() as folder:
            pointer = Path(folder) / 'payload.mp4'
            pointer.write_text('version https://git-lfs.github.com/spec/v1\n'
                               + 'oid sha256:' + digest + '\nsize 123\n',
                               encoding='ascii')
            self.assertTrue(review._matches_payload_or_lfs_pointer(pointer, digest, 123))
            self.assertFalse(review._matches_payload_or_lfs_pointer(pointer, digest, 124))
            self.assertFalse(review._matches_payload_or_lfs_pointer(pointer, 'b' * 64, 123))

    def test_supplemental_flip_clips_preserve_view_limits(self):
        result = supplemental.validate()
        self.assertEqual({row['board_family'] for row in result}, {
            'ultimainboard_2_1_4', 'esp32_devkit_30pin_clone'})
        self.assertTrue(all(row['underside_seen'] for row in result))
        self.assertTrue(all(not row['four_oblique_sides_seen'] for row in result))
        self.assertTrue(all(not row['training_export_eligible'] for row in result))


if __name__ == '__main__':
    unittest.main()
