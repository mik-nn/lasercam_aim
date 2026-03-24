import cv2
import numpy as np

img = cv2.imread("Workspace90x60cm+Sample.png")
h, w = img.shape[:2]
ws_px_per_mm = w / 900.0

fov_mm = (210.0, 122.0)
cam_res = (1240, 720)
cam_start = (780.0, 493.0)

crop_w = int(fov_mm[0] * ws_px_per_mm)
crop_h = int(fov_mm[1] * ws_px_per_mm)
cx = int(cam_start[0] * ws_px_per_mm)
cy = int(cam_start[1] * ws_px_per_mm)
x1 = max(0, cx - crop_w // 2)
y1 = max(0, cy - crop_h // 2)
x2 = min(w, cx + crop_w // 2)
y2 = min(h, cy + crop_h // 2)

crop = img[y1:y2, x1:x2]
frame = cv2.resize(crop, cam_res)

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
px_per_mm = cam_res[0] / fov_mm[0]
max_6mm = (6.0 * px_per_mm) ** 2
min_1mm = (1.0 * px_per_mm) ** 2

print(f"Total contours: {len(contours)}")
print(f"px_per_mm={px_per_mm:.3f}, min_area={min_1mm:.0f}, max_area={max_6mm:.0f}\n")

debug_img = frame.copy()
candidates = []

for i, contour in enumerate(contours):
    if hierarchy is None or hierarchy[0][i][2] == -1:
        continue
    area = cv2.contourArea(contour)
    if area < min_1mm or area > max_6mm:
        continue

    M = cv2.moments(contour)
    if M["m00"] == 0:
        continue
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

    # Interior brightness (mean of pixels inside contour in original gray)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    mean_val = cv2.mean(gray, mask=mask)[0]

    shape = "?"
    angle = 0
    is_sq = False
    if len(approx) == 4:
        rect = cv2.minAreaRect(contour)
        _, (rw, rh), rect_angle = rect
        ar = rw / float(rh) if rh > 0 else 0
        is_diamond = -60 < rect_angle < -30
        if 0.7 <= ar <= 1.4 and not is_diamond:
            shape = "SQUARE"
            is_sq = True
            angle = rect_angle
    elif peri > 0:
        circ = 4 * np.pi * area / (peri * peri)
        if circ > 0.8:
            shape = "CIRCLE"

    if shape != "?":
        candidates.append((cX, cY, area, shape, mean_val, angle))
        color = (0, 255, 0) if mean_val > 100 else (0, 0, 255)
        cv2.drawContours(debug_img, [contour], -1, color, 2)
        cv2.putText(debug_img, f"{area:.0f}b{mean_val:.0f}", (cX, cY),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

cv2.imwrite("diag_candidates.png", debug_img)
print(f"Candidates (area-filtered, shaped): {len(candidates)}")
print(f"{'x':>5} {'y':>5} {'area':>7} {'shape':>7} {'interior':>8} {'angle':>7}")
for c in sorted(candidates, key=lambda x: x[2]):
    print(f"{c[0]:>5} {c[1]:>5} {c[2]:>7.0f} {c[3]:>7} {c[4]:>8.1f} {c[5]:>7.1f}")

print("\nBright interior (>150) = likely on white card:")
bright = [c for c in candidates if c[4] > 150]
print(f"  {len(bright)} candidates")
for c in bright:
    print(f"  ({c[0]},{c[1]}) area={c[2]:.0f} shape={c[3]} interior={c[4]:.1f}")
