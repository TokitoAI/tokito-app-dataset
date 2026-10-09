# Phone photograph collection

Use board IDs in PROJECT_CONTEXT.md. Keep original images; store edits separately. Initial supplied images are identification references, not component annotations.

1. Photograph both board faces straight-on, fully in frame, on a matte contrasting surface under diffuse light. Include a ruler in one separate calibration photo.
2. Capture overlapping close-ups so chip markings, reference designators, connectors and revision text are readable. Avoid glare, motion blur and digital zoom.
3. Capture oblique views from each side for connector and component height. Remove cases when feasible; record heatsinks and other occlusions.
4. Record device, session ID, board ID, physical specimen ID, side, view, lighting, resolution and any modifications. Never claim a hidden component has been observed.
5. Group train/validation/test splits by physical specimen and capture session; near-duplicate frames from the same session belong together.

Suggested name: board-id__specimen01__session01__top__001.jpg

Annotation template fields: image_path, board_id, specimen_id, session_id, side, view, component_refdes, component_class, bbox_xyxy_pixels, marking_text, visibility, confidence, annotation_source, reviewed_by.

Exact refdes and net labels must come from a matched revision schematic/PCB and manual image review. Reference clone sources are useful for comparison but do not establish labels on the photographed board.
