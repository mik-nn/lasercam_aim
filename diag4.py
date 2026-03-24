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
x1, y1 = max(0, cx - crop_w // 2), max(0, cy - crop_h // 2)
x2, y2 = min(w, cx + crop_w // 2), min(h, cy + crop_h // 2)

crop = img[y1:y2, x1:x2]
frame = cv2.resize(crop, cam_res)
px_per_mm = cam_res[0] / fov_mm[0]

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Expected marker locations based on card bbox (408,258)-(837,462)
# Square marker: top-right corner ~(817, 278)
# Circle marker: bottom-left corner ~(428, 442)
sq_cx, sq_cy = 817, 278
ci_cx, ci_cy = 428, 442

print("ALL contours within 60px of square marker location (817, 278):")
print(f"{'i':>4} {'area':>7} {'cx':>5} {'cy':>5} {'approx_pts':>10} {'rect_ar':>7} {'rect_ang':>9} {'circ':>6} {'children':>8}")
for i, c in enumerate(contours):
    if hierarchy is None:
        break
    area = cv2.contourArea(c)
    if area < 5:
        continue
    M = cv2.moments(c)
    if M["m00"] == 0:
        continue
    ccx = int(M["m10"] / M["m00"])
    ccy = int(M["m01"] / M["m00"])
    dist_sq = np.sqrt((ccx - sq_cx)**2 + (ccy - sq_cy)**2)
    dist_ci = np.sqrt((ccx - ci_cx)**2 + (ccy - ci_cy)**2)
    if dist_sq > 80 and dist_ci > 80:
        continue
    label = "SQ" if dist_sq < 80 else "CI"
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    approx6 = cv2.approxPolyDP(c, 0.06 * peri, True)
    rect = cv2.minAreaRect(c)
    (rx, ry), (rw, rh), rang = rect
    ar = rw / rh if rh > 0 else 0
    circ = 4 * np.pi * area / (peri * peri) if peri > 0 else 0
    children = hierarchy[0][i][2]
    has_children = children != -1
    diamond = -60 < rang < -30
    print(f"{label}{i:>3} {area:>7.0f} {ccx:>5} {ccy:>5} "
          f"{len(approx):>5}/{len(approx6):>4} {ar:>7.2f} {rang:>9.1f} "
          f"{circ:>6.2f} {'YES' if has_children else 'no':>8}")

cv2.imwrite("diag_thresh_card.png",
            thresh[max(0,sq_cy-80):sq_cy+80, max(0,sq_cx-80):sq_cx+80])
cv2.imwrite("diag_thresh_ci.png",
            thresh[max(0,ci_cy-80):ci_cy+80, max(0,ci_cx-80):ci_cx+80])
print("\nSaved thresh crops around marker locations.")
