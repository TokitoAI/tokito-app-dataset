# Final selective component pass

`annotations/component-seeds-final.json` adds 29 manually reviewed major-part boxes on four previously unseeded **train** photos: ESP32 (6), ESP8266 (6), Raspberry Pi 3B (9), and Ultimainboard 2.1.4 (8). The pass broadens image coverage; it does not complete component detection ground truth.

The annotation file records each original image's SHA-256, dimensions, board family, split, integer pixel box, normalized box, and visible evidence. Images were opened at their original resolution. The four marked-up overlays in `previews/final-component-pass/` were checked after coordinates were generated. Their filenames do not overlap the other component seed files.

These are **partial major-component seeds**. Small passives and some connectors remain unlabeled, so the unmarked image regions must not be treated as negative examples. The part class is based on visual form only. No exact BOM reference, manufacturer part number, source pin, net, or photographed pin contact is inferred from a nearby silkscreen label. Continue the hierarchy for each family in the same order: verify board identity, then part box/type, then individual pin only with a readable label or a source-backed, orientation-checked mapping.

All four images are views of the already photographed physical specimens. They do not provide independent specimen validation, and paired near-duplicate photos should stay within one split.
