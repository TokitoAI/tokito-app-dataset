#!/usr/bin/env python3
"""Index reference-like text in a text PDF; this is not a BOM extractor.

Requires pdfplumber 0.11.9 (the version used for the committed index).
Coordinates refer to the displayed/rotated page, in PDF points from top left.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re

import pdfplumber


# Boundaries exclude substrings of part numbers, URLs and net names. An optional
# connector-pin suffix is retained as evidence, not counted as another part.
REFERENCE_PATTERN = (
    r"(?<![A-Za-z0-9_/.-])"
    r"(?P<reference>(?P<prefix>TP|SW|JP|FB|LED|R|C|D|U|J|L|Q|Y|F)"
    r"(?P<number>[1-9][0-9]*)(?P<unit>[A-Z])?)"
    r"(?P<pin>[-_][0-9]+)?"
    r"(?![A-Za-z0-9_])"
)
REFERENCE_RE = re.compile(REFERENCE_PATTERN)
WORD_OPTIONS = {
    "x_tolerance": 0.5,
    "y_tolerance": 0.5,
    "extra_attrs": ["fontname", "size"],
    "return_chars": True,
}
DEDUPLICATION_TOLERANCE = 0.1


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded_box(chars: list[dict]) -> list[float]:
    return [
        round(min(c["x0"] for c in chars), 6),
        round(min(c["top"] for c in chars), 6),
        round(max(c["x1"] for c in chars), 6),
        round(max(c["bottom"] for c in chars), 6),
    ]


def matching_chars(word: dict, start: int, end: int) -> list[dict]:
    """Match a character span without estimating its width from the word box."""
    chars = word["chars"]
    # Refdes are ASCII. Refuse ambiguous glyph-to-text mappings rather than
    # assigning a potentially wrong box (e.g. if ligature expansion differs).
    joined = "".join(c["text"] for c in chars)
    if joined != word["text"]:
        raise ValueError(f"Ambiguous character mapping for word {word['text']!r}")
    selected = []
    cursor = 0
    for char in chars:
        next_cursor = cursor + len(char["text"])
        if cursor < end and next_cursor > start:
            selected.append(char)
        cursor = next_cursor
    if "".join(c["text"] for c in selected) != joined[start:end]:
        raise ValueError(f"Match does not align with PDF glyphs: {joined!r}")
    return selected


def make_index(pdf_path: Path, index_path: Path) -> dict:
    occurrences = []
    pages = []
    by_refdes: dict[str, list[str]] = defaultdict(list)
    counters: Counter[tuple[int, str]] = Counter()
    with pdfplumber.open(pdf_path) as document:
        for page_number, page in enumerate(document.pages, 1):
            pages.append(
                {
                    "page": page_number,
                    "width_pt": page.width,
                    "height_pt": page.height,
                    "pdf_rotation_degrees": page.rotation,
                }
            )
            words = page.dedupe_chars(
                tolerance=DEDUPLICATION_TOLERANCE
            ).extract_words(**WORD_OPTIONS)
            for word_index, word in enumerate(words):
                for match in REFERENCE_RE.finditer(word["text"]):
                    raw = match.group(0)
                    refdes = match.group("reference")
                    unit = match.group("unit")
                    # U1A is a unit of U1. A suffix on a different prefix is
                    # retained, as its physical interpretation is unproven.
                    normalized = (
                        f"U{match.group('number')}"
                        if unit and match.group("prefix") == "U"
                        else refdes
                    )
                    box = rounded_box(matching_chars(word, *match.span()))
                    x0, top, x1, bottom = box
                    if not (
                        all(math.isfinite(v) for v in box)
                        and -0.001 <= x0 < x1 <= page.width + 0.001
                        and -0.001 <= top < bottom <= page.height + 0.001
                    ):
                        raise ValueError(f"Out-of-page reference: {page_number}, {raw}, {box}")
                    counters[(page_number, refdes)] += 1
                    identifier = (
                        f"p{page_number:03d}-{refdes}-"
                        f"{counters[(page_number, refdes)]:02d}"
                    )
                    occurrence = {
                        "id": identifier,
                        "page": page_number,
                        "bbox_pt": box,
                        "raw_text": raw,
                        "reference_text": refdes,
                        "normalized_refdes": normalized,
                        "symbol_unit": unit if match.group("prefix") == "U" else None,
                        "pin_suffix": match.group("pin"),
                        "source_word": word["text"],
                        "word_index_zero_based": word_index,
                        "match_span_zero_based": list(match.span()),
                        "context": "unclassified_reference_like_text",
                    }
                    occurrences.append(occurrence)
                    by_refdes[normalized].append(identifier)
            page.close()
    page_counts = Counter(item["page"] for item in occurrences)
    prefix_counts = Counter(
        re.match(r"[A-Z]+", item["normalized_refdes"]).group()
        for item in occurrences
    )
    return {
        "schema_version": "1.0",
        "kind": "schematic_reference_text_occurrences",
        "source": {
            "pdf_path_relative_to_index": Path(
                os.path.relpath(pdf_path, index_path.parent)
            ).as_posix(),
            "pdf_sha256": file_hash(pdf_path),
            "pdf_bytes": pdf_path.stat().st_size,
            "page_count": len(pages),
        },
        "extraction": {
            "library": "pdfplumber",
            "library_version": pdfplumber.__version__,
            "method": "dedupe_chars then extract_words, regex spans and exact glyph bounds",
            "deduplication_tolerance_pt": DEDUPLICATION_TOLERANCE,
            "word_options": WORD_OPTIONS,
            "reference_pattern": REFERENCE_PATTERN,
            "coordinate_system": {
                "units": "PDF points (1/72 inch)",
                "origin": "top-left of displayed page after PDF page rotation",
                "bbox_order": ["x0", "top", "x1", "bottom"],
                "x_axis": "right",
                "y_axis": "down",
                "precision_decimal_places": 6,
                "note": "Not native unrotated PDF bottom-left coordinates or PCB placement coordinates.",
            },
            "normalization": "U1A-style IC units normalize to U1; connector pin suffixes are retained separately.",
        },
        "limitations": [
            "This indexes reference-like PDF text, not fitted components, BOM quantities, values, packages, or connectivity.",
            "Change history, signal aliases, notes, DNP lists and repeated symbol units can all contribute occurrences.",
            "BGA ball names and other pin labels can share reference syntax (for example C1, D1 or F1); candidates are not semantically classified.",
            "A normalized reference does not establish that the component exists in the current revision or on the photographed board.",
            "PDF text extraction and an allowlist of prefixes can miss references; most occurrences have not been individually visually reviewed.",
            "Coordinates enclose reference text, not schematic symbols, PCB footprints or components in photos.",
            "The matching board revision and exact photo-to-component association require separate evidence.",
        ],
        "statistics": {
            "occurrence_count": len(occurrences),
            "unique_normalized_reference_texts": len(by_refdes),
            "occurrences_by_page": {str(p["page"]): page_counts[p["page"]] for p in pages},
            "occurrences_by_prefix": dict(sorted(prefix_counts.items())),
        },
        "pages": pages,
        "by_refdes": dict(sorted(by_refdes.items())),
        "occurrences": occurrences,
    }


def validate_index(pdf_path: Path, index_path: Path) -> dict:
    stored = json.loads(index_path.read_text(encoding="utf-8"))
    if stored["source"]["pdf_sha256"] != file_hash(pdf_path):
        raise ValueError("PDF SHA-256 differs from indexed source")
    # Re-extract all matches: compares page dimensions, raw text, glyph boxes,
    # normalization, cross-reference lookup, counts and source-word spans.
    current = make_index(pdf_path, index_path)
    if stored != current:
        raise ValueError(
            "Index differs from regenerated PDF evidence; use the recorded "
            "pdfplumber version or regenerate and review the differences"
        )
    return stored["statistics"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("index", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate an existing index without writing")
    args = parser.parse_args()
    pdf_path, index_path = args.pdf.resolve(), args.index.resolve()
    if args.check:
        statistics = validate_index(pdf_path, index_path)
        operation = "validated"
    else:
        result = make_index(pdf_path, index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        statistics = result["statistics"]
        operation = "generated"
    print(json.dumps({"operation": operation, "index": str(index_path), **statistics}, indent=2))


if __name__ == "__main__":
    main()
