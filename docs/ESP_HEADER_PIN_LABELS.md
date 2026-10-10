# ESP contact aliases from phone photographs

Reviewed overlays: [ESP32](../previews/photo-pins/IMG_20261009_221838_1.png) and [ESP8266](../previews/photo-pins/IMG_20261009_221941_1.png).

`annotations/esp-header-pin-labels.json` adds the board → part → pin relationship for two ESP photographs. The part is the visible through-hole solder-contact row; the photographs do not establish a header body on the opposite face.

Original image pixels and rendered bounding-box overlays were inspected. Image SHA-256 values tie each record to the actual photograph. Every contact has a pixel box and a separate evidence box around its adjacent printed alias. Three reviewed parent rows contain 44 reviewed contact aliases:

| Board photograph | Parent rows | Reviewed contact aliases |
| --- | --- | --- |
| ESP8266, `IMG_20261009_221941_1.jpg` | Left and right outer-edge solder-contact rows | 29 |
| ESP32, `IMG_20261009_221838_1.jpg` | Left outer-edge solder-contact row | 15 |

ESP8266 left-row aliases are A0, G, VU, S3, S2, S1, SC, SK, G, 3V, EN, RST, G and VIN. The contact between SC and SK is deliberately omitted because its printed SO/S0 spelling is ambiguous. Right-row aliases are D0, D1, D2, D3, D4, 3V, G, D5, D6, D7, D8, RX, TX, G and 3V. Repeated aliases remain separate physical contact instances under their row parent.

ESP32 left-row aliases are 3V3, GND, D15, D2, D4, RX2, TX2, D5, D18, D19, D21, RX0, TX0, D22 and D23. The photographed right edge has readable text, but its corresponding contacts lie outside this crop; it has no reviewed pin locations in this annotation.

These are **printed board aliases**, not numbered physical connector pins or schematic nets. `pin_number`, `source_refdes` and `source_net` are null. An alias such as D15 is stored as the complete printed string rather than converted to physical pin number 15. Board clone identity, electrical function and external schematic mappings remain unresolved. Source-only pin mappings are not inferred from these labels.

The annotations cover a partial subset and remain `training_eligible: false`. Other board parts and contact instances require annotation before these photos can serve as complete component/pin detection ground truth. The left ESP8266 contact row reaches the crop boundary and is marked truncated.
