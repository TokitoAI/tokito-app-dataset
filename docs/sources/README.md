# Tokito board dataset

Collection for the iQOO hackathon finale, with Afnan and Navaneeth. The final product aim will be supplied later. Repository work has not started.

Start with COVERAGE.md for current coverage and gaps. PROJECT_CONTEXT.md preserves the team context and acquisition history. PHOTO_CAPTURE.md describes the planned phone-photo collection.

## Files for data work

- asset-catalog.json and file-inventory.csv: saved assets, classifications, sizes and SHA-256 hashes. Partial downloads and superseded extractions are excluded.
- manifest.csv: original acquisition results and URLs, including failed attempts. Use status=downloaded entries when checking source acquisitions.
- dataset-audit.json: original-source checksums, photo checksums and verified GLB source chains. A passing checksum audit does not prove a physical-board match or engineering correctness.
- LICENSE_NOTES.md: observed source terms and locations of retained evidence.
- Each board folder contains original photographs, native source files and labeled structured/derived data where available.
- auxiliary/DeepPCB: verified 1500-pair defect dataset with original splits and samples.jsonl. This data does not label components on our boards.
- auxiliary/PCBVision: source metadata and archive-member inventory. Image/label acquisition remains incomplete.

## Board matching

The Pi photo identifies Model 3B V1.2 and the Ultimaker photo identifies Ultimainboard 2.1.4. The NXP suffix/revision and ESP board manufacturers/revisions require confirmation. Official NodeMCU reference files differ from the photographed wide CH340-style clone. The ESP32 and Pi community models are comparison references until geometry is checked.

Missing files and remaining acquisition routes are recorded in REMAINING_SOURCE_LEADS.md. Keep original images intact. New phone photos and physical-board revision confirmations can be added without changing source design labels.
