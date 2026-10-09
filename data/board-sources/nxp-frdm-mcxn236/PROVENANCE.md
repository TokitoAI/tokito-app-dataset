# FRDM-MCXN236 source acquisition

Collected 2026-10-09 after new photos identified FRDM-MCXN236, replacing the earlier MCXN947 hypothesis. The existing MCXN947 folder is preserved as a different-board reference. Matching this specimen's PCB revision is still required.

Official product page: https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-MCXN236

The official page lists:

- FRDM-MCXN236 Schematics, SPF-90828, PDF Rev C, 2024-04-26, 3.35 MB. Download: https://www.nxp.com/webapp/Download?colCode=SPF-90828
- FRDM-MCXN236 Design Files, ZIP Rev C, 2024-04-26, 20.43 MB. Download: https://www.nxp.com/webapp/Download?colCode=FRDM-MCXN236-DESIGN-FILES

## Collected schematic

`SPF-90828.pdf` was copied without modification from the pre-existing local `C:/Users/Acer/Downloads/SPF-90828.pdf`. The local download's earlier provenance is not known. Its content identifies NXP FRDM-MCXN236, SCH-90828/PDF SPF-90828, revision C, 13 sheets, and schematic date 2024-03-25. This matches the official product page's advertised document and revision; publication/listing date is separate from drawing date.

- Bytes: 3,511,914
- SHA-256: 243b93184f692b0f7c0deb3a9a63f6262ea3083a05c30c0143b4a4faa54b1868
- `schematic-text.txt` is derived text extracted with pypdf, all 13 pages. It is for search; original PDF remains authoritative.

The PDF contains a proprietary-use notice requiring express written NXP permission for engineering design, procurement or manufacture. Public redistribution/use rights are not established by downloading it.

## Acquired native design archive

On 2026-10-10 the user completed the official NXP download into Downloads and confirmed completion. The archive was ingested with a passing ZIP CRC check.

- Archive: `FRDM-MCXN236-DESIGN-FILES.zip`
- Bytes: 21,418,523
- SHA-256: `e1ee1755a9cc2c1efa27ceb25cc459d7e55f0626f4ee3037199183ee45482ff2`
- Ingestion timestamp: 2026-10-09T20:43:53.598501+00:00 (2026-10-10 in Asia/Calcutta)
- `archive-inventory.json` records all eight extracted files, byte sizes, SHA-256 hashes and archive CRC values.

The eight files under `original-design-files/Design Files` are:

1. `LAY-90828_C.brd`
2. `SCH-90828_C.DSN`
3. `SCH-90828_C.opj`
4. `SCH-90828_C.BOM`
5. `SCH-90828_C.BOM.xlsx`
6. `allegro/pstchip.dat`
7. `allegro/pstxnet.dat`
8. `allegro/pstxprt.dat`

There are no separately exported Gerber, drill, STEP or GLB files in these eight members. The manufacturer's broader download-page description does not change the observed archive inventory. Native CAD has not been engineering-validated in the authoring tools, and the physical specimen's PCB revision remains unconfirmed.

## Verified structured extraction

`structured-rev-c` preserves 96 source BOM items expanded to 391 reference designators. Text BOM, XLSX, pstxprt and pstxnet reference sets agree. The extraction retains 92 primitive definitions, 296 electrical nets with 1,243 pin records, and a separate literal NC group with 87 pin records; NC pins must not be treated as electrically connected.

The BOM explicitly marks 63 references DNP, and 37 references have NO PART TO ORDER descriptions. The 391 designators are not a fitted-part or procurement count. Source rows, typed fields, native properties and hashes are retained; no manufacturer-alternative list is inferred. See `structured-rev-c/README.md` and `extraction-report.json` for the verified comparisons and interpretation limits.

## Schematic search and photo link

The derived `schematic-reference-index.json` contains 629 reference-like text occurrences and 410 distinct normalized strings with PDF page/text coordinates. BGA pin names, aliases, repeated symbols and change-history entries can resemble component references. These are searchable text counts, not BOM quantities or a verified component inventory.

379 native references have schematic-text candidates; text matching does not establish symbol identity. SW3 joins to source BOM item 79, worksheet row 93 (A93:K93), source MPN `434123025826`, and the ISP pushbutton on schematic page 10 with value `SW SPST NO`. Its photograph link remains model-level; exact installed-part identity and specimen revision are unresolved. See `README_INDEX.md` and `structured-rev-c/README.md` for source-coordinate and join scope.

## Acquisition history

The web retrieval tool redirected both official download routes to NXP login. The actual in-app browser instead reached NXP's pre-download page without a login prompt. That page explicitly describes the ZIP as Gerbers, Layout, BOM and Schematics and exposed this download link:

https://cache.nxp.com/secured/assets/downloads/en/design-support/FRDM-MCXN236-DESIGN-FILES.zip?fileExt=.zip

An earlier HTTP request to that observed link returned a CDN error, and the browser link download timed out after 120 seconds. No completed archive was found in Downloads or the workspace.

### Earlier failed 2026-10-10 retrieval

The official design-file download page was observed again. The browser download timed out after 45 seconds. A curl request to the observed official cache URL above returned HTTP 403 and zero bytes. That attempt produced no usable FRDM-MCXN236 design ZIP.

The user's later successful official download, verified eight-file ingestion and completed structured extraction supersede this access failure. Remaining work is native CAD review, missing manufacturing/3D exports, and matching the physical specimen's revision and photo geometry. MCXN947 files remain a different-board reference and must not be substituted.
