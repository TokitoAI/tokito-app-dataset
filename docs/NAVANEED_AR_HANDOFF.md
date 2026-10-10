# Working dataset handoff for Navaneed

Repository: https://github.com/TokitoAI/tokito-app-dataset

Working branch: `dataset/board-view-intake-and-guards` (PR #18). Fetch actual
Git LFS payloads after cloning; image, video, CAD and model pointer text is not
the source asset. This is a working reference corpus, not a final training release.

## Responsibilities

Navaneed owns camera calibration, augmentation, pose tracking and 3D alignment.
Codex owns YOLO annotation completion, export, training and evaluation. Active
boards are ESP32 30-pin DevKit, ESP-12E/NodeMCU, NXP FRDM-MCXN236 and
Ultimainboard 2.1.4. Raspberry Pi work is deferred.

Use the original phone photos under `data/phone-captures/2026-10-10`, earlier
photos under `data/photo-model/photos/raw`, and clips/keyframes under
`data/video-captures/2026-10-10`. Capture and physical-view reviews describe
what is present; a front pan does not establish underside or flip coverage.

`annotations/esp32-dense-component-review.json` contains 84 body masks across
three full-board photos: 15 corrected selected-package boundaries and 69 new
smaller-package boundaries. The same specimen and session appear in all three.
The 90 literal printed header aliases remain point metadata, without invented
chip-pin numbering. U2's CP2102 family is readable; other complete ordering
codes remain unresolved. The ESP-12E and Ultimainboard review files are also
partial. Keep incomplete labels out of ordinary YOLO loss.

## 3D and source evidence

Each board's files live under `data/board-sources`. Use populated/selectable
source candidates and their provenance where present. `generated-kicad`
board-only models do not contain component meshes. The NXP populated asset
`nxp-frdm-mcxn236/ar-reference/frdm-mcxn236-rev-c-source-candidate.glb` is the
5,250,580-byte source asset with SHA-256
`ba9db807d2141189facb33039f57861d99a460cf595dd71bf80eb5f9cbe1268c`.
It remains a Rev C source candidate; the photographed layout revision is not
confirmed by the SCH Rev C text. ESP source clones also require specimen checks.

The existing `data/ar-alignment/manifest.json` is a historical scaffold. Its
input digests may be stale after annotation updates; regenerate and validate
your own alignment artifacts against the current inputs. Preserve the metric
coordinate convention and semantic landmark IDs. Do not substitute outline
corners for mounting-hole centres or infer physical population from a BOM.

## Task to send

Build and verify camera calibration, board pose tracking and component-to-mesh
mapping for the four active boards. Highlight individual components and retain
alignment through rotations; verify underside/flip behaviour where the capture
evidence supports it. Report missing views explicitly. Confirm source variants
before joining components, and retain uncertain links as candidates. Work on
an AR-specific branch, keep YOLO annotation and training changes separate, and
submit focused PRs. Test on the connected iQOO and report measured alignment
error, supported views and unresolved items.

## Working ZIP

The working handoff ZIP includes source designs, originals, clips/keyframes,
annotations, reference geometry, relevant scripts/docs and a per-file hash
manifest. It excludes Git internals, build caches and trained detector binaries.
It is a snapshot for parallel development; final construction and YOLO model
readiness remain incomplete.
