import os
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path('.').resolve()
YOLO_DIR = ROOT / 'data/photo-model/yolo-ultimaker-seg'

for sub in ['images/train', 'images/val', 'labels/train', 'labels/val']:
    (YOLO_DIR / sub).mkdir(parents=True, exist_ok=True)

# Classes:
# 0: board
# 1: component
# 2: pin

# 1. Base component polygons normalized on Ultimaker primary view (IMG_20261009_222135_1.jpg)
# Board substrate:
board_poly_norm = [
    (0.01, 0.01), (0.99, 0.01), (0.99, 0.99), (0.01, 0.99)
]

# Major components normalized:
components_boxes = [
    (0.5588, 0.1348, 0.7778, 0.2339), # U1 ATmega2560
    (0.7896, 0.7896, 0.8770, 0.8188), # U2 ATmega16U2
    (0.6332, 0.0073, 0.7735, 0.0264), # J22 SERIAL
    (0.5049, 0.0078, 0.6030, 0.0405), # J23 EXT/IO
    (0.5049, 0.0518, 0.6030, 0.0835), # J1 ICSP1
    (0.3970, 0.7788, 0.4898, 0.8135), # J2 ICSP2
    (0.7789, 0.9351, 0.8997, 1.0000), # J19 USB-B
    (0.4606, 0.9272, 0.6451, 1.0000), # J21 Heated Bed
    (0.6300, 0.8433, 0.6947, 0.9150), # Y1 Resonator
    (0.3172, 0.3369, 0.4024, 0.3750), # U8 Stepper Z
    (0.3161, 0.2227, 0.4024, 0.2593), # U10 Stepper E1
]

# Header pins normalized:
# J22 pins:
j22_pins = [
    (902/1408, 27/3112, 946/1408, 73/3112),
    (948/1408, 27/3112, 992/1408, 73/3112),
    (995/1408, 27/3112, 1039/1408, 73/3112),
    (1041/1408, 27/3112, 1085/1408, 73/3112)
]

# J23 pins:
j23_pins = [
    (720/1408, 82/3112, 750/1408, 117/3112),
    (720/1408, 32/3112, 750/1408, 69/3112),
    (766/1408, 82/3112, 796/1408, 117/3112),
    (766/1408, 32/3112, 796/1408, 69/3112),
    (811/1408, 82/3112, 841/1408, 117/3112),
    (811/1408, 32/3112, 841/1408, 69/3112)
]

# J1 pins:
j1_pins = [
    (720/1408, 216/3112, 750/1408, 251/3112),
    (720/1408, 170/3112, 750/1408, 208/3112),
    (766/1408, 216/3112, 796/1408, 251/3112),
    (766/1408, 170/3112, 796/1408, 208/3112),
    (811/1408, 216/3112, 841/1408, 251/3112),
    (811/1408, 170/3112, 841/1408, 208/3112)
]

all_pins = j22_pins + j23_pins + j1_pins

def box_to_poly(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def poly_to_line(cls_id, poly):
    coords = " ".join(f"{max(0.0, min(1.0, x)):.6f} {max(0.0, min(1.0, y)):.6f}" for x, y in poly)
    return f"{cls_id} {coords}\n"

def make_primary_label():
    lines = []
    lines.append(poly_to_line(0, board_poly_norm))
    for bx in components_boxes:
        lines.append(poly_to_line(1, box_to_poly(*bx)))
    for px in all_pins:
        lines.append(poly_to_line(2, box_to_poly(*px)))
    return "".join(lines)

primary_label_str = make_primary_label()

# 2. Populate Train split (2026-10-09 captures)
train_src_dir = ROOT / 'data/photo-model/by_board/ultimainboard'
train_imgs = list(train_src_dir.glob('*.jpg'))
print(f"Found {len(train_imgs)} train images in {train_src_dir}")

for img_path in train_imgs:
    dst_img = YOLO_DIR / 'images/train' / img_path.name
    shutil.copy2(img_path, dst_img)
    dst_lbl = YOLO_DIR / 'labels/train' / f"{img_path.stem}.txt"
    dst_lbl.write_text(primary_label_str, encoding='utf-8')

# 3. Populate Val split (2026-10-10 intake captures + video keyframes)
val_src_dir = ROOT / 'data/phone-captures/2026-10-10'
val_intake_imgs = [
    'IMG_20261010_092241.jpg', 'IMG_20261010_092241_1.jpg',
    'IMG_20261010_092244.jpg', 'IMG_20261010_092244_1.jpg',
    'IMG_20261010_092247.jpg', 'IMG_20261010_092247_1.jpg'
]

# For wide shots:
wide_board_poly = [
    (0.3289, 0.2133), (0.6842, 0.2133), (0.6842, 0.7648), (0.3289, 0.7648)
]
wide_label_lines = [poly_to_line(0, wide_board_poly)]
# Scaled component positions inside wide shot:
for bx in components_boxes:
    x1, y1, x2, y2 = bx
    wx1 = 0.3289 + x1 * (0.6842 - 0.3289)
    wy1 = 0.2133 + y1 * (0.7648 - 0.2133)
    wx2 = 0.3289 + x2 * (0.6842 - 0.3289)
    wy2 = 0.2133 + y2 * (0.7648 - 0.2133)
    wide_label_lines.append(poly_to_line(1, box_to_poly(wx1, wy1, wx2, wy2)))
for px in all_pins:
    x1, y1, x2, y2 = px
    wx1 = 0.3289 + x1 * (0.6842 - 0.3289)
    wy1 = 0.2133 + y1 * (0.7648 - 0.2133)
    wx2 = 0.3289 + x2 * (0.6842 - 0.3289)
    wy2 = 0.2133 + y2 * (0.7648 - 0.2133)
    wide_label_lines.append(poly_to_line(2, box_to_poly(wx1, wy1, wx2, wy2)))

wide_label_str = "".join(wide_label_lines)

for vname in val_intake_imgs:
    src = val_src_dir / vname
    if src.exists():
        dst_img = YOLO_DIR / 'images/val' / vname
        shutil.copy2(src, dst_img)
        dst_lbl = YOLO_DIR / 'labels/val' / f"{Path(vname).stem}.txt"
        if '_1' in vname:
            dst_lbl.write_text(primary_label_str, encoding='utf-8')
        else:
            dst_lbl.write_text(wide_label_str, encoding='utf-8')

# Copy extracted video keyframes into val split
scratch_dir = ROOT.parents[1] / 'brain/5ac02572-1634-48c3-bfaf-dd326b1fc286/scratch'
for idx in range(4):
    kframe = scratch_dir / f"video_20261010_135936.mp4_f{idx}.jpg"
    if kframe.exists():
        dst_kframe = YOLO_DIR / 'images/val' / f"video_frame_{idx+1:03d}.jpg"
        shutil.copy2(kframe, dst_kframe)
        dst_lbl = YOLO_DIR / 'labels/val' / f"video_frame_{idx+1:03d}.txt"
        dst_lbl.write_text(primary_label_str, encoding='utf-8')

# Write dataset.yaml
dataset_yaml = f"""path: {YOLO_DIR.as_posix()}
train: images/train
val: images/val

names:
  0: board
  1: component
  2: pin
"""

(YOLO_DIR / 'dataset.yaml').write_text(dataset_yaml, encoding='utf-8')
print("Successfully generated Ultimaker YOLO segmentation dataset!")
