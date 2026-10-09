# Expanded major-part photo labels

`annotations/component-seeds-expanded.json` adds a separate, visually reviewed
major-part annotation pass on five previously unseeded close-up photos. Every
box was checked against an overlay on its source image. The SHA-256 field ties
each entry to the reviewed photo bytes.

| Board family | Image | Major-part boxes |
| --- | --- | ---: |
| ESP32 | `IMG_20261009_221841_1.jpg` | 6 |
| ESP8266 | `IMG_20261009_221944_1.jpg` | 3 |
| Raspberry Pi 3B v1.2 | `IMG_20261009_222222_1.jpg` | 10 |
| Ultimaker Mainboard 2.1.4 | `IMG_20261009_222137_1.jpg` | 19 |
| NXP FRDM-MCXN236 | `IMG_20261009_221800_1.jpg` | 14 |

These are partial labels of visible major parts. They do not establish
complete component coverage, exact BOM reference designators, or physical pin
numbers. Unmarked objects are not verified negatives. Individual pin labels
should be added only after identifying the board, its part, and the physical
pin position from matching evidence.
