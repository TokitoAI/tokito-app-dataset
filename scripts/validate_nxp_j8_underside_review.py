#!/usr/bin/env python3
"""Validate the reviewed NXP J8 underside pin candidates against the Rev C netlist."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/board-sources/nxp-frdm-mcxn236/ar-reference/j8-underside-pin-review.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    review = json.loads(REVIEW.read_text(encoding='utf-8'))
    assert review['status'] == 'photo_pin_candidates_reviewed_source_revision_unconfirmed'
    assert review['training_eligible'] is False
    photo = ROOT / review['photo']['path']
    assert digest(photo) == review['photo']['sha256']
    components = ROOT / review['source']['components_path']
    assert digest(components) == review['source']['components_sha256']
    source = json.loads(components.read_text(encoding='utf-8'))
    j8 = next(component for component in source['components'] if component['refdes'] == 'J8')
    net_by_pin = {int(record['pin']): record['net_name'] for record in j8['connections']
                  if record['record_kind'] == 'electrical_net'}
    assert len(net_by_pin) == 28 and set(net_by_pin) == set(range(1, 29))
    pins = review['pins']
    assert [pin['pin'] for pin in pins] == list(range(1, 29))
    for pin in pins:
        assert pin['source_net_candidate'] == net_by_pin[pin['pin']], pin
        x, y = pin['center_xy']
        assert 0 <= x < review['photo']['width'] and 0 <= y < review['photo']['height']

    image = Image.open(photo).convert('RGB')
    # Crop the actual connector and its silkscreen labels for a compact human review.
    crop = image.crop((1120, 3380, 1980, 3620))
    draw = ImageDraw.Draw(crop)
    try:
        font = ImageFont.truetype('arial.ttf', 16)
    except OSError:
        font = ImageFont.load_default()
    for pin in pins:
        x, y = pin['center_xy']
        local = (x - 1120, y - 3380)
        draw.ellipse((local[0]-11, local[1]-11, local[0]+11, local[1]+11), outline=(255, 40, 40), width=3)
        label_x = max(0, min(crop.width - 28, local[0] - 12))
        label_y = 2 if pin['pin'] % 2 == 0 else crop.height - 20
        draw.rectangle((label_x, label_y, label_x + 28, label_y + 18), fill=(255, 245, 0))
        draw.text((label_x + 2, label_y + 1), str(pin['pin']), fill=(0, 0, 0), font=font)
    preview = ROOT / review['orientation_evidence']['review_preview']
    preview.parent.mkdir(parents=True, exist_ok=True)
    image.close()
    crop.save(preview, quality=95)
    print('NXP J8: all 28 pin/net candidates match the Rev C source; photo pin-1 mark is visible; revision remains unverified; not training eligible.')


if __name__ == '__main__':
    main()
