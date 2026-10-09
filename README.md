# Tokito dataset review preview

This PR publishes a small reviewable subset while the full photo/CAD Git LFS upload continues. It contains board annotations, source-match metadata, partial component seeds, and contact-sheet previews. Full-resolution images and native CAD binaries are not in this preview branch yet.

80 photo files comprise47 captures and33 cropped variants. Board families: ESP32, ESP8266, Ultimainboard2.1.4, NXP FRDM-MCXN236, and Pi3B V1.2. The clearer NXP silkscreen corrects the earlier947 assumption. Do not link947 BOM data as exact236 ground truth.

![Board previews1](previews/boards-01.jpg)
![Board previews2](previews/boards-02.jpg)
![Board previews3](previews/boards-03.jpg)

`annotations/board-annotations.json` records reviewed board boxes and capture groups. Component seeds total107 major visible objects across five photos; they remain partial and are not complete component-training ground truth. `source-bundles.json` records compatibility limits.

The experimental board detector was trained locally. Its highest-confidence family matched64 of80 supplied files in the known-photo demo. That is not an independent test. A crop classifier is being investigated to improve family disambiguation. Exact part/BOM/refdes linkage remains unresolved.

Review here and merge only through the PR workflow. The full corpus and model results will be separate PRs. Large source file licenses differ; source/license notes are included.
