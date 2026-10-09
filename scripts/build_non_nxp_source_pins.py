"""Index native Altium schematic pins without claiming photographic pin locations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/board-sources/non-nxp-source-pins.json"
SOURCES = {
    "esp8266_board": {
        "directory": "data/board-sources/esp8266-nodemcu-reference/structured-source",
        "relationship": "different_usb_uart_reference_variant",
        "physical_mapping_allowed": False,
    },
    "ultimainboard": {
        "directory": "data/board-sources/ultimainboard-2.1.4/structured-source",
        "relationship": "revision_marking_matches_source_registration_pending",
        "physical_mapping_allowed": False,
    },
}


def extract_family(family: str, source: dict) -> dict:
    base = ROOT / source["directory"]
    inventory = json.loads((base / "schematic-component-inventory.json").read_text(encoding="utf-8"))
    symbols = {(item["sheet"], item["record_index"]): item for item in inventory}
    pins = []
    for path in sorted((base / "schematic-records").glob("*.json")):
        sheet = path.stem
        records = json.loads(path.read_text(encoding="utf-8"))
        by_index = {item["stream_record_index"]: item["fields"] for item in records}
        for item in records:
            fields = item["fields"]
            if fields.get("RECORD") != "2":
                continue
            # Native OWNERINDEX is one less than the stream_record_index in
            # these extracted Altium files. Verify every join against RECORD 1.
            parent_index = int(fields["OWNERINDEX"]) + 1
            parent = by_index.get(parent_index)
            if parent is None or parent.get("RECORD") != "1":
                raise ValueError(f"Unresolved pin owner: {path}:{item['stream_record_index']}")
            symbol = symbols.get((sheet, parent_index))
            if symbol is None:
                raise ValueError(f"Missing inventory symbol: {sheet}:{parent_index}")
            pins.append({
                "refdes": symbol["designator"],
                "pin_number": fields["DESIGNATOR"],
                "pin_name": fields.get("NAME") or None,
                "source_sheet": sheet,
                "source_record_index": item["stream_record_index"],
                "source_symbol_record_index": parent_index,
                "photo_bbox_xyxy_pixels": None,
                "photo_mapping_status": "source_pin_unregistered_in_photo",
            })
    pins.sort(key=lambda pin: (pin["refdes"], pin["pin_number"], pin["source_sheet"], pin["source_record_index"]))
    counts = Counter(pin["refdes"] for pin in pins)
    return {
        "board_family": family,
        "source_directory": source["directory"],
        "source_relationship": source["relationship"],
        "physical_mapping_allowed_without_review": source["physical_mapping_allowed"],
        "source_symbol_count": len(inventory),
        "source_pin_record_count": len(pins),
        "source_components_with_pins": len(counts),
        "distinct_refdes_pin_numbers": len({(pin["refdes"], pin["pin_number"]) for pin in pins}),
        "pins": pins,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when generated catalog differs")
    args = parser.parse_args()
    families = [extract_family(family, source) for family, source in SOURCES.items()]
    result = {
        "schema_version": "1.0",
        "scope": "schematic source pin identity only; no photo pin position or net inference",
        "families": families,
    }
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != payload:
            raise SystemExit(f"Outdated: {OUTPUT}")
    else:
        OUTPUT.write_text(payload, encoding="utf-8")
    print("; ".join(f"{entry['board_family']}: {entry['source_pin_record_count']} source pins" for entry in families))


if __name__ == "__main__":
    main()
