# Physical board provenance sample: Ultimainboard rev. 2.1.4

The user-held board in [IMG_20261009_222135_1.jpg](../../../data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg) is identified by the visible **Ultimainboard rev. 2.1.4** silkscreen. This confirms the marked revision; manufacturer authenticity, fitted supplier parts, and complete geometric registration remain unverified.

![Revision evidence](revision-evidence.png)

## Source PCB and licences

The original layout is [Ultimaker_V2.1.4.PcbDoc](../../../data/board-sources/ultimainboard-2.1.4/1546%20ultimainboard%20V2.1.4/Ultimaker_V2.1.4.PcbDoc) (Altium PcbDoc). SHA-256: `53696e9f6f38df54a0c4d6065f8f8336e9df918773ea949b0b687fdf659d0160`. It is byte-identical to the [official electronics file](https://github.com/Ultimaker/Ultimaker2Go/blob/b9a1bd0ce6d664a192067781673fec3aa40ad01d/1546/1546%20ultimainboard%20V2.1.4%20electronics/Ultimaker_V2.1.4.PcbDoc) at Ultimaker2Go commit `b9a1bd0ce6d664a192067781673fec3aa40ad01d` (Git blob `4501461ca707656f95318c9919ea1b6c39e9a8fa`). Native component coordinates are in **mil**, where 1 mil = 0.0254 mm.

The [directory notice](https://github.com/Ultimaker/Ultimaker2Go/blob/b9a1bd0ce6d664a192067781673fec3aa40ad01d/1546/1546%20ultimainboard%20V2.1.4%20electronics/readme.txt) states GPLv2 for the electronics, with [GPL text](https://github.com/Ultimaker/Ultimaker2Go/blob/b9a1bd0ce6d664a192067781673fec3aa40ad01d/1546/1546%20ultimainboard%20V2.1.4%20electronics/gpl-2.0.txt) retained locally. The separate assembly model uses the repository's [CC BY-NC 3.0 default](https://github.com/Ultimaker/Ultimaker2Go/blob/b9a1bd0ce6d664a192067781673fec3aa40ad01d/LICENSE); a model-specific grant is unverified. Extracted vendor-model licences and an independent licence for user photos remain unverified.

The [imported KiCad layout](../../../data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb) uses millimetres and degrees. Its UUIDs belong to this exact file (SHA-256 `f763641f75470b4fb5b95391ae1ec40ab4ffe2a80bc28dafd2685901c08680b7`); another import may produce new UUIDs. The conversion has 293 DRC errors and 569 warnings and is a reference candidate requiring engineering review. Its outline is 175 × 79 mm. Full board-to-photo registration is unverified.

## Available 3D models and units

| Model | Units | Physical relationship | SHA-256 |
| --- | --- | --- | --- |
| [ultimainboard-part1546.glb](../../../data/board-sources/ultimainboard-2.1.4/derived/ultimainboard-part1546.glb) | metres | assembly geometry match unverified | `fad1530309ec35e6ba3101832703534319e8cbf10fbade1279f45311844015c4` |
| [board-only.glb](../../../data/board-sources/ultimainboard-2.1.4/generated-kicad/board-only.glb) | metres | board body only | `c74b63dadc87d3cd119b11212d5e2ce29db0208117db43932b4fa3bb083c3291` |
| [board-only.step](../../../data/board-sources/ultimainboard-2.1.4/generated-kicad/board-only.step) | millimetres | board body only | `cceca2762ee488e79c783a02d28a96a38e944a419efae2ce6ce581df2a019830` |
| [1546-A.STEP](../../../data/board-sources/ultimainboard-2.1.4/official-3d/1546-A.STEP) | millimetres | assembly geometry match unverified | `cc26f03e5c7db5e962b7a00f287fa6b4451f2cc74a8b82faea169e7de4760417` |

There are **61 extracted embedded STEP files**, representing **39 distinct byte hashes**: 49 declare millimetres, 9 centimetres and 3 metres. Units were read from each STEP LENGTH_UNIT/SI_UNIT declaration. Do not assume every STEP uses mm. [assets.json](assets.json) enumerates every model, source file, byte count, hash, units, source and licence link. Model-stream numbers are not verified reference designators; component assignment is unverified. GLB uses metres.

## Verified UUID → reference → photo mapping

[footprint-mapping.json](footprint-mapping.json) and [CSV](footprint-mapping.csv) contain 574 unique imported footprint UUIDs joined to 574 native reference designators: 572 match both reference and footprint name exactly; J32/J33 match reference and Value but their imported footprint name is truncated from `BOXHEADER-10P-R/A-ST-2.54` to `A-ST-2.54`. The original names and this conversion difference are recorded. These joins do not establish a global geometry transform or installed part identity. Every row has an explicit photo verification status.

**Only J22 is verified against this sample photo.** Its footprint UUID is `24ee97da-cf16-4509-add4-6886f42b21e0`, native Altium component ID `MWFWPWHQ`, schematic ID `SIOTLFTE`, and footprint `HEADER-1X4P-ST-2.54`. Photo seed `major-020` identifies the connector. Readable J22/SERIAL text and the pin-1 triangle support contact orientation.

![J22 reviewed contacts](j22-evidence.png)

| Photo contact left to right | Source pin | Source net |
| --- | --- | --- |
| 1 | 1 | +5V |
| 2 | 2 | GND |
| 3 | 3 | TXD2 |
| 4 | 4 | RXD2 |

[j22-photo-source-link.json](j22-photo-source-link.json) records the exact photo hash, pixel boxes, footprint/pad UUIDs, source hashes and schematic record indices. Native schematic pin endpoints, wires and net labels were checked. Net names are source-design assertions; the physical board's voltage and electrical behaviour were not measured. No pin numbers are propagated to other photos.

[component-label-status.json](component-label-status.json) preserves the sample's available seed labels. All uncertain component classes, reference labels and installed part identities remain **unverified**. This sample does not claim exhaustive labeling.

## MCXN236 / MCXN947 separation

The NXP photographs identify **FRDM-MCXN236**; its physical revision remains **unverified**. Its [official Rev C sources](https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-MCXN236) are stored separately under `data/board-sources/nxp-frdm-mcxn236`. The `nxp-frdm-mcxn947` directory is a **different-board reference**, never a substitute for the photographed MCXN236 or evidence of its component UUIDs. Neither board is used to establish the Ultimainboard mapping.

[manifest.json](manifest.json) records scope and evidence. [verification.json](verification.json) records file/hash, unit, UUID and J22 checks. Large binaries in this repository use Git LFS; hashes refer to the complete downloaded asset bytes, not pointer text.

## Offline, conversion, model and AR records

[offline-manifest.json](offline-manifest.json) distinguishes fully materialized files from Git LFS pointers. An offline bundle is valid only when it has no pointer entries and every byte hash matches.

[conversion-provenance.md](conversion-provenance.md) records the input/output hashes, KiCad version, captured import report, export logs and the two zero-sized-pad warnings. [model-component-mapping.json](model-component-mapping.json) lists every imported model URI with its footprint UUID, reference designator and composed placement inputs; unknown native STEP associations are marked explicitly. [ar-registration.json](ar-registration.json) records the reviewed J22 landmark and four mounting-hole candidates, while withholding an AR transform until enough independently verified correspondences exist.

The repository-wide [all-board index](../../ALL_BOARD_INDEX.json) records revision evidence, CAD/model coverage, verification status and missing inputs for each board family.
