# Model-readiness audit

Run `python scripts/model_readiness.py` from the repository root for a live report; add `--json` for machine-readable output. The script checks image hashes against the manifest and fails if an original/crop capture group spans train and validation.

As audited on 2026-10-10, the board-family layer has 80 reviewed photo boxes: 62 train, 11 validation, and seven crop variants held out. The five families are represented by 12 ESP32, 14 ESP8266, 18 NXP FRDM-MCXN236, 18 Raspberry Pi 3B, and 18 Ultimainboard photos. The 80 files form 47 capture groups, with no original/crop group crossing train and validation. This split can support a **diagnostic board-family experiment**, but the validation set has no ESP32 photo and all photos come from one capture session and one specimen per family. It cannot establish generalization to other physical boards, lighting, cameras, or revisions.

| Board family | Photos | Photos with partial part seeds | Part boxes | Photo pin boxes |
| --- | ---: | ---: | ---: | ---: |
| ESP32 | 12 | 2 | 12 | 0 |
| ESP8266 | 14 | 2 | 9 | 0 |
| NXP FRDM-MCXN236 | 18 | 2 | 39 | 0 |
| Raspberry Pi 3B | 18 | 2 | 23 | 0 |
| Ultimainboard | 18 | 2 | 76 | 0 |
| **Total** | **80** | **10** | **159** | **0** |

The 159 part boxes span 13 broad visual classes. The largest are connector headers (52) and integrated circuits (41); several classes have only one or two instances. Only 52 boxes currently carry the `visual_reviewed_major_component_box` status. The other 107 carry seed or review-pending statuses. All ten part-annotated photos have **partial** major-part coverage, and the other 70 photos have no part review. Critically, the current validation split has **zero part boxes** for every family. Treating unlabeled regions as negatives would teach false background; using this split for component mAP would produce a misleading score.

The 352 NXP pin records under ten source-linked part candidates describe electrical source pins. They contain no registered pixel boxes. Other source pin catalogs also remain separate from photo pin labels. A photo pin detector has zero annotated targets across all five families and cannot yet be trained or evaluated honestly.

For the requested board → part → pin workflow, the shortest sound path is:

1. Use the existing board-family model only as a diagnostic baseline and label it as single-specimen evidence. Add at least one independent physical specimen and capture session per family for a real test set.
2. Review all visible parts on selected training and validation photos, including background/ignore regions, and resolve review-pending seed boxes. Split complete component annotations by specimen or at minimum capture group, with annotated validation examples for every intended class.
3. Add pixel-located pin annotations attached to a reviewed part and verified board identity. Keep schematic-only pin records as source metadata until visual pin orientation and location are confirmed. Evaluate board identity, then part identity, then pin identity separately.

This audit is a preparation and quality gate. It does not export incomplete boxes as a YOLO component dataset or claim an every-part or pin model is trained.
