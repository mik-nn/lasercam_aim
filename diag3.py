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

# Find where the white card is (bright region > 200)
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
_, bright = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
cnts, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
card_cnts = [(cv2.contourArea(c), c) for c in cnts if cv2.contourArea(c) > 5000]
card_cnts.sort(reverse=True)
print(f"Bright regions (>200, >5000px²): {len(card_cnts)}")
for a, c in card_cnts[:3]:
    x,y,cw,ch = cv2.boundingRect(c)
    print(f"  area={a:.0f} bbox=({x},{y},{cw},{ch}) -> {cw/px_per_mm:.1f}x{ch/px_per_mm:.1f}mm")

# Look at crop around card area where markers should be
if card_cnts:
    bx, by, bw, bh = cv2.boundingRect(card_cnts[0][1])
    print(f"\nCard bounding box: ({bx},{by}) {bw}x{bh}px")
    print(f"Card size: {bw/px_per_mm:.1f}x{bh/px_per_mm:.1f}mm")
    
    # Check top-right and bottom-left corners for markers
    margin = 60
    # Bottom-left corner (circle marker expected)
    bl_crop = frame[max(0,by+bh-margin):by+bh+margin, max(0,bx-margin):bx+margin]
    # Top-right corner (square marker expected)
    tr_crop = frame[max(0,by-margin):by+margin, max(0,bx+bw-margin):bx+bw+margin]
    
    cv2.imwrite("diag_bl_corner.png", bl_crop)
    cv2.imwrite("diag_tr_corner.png", tr_crop)
    print("Saved corner crops: diag_bl_corner.png, diag_tr_corner.png")
    
    # Run full threshold + contour on a small patch around card corners
    for name, patch_frame in [("BL(circle)", bl_crop), ("TR(square)", tr_crop)]:
        if patch_frame.size == 0:
            continue
        g = cv2.cvtColor(patch_frame, cv2.COLOR_BGR2GRAY)
        bl = cv2.GaussianBlur(g, (5,5), 0)
        th = cv2.adaptiveThreshold(bl, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 2)
        cnts2, hier2 = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        print(f"\n{name} patch {patch_frame.shape[1]}x{patch_frame.shape[0]}px:")
        print(f"  Total contours: {len(cnts2)}")
        if hier2 is not None:
            areas_with_children = sorted([cv2.contourArea(c) for i,c in enumerate(cnts2)
                                         if hier2[0][i][2] != -1 and cv2.contourArea(c) > 5], reverse=True)
            print(f"  With children, area>5: {areas_with_children[:20]}")

# Also: measure actual marker size in workspace pixels directly
print("\n\nWorkspace image marker size analysis:")
print(f"workspace_pixels_per_mm = {ws_px_per_mm:.4f}")
print(f"4mm shape in workspace: {4*ws_px_per_mm:.1f}px")
print(f"0.5mm stroke in workspace: {0.5*ws_px_per_mm:.1f}px -> ceil to {max(1,int(0.5*ws_px_per_mm))}px")
print(f"Outer boundary in workspace: {(4+0.5)*ws_px_per_mm:.1f}px")
print(f"Outer boundary in camera frame ({cam_res[0]}x{cam_res[1]}): {(4+0.5)*ws_px_per_mm*(cam_res[0]/crop_w):.1f}px")
print(f"Expected outer contour area in camera frame: {((4+0.5)*ws_px_per_mm*(cam_res[0]/crop_w))**2:.0f}px^2")
