# Model-readiness audit

Run `python scripts/model_readiness.py` from the repository root for a live report; add `--json` for machine-readable output. The script checks image hashes against the manifest and fails if an original/crop capture group spans train and validation.

As audited on 2026-10-10, the board-family layer has 80 reviewed photo boxes: 62 train, 11 validation, and seven crop variants held out. The five families are represented by 12 ESP32, 14 ESP8266, 18 NXP FRDM-MCXN236, 18 Raspberry Pi 3B, and 18 Ultimainboard photos. The 80 files form 47 capture groups, with no original/crop group crossing train and validation. This split can support a **diagnostic board-family experiment**, but the validation set has no ESP32 photo and all photos come from one capture session and one specimen per family. It cannot establish generalization to other physical boards, lighting, cameras, or revisions.

| Board family | Photos | Photos with partial part seeds | Part boxes | Photo pin boxes |
| --- | ---: | ---: | ---: | ---: |
| ESP32 | 12 | 4 | 24 | 0 |
| ESP8266 | 14 | 4 | 21 | 0 |
| NXP FRDM-MCXN236 | 18 | 3 | 52 | 0 |
| Raspberry Pi 3B | 18 | 4 | 42 | 0 |
| Ultimainboard | 18 | 4 | 94 | 4 |
| **Total** | **80** | **19** | **233** | **4** |

The 233 part boxes span 17 broad visual classes, including aliases that need harmonization before training. The largest are connector headers (64) and integrated circuits (60). The final pass adds 29 visually reviewed boxes; the reviewed J22 parent is also promoted. All nineteen part-annotated photos have **partial** major-part coverage, and the other 61 photos have no part review. Four validation originals have 39 selected part boxes across ESP8266, NXP, Pi 3B and Ultimainboard. Their unboxed objects are not verified negatives, so component recall or mAP would still be misleading. ESP32 has no validation photo in the current split.

Four contacts on the photographed Ultimainboard J22 header have reviewed pixel boxes and physical pin numbers. The 352 NXP pin records under ten source-linked part candidates describe electrical source pins and contain no registered pixel boxes. Other source pin catalogs also remain separate from photo pin labels. Four boxes on one specimen are not enough to train or evaluate a useful pin detector.

For the requested board → part → pin workflow, the shortest sound path is:

1. Use the existing board-family model only as a diagnostic baseline and label it as single-specimen evidence. Add at least one independent physical specimen and capture session per family for a real test set.
2. Review all visible parts on selected training and validation photos, including background/ignore regions, and resolve review-pending seed boxes. Split complete component annotations by specimen or at minimum capture group, with annotated validation examples for every intended class.
3. Add pixel-located pin annotations attached to a reviewed part and verified board identity. Keep schematic-only pin records as source metadata until visual pin orientation and location are confirmed. Evaluate board identity, then part identity, then pin identity separately.

This audit is a preparation and quality gate. It does not export incomplete boxes as a YOLO component dataset or claim an every-part or pin model is trained.
