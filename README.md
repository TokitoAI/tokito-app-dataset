# Tokito app dataset

Private dataset repository for the Tokito iQOO hackathon work with Afnan and Navaneeth. Dataset changes go through pull requests. The Tokito application code belongs in a separate repository.

## Included corpus

80 phone files: 47 captures and33 cropped variants, sorted under `data/photo-model/by_board`. Board boxes and provenance are in `board-annotations.json`. The five families are ESP32, ESP8266, Ultimainboard2.1.4, NXP FRDM-MCXN236, and Raspberry Pi3B V1.2.

The clearer NXP photos identify **MCXN236**. The previously collected MCXN947 files are a different-board reference and must not be used as its exact BOM or schematic.

`data/board-sources` preserves native source documents, inventories, Gerbers, models, and licenses where collected. `docs/sources` records coverage and limitations. External vision-dataset metadata is under `data/external`; bulk auxiliary images and partial downloads are excluded from this repository.

## Clone and validate

Install Git LFS before cloning, then run `git lfs pull`. Large photos, CAD files, PDFs and checkpoints use LFS. Run `python scripts/validate_dataset.py` from the repository root.

## Train the first board detector

Use a virtual environment and install `requirements-training.txt`. Run `python scripts/train_board_detector.py` from the repository root. Training uses the reviewed five-class YOLO dataset at `data/photo-model/yolo-boards`.

The first split has62 training images and11 validation originals. Seven validation crop variants are excluded, and no original/crop pair crosses folds. There is one physical specimen per family and no independent specimen test. ESP32 has no separate validation pose group, so no held-out ESP32 accuracy can be reported.

## Component labeling and document links

Experimental trained checkpoints and measured error reports are proposed in the model-results PR under `models/board-family-v1`. The detector/crop-classifier CLI is `scripts/predict_boards.py`; its model card distinguishes known-photo diagnostics from independent accuracy and documents the front-view geometric gate.

Component seed annotations cover107 major visible objects across five photos. They are partial and are excluded from complete component-detector training. Tiny passives, exact part IDs, hidden components and board backs still require labeling/review. See `data/photo-model/MODEL_SCOPE.md`.

BOM entries, schematic pages and Gerber layers are linked documents. They are not YOLO object classes. Exact links need matched revisions and readable markings or registered PCB geometry. Unknown links remain unknown.

Retain source attribution and file-specific licenses. Check `docs/sources/LICENSE_NOTES.md` before changing visibility or distributing assets. All updates, annotation review and model-results changes should be proposed in PRs.
