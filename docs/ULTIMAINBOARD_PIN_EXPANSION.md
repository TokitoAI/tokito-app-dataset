# Ultimainboard 2.1.4 physical pin expansion

Reviewed overlays: [J23/J1](../previews/photo-pins/ulti-review-top.png) and [J2](../previews/photo-pins/ulti-review-bottom.png).

The expansion file adds 18 individually inspected contact-tip boxes for J23 (EXT/IO), J1 (ICSP1), and J2 (ICSP2) in `IMG_20261009_222135_1.jpg`. It preserves the required board → reviewed connector → pin relationship. These are additional labels beyond the four existing J22 labels.

Photo: `data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg`, 1408 × 3112 pixels, SHA-256 `a27826395afbbd16c45d6afe0085d43f526f31058b287a768e86c367021682df`. The printed board revision is 2.1.4. Coordinates in the JSON are full, unrotated photo pixels. Boxes mark exposed contact tips, not entire bent leads or hidden solder joints.

| Header | Existing parent seed | Pin 1 in original photo | Source pad nets for pins 1–6 |
| --- | --- | --- | --- |
| J23 / EXT/IO | major-018 | Lower left, beside triangle | GND, GND, +5V, +5V, PC7, PD7 |
| J1 / ICSP1 | major-019 | Lower left, beside triangle | PB3, +5V, PB1, PB2, NRESET, GND |
| J2 / ICSP2 | major-025 | Upper right, beside triangle | NetJ2_1, +5V, NetJ2_3, NetJ2_4, NetD2_1, GND |

`annotations/ultimainboard-pin-expansion.json` includes three `reviewed_parent_updates`. The hierarchy generator applies these to the parent records and ingests the 18 pins alongside the four J22 pins without changing the original seed files. Parent connector extents and refdes were reviewed together with the contact positions. Every contact box lies inside the existing parent box.

The source match uses the exact-version Altium PCB and its hash-addressed KiCad import. For each pin the expansion records its unique imported through-hole pad UUID, local pad coordinates, literal source net, and native schematic pin stream index. All 18 native schematic pin records were checked for RECORD=2 and the matching pin number; all 18 imported pad net names occur in the native PCB net-name inventory. Source pin-to-net assignments are derived from imported through-hole pads, not an independent native binary pad decoder or electrical measurement.

The imported 2×3 footprints also contain bottom-layer SMD copper additions with repeated pad numbers and different nets. A join on pad number across every footprint pad is ambiguous. This review selects the six unique `thru_hole` pads only. The source files, footprint IDs, native component IDs and hashes are included for reproduction.

Pin orientation was inspected from the actual photo triangles and compared to the imported footprint triangle beside local pad 1=(0,0). J23 and J1 share an orientation; J2 faces the opposite direction. Each photo box was subsequently inspected in an overlay. The lower J2 crop was additionally rotated 180 degrees for reading ICSP2/J2, while all saved label coordinates remain in the original orientation.

The adjacent ADC1 / ADC2 / EXP3 headers remain candidates. Repeated photographed J26 markings do not justify assigning a whole eight-contact group to the source's three-pin J26. No candidate pin positions were promoted there, and these labels were not propagated to other photographs.
