# Cross-board photo pin evidence (review queue)

The labeling order applies to every family: identify the board, identify its physical connector or component, then identify a visible contact within that parent. A source pin number or net is not itself a photographed pin box. This review deliberately keeps source records and photo contacts separate.

## ESP8266 NodeMCU-style clone

`data/photo-model/by_board/esp8266_board/IMG_20261009_221941_1.jpg` is a 1016 × 1866 close-up of the actual photographed clone. The silkscreen is unusually useful: `A0`, `G`, `VU` are readable along the left contact row and `D0`, `D1`, `D2`, etc. along the right. The first four contact boxes in `annotations/crossboard-pin-proposals.json` were positioned over visible solder joints aligned with `A0`, `G`, `D0`, and `D1`. The asserted names are the **photo's own silkscreen names**. No source refdes, electrical net, or bare ESP8266 chip pin number is asserted. The available NodeMCU schematic is a different USB-UART variant, so its component/refdes identity cannot be transferred to this clone without registration.

The existing major-component seed list for this image does not include the two edge header/contact rows. Before canonical import, add and review a parent part object for each row (or the actual header if a different photo shows its body), then check the four pixel boxes at full resolution. These proposals are intentionally not training labels yet.

`data/photo-model/by_board/esp32_board/IMG_20261009_221838_1.jpg` likewise shows legible `3V3`, `GND`, `D15` and other text beside plated side contacts, but the contacts are soft and the lower board is cropped. It is a second direct-silkscreen route after parent header review. The community pinout is corroborating context, not proof of the photographed board's internal netlist.

## Raspberry Pi 3 Model B V1.2

`data/photo-model/by_board/raspberry_pi_3b_board/IMG_20261009_222248_1.jpg` visibly carries the exact `Raspberry Pi 3 Model B V1.2` legend. Its right-side 2 × 20 GPIO header is already a major-component seed, `major-003`. Raspberry Pi's [revision 1.2 reduced schematic](https://pip-assets.raspberrypi.com/categories/520-raspberry-pi-3-model-b/documents/RP-008340-DS-1-raspberry-pi-3-b-reduced-schematics.pdf) identifies that connector as `J8`, 40-way, numbered as odd/even rows from 1/2 to 39/40; the [official hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) links this revision's schematic and mechanical drawing. This is a strong board → part → *source pin inventory* chain. However, pin 1's corner has not been independently resolved from a numbered board mark or pad geometry in this front-side phone image. The connector can be linked to J8 for review, but all 40 photo contact positions remain unregistered. Do not distribute the 1–40 source labels across the visible contacts until orientation is verified from a second view or pad-numbered layout.

## Ultimainboard 2.1.4

`data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg` (1408 × 3112) visibly prints `Ultimainboard rev. 2.1.4`, matching the local CAD source. It shows a four-contact `J22` header with a nearby `SERIAL` label and a triangle below its left end. Existing seed `major-020` bounds this same header. The extracted PCB component record has `SOURCEDESIGNATOR: J22`, footprint `HEADER-1X4P-ST-2.54`, and rotation 270 degrees.

The exact Altium board was imported into `data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb`. Its J22 footprint places pad 1 at local `(0,0)` and pads 2–4 in successive 2.54 mm steps. The front silk triangle is drawn at that same pad-1 end. The triangle appears at the left end in the phone photo, giving independent source plus photo orientation evidence for left-to-right numbering 1–4. The imported electrical nets are respectively `+5V`, `GND`, `TXD2`, `RXD2`. Four individual contact boxes were independently reviewed at full image pixels and promoted to `annotations/pin-annotations.json` under the reviewed J22 parent. The net names remain in `annotations/crossboard-pin-proposals.json` until a structured source link is added to the hierarchy. The other white headers still require individual refdes and orientation checks.

## Decision gate

The four ESP8266 boxes are *review proposals*, because their parent header rows are absent from canonical part seeds. The four Ultimainboard J22 pin locations and numbers are reviewed in the canonical pin intake. The Pi J8 has source pin records but no verified photo pin-1 corner. Keep unknowns explicit; do not count source pin inventories as located photo pins.
