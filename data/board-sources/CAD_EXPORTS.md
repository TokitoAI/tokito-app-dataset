# Generated CAD reference exports

KiCad CLI 10.0.7 generated the files under each `generated-kicad/` directory. Each directory contains the board file, Gerber and Excellon drill files, board-only STEP and GLB models, the KiCad DRC report, and `provenance.json` with SHA-256 hashes. These are dataset reference assets. **Do not send the generated Gerbers to a fabricator without engineering review.**

| Board source | Source design match | Imported or native PCB | Board outline | Source reference designators | DRC errors / warnings |
| --- | --- | --- | --- | --- | --- |
| ESP32 Dev Kit community clone | Clone reference; photographed variant unconfirmed | Native KiCad PCB | 47.0096 × 29.1846 mm | Native board copied byte-for-byte from source ZIP | 19 / 128 |
| Ultimainboard v2.1.4 | Matching version family; photo registration pending | Altium PcbDoc imported | 175 × 79 mm | 574 / 574 match structured source | 293 / 569 |
| FRDM-MCXN236 Rev C | Official design; photographed specimen revision unconfirmed | Allegro BRD imported | 118 × 55 mm | 391 / 391 BOM references match | 1,087 / 315 |

The GLB files are valid glTF 2 binary files; their board outline dimensions match KiCad PCB statistics. The STEP files are valid STEP AP214 files with a solid board body. **Both 3D formats contain the board body only**, not component bodies or a populated assembly. The Ultimainboard and NXP conversion outputs showed zero-size-pad warnings on reload, and the NXP Allegro import printed padstack antipad/thermal warnings. The import JSON reports did not include those command-line warnings. The complete DRC reports and hashes are retained beside each board.

ESP8266 already has collected upstream Gerber sets under `esp8266-nodemcu-reference/gerbers-verified/`; its source is a different USB-UART variant from some photographed boards. Raspberry Pi 3B v1.2 currently has reduced schematics but no exact PCB CAD in this corpus, so neither family was represented by a newly generated KiCad export here.
