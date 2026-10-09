"""Acquire only PCB-Vision's RGB ZIP prefix and verify every selected member.

The upstream ZIP interleaves HSI after the RGB directory. A verified central
directory inventory lets us stop the stream after the RGB data, even when the
server ignores Range. This does not verify/download the full HSI archive.
"""
import argparse
import hashlib
import json
import struct
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SOURCES = [
    "https://zenodo.org/api/records/10617721/files/PCBDataset.zip/content",
    "https://zenodo.org/records/10617721/files/PCBDataset.zip?download=1",
    "https://rodare.hzdr.de/api/files/671920b9-68a5-4a82-98d1-c696f25e497c/PCBDataset.zip",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true", help="Reverify existing prefix/files without network access")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory_path = REPO / "data/external/PCBVision/remote-archive-members.json"
    inventory_bytes = inventory_path.read_bytes()
    selected = [m for m in json.loads(inventory_bytes)
                if m["name"].startswith("PCBDataset/RGB/")
                and m["name"].endswith((".png", ".jpg"))]
    required = max(m["header_offset"] + m["compressed_bytes"]
                   + 30 + len(m["name"].encode()) + 4096 for m in selected)
    prefix = out / "rgb-archive-prefix.bin"
    attempt_file = out / "rgb-prefix-attempts.json"
    attempts = json.loads(attempt_file.read_text()) if attempt_file.exists() else []
    if not prefix.exists() or prefix.stat().st_size != required:
        if args.verify_only:
            raise ValueError("Required RGB prefix is missing or has a different size")
        attempts = []
        for url in SOURCES:
            attempt = {"url": url, "requested_range": f"bytes=0-{required-1}"}
            attempts.append(attempt)
            try:
                request = urllib.request.Request(url, headers={
                    "Range": attempt["requested_range"],
                    "User-Agent": "Tokito-dataset-acquisition/1.0",
                })
                with urllib.request.urlopen(request, timeout=90) as response:
                    attempt.update(http_status=response.status,
                                   final_url=response.url,
                                   content_range=response.headers.get("Content-Range"))
                    if response.status == 206:
                        assert response.headers.get("Content-Range", "").startswith("bytes 0-")
                    else:
                        assert response.status == 200
                    count = 0
                    with prefix.open("wb") as handle:
                        while count < required:
                            data = response.read(min(262144, required-count))
                            if not data:
                                raise ValueError("Archive stream ended before RGB prefix")
                            handle.write(data)
                            count += len(data)
                            if count % (1024*1024) == 0:
                                print(f"RGB prefix {count}/{required}", flush=True)
                    attempt["downloaded_bytes"] = count
                    attempt_file.write_text(json.dumps(attempts, indent=2))
                break
            except Exception as exc:
                attempt["error"] = str(exc)
                print(f"Source attempt failed: {exc}", flush=True)
                attempt_file.write_text(json.dumps(attempts, indent=2))
        else:
            raise RuntimeError("All official archive-prefix endpoints failed")
    raw = prefix.read_bytes()
    records = []
    extraction = (out / "rgb-subset").resolve()
    for member in selected:
        offset = member["header_offset"]
        fields = struct.unpack_from("<4s5H3I2H", raw, offset)
        magic, version, flags, method, mtime, mdate, crc, packed, unpacked, nlen, xlen = fields
        assert magic == b"PK\x03\x04", member["name"]
        assert not flags & 1, "Encrypted member"
        name = raw[offset+30:offset+30+nlen].decode("utf-8")
        assert name == member["name"]
        start = offset+30+nlen+xlen
        compressed = raw[start:start+member["compressed_bytes"]]
        assert len(compressed) == member["compressed_bytes"]
        if method == 0:
            payload = compressed
        elif method == 8:
            payload = zlib.decompress(compressed, -15)
        else:
            raise ValueError(f"Unsupported ZIP method: {method}")
        assert len(payload) == member["bytes"]
        assert zlib.crc32(payload) & 0xffffffff == member["crc32"]
        if not flags & 8:
            assert crc == member["crc32"]
            assert unpacked == member["bytes"]
        dest = (extraction / name).resolve()
        assert dest.is_relative_to(extraction), "Unsafe archive member"
        if args.verify_only:
            assert dest.read_bytes() == payload, f"Extracted file differs: {name}"
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        with Image.open(dest) as image:
            image.load()
            shape = list(image.size)
            mode = image.mode
            is_mask = "/General/" in name or "/Monoseg/" in name
            values = sorted(set(image.tobytes())) if is_mask and mode in ("L", "P") else None
            if is_mask:
                assert mode == "L" and set(values).issubset({0, 1, 2, 3}), name
        records.append({"name": name, "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "crc32": f"{member['crc32']:08x}", "zip_crc_verified": True,
                        "image_decoded": True, "size_width_height": shape,
                        "mode": mode, "mask_values": values})
    photos = {Path(m["name"]).stem: m for m in records
              if Path(m["name"]).parent.as_posix() == "PCBDataset/RGB"}
    pairing = []
    for family in ("General", "Monoseg"):
        masks = {Path(m["name"]).stem: m for m in records if f"/{family}/" in m["name"]}
        assert set(masks) == set(photos), f"{family} mask/photo IDs differ"
        for key in sorted(photos, key=int):
            pairing.append({"image_id": key, "mask_family": family,
                            "rgb": photos[key]["name"], "mask": masks[key]["name"],
                            "same_dimensions": photos[key]["size_width_height"] == masks[key]["size_width_height"],
                            "rgb_size": photos[key]["size_width_height"],
                            "mask_size": masks[key]["size_width_height"]})
    assert len(photos) == 53 and len(pairing) == 106
    assert all(p["same_dimensions"] for p in pairing)
    report = {
        "schema_version": 1, "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "rgb_subset_acquired_and_member_crc_verified",
        "official_record": "https://rodare.hzdr.de/record/2704",
        "official_mirror": "https://zenodo.org/records/10617721",
        "doi": "10.14278/rodare.2704", "dataset_license": "CC BY 4.0",
        "source_archive_bytes": 11392398155,
        "published_full_archive_md5": "caeee8bafb7857e9bef3479d5ab3f9b4",
        "full_archive_checksum_verified": False,
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "prefix_bytes": len(raw), "prefix_sha256": hashlib.sha256(raw).hexdigest(),
        "attempts": attempts, "rgb_images": len(photos),
        "general_masks": sum("/General/" in m["name"] for m in records),
        "monoseg_masks": sum("/Monoseg/" in m["name"] for m in records),
        "all_mask_pairs_match_dimensions": all(p["same_dimensions"] for p in pairing),
        "scope": "External component-segmentation reference; does not identify our board models, reference designators, or pins. HSI excluded.",
        "bulk_workspace_path": str(extraction), "members": records, "mask_pairs": pairing,
    }
    target = REPO / "data/external/PCBVision/rgb-acquisition-verified.json"
    if args.verify_only:
        saved = json.loads(target.read_text(encoding="utf-8"))
        for key in ("inventory_sha256", "prefix_bytes", "prefix_sha256", "members", "mask_pairs"):
            assert saved[key] == report[key], f"Verified data differs from saved acquisition report: {key}"
    else:
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        (out / "rgb-acquisition-verified.json").write_text(target.read_text(), encoding="utf-8", newline="\n")
    print(json.dumps({key: report[key] for key in ("state", "rgb_images", "general_masks", "monoseg_masks", "all_mask_pairs_match_dimensions")}), flush=True)


if __name__ == "__main__":
    main()
