# PCB-Vision RGB acquisition

The complete RGB subset of the official PCB-Vision release is now acquired and verified: **53 RGB photographs, 53 General segmentation masks, and 53 Monoseg segmentation masks**. These are external component-segmentation references. They do not establish the model, BOM reference designator, or pin identity of any photographed Tokito board.

Source and attribution: Arbash et al., *PCB-Vision: A Multiscene RGB-Hyperspectral Benchmark Dataset of Printed Circuit Boards*, Version 1, 2024, [DOI 10.14278/rodare.2704](https://doi.org/10.14278/rodare.2704). The [official code repository](https://github.com/hifexplo/PCBVision) links both [RODARE](https://rodare.hzdr.de/record/2704) and [Zenodo](https://zenodo.org/records/10617721). Dataset files are licensed under CC BY 4.0; the code repository's Apache license is a separate license.

The source ZIP is 11,392,398,155 bytes and also contains hyperspectral data. Its existing central-directory inventory showed every RGB image and mask within the archive's first 20.53 MB. The acquisition requested `bytes=0-20525036` from the official Zenodo content endpoint. Zenodo returned HTTP 206 with exactly `Content-Range: bytes 0-20525036/11392398155`. The 20,525,037-byte prefix was retained locally, SHA-256 `9edfbe822e7fdf20e5ce9320cf7644564c7b43a74d792d8b22966f3ed6c1ce9d`.

The extractor validates each selected local ZIP header and member name, decompresses each member, compares its uncompressed length and CRC32 with the central-directory inventory, and records a SHA-256 for each extracted file. All 159 images decode successfully. All 106 mask/image pairs have matching IDs and dimensions. Photos are RGB; masks are grayscale with pixel values drawn only from `{0, 1, 2, 3}`. The official class mapping is 0 = others, 1 = IC, 2 = capacitors, and 3 = connectors. General and Monoseg are two annotation variants for the same 53 images; they must not be counted as independent photographs or split across training and validation by mask variant.

The repository includes [rgb-subset.zip](../data/external/PCBVision/rgb-subset.zip), a 20,517,044-byte package containing all 159 verified image/mask files and `ATTRIBUTION_AND_LICENSE.txt`. The attribution names the original creators, links the DOI and official records, identifies CC BY 4.0, and states that image bytes are unchanged. The archive contains no HSI data or source ZIP prefix. Existing `*.zip` Git LFS tracking applies, so teammates must fetch its LFS object before extraction:

```powershell
git lfs pull --include='data/external/PCBVision/rgb-subset.zip'
Expand-Archive -LiteralPath data/external/PCBVision/rgb-subset.zip -DestinationPath work/pcbvision-rgb
```

The packaged ZIP has SHA-256 `4220af2016b5e315abb47b4d443bdda454c7ffa3c408ab6f827352932a072954`. ZIP CRC testing passed for all 160 members, and every image/mask member matches its acquired SHA-256, byte count, and source-member CRC32. [rgb-subset-package.json](../data/external/PCBVision/rgb-subset-package.json) records these checks and the archive manifest. Per-file acquisition hashes, dimensions, and paired names are in [rgb-acquisition-verified.json](../data/external/PCBVision/rgb-acquisition-verified.json). The original extracted workspace copies remain at:

```text
C:\Users\Acer\Documents\Codex\2026-10-09\in\outputs\board-dataset\auxiliary\PCBVision\rgb-subset\PCBDataset\RGB
```

The hyperspectral subset was not downloaded. The published MD5 `caeee8bafb7857e9bef3479d5ab3f9b4` applies to the entire upstream archive and was **not** verified against this prefix. Member CRC validation and the recorded prefix/file SHA-256 hashes describe the acquired RGB subset accurately; they do not claim full-archive verification.

To acquire or extract the same prefix, run [acquire_pcbvision_rgb_prefix.py](../scripts/acquire_pcbvision_rgb_prefix.py) using Python with Pillow. To reverify all existing extracted files without network access:

```powershell
python scripts/acquire_pcbvision_rgb_prefix.py --output 'C:\Users\Acer\Documents\Codex\2026-10-09\in\outputs\board-dataset\auxiliary\PCBVision' --verify-only
```

Acquisition and a subsequent independent pass over the retained prefix and extracted files both passed. Component detection training still requires an explicit choice of segmentation task or reviewed conversion to detection boxes. This acquisition does not create YOLO pin annotations.
