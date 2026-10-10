# Diagnostic YOLO11m board detector

This release-ineligible experiment identifies the five reviewed board identities in
data/photo-model/yolo-boards/data.yaml. A 500-epoch ceiling stopped dynamically
at epoch 135 after 60 non-improving epochs; validation selected epoch 75.

best.pt is the selected training checkpoint. best.tflite is the float32 LiteRT
export used by the camera-only iQOO smoke app. See training-report.json for
hashes, metrics and limits.

The 11-image validation fold uses the same physical specimens as training and
contains no ESP32 image. These results measure fit to the current corpus and do
not establish accuracy on new boards. Exact part and pin names require board
registration plus a revision-matched BOM/PCB/netlist resolver; the detector does
not invent them.
