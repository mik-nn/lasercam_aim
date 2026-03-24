import cv2
import numpy as np
import os

img_path = "Workspace90x60cm+Sample.png"
img = cv2.imread(img_path)
if img is None:
    print("NOT FOUND:", img_path)
    print("Available PNGs:", [f for f in os.listdir(".") if f.lower().endswith(".png")])
    exit()

h, w = img.shape[:2]
print(f"Workspace image: {w}x{h} px")

# Config
fov_mm = (210.0, 122.0)
cam_res = (1240, 720)
ws_px_per_mm = w / 900.0  # if image is 900mm wide
print(f"Inferred ws_px_per_mm: {ws_px_per_mm:.4f}")

cam_start = (780.0, 493.0)
crop_w = int(fov_mm[0] * ws_px_per_mm)
crop_h = int(fov_mm[1] * ws_px_per_mm)
cx = int(cam_start[0] * ws_px_per_mm)
cy = int(cam_start[1] * ws_px_per_mm)
x1 = max(0, cx - crop_w // 2)
x2 = min(w, cx + crop_w // 2)
y1 = max(0, cy - crop_h // 2)
y2 = min(h, cy + crop_h // 2)
print(f"Crop at camera ({cam_start}): [{x1}:{x2}, {y1}:{y2}] = {x2-x1}x{y2-y1}px")

crop = img[y1:y2, x1:x2]
frame = cv2.resize(crop, cam_res)
cv2.imwrite("diag_frame.png", frame)
print(f"Camera frame saved: diag_frame.png")

# Measure contours in this frame
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

areas = []
if hierarchy is not None:
    for i, c in enumerate(contours):
        if hierarchy[0][i][2] == -1:
            continue
        a = cv2.contourArea(c)
        if a > 50:
            areas.append(a)

areas.sort()
print(f"\nContour areas (with children, >50px^2): {len(areas)} found")
if areas:
    print(f"  Min: {areas[0]:.0f}, Max: {areas[-1]:.0f}, Median: {areas[len(areas)//2]:.0f}")
    buckets = {}
    for a in areas:
        key = int(a / 500) * 500
        buckets[key] = buckets.get(key, 0) + 1
    for k in sorted(buckets):
        print(f"  {k:5d}-{k+499:5d} px^2: {buckets[k]} contours")

# Mark marker 4mm at cam calibration
px_per_mm_cam = cam_res[0] / fov_mm[0]
marker_4mm_area = (4.5 * px_per_mm_cam) ** 2
max_6mm = (6.0 * px_per_mm_cam) ** 2
print(f"\nCamera px_per_mm: {px_per_mm_cam:.3f}")
print(f"Expected 4mm marker outer contour area: {marker_4mm_area:.0f} px^2")
print(f"Max area threshold (6mm): {max_6mm:.0f} px^2")
