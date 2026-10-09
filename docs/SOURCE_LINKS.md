# Photo-to-source links

`annotations/component-source-links.json` records the evidence connecting a visible object to a source document. Paths resolve from the repository root. Image and PDF SHA-256 values bind each link to the files actually reviewed.

Each record identifies the annotation file and object ID, the photo observation, and a source candidate with its own board model, revision and PDF page. `observed_reference_designator` is a readable photo marking. A schematic candidate is not proof of the installed manufacturer's part number or of a matching physical-board revision.

The first record links `nxp_seed_009`, the photographed SW3/ISP pushbutton, to SW3 on sheet 10 of SPF-90828 Rev C. The photo confirms FRDM-MCXN236, but its revision is unconfirmed. The link therefore has `match_status: model_match_revision_unconfirmed` and `exact_installed_part_mapping: false`. Component boxes remain partial review seeds and are not a complete training set.

Its `source_component` also binds the structured Rev C entry to BOM item 79, worksheet row 93, and the native `SILK=ISP` record. The source manufacturer part number is `434123025826`; the top-level installed-part field remains null. The source record and workbook are hash-bound separately. The [structured-source guide](../data/board-sources/nxp-frdm-mcxn236/structured-rev-c/README.md) explains all 391 reference records, DNP flags, and the separate no-connect group.

The schematic reference index preserves text occurrences and their PDF coordinates. Notes, cover-page change history, multi-unit symbols and repeated references can all appear. Occurrence counts are not BOM quantities. Use the original PDF to inspect a candidate before asserting an exact link.

FRDM-MCXN947 is a different source board. Its BOM, PCB and netlist must not be attached to the photographed MCXN236. The original identification photo was relocated into the MCXN236 source folder without changing its bytes; the old hypothesis and hash are retained in the MCXN947 `REFERENCE_STATUS.json` and import record.

`data/photo-model/nxp-component-seeds.json` mirrors the canonical `annotations/nxp-component-seeds.json`; keep both copies synchronized. The `by_board/nxp_frdm_mcxn_board` folder name and unreviewed fields in the raw ingestion manifest are historical acquisition metadata. The reviewed board annotations and YOLO class 3 use `nxp_frdm_mcxn236_board`.

Run `python scripts/validate_source_links.py` to check paths, file hashes (including LFS pointers in CI), structured source joins, reference-page membership, mirrored annotations and relocation metadata. These checks establish file consistency; visual evidence and source/specimen matching remain separate review requirements.
