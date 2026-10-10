# Experimental board-family pipeline

Two trained Ultralytics models: YOLOv8n detection followed by YOLOv8n-cls on the selected detected crop. CPU environment: Python3.13, PyTorch2.14.1, Ultralytics8.4.174. SHA-256 hashes and artifact sizes are in manifest.json.

Supported classes: ESP32, ESP8266, Ultimainboard2.1.4, NXP FRDM-MCXN236, Pi3B. These models do not detect individual components, recognize exact part numbers, infer nets, or create Gerber files. Source-bundle outputs are candidate document links with explicit compatibility limits.

## Measured observations

| Check | Result | Scope |
|---|---|---|
| Detector diagnostic validation | precision0.843, recall0.905, mAP50 0.995, mAP50-95 0.853 |11 images, four classes, one specimen/session; no ESP32 held-out metric |
| Detector top-confidence family on supplied files |64/80 |train/val/cropped files combined; known-photo demo |
| Classifier on reviewed manual board crops |80/80;12/12 diagnostic validation |manual crops; one specimen/session; not independent test |
| Detector crop plus classifier, ungated |78/80 class and box IoU50 |two elongated background false positives retained in the report |
| Front-view aspect gate plus classifier |80/80 class and box IoU50 |gate tuned after known-photo error review; not independent accuracy |

The gate requires the detected box's shorter/longer side ratio to be at least0.35. It rejects elongated background regions in the supplied front-view images. Unusual viewing angles, thin visible portions, unrelated boards, multiple boards and new physical specimens have not been validated. Classifier confidence is not proof that an unknown object belongs to a supported family.

Detector training used62 images with11 validation originals and7 validation crop variants withheld. The detector ran57 of60 requested continuation epochs with early stopping. The classifier ran40 epochs with60 training files,12 validation originals and8 withheld crop variants. Its additional ESP32 validation group is still from the same pose/session and was part of the detector's training corpus, so the combined pipeline has no independent test split. Original/crop groups do not cross each model's folds.

## Run

Install requirements-training.txt in a virtual environment and fetch Git LFS objects. From the repository root:

```text
python scripts/predict_boards.py path/to/photos --output predictions.json
```

The CLI returns one candidate board per photo, its box, confidences and a candidate source bundle. Missing candidates and exact component identities remain unresolved. Further component annotations and independent specimen/session validation are required before claiming a model that labels every part.
