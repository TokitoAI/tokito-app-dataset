# Dataset board index

| Board | Exact revision status | CAD and models available | Verification status | Missing inputs |
| --- | --- | --- | --- | --- |
| ESP32 DevKit 30-pin | Physical revision unverified | Native KiCad clone PCB; board-only STEP/GLB; separate assembly STEP/GLB | Community clone reference; physical board match unconfirmed | Reviewed photo-to-CAD registration and exact physical revision |
| NodeMCU DevKit V1.0 | Source V1.0; photographed USB-UART variant unverified | Altium PCB; four Gerber archives; 17 extracted STEP models | Source reference differs from some photographed boards | Exact physical variant, native import/export, photo registration |
| FRDM-MCXN236 | Official source Rev C; physical revision unverified | Allegro BRD; KiCad import; board-only STEP/GLB; Gerber/drill | Photographed model is MCXN236 | Physical revision and registration; import padstack review |
| FRDM-MCXN947 | Source Rev C | Reference sources only | A different-board reference only; never assigned to MCXN236 photos | Separate photograph before registration |
| Raspberry Pi 3B | V1.2 family only | Reduced schematics; community cluster assembly model only | Board family inferred; exact physical revision unverified | Exact PCB CAD, standalone board model, licence and photo registration |
| Ultimainboard | **2.1.4**, photographed silkscreen verified | Altium PCB; imported KiCad PCB; 61 STEP streams; assembly STEP/GLB; board-only STEP/GLB | Design revision matches marking; full physical-geometry registration pending | At least four reviewed board/photo landmarks and transform validation |

The machine-readable companion, [ALL_BOARD_INDEX.json](ALL_BOARD_INDEX.json),
contains the same statuses and is intended for tooling.
