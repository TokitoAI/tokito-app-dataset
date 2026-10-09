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

## Archive acquisition status

The web retrieval tool redirected both official download routes to NXP login. The actual in-app browser instead reached NXP's pre-download page without a login prompt. That page explicitly describes the ZIP as Gerbers, Layout, BOM and Schematics and exposed this download link:

https://cache.nxp.com/secured/assets/downloads/en/design-support/FRDM-MCXN236-DESIGN-FILES.zip?fileExt=.zip

A normal HTTP request to that observed link returned a CDN error. Browser link download timed out after 120 seconds. No completed archive was found in Downloads or the workspace. No ZIP is claimed collected, and no retry/download process is confirmed live. The remaining action is completing the official browser download (or user login if prompted) and validating its ZIP before extraction. Do not substitute MCXN947 design files for this board.
