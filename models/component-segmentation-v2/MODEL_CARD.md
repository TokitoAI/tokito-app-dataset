# Tokito Component Segmentation v2

YOLO11m-seg candidate trained on PCB-Vision pixel masks and reviewed Tokito polygons. It predicts coarse visible package categories, not exact part numbers or pins. Public semantic regions are converted to instance proposals; touching parts may merge. Scores in REPORT.json are diagnostic, not independent Tokito-board accuracy.
