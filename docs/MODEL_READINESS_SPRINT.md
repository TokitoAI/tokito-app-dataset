# Model-readiness audit

Run `python scripts/model_readiness.py` from the repository root for a live report; add `--json` for machine-readable output. The script checks image hashes against the manifest and fails if an original/crop capture group spans train and validation.

As audited on 2026-10-10, the board-family layer has 80 reviewed photo boxes: 62 train, 11 validation, and seven crop variants held out. The five families are represented by 12 ESP32, 14 ESP8266, 18 NXP FRDM-MCXN236, 18 Raspberry Pi 3B, and 18 Ultimainboard photos. The 80 files form 47 capture groups, with no original/crop group crossing train and validation. This split can support a **diagnostic board-family experiment**, but the validation set has no ESP32 photo and all photos come from one capture session and one specimen per family. It cannot establish generalization to other physical boards, lighting, cameras, or revisions.

| Board family | Photos | Photos with partial part seeds | Part boxes | Numbered pins | Printed-alias contacts |
| --- | ---: | ---: | ---: | ---: | ---: |
| ESP32 | 12 | 4 | 27 | 0 | 45 |
| ESP8266 | 14 | 4 | 25 | 0 | 58 |
| NXP FRDM-MCXN236 | 18 | 3 | 52 | 0 | 0 |
| Raspberry Pi 3B | 18 | 4 | 42 | 40 | 0 |
| Ultimainboard | 18 | 4 | 94 | 22 | 0 |
| **Total** | **80** | **19** | **240** | **62** | **103** |

The 240 part boxes span 18 broad visual classes, including aliases that need harmonization before training. The largest are connector headers (64) and integrated circuits (60). Seven reviewed ESP contact-row parents were added, and the four Ultimainboard headers plus Pi J8 have reviewed reference designators. All nineteen part-annotated photos have **partial** major-part coverage, and the other 61 photos have no part review. Four validation originals have 39 selected part boxes across ESP8266, NXP, Pi 3B and Ultimainboard. Their unboxed objects are not verified negatives, so component recall or mAP would still be misleading. ESP32 has no validation photo in the current split.

Ultimainboard J22/J23/J1/J2 provide 22 reviewed numbered contacts and source-net links. Pi J8 adds 40 numbered contacts with revision 1.2 reduced-schematic net names; lower contact positions are less sharp. The 103 ESP contact boxes across four photos carry only directly observed silkscreen aliases: numeric pin numbers, chip-pin identities and source nets remain unknown. The 352 NXP pin records under ten source-linked part candidates describe electrical source pins and contain no registered pixel boxes. Only 22 of the separate 1,443 Altium reference catalog records are registered to photos. These 165 contact boxes across six photos are partial seeds from repeated physical specimens, insufficient to train or evaluate a useful general pin detector.

For the requested board → part → pin workflow, the shortest sound path is:

1. Use the existing board-family model only as a diagnostic baseline and label it as single-specimen evidence. Add at least one independent physical specimen and capture session per family for a real test set.
2. Review all visible parts on selected training and validation photos, including background/ignore regions, and resolve review-pending seed boxes. Split complete component annotations by specimen or at minimum capture group, with annotated validation examples for every intended class.
3. Add pixel-located pin annotations attached to a reviewed part and verified board identity. Keep schematic-only pin records as source metadata until visual pin orientation and location are confirmed. Evaluate board identity, then part identity, then pin identity separately.

This audit is a preparation and quality gate. It does not export incomplete boxes as a YOLO component dataset or claim an every-part or pin model is trained.
