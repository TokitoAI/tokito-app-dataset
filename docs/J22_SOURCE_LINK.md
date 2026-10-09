# Ultimainboard J22 photo-to-source pin link

The photographed Ultimainboard rev. 2.1.4 has a visually reviewed J22 four-contact header in `IMG_20261009_222135_1.jpg`, seed `major-020`. Its `SERIAL` label and pin-1 triangle identify the leftmost contact. The exact-revision Altium PCB component is J22 with `HEADER-1X4P-ST-2.54` footprint; the imported PCB shows the same triangle at pad 1 and pads 1–4 at 2.54 mm pitch. The schematic `schema3.SchDoc` independently numbers J22's four pins and labels their connected nets.

| Photo contact, left to right | J22 pad | Source net |
| --- | ---: | --- |
| 1 | 1 | `+5V` |
| 2 | 2 | `GND` |
| 3 | 3 | `TXD2` |
| 4 | 4 | `RXD2` |

The exact image boxes, board and source SHA-256 hashes, footprint and pad UUIDs, and schematic record indices are in [the machine-readable link](../annotations/ultimainboard-j22-source-link.json). Four existing entries in [canonical pin annotations](../annotations/pin-annotations.json) supply reviewed photo positions. The source nets are design assertions; the photographed board's electrical behavior was not measured. Other connector contacts and photos still require individual identity and orientation review.
