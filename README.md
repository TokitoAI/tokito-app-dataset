# Tokito app dataset

Private dataset repository for the Tokito iQOO hackathon work with Afnan and Navaneeth. Dataset changes go through pull requests. The Tokito application code belongs in a separate repository.

The [active goal tracker](docs/DATASET_GOAL.md) records the full dataset, labeling, training and publication scope and remaining work.

## Included corpus

80 phone files: 47 captures and33 cropped variants, sorted under `data/photo-model/by_board`. Board boxes and provenance are in `board-annotations.json`. The five families are ESP32, ESP8266, Ultimainboard2.1.4, NXP FRDM-MCXN236, and Raspberry Pi3B V1.2.

The clearer NXP photos identify **MCXN236**. The previously collected MCXN947 files are a different-board reference and must not be used as its exact BOM or schematic.

`data/board-sources` preserves native source documents, inventories, Gerbers, models, and licenses where collected. `docs/sources` records coverage and limitations. External vision-dataset metadata is under `data/external`; bulk auxiliary images and partial downloads are excluded from this repository.

KiCad-derived [CAD reference exports](data/board-sources/CAD_EXPORTS.md) now cover the ESP32 community clone, Ultimainboard 2.1.4 and FRDM-MCXN236. They include Gerber/drill and board-only STEP/GLB files, with DRC reports and hashes. All require engineering review before fabrication.

## Clone and validate

Install Git LFS before cloning, then run `git lfs pull`. Large photos, CAD files, PDFs and checkpoints use LFS. Run `python scripts/validate_dataset.py` from the repository root.

## Train the first board detector

Use a virtual environment and install `requirements-training.txt`. Run `python scripts/train_board_detector.py` from the repository root. Training uses the reviewed five-class YOLO dataset at `data/photo-model/yolo-boards`.

The first split has62 training images and11 validation originals. Seven validation crop variants are excluded, and no original/crop pair crosses folds. There is one physical specimen per family and no independent specimen test. ESP32 has no separate validation pose group, so no held-out ESP32 accuracy can be reported.

## Component labeling and document links

Component seed annotations cover 204 major visible objects across fifteen photos. They are partial and are excluded from complete component-detector training. Tiny passives, exact part IDs, hidden components and board backs still require labeling/review. See `data/photo-model/MODEL_SCOPE.md`, `docs/EXPANDED_COMPONENT_SEEDS.md` and `docs/COMPONENT_SPRINT.md`.

The [board, part and pin hierarchy](docs/LABEL_HIERARCHY.md) records the labeling order across all 80 photos. Four Ultimainboard J22 contacts now have reviewed photo boxes and pin numbers. Ten NXP parts have source links and 352 unregistered source pin records. Another 1,443 ESP8266-reference and Ultimainboard [source pin records](docs/SOURCE_PIN_COVERAGE.md) remain separate from photo pin labels.

BOM entries, schematic pages and Gerber layers are linked documents. They are not YOLO object classes. Exact links need matched revisions and readable markings or registered PCB geometry. Unknown links remain unknown.

The [MCXN236 schematic index](data/board-sources/nxp-frdm-mcxn236/README_INDEX.md) locates reference-designator text on PDF pages. Ten [component source links](annotations/component-source-links.json) pair readable photo markings with checked schematic symbols and source BOM records. Their installed part numbers and the specimen revision are still unknown. See [source-link conventions](docs/SOURCE_LINKS.md).

The downloaded [MCXN236 Rev C design bundle](data/board-sources/nxp-frdm-mcxn236/PROVENANCE.md) includes the native BRD, schematic project, BOM and netlists. Its [structured extraction](data/board-sources/nxp-frdm-mcxn236/structured-rev-c/README.md) joins 96 BOM items to 391 reference designators and 296 electrical nets. DNP entries and the separate no-connect group are preserved. The archive contains no separate Gerber, drill or STEP/GLB exports.

Run `python scripts/model_readiness.py` for a [live audit](docs/MODEL_READINESS_SPRINT.md) of board, part and pin label coverage before training. Partial component seeds and source-only pin records are excluded from claims of a trained component or pin detector.

`python scripts/prepare_board_labels.py` creates foreground-box proposals in ignored `work/photo-contact/`. It requires hash-matched board-class reviews and preserves reviewed annotations, split assignments and photo folders. Review proposals before manually promoting them into the curated labels.

Retain source attribution and file-specific licenses. Check `docs/sources/LICENSE_NOTES.md` before changing visibility or distributing assets. All updates, annotation review and model-results changes should be proposed in PRs.
