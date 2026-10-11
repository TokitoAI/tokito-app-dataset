# iQOO gallery intake — 2026-10-11

The iQOO I2501 gallery supplied 70 original JPEG files (197,974,870 bytes). They are preserved byte-for-byte under `data/phone-captures/2026-10-11/gallery/`; `manifest.json` records the source filename, dimensions, EXIF orientation/time where available, candidate capture group and SHA-256 for each file. The `IMG_*_1.jpg` suffix is treated only as a candidate grouping hint, not proof that the images are duplicates.

The raw contact sheets show useful board and component close-ups, and include multiple board surfaces. They do not establish calibrated camera poses or a complete set of four oblique/side views. Individual board identity, component boundaries, installed part identity and view slot remain unreviewed. Every image is marked `training_export_eligible: false` and `evaluation_eligible: false`; do not use this intake in YOLO splits until its annotations and capture groups are reviewed. Keep correlated views of one specimen/session in a single split.

Reproduce the byte-checked import from the ignored local intake folder with:

```powershell
python scripts/import_iqoo_gallery_intake.py
```

The importer never turns identity or label guesses into ground truth. A matching SHA-256 confirms the copied image bytes only.
