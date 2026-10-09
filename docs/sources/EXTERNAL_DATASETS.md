# External dataset leads

These are auxiliary PCB-vision resources, not board-specific ground truth for our five physical specimens. Downloads and license audits are pending.

- DeepPCB: https://github.com/tangsanli5201/DeepPCB . Author-maintained copper-defect dataset of 1,500 aligned image pairs, six defect classes. Useful for bare-PCB defect research, not assembled-board component/refdes recognition.
- PCB-Vision: https://github.com/hifexplo/PCBVision . Author resource for RGB/hyperspectral assembled-PCB research. Paper: https://arxiv.org/abs/2401.06528 . Candidate for component segmentation transfer; verify data access, labels and license before use.
- ESP32 community clone: https://github.com/BrijModi/ESP32-Dev-Kit-Clone . Custom 30-pin KiCad design with BOM and STEP advertised. Treat all files as a different reference board until physical geometry and component populations are checked.

Never mix auxiliary training images into evaluation sets of our photographed boards without tracking their origins. Exact schematic-to-photo connectivity labels still require a matched board revision.

DeepPCB acquisition completed: full original archive extracted and CRC validated. Official split samples indexed in auxiliary/DeepPCB/samples.jsonl; 1500 pairs (1000 trainval, 500 test) and 10013 validated boxes. MIT LICENSE preserved. Earlier download-pending statement is superseded for DeepPCB; PCB-Vision remains pending.
