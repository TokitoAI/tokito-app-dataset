"""Guard physical-camera coverage against synthetic or unreviewed evidence."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_multiview_capture_coverage import audit


class TestMultiviewCaptureCoverage(unittest.TestCase):
    def test_current_partial_manifest_is_not_release_eligible(self):
        result = audit(Path(__file__).resolve().parents[1] / "annotations/multiview-capture-review.json")
        self.assertFalse(result["physical_multiview_complete"])
        self.assertEqual(result["physical_specimens"], 5)
        self.assertEqual(result["complete_physical_multiview_specimens"], 0)
        nxp = next(b for b in result["boards"] if b["specimen_id"] == "bench-frdm-mcxn236-01")
        self.assertIn("oblique_positive_board_x", nxp["missing_pose_verified_view_slots"])
        self.assertIn("bottom", nxp["recorded_view_slots_without_pose_claim"])
        inventories = result["unregistered_capture_evidence"]
        gallery = next(row for row in inventories if row["source_manifest"].endswith("gallery/view-review.json"))
        self.assertEqual(gallery["record_count"], 6)
        flips = next(row for row in inventories if "additional-flip-clips/manifest.json" in row["source_manifest"])
        self.assertEqual(flips["record_count"], 2)
        flip_rows = flips["records"]
        self.assertTrue(all(row["hash_verified"] for row in flip_rows))
        self.assertTrue(all(row["underside_seen"] for row in flip_rows))
        self.assertTrue(all(row["continuous_flip_video_present"] for row in flip_rows))
        self.assertTrue(all(not row["continuous_flip_verified"] for row in flip_rows))
        self.assertTrue(all(row["physical_specimen_id"] is None for row in flip_rows))
        self.assertEqual(inventories[1]["record_count"], 4)  # four earlier board-pan videos
        self.assertEqual(inventories[3]["record_count"], 1)  # NXP top keyframe
        for source in inventories:
            self.assertTrue(all(row["hash_verified"] for row in source["records"]))
            if source.get("source_video"):
                self.assertTrue(source["source_video"]["hash_verified"])

    def test_requires_calibrated_reviewed_views_and_hashed_flip_video(self):
        root = Path(__file__).resolve().parents[1]
        required = ["top", "bottom", "oblique_positive_board_x", "oblique_negative_board_x",
                    "oblique_positive_board_y", "oblique_negative_board_y"]
        specimen = "test-board-01"
        captures = [
            {"specimen_id": specimen, "board_family": "test", "view_slot": slot,
             "camera_calibration_id": "cal-1", "board_to_camera_pose": {}, "review_status": "reviewed"}
            for slot in required
        ]
        manifest = {"required_view_slots": required, "captures": captures,
                    "flip_sequences": [{"specimen_id": specimen, "review_status": "reviewed",
                                        "continuous_video_sha256": "a" * 64}]}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "manifest.json"
            import json
            source.write_text(json.dumps(manifest), encoding="utf-8")
            result = audit(source)
        self.assertTrue(result["physical_multiview_complete"])


if __name__ == "__main__":
    unittest.main()
