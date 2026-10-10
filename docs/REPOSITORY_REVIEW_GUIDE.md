# Repository layout and review order

The former integration PR #6 contained 33 mixed commits. Its content and the NXP
follow-up in #8 are preserved on `archive/pr6-and-nxp-review-preserved-20261010`.
Eight focused replacement branches reproduce the preserved file tree exactly
(214 changed files). Review navigation is the only additional content added after
that tree comparison. The archive and original branches are retained.

## Review and merge sequence

| Order | PR | Scope |
| --- | --- | --- |
| 1 | [#9](https://github.com/TokitoAI/tokito-app-dataset/pull/9) | Capture intake, reviewed labels, hierarchy and source checks |
| 2 | [#10](https://github.com/TokitoAI/tokito-app-dataset/pull/10) | Diagnostic model experiments and phone evidence |
| 3 | [#11](https://github.com/TokitoAI/tokito-app-dataset/pull/11) | Shared AR source joins, synthetic views and tooling |
| 4 | [#12](https://github.com/TokitoAI/tokito-app-dataset/pull/12) | ESP-12E video bodies, header/module contacts and spacing |
| 5 | [#13](https://github.com/TokitoAI/tokito-app-dataset/pull/13) | Ultimaker source geometry and identity audit |
| 6 | [#14](https://github.com/TokitoAI/tokito-app-dataset/pull/14) | Provisional ESP32 substrate tooling |
| 7 | [#15](https://github.com/TokitoAI/tokito-app-dataset/pull/15) | NXP video review and B/C revision constraints |
| 8 | [#16](https://github.com/TokitoAI/tokito-app-dataset/pull/16) | Connected validation and final ZIP delivery tooling |

The PRs are stacked: each compares against the preceding branch, so its diff
contains only that scope. Merge in order, preserving preceding commit ancestry;
retarget the next PR to `main` after its dependency merges. Avoid squash/rebase
merging an early dependency without rebasing its descendants, which would make
already reviewed parent content appear again. No merge to `main` is performed
as part of this organization change.

PR #7's Ultimaker source-provenance sample and PR #4's earlier experimental model
publication are separate existing work; they are not silently overwritten.
Compare overlapping files before integrating those branches. Antigravity scratch
directories are inputs under review, not the authoritative merged dataset.

## Where files belong

| Directory | Contents |
| --- | --- |
| `annotations/` | Reviewed image labels and hierarchy/source links |
| `data/photo-model/` | Original photo groups, YOLO board data and diagnostic runs |
| `data/phone-captures/`, `data/video-captures/` | Captures, checksums, grouped keyframes and review evidence |
| `data/board-sources/<board>/` | Native sources, BOM, schematic, PCB/Gerber and geometry provenance |
| `data/ar-alignment/` | Image-instance joins, semantic/metric constraints and coverage limits |
| `scripts/`, `tests/` | Reproducible preparation, validators and regression checks |
| `docs/`, `previews/` | Review instructions, readiness evidence and visual overlays |
| `work/` | Ignored local scratch outputs; not part of the final shareable dataset |

Large payloads use Git LFS. The final ZIP exporter requires actual downloaded
payloads rather than LFS pointers and includes per-file checksums. Account tokens,
Git internals and local scratch state do not belong in dataset delivery.

## Readiness

Repository organization and passing metadata checks are not production model
readiness. None of the four active boards is yet proven complete end to end.
NXP final geometry must resolve the B-marked specimen versus C source; full labels,
medium-model training/evaluation and real phone calibration/flip/highlight tests
remain required before final delivery. Raspberry Pi work is deferred; its data is
retained. See [goal](DATASET_GOAL.md), [NXP revision review](NXP_REVISION_COMPATIBILITY.md)
and [final delivery](FINAL_DATASET_DELIVERY.md).
