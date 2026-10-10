# NXP J8 underside pin review

The underside capture provides a useful physical registration for the 28-pad
J8 header: the `J8` designator and printed port labels are visible, and pin 1
has a square pad at the lower-left of this view. The [numbered review crop](../previews/nxp-j8-underside-pin-review.jpg)
marks the approximate center of every visible solder pad. Pin numbers follow
the 2×14 convention: odd pins along the lower row and even pins along the
upper row, left to right.

The [machine-readable review](../data/board-sources/nxp-frdm-mcxn236/ar-reference/j8-underside-pin-review.json)
records the photographed label, approximate pixel center and matching Rev C
netlist candidate for each pin. The validator checks all 28 pin/net pairs
against the structured native source. Photo labels are the shorter printed
GPIO names; the Rev C source adds alternate peripheral functions to some net
names, for example `P4_7` versus `P4_7/FXIO_LCD_RST`.

This registers strong per-pin evidence, but does not certify the photographed
PCB artwork revision. `SCH-90828 REV C` is printed on an adhesive schematic
label, while `700-90828 REV A1` identifies the assembly domain. Neither is
treated as proof that the underlying layout is Rev C. The points are approximate
pixel centers rather than reviewed segmentation polygons or calibrated metric
anchors. The proposals therefore remain ineligible for training ground truth
until the physical layout revision and pixel geometry are independently
verified.

Rebuild the review image and validate the source join with:

```text
python scripts/validate_nxp_j8_underside_review.py
```
