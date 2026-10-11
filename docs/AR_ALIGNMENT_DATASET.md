# Dataset for calibrated per-component AR

The dataset must connect a physical board and a visible component instance to
its particular 3D mesh. Board recognition alone cannot make a component
highlight correctly. The common identity is a revision-bound reference such as
`nxp-frdm-mcxn236:C:U1`, while each photograph has its own instance annotation.
Physical specimen IDs preserve that same part across views and sessions.

`data/ar-alignment/manifest.json` joins the existing five-family hierarchy,
reviewed phone references, visible-body polygons, metric calibration landmarks,
physical pin/contact evidence and the released NXP component selectors. Its
input digests make the joins reproducible. Source-only electrical pins retain
their missing image geometry; the 60 new ESP aliases still need reviewed
connector parents. They cannot become numeric pin identities by proximity.

## Geometry and identity

- Image coordinates refer to the EXIF-upright original, never a resized preview.
- A box, a visible-body mask and a CAD footprint are different geometries. A box
  is not promoted to a segmentation polygon.
- Each calibrated keypoint pairs an explicit source ID with its image location
  and metric location. NXP `BH1, BH4, BH2, BH3` are mounting-hole centers in that
  order, not unnamed top-left/right outline corners.
- The GLB is metre/Y-up. Asset X/Z represent board X/Y and asset Y is height.
  Top, underside and side views keep this one frame; flipping does not reset
  the origin, replace component IDs or mirror the source geometry.
- A component reference resolves to exactly one non-empty `ref:<designator>`
  subtree. Shared nodes/meshes are rejected because they would highlight other
  components along with the selected one.
- The photographed NXP revision is unverified. Its mesh joins are source
  candidates; the design BOM order code is not a confirmed fitted part number.

The [Ultimaker photo-to-mesh crosswalk](../data/ar-alignment/ultimaker-photo-mesh-crosswalk.json)
now joins 90 of 93 reviewed photographed body instances to distinct
`ref:<designator>` selectors in the source GLB candidate. All 90 selectors
resolve to non-empty, exclusive subtrees (111 meshes total). Two header-strip
instances have conflicting source identity and C106 remains unresolved, so
those three are excluded. These joins identify selectable candidates only:
physical board revision, fitted part identity, metric photo-to-GLB pose and
continuous flip have not been verified, so no link is release eligible.

The [Ultimaker planar anchor candidates](../data/ar-alignment/ultimaker-planar-anchor-candidates.json)
pair the same four native SP1–SP4 spacer-hole centers with both an iQOO
component-face and solder-face photo. The native outline projected from each
four-point homography visually follows the photographed board edge; the
[review overlay](../previews/ultimaker-planar-anchor-candidates.jpg) shows the
correspondences. This is a fixed source-frame candidate for a two-face AR
handoff. Four points fit a homography exactly and do not independently prove
camera intrinsics, 3D pose, specimen equivalence or a continuous flip.

As a separate same-photo check, the projected native U1 footprint center lands
inside the visible U1 package, 59.3 original-image pixels from its thresholded
body center. This supports the proposed planar correspondence but is not a
camera-pose accuracy claim or an independent capture evaluation.

The released NXP manifest uses board-outline corner landmarks. The reviewed
phone photo instead uses mounting holes. The alignment index records
`asset_anchor_override_required` and the paired hole positions; a pose model
trained on those holes must use those same positions at runtime. Combining hole
detections with the old outline positions changes scale and alignment.

## Multi-view and flip coverage

The minimum capture set per physical specimen contains six slots: top,
underside and oblique views from the four board-plane directions. Keep the same
specimen ID, source frame and reference IDs throughout. Additional angles,
distances, lighting, occlusion and independent specimens remain necessary for
evaluation; six stills are a coverage minimum, not proof of tracking quality.

`annotations/multiview-capture-review.json` currently assigns one reviewed
top-side full-board image per family. No specimen has a reviewed complete
six-view real-camera set or a verified rotate-and-flip sequence. The original
and supplementary contact sheets show component-side captures. The connected
phone inventory was checked; newer missing-view captures were not present.

At the next phone test, record a slow continuous rotation and a physical flip
with the board fully visible. Retain original camera intrinsics/distortion,
resolution/crop, lens identity and timestamps. If document mode applies
perspective correction, preserve that transform or use an uncorrected camera
capture for metric calibration. Annotate keyframes with board surface, metric
landmarks, component visibility/occlusion and one rigid board-to-camera pose.
All views, crops and frames of one specimen/session share a split. A rotated
front photo cannot stand in for a real underside capture.

The runtime must update the 3D board pose continuously, clear stale geometry,
retain the selected component identity across reacquisition and respect surface
occlusion. Dataset landmarks and masks support that behavior; they do not
implement or verify the tracker by themselves.

## Photo-to-source identity review

The three reviewed NXP crystal-body instances beside the MCU are **Y3**, not
Y1. The original images show the adjacent Y3 silkscreen; source Y1 is the
separate crystal near the USB circuitry. The annotations retain the correction
evidence and the generated crosswalk preserves it. CAD geometry was not moved
to fit the incorrect label. The regression tests check the three photo-local
identities, their parent-instance links and the `ref:Y3` source selectors.

A named-hole planar diagnostic against one original photo found 26 of 38
projected component centers inside reviewed body polygons after this correction,
with a 13.87-pixel median center offset. This is not independent pose validation:
the homography was fitted to four anchors in that same photo, package height can
affect projection, and small-body annotation outliers remain. Neither these
numbers nor the identity correction grants production AR or training eligibility.

## Current artifacts and commands

The NXP source registry has 391 references, of which 354 have separately
selectable bodies. The GLB audit checks all 354 selectors against actual cached
geometry. The real-image index has 243 partial part boxes, one reviewed U1 body
polygon, 11 candidate image-to-mesh joins, four metric anchor pairs and 165
parented photo-located contacts. BGA contacts under U1 are hidden and receive
no visible-pin labels. Complete real component segmentation and independent
camera evaluation remain unfinished for all five families.

The source registry also joins the acquired Rev C BOM's population flags. The
full-design GLB models 63 references explicitly marked DNP. Default synthetic
views suppress those 63 bodies, retaining their IDs with zero visible pixels;
291 source-populated components remain. This prevents an unfitted source
connector from creating a positive mask or occluding a neighboring part. L10
was hidden in every full-design view and becomes visible after source DNP
suppression. The photographed specimen's fitted population is still a separate
review question.

Download the source asset to an ignored directory, keeping the model out of Git:

```powershell
gh release download v0.1-frdm-mcxn236-3d-asset --repo TokitoAI/tokito-physical-runtime --pattern frdm_mcxn236_ar_visible.glb --dir work/ar-source-release
python scripts/build_ar_alignment_dataset.py --glb work/ar-source-release/frdm_mcxn236_ar_visible.glb
python scripts/build_ar_alignment_dataset.py --glb work/ar-source-release/frdm_mcxn236_ar_visible.glb --check
python scripts/validate_ar_alignment.py
python -m unittest discover -s tests -v
```

`scripts/render_ar_multiview.py` renders top, underside and four oblique CAD
views with known camera intrinsics/rigid transforms, source-named anchors and
depth-tested uint16 component masks. Each mask ID refers to the same source
component in every view; fully hidden components have zero visible pixels.
This is synthetic geometry supervision. Approximate and placeholder packages
keep their model-quality tags, and CAD appearance is not phone appearance.

```powershell
pip install -r requirements-ar-tools.txt
python scripts/render_ar_multiview.py --glb work/ar-source-release/frdm_mcxn236_ar_visible.glb --output work/ar-multiview-nxp
python scripts/package_ar_multiview.py --rendered work/ar-multiview-nxp
```

The synthetic archive contains rendered RGB images, exact instance-ID masks and
camera/identity metadata. Raw masks preserve apertures, disconnected visible
fragments and occlusion. Training adapters must preserve that geometry or
explicitly record any polygon approximation; filling a bounding rectangle is
not a valid conversion. These generated views are not included in real-camera
accuracy, recall or flip-stability scores.

The [synthetic six-view archive](../data/ar-alignment/nxp-synthetic-six-view.zip)
and [provenance/coverage summary](../data/ar-alignment/synthetic-nxp-provenance.json)
retain the camera transforms and pixel labels. The [real U1 review](../previews/ar-u1-mask-review.jpg)
shows the manual package boundary and named source/photo anchors. Use
`--population all-source-bodies` only for a declared full-design geometry
conformance render; it is not the default BOM-populated assembly.
