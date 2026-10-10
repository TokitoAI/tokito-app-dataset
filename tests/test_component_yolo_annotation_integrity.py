import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

spec = importlib.util.spec_from_file_location(
    "component_annotation_validator",
    Path(__file__).resolve().parents[1] / "scripts/validate_component_yolo_annotations.py",
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ComponentYoloAnnotationIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "image.jpg"
        Image.new("RGB", (20, 10), "white").save(self.image)
        self.digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.path = self.root / "review.json"
        self.data = {
            "coverage": "partial_visible_component_bodies",
            "training_export_eligible": False,
            "image_path": "image.jpg",
            "image_sha256": self.digest,
            "masks": [{
                "instance_id": "image.jpg:U1",
                "class_name": "integrated_circuit",
                "polygon_xy_pixels": [[2, 2], [8, 2], [8, 7], [2, 7]],
            }],
        }

    def check(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return validator.validate_file(self.path, self.root)

    def test_partial_review_passes_integrity_but_is_not_trainable(self):
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["trainable"])

    def test_out_of_bounds_polygon_is_rejected(self):
        self.data["masks"][0]["polygon_xy_pixels"][2] = [20, 7]
        self.assertTrue(any("outside the image" in e for e in self.check()["errors"]))

    def test_changed_image_is_rejected(self):
        Image.new("RGB", (20, 10), "black").save(self.image)
        self.assertTrue(any("SHA-256 mismatch" in e for e in self.check()["errors"]))

    def test_only_complete_eligible_review_can_be_trainable(self):
        self.data["coverage"] = "complete_visible_instances"
        self.data["training_export_eligible"] = True
        self.assertTrue(self.check()["trainable"])


if __name__ == "__main__":
    unittest.main()
