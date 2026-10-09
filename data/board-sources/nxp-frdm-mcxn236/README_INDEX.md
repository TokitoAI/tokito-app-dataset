# MCXN236 schematic reference text index

`schematic-reference-index.json` makes text in the collected `SPF-90828.pdf`
searchable by reference-like string, with a page and bounding box for each match.
The source PDF is SCH-90828 / SPF-90828 revision C, 13 sheets, drawing date
2024-03-25. Its SHA-256 is
`243b93184f692b0f7c0deb3a9a63f6262ea3083a05c30c0143b4a4faa54b1868`.
See [PROVENANCE.md](PROVENANCE.md) for collection history and source rights.

The index contains **629 text occurrences and 410 distinct normalized strings**.
These counts are not BOM quantities. Cover-sheet change history, pin aliases,
BGA ball names such as `C1`, `D1` and `F1`, DNP lists, repeated symbol units and
notes can all resemble component references. The extractor leaves each match
as `unclassified_reference_like_text`; it does not decide which candidates are
current, fitted components. It also does not assign values, footprints, nets,
photo boxes, or exact part numbers.

## Finding source evidence

`by_refdes` maps a normalized string to IDs in `occurrences`. A record includes:

- `page`: one-based PDF page number.
- `bbox_pt`: `[x0, top, x1, bottom]` in PDF points (1/72 inch), measured from the
  top-left of the displayed page after applying its page rotation.
- `raw_text`: the exact matched text, including a pin suffix if present.
- `reference_text`, `normalized_refdes`, `symbol_unit`, `pin_suffix`: retained
  spelling plus limited normalization. For example, `U1A` becomes lookup `U1`
  with unit `A`; `J2-18` becomes lookup `J2` with pin suffix `-18`.
- `source_word`, `word_index_zero_based`, `match_span_zero_based`: the exact
  extraction word and character span used to recover its glyph bounds.

All displayed pages measure 842 x 595 points and have PDF rotation 90 degrees.
These are rotated display coordinates, not native unrotated PDF coordinates or
PCB placement coordinates. Bounds enclose the printed reference text, not the
whole schematic symbol.

## Visually checked source link

`by_refdes.SW3` resolves to `p010-SW3-01`:

```json
{
  "page": 10,
  "raw_text": "SW3",
  "bbox_pt": [384.950846, 93.758602, 392.044553, 97.238601]
}
```

Visual inspection of the full page and a detail render confirms SW3 is the
**ISP pushbutton**, with `SW SPST NO` beside its symbol and the signal
`P0_6/ISPMODE_N-SW`. On the same sheet SW1 is RESET and SW2 is WAKEUP.
This supports a schematic reference link. The photograph's board revision and
exact installed part remain separate evidence requirements.

## Reproducing and checking the index

From the repository root, use Python 3.10+ with `pdfplumber==0.11.9`:

```text
python scripts/index_schematic_refs.py data/board-sources/nxp-frdm-mcxn236/SPF-90828.pdf data/board-sources/nxp-frdm-mcxn236/schematic-reference-index.json
python scripts/index_schematic_refs.py data/board-sources/nxp-frdm-mcxn236/SPF-90828.pdf data/board-sources/nxp-frdm-mcxn236/schematic-reference-index.json --check
```

The script deduplicates overprinted glyphs at 0.1 point tolerance, groups words
at 0.5 point x/y tolerance with matching font and size, then finds reference
patterns. Bounds come from the matched glyphs rather than proportional slicing
of a word's box. Prefixes and all extraction options are recorded in JSON.

`--check` reopens the source PDF, verifies its hash, regenerates all matches, and
compares the saved pages, exact text, word spans, glyph bounds, normalization,
lookup IDs and counts. Generation also rejects non-finite or out-of-page boxes
and ambiguous text-to-glyph mappings. This checks the artifact's relationship to
the PDF text; it does not establish semantic completeness or BOM correctness.

The committed output was generated using the Codex bundled Python runtime and
pdfplumber 0.11.9. Rendering for the visual review used pdfplumber's image
renderer; rendering is not required to regenerate the JSON. Most occurrences
have not been individually reviewed visually. The prefix allowlist and PDF text
layout can omit valid references, so an absent lookup does not prove absence
from the board.
