# NXP planar review proposals

This catalog projects 354 Rev C source mesh footprints onto the original upright
NXP photograph using four reviewed mounting-hole centers, not board corners.
Only 255 top-side candidates are drawn after suppressing documented revision
conflicts, bottom-side geometry and source-BOM DNP references. All records are
retained with reasons; source DNP does not prove the B-marked specimen is unpopulated.

These are **review proposals**, not component masks or training labels. Convex
hulls include leads, hidden surfaces and empty regions. Component height/parallax,
camera distortion and B/C placement differences are unverified. Near-zero residual
on four fitted anchors is not an independent camera-accuracy measurement.

The source GLB is preserved as `frdm-mcxn236-rev-c-source-candidate.glb` under
the NXP `ar-reference` directory. This improves final-package completeness but
does not finalize the model for the B-marked specimen. Rebuilding requires actual
Git LFS payloads plus the shared NumPy/Pillow rendering dependencies.

```powershell
python data/ar-alignment/nxp-planar-review/project.py
```

All production, ground-truth and training-export flags remain disabled. Review
each boundary against physical visible bodies before promotion, and separately
resolve source revision, fitted identities, metric camera calibration and flip tests.
