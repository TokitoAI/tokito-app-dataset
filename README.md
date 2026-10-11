# Tokito app dataset

Private dataset repository for the Tokito iQOO hackathon work with Afnan and Navaneeth. Dataset changes go through pull requests. The Tokito application code belongs in a separate repository.

Use the [repository layout and review guide](docs/REPOSITORY_REVIEW_GUIDE.md) for
focused PR scopes, dependency/merge order, file locations and current readiness.
The former broad PR #6 is preserved and replaced by the ordered PRs #9–#16.

The [active goal tracker](docs/DATASET_GOAL.md) records the full dataset, labeling, training and publication scope and remaining work.

For the current part-segmentation implementation, use the [component model selection note](models/COMPONENT_MODEL_SELECTION.md). It identifies the best available existing checkpoint, its exact hash and supported label scope, and distinguishes it from the weaker partial-mask diagnostic.

The [AR alignment dataset](docs/AR_ALIGNMENT_DATASET.md) connects reviewed image instances and named metric anchors to per-component 3D selectors, and keeps one board coordinate frame across top, underside and four side views. It includes a checked NXP mesh registry and six synthetic CAD views; real multi-view masks and phone flip-tracking validation remain incomplete.

## Included corpus

80 phone files: 47 captures and33 cropped variants, sorted under `data/photo-model/by_board`. Board boxes and provenance are in `board-annotations.json`. The five families are ESP32, ESP8266, Ultimainboard2.1.4, NXP FRDM-MCXN236, and Raspberry Pi3B V1.2.

The clearer NXP photos identify **MCXN236**. The previously collected MCXN947 files are a different-board reference and must not be used as its exact BOM or schematic.

`data/board-sources` preserves native source documents, inventories, Gerbers, models, and licenses where collected. The Raspberry Pi 3B folder now includes the official mechanical PDF and DXF with a hash-verified source record; the DXF is mechanical geometry, not an electrical PCB project or Gerber set. `docs/sources` records coverage and limitations. External vision datasets are under `data/external`, including the verified [PCB-Vision RGB package](docs/PCB_VISION_RGB_ACQUISITION.md): 53 photos and 106 masks in Git LFS. Partial downloads remain local.

The board-by-board source inventory is in [`docs/ALL_BOARD_SOURCE_COVERAGE.md`](docs/ALL_BOARD_SOURCE_COVERAGE.md). It covers the ESP32, ESP8266, Ultimainboard, NXP and Raspberry Pi packages and clearly marks where a community/reference design is not proven to match the photographed specimen. The NXP download is not the only source bundle.

KiCad-derived [CAD reference exports](data/board-sources/CAD_EXPORTS.md) now cover the ESP32 community clone, Ultimainboard 2.1.4 and FRDM-MCXN236. They include Gerber/drill and board-only STEP/GLB files, with DRC reports and hashes. All require engineering review before fabrication.

## Clone and validate

Install Git LFS before cloning, then run `git lfs pull`. Large photos, CAD files, PDFs and checkpoints use LFS. Run `python scripts/validate_dataset.py` from the repository root.

## Train the first board detector

Use a virtual environment with a CUDA-enabled PyTorch build and install `requirements-training.txt`. Run `python scripts/train_board_detector.py` from the repository root. The default is a pretrained YOLO11m model with a 1,000-epoch ceiling and 100-epoch early-stopping patience; the actual duration is selected dynamically from validation fitness, and `best.pt` is selected instead of the last epoch. Training uses the reviewed five-class YOLO dataset at `data/photo-model/yolo-boards`.

The detector identifies the five currently reviewed board identities. Exact component reference designators, manufacturer part numbers and pins are resolved after board registration against a revision-matched PCB/BOM/netlist; they are not global YOLO classes.

The board model uses readable labels from [`board-class-display-names.json`](data/photo-model/board-class-display-names.json). The release-ineligible [YOLO11m baseline](data/photo-model/board-yolo11m-experiment/README.md) retains its LiteRT export. A newer [dynamic fine-tune candidate](data/photo-model/board-yolo11m-finetune-experiment/README.md) reached mAP50-95 0.942 versus 0.919 for the baseline, but fixed-threshold review found one Raspberry Pi false positive on an Ultimainboard photo at confidence 0.761. The baseline had none on the same 11-image fold. The matching fine-tuned LiteRT export is included as a runtime experiment and passed numerical conformance on the same 11 known validation images. This fold omits ESP32 and shares physical specimens with training, so these results are diagnostic only.

The first split has62 training images and11 validation originals. Seven validation crop variants are excluded, and no original/crop pair crosses folds. There is one physical specimen per family and no independent specimen test. ESP32 has no separate validation pose group, so no held-out ESP32 accuracy can be reported.

## Component labeling and document links

Component seed annotations cover 240 visible part boxes across nineteen original photos. They are partial and are excluded from complete component-detector training. On 2026-10-10, 34 additional original iQOO photos (full-board and high-resolution close-ups spanning all five board families, including a reviewed NXP underside view) were copied and hash-indexed in [`data/phone-captures/2026-10-10`](data/phone-captures/2026-10-10/manifest.json); their board, part and pin boxes still need review before training. Tiny passives, exact installed part IDs, hidden components and board backs still require labeling/review. See `data/photo-model/MODEL_SCOPE.md`, `docs/EXPANDED_COMPONENT_SEEDS.md`, `docs/COMPONENT_SPRINT.md` and [`docs/PHONE_CAPTURE_INTAKE.md`](docs/PHONE_CAPTURE_INTAKE.md).

The [board, part and pin hierarchy](docs/LABEL_HIERARCHY.md) records the labeling order across all 80 photos. Ultimainboard J22/J23/J1/J2 have 22 reviewed numbered contacts linked to source nets; [Pi J8](docs/PI_J8_PIN_LABELS.md) adds 40 numbered contacts linked to its revision 1.2 schematic. ESP32 and ESP8266 have 103 [printed contact aliases](docs/ESP_ADDITIONAL_CONTACTS.md) across four photos, with numeric pin numbers and source nets unknown. Ten NXP parts have source links and 352 unregistered source pin records. The ESP8266-reference and Ultimainboard [source catalog](docs/SOURCE_PIN_COVERAGE.md) has 1,443 records, including 22 now joined to photo pins.

BOM entries, schematic pages and Gerber layers are linked documents. They are not YOLO object classes. Exact links need matched revisions and readable markings or registered PCB geometry. Unknown links remain unknown.

The [MCXN236 schematic index](data/board-sources/nxp-frdm-mcxn236/README_INDEX.md) locates reference-designator text on PDF pages. Ten [component source links](annotations/component-source-links.json) pair readable photo markings with checked schematic symbols and source BOM records. Their [Rev C part-number candidates](docs/NXP_COMPONENT_SOURCE_CANDIDATES.md) are available for display with the revision uncertainty attached; installed part numbers and the specimen revision are still unverified. See [source-link conventions](docs/SOURCE_LINKS.md).

The downloaded [MCXN236 Rev C design bundle](data/board-sources/nxp-frdm-mcxn236/PROVENANCE.md) includes the native BRD, schematic project, BOM and netlists. Its [structured extraction](data/board-sources/nxp-frdm-mcxn236/structured-rev-c/README.md) joins 96 BOM items to 391 reference designators and 296 electrical nets. DNP entries and the separate no-connect group are preserved. The archive contains no separate Gerber, drill or STEP/GLB exports.

The local scan test packages reviewed photo references separately from YOLO training. The [new reference preview](previews/scan-references-reviewed-20261010.jpg) shows 60 additional literal ESP header contacts, three readable part/module families and reviewed NXP mounting-hole landmarks. `scripts/build_camera_reference_bundle.py` combines them with the existing hierarchy into a bounded local camera bundle; it does not promote source-only pins or incomplete seeds into trained exact identities.

Run `python scripts/model_readiness.py` for a [live audit](docs/MODEL_READINESS_SPRINT.md) of board, part and pin label coverage before training. Partial component seeds and source-only pin records are excluded from claims of a trained component or pin detector.

`python scripts/prepare_board_labels.py` creates foreground-box proposals in ignored `work/photo-contact/`. It requires hash-matched board-class reviews and preserves reviewed annotations, split assignments and photo folders. Review proposals before manually promoting them into the curated labels.

Retain source attribution and file-specific licenses. Check `docs/sources/LICENSE_NOTES.md` before changing visibility or distributing assets. All updates, annotation review and model-results changes should be proposed in PRs.
