"""Byte provenance and fail-closed label status for gallery intake."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_iqoo_gallery_intake import import_gallery


class TestIqooGalleryIntake(unittest.TestCase):
    def test_copies_original_and_never_marks_it_training_eligible(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as directory:
            fixture = Path(directory)
            source = fixture / "source"
            output = fixture / "output"
            source.mkdir()
            image_path = source / "IMG_20261011_011741_1.jpg"
            image = Image.new("RGB", (48, 32), "#334455")
            exif = Image.Exif()
            exif[274] = 1
            image.save(image_path, exif=exif)

            result = import_gallery(source, output)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            record = manifest["images"][0]
            copied = ROOT / record["path"]
            self.assertEqual(result["photo_count"], 1)
            self.assertEqual(copied.read_bytes(), image_path.read_bytes())
            self.assertEqual(record["sha256"], hashlib.sha256(image_path.read_bytes()).hexdigest())
            self.assertEqual(record["candidate_capture_group"], "IMG_20261011_011741.jpg")
            self.assertEqual(record["review_status"], "unreviewed")
            self.assertFalse(record["training_export_eligible"])
            self.assertFalse(record["evaluation_eligible"])


if __name__ == "__main__":
    unittest.main()
