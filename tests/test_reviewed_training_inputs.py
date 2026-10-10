import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('trainer', Path(__file__).resolve().parents[1] / 'scripts/train_reviewed_components.py')
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)


class ReviewedTrainingInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = []
        for split in ('train', 'val', 'test'):
            image = self.root / 'images' / split / 'reviewed.jpg'
            label = self.root / 'labels' / split / 'reviewed.txt'
            image.parent.mkdir(parents=True)
            label.parent.mkdir(parents=True)
            image.write_bytes(b'image')
            label.write_text('0 0 0 1 0 1 1')
            self.rows.append(dict(split=split, image_path=str(image), label_path=str(label)))
        self.manifest = {'images': self.rows}
        self.data = {s: 'images/' + s for s in ('train', 'val', 'test')}
        self.data['path'] = str(self.root)

    def check(self):
        return trainer.validate_loader_inputs(self.manifest, self.data, self.root / 'data.yaml')

    def test_exact_export_passes(self):
        self.assertEqual(self.check(), [])

    def test_extra_unreviewed_image_rejected(self):
        (self.root / 'images/train/unknown.jpg').write_bytes(b'unknown')
        self.assertTrue(any('1 unreviewed' in e for e in self.check()))

    def test_swapped_validation_set_rejected(self):
        self.data['val'] = 'images/train'
        self.assertTrue(any('Dataset val differs' in e for e in self.check()))

    def test_label_elsewhere_rejected(self):
        self.rows[0]['label_path'] = str(self.root / 'different.txt')
        self.assertTrue(any('label mapping differs' in e for e in self.check()))

    def test_download_hook_rejected(self):
        self.data['download'] = 'arbitrary replacement'
        self.assertTrue(any('download hooks' in e for e in self.check()))


if __name__ == '__main__':
    unittest.main()
