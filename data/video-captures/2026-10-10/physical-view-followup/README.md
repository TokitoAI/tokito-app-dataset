# Physical-view follow-up capture review

Four original iQOO videos retrieved from DCIM/Camera on 2026-10-10 are preserved
by board identity and SHA-256 in `manifest.json`. The association is based on
visible board silkscreen/module markings in sampled frames. Each source is
1920x1080 HEVC with a -90 degree display matrix; decoded review frames are
upright after display-matrix autorotation.

Review sampling used frames at one-second intervals across each clip. The
NXP contact sheets cover the full 50-second recording. The visible material shows the
component-bearing face and close pans. It does not establish any full underside,
four oblique side views, or a continuous rotate-and-flip sequence. Views are
unregistered and do not provide metric pose, independent calibration, or
training labels. In particular, the NXP clip is a different session and does
not replace the previously reviewed underside stills.

| Board | Source | Duration | Review |
|---|---|---:|---|
| Ultimainboard 2.1.4 | `ultimaker/video_20261010_202209.mp4` | 27.595 s | component face, overview and pans |
| ESP-12E clone | `esp12e/video_20261010_202254.mp4` | 12.798 s | component face, overview and pans |
| FRDM-MCXN236 | `nxp/video_20261010_202323.mp4` | 50.048 s | component face, overview and pans; tail reviewed |
| ESP32 30-pin clone | `esp32/video_20261010_202431.mp4` | 21.896 s | component face, overview and pans |

All recordings and keyframes remain outside training pending independent
identity, boundary and coverage review.
