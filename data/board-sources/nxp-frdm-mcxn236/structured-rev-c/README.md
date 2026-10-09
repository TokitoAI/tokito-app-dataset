# FRDM-MCXN236 Rev C structured sources

These artifacts preserve the BOM and Cadence PST text from the collected
official Rev C design archive. They describe that design revision. Matching the
photographed specimen's revision and fitted population remains a separate task.

The source BOM has **96 items and 391 reference designators**. Both the text BOM
and XLSX contain exactly the same references as `pstxprt.dat` and `pstxnet.dat`.
The BOM explicitly marks **63 references across 22 items as DNP**. Another 37
references describe mounting holes, test pads or solder jumpers with
`NO PART TO ORDER` in their descriptions. The 391 total is therefore not a count
of purchasable or physically fitted components.

The netlist contains **296 electrical net records with 1,243 pin records**, plus
one literal `NC` group with 87 pin records. Pins in the `NC` group must not be
treated as electrically connected to each other. The four mounting-hole
references BH1-BH4 occur only in that group. There are 92 native primitive
definitions, all referenced by the expanded part list.

## Files and provenance

| File | Contents |
| --- | --- |
| `bom-workbook.json` | All source worksheet rows, typed values, cell types and number formats; headers and preamble retained. |
| `bom-items.json` | 96 grouped BOM items with all 11 original columns, sheet/row/range provenance and expanded reference lists. |
| `bom-SCH-90828_C.csv` | Original 11 BOM columns in their original order, one item per row. JSON retains types and distinguishes nulls from whitespace. |
| `bom-text.json` | Text BOM preamble, original columns, physical source lines and reconstructed continuation rows. |
| `native-parts.json` | 391 `PART_NAME` records, literal properties, symbol sections, instance paths and source line ranges. |
| `primitives.json` | 92 primitives, literal body properties, symbol pin names and physical pin numbers. |
| `netlist.json` | Native net records and nodes, with `record_kind` separating electrical nets from the no-connect group. |
| `net-pins.csv` | Flat net/pin lookup including record kind and original source line. |
| `components.json` | Per-reference joins from BOM to native part/primitive properties, net pins and candidate schematic text occurrences. |
| `extraction-report.json` | Source paths, byte sizes, SHA-256 hashes, counts, discrepancies and interpretation limits. |

`components.json` has a `components` array. Find an entry by `refdes`; then use
`bom_source` to locate its worksheet row, `bom_columns` for original values,
`native_part` for section provenance, `primitive_body_properties` for the native
footprint identifier and value, and `connections` for its source pin records.
Every source path is relative to the parent `nxp-frdm-mcxn236` directory.

The original XLSX stores some `MFG_PN` identifiers as numeric cells. JSON keeps
those original numbers in `source_columns` / `bom_columns` and also supplies
`manufacturer_part_number_text` for lookup. Empty cells and the literal single
space in the crystal rows' `ASSY_OPT` fields remain distinct. `PRE_APN` is kept
as supplied; it is not interpreted as an alternate manufacturer part. There is
no explicit alternate-part list in these BOM columns.

## SW3 source example

The entry with `refdes: "SW3"` joins to `bom-item-079`, worksheet `SCH-90828_C`,
row **93**, range **A93:K93**:

| Original field | Source value |
| --- | --- |
| Item | 79 |
| Quantity | 3 (the grouped row contains SW1, SW2 and SW3) |
| AgilePN | 510-78653 |
| Description | SW SP PB 50mA 16V SMT |
| MFG_PN | 434123025826 (numeric source cell F93) |
| VALUE | SW SPST NO |
| ASSY_OPT / FIND# / PRE_APN | Empty |
| Reference | SW1,SW2,SW3 |

The manufacturer name is retained verbatim in `bom_columns.MFG`.
`pstxprt.dat` lines 3666-3676 give `SILK='ISP'` and a page-10 instance path.
The primitive gives footprint identifier `sw4_4p15_4p2x3p2_sm` and literal
height string `2.60` (no units have been added). Net records connect pins **3/4**
to `P0_6/ISPMODE_N-SW` and pins **1/2** to `GND`. The preserved source rows
identify the Rev C design part; they do not by themselves identify the exact
installed part on an unconfirmed board revision.

## Schematic text candidates

379 of the 391 native references have one or more matches in the existing
`schematic-reference-index.json`. `schematic_text_candidates` preserves matching
IDs, page numbers, text bounds and raw text. The index and PDF hashes are
recorded in `schematic_join_sources`, and the PDF's current hash is checked
against the index during extraction.

This is a match on normalized text. BGA ball labels, change history, notes and
DNP lists can share a component's spelling, so it does not confirm symbol
identity. Missing candidates do not prove the reference is absent from the
schematic. The current unmatched references are BH1-BH4, R132, R135, R136 and
SJ1-SJ5. SW3 resolves to the previously visually inspected `p010-SW3-01` on
page 10; its candidate status remains explicit in the data.

## Reproduction and checks

From the repository root, use Python 3.10+ with `openpyxl==3.1.5`:

```text
python scripts/extract_mcxn236_sources.py
python scripts/extract_mcxn236_sources.py --check
```

`--bundle` changes the board-source directory. `--output-dir` can select another
artifact directory. `--check` regenerates the extraction in memory and compares
every JSON and CSV with the saved output; it does not modify sources or outputs.

The extractor fully consumes the observed native text grammar, preserving
property strings and source lines. Unknown syntax stops extraction. Checks
compare parsed counts with the source's record markers, BOM quantities with
expanded reference lists, all four reference sets, all common text/XLSX BOM
fields, internal part numbers, DNP flags, primitive membership, node physical
pins, section instance paths and duplicate pin assignments. All comparisons
pass for this bundle; there are no discrepancies or exact value-text differences.
The source workbook contains no formulas.

The native BRD, DSN and OPJ are hashed for provenance but are not decoded here.
This extraction does not generate PCB geometry, Gerbers, STEP/GLB models or photo
bounding boxes. See the parent provenance and archive inventory for the actual
download contents and rights information.
