# NXP component source candidates

These ten photo links identify readable reference designators on the photographed FRDM-MCXN236-family board and join them to the Rev C schematic/BOM records. The physical board revision and installed part numbers have not been verified, so the strings below are **design BOM candidates**, not confirmed installed-component labels. Full evidence and source hashes are in [`component-source-links.json`](../annotations/component-source-links.json).

| Photo reference | Rev C source value/function | Rev C BOM part-number text | Status |
|---|---|---|---|
| U1 | MCU reference U1 | `MCXN236VDFT` | Board-model candidate; physical revision unverified |
| U8 | IC reference U8 | `LPC55S69JEV98` | Board-model candidate; physical revision unverified |
| U12 | IC reference U12 | `W25Q64JVSSIQ` | Board-model candidate; physical revision unverified |
| SW3 | `SW SPST NO`, ISP | `434123025826` | Photo silkscreen SW3 and source symbol reviewed; physical revision unverified |
| J3 | `CON 1x8` | `08010S31611-29RF` | Board-model candidate; physical revision unverified |
| J4 | `CON 2x6` | `08010S31211-29RF` | Board-model candidate; physical revision unverified |
| J5 | `SKT_1X8` | `08001S3 0811-29RF` | Board-model candidate; physical revision unverified |
| J6 | `SKT_1X8` | `08001S3 0811-29RF` | Board-model candidate; physical revision unverified |
| J12 | Source connector record | `0922S0205011N6T-2LF` | Board-model candidate; pin 1/orientation and physical revision unverified |
| J13 | Source connector record | `5-146258-2` | Board-model candidate; physical revision unverified |

The board detector returns the readable board-family name first. A part label can then show a reviewed photo reference plus a source candidate, for example `U1 — MCXN236VDFT (Rev C BOM candidate; board revision unverified)`. Do not shorten this to a confirmed part identity, and do not infer the number of a physical pin from these BOM records. Pin mapping still requires verified orientation and a matching physical revision.
