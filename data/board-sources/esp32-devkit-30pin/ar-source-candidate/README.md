# ESP32 package geometry candidate

This improves the previous component-box model with a nominal drilled substrate
(four mounting and thirty header openings), a hollow micro-USB shell, tactile
switch actuators, QFN contacts, SOT-223 regulator tab/leads and RF module shield/PCB.
All fifteen original `ref:` selectors retain separate meshes. The preview and
the reviewed 7-second source video frame were inspected.

The metric dimensions and placements remain unverified nominal assumptions.
The pictured module shield reads **ESP-32**; exact WROOM/module identity is not
confirmed. Header tops do not show protruding pins, but underside population is
unknown. Do not claim absent underside pins or use nominal openings as calibrated
physical landmarks. Small-part identity and source reference correspondence are
not verified. Release and calibration activation remain disabled.

`input/` preserves the Antigravity provisional map and old box GLB for reproducible
selector continuity; statements in that legacy input about exact geometry or
physical measurement have not been verified. The new node extras/provenance
take precedence for readiness.

Rebuild in this directory with NumPy, SciPy, Pillow installed:

```powershell
python build_candidate.py
python validate_candidate.py
```

Validation checks selector/mesh uniqueness and absence of substrate surface at
all thirty-four nominal hole centers. These are structural checks, not camera
accuracy or a proof that dimensions match the physical specimen. The source video
is preserved in `data/video-captures/2026-10-10/video_20261010_132302.mp4`.
