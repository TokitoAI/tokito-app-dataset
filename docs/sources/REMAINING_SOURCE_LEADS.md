# Remaining source leads

Updated 2026-10-10. Source files must retain their actual board and revision identity. The photographed NXP board is FRDM-MCXN236; MCXN947 is an incompatible reference.

## FRDM-MCXN236 manufacturing exports and 3D

The correct 13-page SPF-90828 Rev C schematic is preserved in `nxp-frdm-mcxn236`. It was copied from Downloads, with its earlier download provenance unknown; its content identifies SCH-90828 / SPF-90828, Rev C, dated 2024-03-25. The physical specimen's PCB revision remains unconfirmed.

Official product page: https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-MCXN236

Official design-file route: https://www.nxp.com/webapp/Download?colCode=FRDM-MCXN236-DESIGN-FILES

The official page describes a Rev C ZIP as Gerbers, layout, BOM and schematics. Its observed cache link is:

https://cache.nxp.com/secured/assets/downloads/en/design-support/FRDM-MCXN236-DESIGN-FILES.zip?fileExt=.zip

The user completed the official download on 2026-10-10. The 21,418,523-byte ZIP passed CRC verification and is preserved with SHA-256 `e1ee1755a9cc2c1efa27ceb25cc459d7e55f0626f4ee3037199183ee45482ff2`. Its eight actual files are LAY-90828_C.brd, SCH-90828_C.DSN/.opj/.BOM/.BOM.xlsx, and allegro/pstchip.dat/pstxnet.dat/pstxprt.dat. See `archive-inventory.json` for individual hashes. Earlier browser timeouts and curl HTTP 403/zero-byte responses are retained in PROVENANCE.md as history.

The acquired archive has no separate Gerber or drill exports. Obtain manufacturer exports or produce them with a compatible CAD tool and review them against the native source. Structured extraction is complete and cross-source reference comparisons pass; see `structured-rev-c/README.md` and `extraction-report.json`. Its 96 BOM items / 391 designators include DNP and NO PART TO ORDER entries and do not establish the photographed population. The CAD files have not been engineering-validated, and the specimen's physical PCB revision remains unconfirmed.

The archive also contains no STEP or GLB, and a complete MCXN236 populated-board model has not been located. Obtain a model for this board or export from the acquired native layout using compatible tools, then check the specimen/revision and geometry. An MCXN947 enclosure model does not fill this gap.

## MCXN947 reference only

The already collected MCXN947 Rev C design archive includes Allegro BRD, OrCAD DSN, BOM, manufacturing files and schematic/fabrication PDFs. It has no complete board STEP/GLB. Preserved community STEP files are enclosure geometry. These records remain useful as separately identified reference material and must not populate MCXN236 labels.

## ESP8266 photographed wide CH340-style clone

A paid community STEP listing exists at https://craftedtechengineering.com/product.html?id=3d-cad-model-lolin-nodemcu-esp8266-v3-development-board-ch340g-wider-base-standard-step-file . Listing price observed 2026-10-09: PHP 175. It has not been purchased, downloaded or verified. The listing claims a wide-base LoLin V3 / CH340G model; actual clone dimensions/revision and model fidelity still need confirmation.

Free library source https://github.com/Jefferson-Lopes/kicad-libs lists NodeMCU LoLin without a 3D shape. Its NodeMCU v1 models are a different reference variant. No complete, exact photographed-clone STEP model has been verified.

## Other manufacturing and part sources

Exact-revision Ultimaker Gerber exports and exact ESP32 clone manufacturing files remain unverified. Native Ultimaker Altium PCB and ESP32 community-reference KiCad PCB are preserved, but exports need compatible CAD tools and source-layout review. Different revisions must retain their actual identities.

The Raspberry Pi 3B V1.2 reduced schematic and mechanical documents do not provide a complete procurement BOM, native PCB or Gerbers. Those exact sources remain missing. The community STEP/GLB is a geometry reference pending physical-board comparison.

## PCB-Vision

Official repository https://github.com/hifexplo/PCBVision links Zenodo record 10617721 and Rodare record 2704. Metadata, licensing and remote member inventory are preserved. Earlier file-data access stalled across the tested endpoints; no RGB image/label acquisition is complete. A working source download or an existing complete local archive would enable acquisition and image/mask validation.

## Photo and part-label work

The 80 phone files and reviewed board boxes are collected. The 233 major-component seed boxes remain partial. Additional independent specimens/sessions, board-back photos, full visible-component review and photo-to-PCB registration are still needed for complete component labels and useful evaluation. Readable refdes may support a candidate source link while physical revision or installed-part identity remains unresolved.
