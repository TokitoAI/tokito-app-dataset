# Ultimainboard 2.1.4 conversion provenance

## Inputs

- Native Altium layout: `data/board-sources/ultimainboard-2.1.4/1546 ultimainboard V2.1.4/Ultimaker_V2.1.4.PcbDoc`
- Native SHA-256: `53696e9f6f38df54a0c4d6065f8f8336e9df918773ea949b0b687fdf659d0160`
- Imported output: `data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb`
- Imported SHA-256: `f763641f75470b4fb5b95391ae1ec40ab4ffe2a80bc28dafd2685901c08680b7`
- Importer: KiCad CLI 10.0.7 on Windows

## Recorded commands and outputs

The stored `import-report.json` is the authoritative import record. It reports an Altium Designer source, 574 footprints, 2,330 tracks, 511 vias, 190 zones, no importer-reported errors and no importer-reported warnings.

The reproduction commands, using the verified KiCad 10.0.7 CLI syntax, are:

```text
kicad-cli pcb import --format altium --report-format json --report-file data/board-sources/ultimainboard-2.1.4/generated-kicad/import-report.json --output data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb "data/board-sources/ultimainboard-2.1.4/1546 ultimainboard V2.1.4/Ultimaker_V2.1.4.PcbDoc"
kicad-cli pcb export step --board-only --output data/board-sources/ultimainboard-2.1.4/generated-kicad/board-only.step data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb
kicad-cli pcb export glb --board-only --output data/board-sources/ultimainboard-2.1.4/generated-kicad/board-only.glb data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb
kicad-cli pcb drc --format json --output data/board-sources/ultimainboard-2.1.4/generated-kicad/drc-report.json data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb
```

The raw terminal command line was not retained, so these reproduction commands are not claimed as execution telemetry. The filenames, KiCad version, input/output hashes, import report and export logs are verified artifacts.

## Warnings and limits

The imports report no warnings, but each STEP/GLB export log recorded two warnings: `Invalid zero-sized pad pinned to 1 µm`, at lines 63047 and 63055 of the imported PCB. The DRC report records 293 errors, 569 warnings and one unconnected item. The generated Gerbers, drill files and 3D board body are reference outputs only; they are not fabrication-approved.

The board-only STEP and GLB include the PCB body, not a populated assembly. `model-component-mapping.json` carries model references and placement transforms emitted by the imported KiCad board. It marks native-Altium-to-STEP equivalence as unverified wherever no source association was retained.
