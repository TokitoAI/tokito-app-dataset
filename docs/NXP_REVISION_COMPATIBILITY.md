# NXP photographed revision versus source geometry

The new video shows `FRDM-MCXN236` and copyright text `2024 NXP B.V.`. The earlier
interpretation of its `B` as a hardware revision was incorrect and is retracted.
The source PCB places that copyright on F.SilkS; the actual `170-90828 REV C`
identifier is on B.Cu. The photographed physical revision remains unverified.
The downloaded
design ZIP contains only `LAY-90828_C.brd`, `SCH-90828_C` schematic/BOM and
associated C records. The schematic cover's revision history was inspected as
text and as a rendered page; this provides direct evidence of meaningful changes.

B1 marks U6, J14 and J21 DNP and changes C28, C18 and C30 values. B2 reports an
administrative revision change with no design changes. Rev C changes signals on
J8 contacts 6 and 8, deletes C157/C155/R301/R300, changes R89/R121 to zero ohms,
marks R91/R122 DNP and adds TP10 through TP32. The B marking alone does not
establish a physical revision; underside revision evidence is needed.

The reviewed history is recorded in
`data/board-sources/nxp-frdm-mcxn236/ar-reference/revision-compatibility-review.json`.
Its PDF digest and page identify the evidence. Do not transfer C-only testpoints
to a revision-unverified photograph, apply C J8 pin routing, or claim a deleted B component
is absent from the specimen. Unlisted references still require photo/source
registration; absence from the history is not proof of geometry equivalence.

The existing C GLB remains a useful source candidate with independent component
selectors. No B/C mismatch has been established for this specimen. Revision-matched records or
documented per-component physical equivalence are required before final model
training and AR calibration activation.
