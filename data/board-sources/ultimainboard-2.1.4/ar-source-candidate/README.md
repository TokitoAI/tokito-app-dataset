# Ultimainboard source geometry candidate

This asset is exported from the preserved imported Ultimainboard 2.1.4 PCB, using
its embedded package geometry. It improves the earlier Antigravity component-box
candidate by preserving actual source package shapes, PCB substrate, pads,
soldermask and silkscreen. Source design geometry does not establish photographed
population, installed ordering codes or registered image overlap.

`ultimaker-source-selectable.glb` has 310 source-reference subtrees named
`ref:<designator>`. The index verifies disjoint component node/mesh ownership;
the original vertex buffers, coordinate transforms and geometry are preserved.
The export includes 439 meshes and 869 nodes. Source reference names are not
automatically labels for the photographed components.

Exported with KiCad CLI 10.0.7:

```powershell
kicad-cli pcb export glb --force --include-pads --include-silkscreen --include-soldermask --user-origin '148.5011x105.0036mm' --output source.glb Ultimainboard-2.1.4.imported.kicad_pcb
python scripts/index_ultimaker_source_glb.py source.glb selectable.glb
```

The source import emits two zero-sized-pad warnings. Existing DRC issues remain;
this is not fabrication approval. The source export origin was chosen at the
substrate center; GLB uses metre units and Y-up. Preserve the source transforms
when adding camera calibration. Do not use earlier hand-entered Antigravity
mounting-hole coordinates without source/photo verification.

The surface preview was rendered with depth occlusion at 640×480 and visually
inspected. It omits GLB line/point primitives; these remain in the downloadable
asset. It is a synthetic review image, not real-camera tracking evidence.

Of 264 source references without selectable bodies, 252 are test contacts, three
are fiducials, four are mechanical spacers, one is a solder jumper and four are
missing package bodies (J34, U9, K1, L2). Test contacts and fiducials need exact
source copper/pad regions, not fabricated 3D IC bodies.

Production activation remains disabled pending source/photo registration,
component/contact labels, verified physical landmarks, camera calibration,
multi-view coverage and phone flip/highlight evaluation.
