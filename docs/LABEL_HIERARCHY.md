# Board, part and pin labels

The [label hierarchy](../data/photo-model/label-hierarchy.json) applies the same **board → part → pin** order to ESP32, ESP8266, Ultimainboard 2.1.4, NXP FRDM-MCXN236 and Raspberry Pi 3B V1.2. It joins reviewed board labels, existing component seeds, available linked design sources and the shared [photo pin annotation intake](../annotations/pin-annotations.json). Run `python scripts/build_label_hierarchy.py --check` to confirm it still matches those files.

Every one of the 80 images has a reviewed board family and box. Fifteen images currently have partial component seeds: 204 part boxes in total, including an [expanded visual review](EXPANDED_COMPONENT_SEEDS.md) and a [validation-photo sprint](COMPONENT_SPRINT.md). Ten NXP parts have readable photo reference labels linked to visually reviewed Rev C schematic symbols and BOM records. Those ten source parts provide 352 distinct pin records with source pin numbers and nets.

Four J22 contacts on the photographed Ultimainboard 2.1.4 now have reviewed pixel boxes and physical pin numbers 1–4. The board's revision marking, J22 reference and pin-1 triangle match the version-matched PCB pad order. Source net names remain in the [review proposal](../annotations/crossboard-pin-proposals.json) until linked source records are checked in the hierarchy. The 352 NXP source records under ten candidate photo parts remain unregistered. A separate [source-only catalog](SOURCE_PIN_COVERAGE.md) holds 151 ESP8266-reference and 1,292 Ultimainboard schematic pin records; those catalog records are not automatically attached to photographed pins or parts. ESP32 and Raspberry Pi sources remain at pinout/document level. All five families follow the same labeling rule. Unknown pins are never used as negative training examples.

For example, the photographed NXP board contains a seeded MCU SWD header marked J12. The Rev C source lists J12 pin 1 on `JTAG_VREF`, pin 2 on `P0_0/SWDIO` and pin 4 on `P0_1/SWCLK`. The photo shows the header and the J12 marking. Assigning those numbers to individual photographed contacts still requires registration to the PCB layout or an independently checked pin-1 orientation.

A [J12 review proposal](NXP_PIN_REGISTRATION_SPRINT.md) now records ten visible contact boxes and candidate Rev C pad/net numbers. It remains outside the canonical photo pin labels because the photographed revision and pin-1 mark have not been confirmed.

The next review must follow this order for each photo, regardless of board manufacturer:

1. Confirm board family, model and revision where visible. Keep unknown revisions explicit.
2. Review each visible part box, class and reference marking. The current 204 boxes are partial seeds.
3. For each visible contact or lead, identify its physical pin number from an oriented layout or legible pin-1 evidence, record its photo box and identity evidence in `annotations/pin-annotations.json`, then attach a source net only when the source matches the photographed board. BGA balls and hidden pins have no photo label from a top-view image.

Each photo pin entry needs a unique `id`, `image_file`, the matching `image_sha256`, exact `board_family`, reviewed parent `part_id` from the generated hierarchy, `pin_number` as a string, `photo_bbox_xyxy_pixels` within that image, `pin_identity_evidence` explaining orientation or marking, and `review_status: visually_reviewed_pin_location`. The generator checks the photo hash, board and part parent before accepting the pin. An entry can have a reviewed physical pin number without a source net; that status stays explicit. If the pin cannot be numbered reliably, do not put it in the training labels.

Board identification, source component identity and physical pin position have separate evidence requirements. Component and pin model training waits for reviewed, sufficiently complete photo labels and independent validation images.
