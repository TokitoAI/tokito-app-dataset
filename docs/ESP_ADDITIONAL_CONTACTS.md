# Additional ESP contact labels

The new per-photo labels are in [`annotations/esp-additional-contact-labels.json`](../annotations/esp-additional-contact-labels.json). Review overlays show [ESP32](../previews/photo-pins/IMG_20261009_221841_1-additional.png) and [ESP8266](../previews/photo-pins/IMG_20261009_221952_1-additional.png). The SHA-256 in each image record identifies the exact photographed pixels inspected.

| Photo crop | Reviewed contact rows | Reviewed contacts with printed aliases |
| --- | ---: | ---: |
| ESP32 `IMG_20261009_221841_1.jpg` | 2 | 30 |
| ESP8266 `IMG_20261009_221952_1.jpg` | 2 | 29 |

The ESP32 photograph gives both outer rows in one frame. Its left row reads 3V3, GND, D15, D2, D4, RX2, TX2, D5, D18, D19, D21, RX0, TX0, D22, D23. Its right row reads VN, GND, D13, D12, D14, D27, D26, D25, D33, D32, D35, D34, VN, VP, EN. The prior ESP32 crop did not show the right-side contacts; these 15 right-row boxes are a new visible location set.

The ESP8266 photograph contains 29 reviewed contacts. The left row reads A0, G, VU, S3, S2, S1, SC, [omitted], SK, G, 3V, EN, RST, G, VIN. The omitted contact's printed text could be the letter O or digit zero in `SO/S0`; its contact is visible in the preview but has no alias label. The right row reads D0, D1, D2, D3, D4, 3V, G, D5, D6, D7, D8, RX, TX, G, 3V.

These are additional captures of the same physical ESP specimens already present in the dataset. They add **59 per-image contact boxes** and four row parents, not 59 new independently photographed physical contacts. The outer solder contacts and adjacent silkscreen are visible; a connector body or mating header on the other board face has not been established. Printed aliases are stored verbatim. Numeric physical pin numbers, schematic net assignments, and connector refdes remain null. For example, `D15` is one printed string, not pin number 15.

Coverage remains partial and `training_eligible` is false. All captures of each physical specimen must stay in the same train/validation group; a duplicate crop cannot serve as an independent validation board.
