# NXP photographed body review

`annotations/nxp-dense-component-review.json` records 104 reviewed polygons across three original 3072 × 4096 photos: 66 on `IMG_20261010_092203.jpg`, 19 on `IMG_20261010_092206.jpg`, and 19 on `IMG_20261009_221755.jpg`. Three are the existing central U1/J10/J11 masks; 101 additional mask records cover observed IC packages, header housings, tactile switches, metal resonator packages and selected passives. Do not count repeated central instances twice.

Original-pixel top/middle/bottom crops and grids were used to review the bodies. Full and three panel overlays are in `previews/nxp-dense-*-review.jpg`. This is partial annotation evidence; image hashes, dimensions and bounds are verified by the component annotation validator. Bounds validity is not a guarantee of every identity or silhouette. Conservative boundary uncertainty is recorded.

## Current class coverage

- USB receptacle bodies: both J10 and J11 are covered on this photo.
- Tactile switches: four visible switch bodies are covered on this photo.
- Metal resonator packages: three visible bodies are covered; device family/frequency/order code remains distinct from body recognition.
- IC packages: additional bodies are covered, but upper packages and unreadable markings still require review. U1 has a visible NXP MCXN236V family; U12 shows Winbond 25Q64JV family, with full installed suffix unconfirmed.
- Header housings: multiple visible housings are traced, with further silhouette refinement required. Socket apertures belong to the housing; unpopulated PCB holes/pads are excluded. This is not per-contact segmentation.
- Resistors/capacitors: many small bodies around U11, U1, U12, U10, J12 and the left audio footprint region remain unlabelled. Crowded arrays must be reviewed one body at a time, not represented by cluster boxes.

## Eligibility

`training_export_eligible`, `evaluation_valid`, and `release_eligible` remain false. Standard training with all component classes must not turn omitted bodies into background. An intentionally restricted observable-class dataset requires its own exhaustive per-image coverage review and separate class contract; the three complete small class scopes do not make all-component training complete.

The photographed PCB revision remains unverified. Rev C CAD/BOM source candidates do not prove an installed order code or population. This review does not create underside labels, hidden BGA contacts, camera calibration or 3D alignment. Other photo/view sessions remain to be reviewed.

Validation: `python scripts/validate_component_yolo_annotations.py annotations/nxp-dense-component-review.json`.

## Additional capture review

The two added photos each contain 10 reviewed IC body instances, 2 USB receptacles, 4 tactile switches and 3 visible metal resonator bodies. Feature registration initialized provisional polygons; target pixel crops and overlays were checked and several target boundaries manually corrected for package height/parallax. It did not supply identity ground truth. Oct9 markings are too blurry for fresh family claims, so those rows keep observed family null and linked family context separate. Dated capture-session and shared physical-specimen IDs are recorded per row. A same-specimen session split cannot establish unseen-board generalization. Crowded passives remain omitted on those photos.
