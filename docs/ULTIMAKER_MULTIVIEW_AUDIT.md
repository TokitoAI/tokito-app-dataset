# Ultimaker Multi-View Video & Photo Capture Audit

**Specimen:** Ultimaker Ultimainboard v2.1.4  
**Date of Review:** 2026-10-10  
**Capture Device:** iQOO I2501 (50 MP main sensor, 1080p video recording)  
**Evaluator:** Tokito Dataset & AR Toolchain  

---

## 1. Overview of Multi-View Visual Inventory

The Ultimaker Ultimainboard 2.1.4 visual corpus comprises high-resolution DSLR/phone stills and supplementary continuous video inspection sweeps:

| Intake Session | Media Type | File Count / Duration | Primary Target Region |
|---|---|---|---|
| `2026-10-09` | High-Res JPEG (3072×4096) | 18 images (9 pairs) | Multi-angle board coverage, orthogonal and 45° oblique |
| `2026-10-10` | High-Res JPEG (3072×4080) | 6 images (3 pairs) | Full board context (`092241`), macro header details (`092241_1`, `092244_1`, `092247_1`) |
| `2026-10-10:1359` | MP4 Video (1080×1920, 30fps) | 55.7 seconds (1,672 frames) | Continuous orbital sweep across top-side components |

---

## 2. Phone Video Trajectory & Quality Assessment

Continuous video recording `video_20261010_135936.mp4` captures the physical board resting on an inspection workbench:

- **Orbital Trajectory:**
  1. **Phase 1 (Frames 0–350):** Approach from the bottom-left corner over the high-current power terminals (`J24`, `J21`, `J8`, `J9`) and switching regulator coil `L1`.
  2. **Phase 2 (Frames 350–850):** Close-up translation over stepper motor drivers (`E1`, `E2`, `Z`, `Y`, `X`) and heat dissipation thermal zones, showing QFN IC markings and current adjust trimmers.
  3. **Phase 3 (Frames 850–1250):** Overhead hold above the central logic core: Atmel ATmega2560 MCU (`U1`), crystal oscillator (`Y1`), and adjacent programming/expansion headers (`J1` ICSP1, `J23` EXT/IO, `J22` SERIAL, `J20` FAN).
  4. **Phase 4 (Frames 1250–1672):** Sweep toward the top-right USB interface: FTDI FT232RL (`U2`), USB Type-B jack (`J19`), and auxiliary ICSP2 (`J2`).
- **Optical Conditions & Motion:**
  - **Illumination:** Neutral white overhead studio/lab lighting with mild diffuse reflections.
  - **Focus & Exposure:** Auto-focus locked reliably during holding phases; minimal shutter rolling distortion.
  - **Resolution:** Full HD 1080×1920 portrait orientation, sufficient for resolving 0603 passive packages and silkscreen pin triangles.

---

## 3. Coverage Analysis & Blindspots

| Board Sub-assembly | Multi-View Photo Visibility | Video Sweep Visibility | AR Registration Suitability |
|---|---|---|---|
| **Board Substrate & Corners** | Complete (all 4 corners clear) | Complete | High — four 3.2mm mounting holes provide stable metric anchors |
| **ATmega2560 MCU (`U1`)** | Clear (pin 1 dot readable) | Clear overhead view | High — 100-pin TQFP provides 4 distinct corner features |
| **FT232RL USB Interface (`U2`)** | Clear | Clear | High — SSOP-28 package geometry |
| **Stepper Drivers (`U6`–`U10`)** | Good | High resolution | High — repeated layout with distinct reference designators |
| **Headers (`J22`, `J23`, `J1`, `J2`)** | Excellent macro resolution | Excellent | Very High — pin-1 triangles clearly visible in multiple frames |
| **Power Screw Terminals** | Clear | Clear | High — 3D protruding geometry provides strong depth cues |
| **Underside SMD Passives** | Not Photographed | Not Documented | Out of Scope — bottom-side SMD passives require separate bottom capture |

---

## 4. Keyframe Selection for Validation

Representative video frames exhibiting optimal sharpness and distinct viewing angles were extracted for cross-validation against the static CAD model:

1. `video_frame_001`: Low-angle oblique view of power stage and Extruder heater terminals.
2. `video_frame_002`: Close-up top view of `E1` / `E2` stepper drivers and `FAN 19-24V` (`J20`) connector.
3. `video_frame_003`: Orthogonal inspection view of `ICSP1` (`J1`), `EXT/IO` (`J23`), and `SERIAL` (`J22`).
4. `video_frame_004`: Wide contextual view showing entire board substrate and mounting holes.
