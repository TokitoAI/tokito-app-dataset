"""Validate packaged PCB-Vision RGB assets or their Git LFS identity in CI."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-images', action='store_true', help='Decode full image bytes using Pillow; requires Git LFS payload')
    args = parser.parse_args()
    base = ROOT / 'data/external/PCBVision'
    package = json.loads((base / 'rgb-subset-package.json').read_text(encoding='utf-8'))
    acquisition_bytes = (ROOT / package['acquisition_manifest']).read_bytes()
    assert hashlib.sha256(acquisition_bytes).hexdigest() == package['acquisition_manifest_sha256']
    acquired = json.loads(acquisition_bytes)
    members = {row['path']: row for row in package['members']}
    assert len(members) == len(package['members']) == 160
    photos = {row['name']: row for row in acquired['members']}
    assert len(photos) == len(acquired['members']) == 159
    assert set(members) == set(photos) | {package['attribution_member']}
    counts = Counter('general_masks' if '/General/' in name else 'monoseg_masks' if '/Monoseg/' in name else 'rgb' for name in photos)
    assert dict(counts) == package['image_counts'] == {'rgb': 53, 'general_masks': 53, 'monoseg_masks': 53}
    for name, row in photos.items():
        assert members[name]['sha256'] == row['sha256']
        assert members[name]['bytes'] == row['bytes']
        assert members[name]['zip_crc32'] == row['crc32']
    for pair in acquired['mask_pairs']:
        assert photos[pair['rgb']]['size_width_height'] == photos[pair['mask']]['size_width_height']
    assert len(acquired['mask_pairs']) == 106
    data = (ROOT / package['archive_path']).read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        assert f"oid sha256:{package['archive_sha256']}\n".encode() in data
        assert f"size {package['archive_bytes']}\n".encode() in data
        assert not args.check_images, 'Run git lfs pull before checking image pixels'
        print('PCB-Vision: 159 RGB/mask metadata records and archive LFS identity validated; pixels not fetched.')
        return
    assert len(data) == package['archive_bytes']
    assert hashlib.sha256(data).hexdigest() == package['archive_sha256']
    with zipfile.ZipFile(BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist())) == 160
        assert set(archive.namelist()) == set(members)
        for name, row in members.items():
            blob = archive.read(name)
            assert len(blob) == row['bytes'] and hashlib.sha256(blob).hexdigest() == row['sha256']
            if args.check_images and name in photos:
                from PIL import Image
                with Image.open(BytesIO(blob)) as im:
                    im.load()
                    assert list(im.size) == photos[name]['size_width_height']
                    assert im.mode == photos[name]['mode']
                    if im.mode == 'L':
                        assert set(im.tobytes()) <= {0, 1, 2, 3}
        attribution = archive.read(package['attribution_member']).decode('utf-8')
        assert 'CC BY 4.0' in attribution and acquired['doi'] in attribution
    print('PCB-Vision: archive CRC/hash, all 160 member hashes, 53 RGB images and 106 mask pairs validated.' + (' Image pixels decoded.' if args.check_images else ''))


if __name__ == '__main__':
    main()
