# Major-component photo annotation sprint

`annotations/component-seeds-sprint.json` adds selected visible part boxes to five photos that had no prior component seeds. The images retain the board-family label first; every part box belongs to that identified board. No pin label is inferred from a connector's appearance or from another board's schematic.

| Board family | Image | Existing split | Selected part boxes |
| --- | --- | --- | ---: |
| ESP32 | `IMG_20261009_221901_1.jpg` | train | 6 |
| ESP8266 | `IMG_20261009_221154.jpg` | val | 6 |
| NXP FRDM-MCXN236 | `IMG_20261009_221657.jpg` | val | 13 |
| Ultimainboard 2.1.4 | `IMG_20261009_222033.jpg` | val | 10 |
| Raspberry Pi 3 Model B v1.2 | `IMG_20261009_222340.jpg` | val | 10 |

Each image SHA-256 and pixel size were checked against `data/photo-model/photo-manifest.json`. Boxes were placed on the source photos and checked using rendered overlays. They are normalized `xyxy` coordinates with corresponding source-pixel boxes. The 45 boxes cover prominent modules, ICs, connectors, switches, a relay, and a heatsink. Fine passives, many smaller chips, partially obscured hardware, and individual pin positions are outside this pass.

This file is **partial annotation** (`training_eligible: false`). Unboxed regions must not be used as negative component examples. The four validation photos are useful for qualitative review of selected objects; incomplete ground truth prevents valid detector recall or mAP calculations from these labels. Similar views within a capture group are correlated and must not be presented as independent held-out examples. Reference designators and exact BOM part identities remain null until visually checked against the correct board revision and source; the `pin_labels` arrays are empty until a pin number and its photo position are registered and reviewed.
