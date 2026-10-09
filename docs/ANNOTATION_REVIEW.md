# Annotation review before part training

Initial board labels were reviewed on contact sheets. These labels support board detection. Part seeds are a separate partial dataset and are not included in that detector's training labels.

For each component-training image, define the intended classes, review every visible instance of those classes, correct boxes, and record truncation/occlusion. Leave visually indistinguishable resistor/capacitor packages unresolved unless readable markings or registered matched geometry supply evidence. Treat board-wide BOM lists as source records, not proof of visible populated components.

Keep original/crop and near-duplicate capture groups together. Additional physical specimens and independent capture sessions are needed for a meaningful generalization test. The current split cannot measure held-out ESP32 performance.

New images must receive fresh identity and box review. Do not extend timestamp-based proposals from the initial batch to unknown photos. Existing component seed files retain their incomplete-coverage flags until review is completed.

For source joins, check `data/photo-model/source-bundles.json`. MCXN947 records are incompatible with the MCXN236 phone specimen. Exact Ultimaker joins require layout registration even though the revision marking agrees.
