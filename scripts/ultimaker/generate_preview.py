import cv2
import json
import numpy as np
from pathlib import Path

ROOT = Path('.').resolve()
PREVIEW_DIR = ROOT / 'previews'
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

im_path = ROOT / 'data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg'
if not im_path.exists():
    print(f"Image not found: {im_path}")
    exit(1)

img = cv2.imread(str(im_path))
h, w, _ = img.shape

# Load instance masks and scan refs
masks_data = json.loads((ROOT / 'annotations/ultimaker-instance-masks.json').read_text(encoding='utf-8'))
scan_refs = json.loads((ROOT / 'annotations/ultimaker-reviewed-scan-references.json').read_text(encoding='utf-8'))

overlay = img.copy()

# Colors (BGR)
COLOR_BOARD = (0, 255, 128)      # Green-cyan
COLOR_COMP = (255, 160, 50)       # Blue-orange
COLOR_PIN = (0, 220, 255)         # Yellow-gold
COLOR_TEXT = (255, 255, 255)      # White

# 1. Draw board polygon
for m in masks_data['masks']:
    if m['class_name'] == 'printed_circuit_board' and m['image_width'] == w:
        pts = np.array(m['polygon_xy_pixels'], np.int32).reshape((-1, 1, 2))
        cv2.polylines(overlay, [pts], isClosed=True, color=COLOR_BOARD, thickness=6)

# 2. Draw components from scan references
prim_template = scan_refs['templates'][0]
for item in prim_template['labels']:
    bbox = item['bbox_xyxy_normalized']
    x1, y1, x2, y2 = int(bbox[0]*w), int(bbox[1]*h), int(bbox[2]*w), int(bbox[3]*h)
    kind = item['kind']
    label = item['label'].split('·')[0].strip() if '·' in item['label'] else item['label'][:15]
    
    if kind in ['part', 'connector', 'power_connector', 'usb_connector']:
        cv2.rectangle(overlay, (x1, y1), (x2, y2), COLOR_COMP, 4)
        cv2.rectangle(overlay, (x1, max(0, y1 - 32)), (x1 + len(label)*16 + 20, y1), COLOR_COMP, -1)
        cv2.putText(overlay, label, (x1 + 6, max(24, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
    elif kind == 'pin':
        cv2.rectangle(overlay, (x1, y1), (x2, y2), COLOR_PIN, 2)
        cv2.circle(overlay, ((x1+x2)//2, (y1+y2)//2), 3, (0, 0, 255), -1)

# Blend overlay with original image
cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

# Add title banner
banner = np.zeros((120, w, 3), dtype=np.uint8)
cv2.putText(banner, "Tokito AR Verification: Ultimaker Ultimainboard 2.1.4", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
cv2.putText(banner, "Audited 3D Digital Twin | Verified Component Instances | Source-Linked Pin References", (40, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 220, 255), 2, cv2.LINE_AA)
img[:120, :] = banner

out_path = PREVIEW_DIR / 'ultimaker-annotation-review-20261010.jpg'
# Save high quality preview
cv2.imwrite(str(out_path), img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
print(f"Successfully generated preview image: {out_path} ({w}x{h})")
