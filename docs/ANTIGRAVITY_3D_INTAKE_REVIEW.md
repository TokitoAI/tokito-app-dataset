# Antigravity 3D intake review — 2026-10-10

Current work priority: ESP32, ESP-12E, Ultimainboard 2.1.4 and NXP. Raspberry Pi
work is deferred at the user's request; its existing data is retained. Finish
ESP32/Ultimaker model inspection before further NXP modeling. Today's target is
the four active boards, with readiness claims dependent on verification.

Located Antigravity projects:

- `C:/Users/Acer/.gemini/antigravity-ide/scratch/tokito-app-dataset-esp32`
- `C:/Users/Acer/.gemini/antigravity-ide/scratch/tokito-ultimaker-work`

Directly inspected the actual GLB node graphs and generation scripts, rather than
accepting the summary reports as verification. ESP32 GLB is 8,624 bytes with 15
distinct component meshes; Ultimaker GLB is 10,204 bytes with 19 distinct component
meshes. Both generators create rectangular component boxes. Neither inspected
asset has a PCB substrate mesh. Selectable node separation is useful, but does
not establish accurate package shape, board geometry or registered image overlap.

ESP32 metadata assigns mounting-hole dimensions/positions and calls them physical
measurements; the inspected generator hard-codes these values. A measurement
record or variant-matched mechanical drawing is required before calling those
metric anchors verified. The report's date-based train/validation division does
not establish unseen-specimen accuracy when photos share one physical specimen.
Low component/pin results cannot support production release.

Prioritized geometry corrections:

1. Preserve independent component IDs while auditing each against visible
   markings and matched source placement. Distinguish local provisional IDs from
   observed source reference designators.
2. Add an actual board substrate with correct outline, thickness, mounting-hole
   openings and top/bottom coordinate conventions. Validate against source CAD
   and reviewed images; do not invent underside component population.
3. Replace generic boxes with appropriate package profiles: leads, regulator tab,
   USB shell opening, switch actuator, header contacts and insulator bodies,
   RF shield and antenna regions. Use source models when matched; tag approximations.
4. Project source geometry into reviewed photos using explicitly paired physical
   landmarks. Report actual overlap/reprojection errors separately from generator
   self-consistency and synthetic views.
5. Verify independent per-component highlight and depth occlusion from top,
   underside and four side directions. Real physical flip behavior remains a
   separate phone evaluation requirement.

Antigravity working directories were inspected read-only. No blind branch merge,
model activation, calibration activation or Raspberry Pi change was performed.
