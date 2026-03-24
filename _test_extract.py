import os
import sys
sys.path.insert(0, '.')

import cv2
import numpy as np

WORKSPACE_BG = "Workspace90x60cm.png"
WORKSPACE_WITH_SAMPLE = "Workspace90x60cm+sample.png"
SAMPLE_FILE = "TestPrint.png"

if os.path.exists(SAMPLE_FILE):
    os.remove(SAMPLE_FILE)

bg = cv2.imread(WORKSPACE_BG)
ws = cv2.imread(WORKSPACE_WITH_SAMPLE)

diff = cv2.absdiff(bg, ws)
mask = (diff.sum(axis=2) > 20).astype(np.uint8)

ys, xs = np.where(mask)
y1, y2 = int(ys.min()), int(ys.max()) + 1
x1, x2 = int(xs.min()), int(xs.max()) + 1

sample_crop = ws[y1:y2, x1:x2].copy()
mask_crop = mask[y1:y2, x1:x2]
output = np.ones_like(sample_crop) * 255
output[mask_crop == 1] = sample_crop[mask_crop == 1]

cv2.imwrite(SAMPLE_FILE, output)
print(f"Saved {SAMPLE_FILE}: shape={output.shape}")
