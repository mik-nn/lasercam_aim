# recognizer.py
import math

import cv2
import numpy as np


class MarkerRecognizer:
    def __init__(self, min_area_px: float = 50, max_area_px: float = 50000):
        # AICODE-NOTE: area limits are in camera-frame pixels. Calibrate via
        # px_per_mm from camera FOV so mesh holes (>>marker size) are rejected.
        self._min_area = min_area_px
        self._max_area = max_area_px

    def find_marker(self, frame, prefer_shape: str = None):
        """
        Finds a marker in the frame. Supports square and circle shapes.
        Returns (found, center, shape_type, angle_deg).

        prefer_shape: 'square', 'circle', or None.
          None → prefer squares (so IDLE finds M1 when both markers are visible).
          'circle' → prefer circles (use during navigation to M2 / CONFIRM_M2).
        """
        if frame is None or frame.size == 0:
            return False, None, None, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        if hierarchy is None:
            return False, None, None, None

        # AICODE-NOTE: collect ALL valid markers, then prefer squares so the
        # IDLE→CONFIRM_M1 transition triggers even when both markers are visible.
        found_markers = []  # list of (center, shape_type, angle_deg)

        for i, contour in enumerate(contours):
            if hierarchy[0][i][2] == -1:
                continue

            area = cv2.contourArea(contour)
            if area < self._min_area or area > self._max_area:
                continue

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

            is_candidate = False
            shape_type = None
            if len(approx) == 4:
                rect = cv2.minAreaRect(contour)
                (x, y), (w, h), angle = rect
                if h > 0:
                    ar = w / float(h)
                    # AICODE-NOTE: angle from minAreaRect is in [-90, 0).
                    # Mesh-grid holes are ~45°-rotated diamonds → angle ≈ -45°.
                    # Real square markers are axis-aligned (≤30° tilt from axes)
                    # → angle ∈ [-30°, 0°] or [-90°, -60°].
                    # Reject the ±15° band around -45° to filter mesh diamonds.
                    is_diamond_angle = -60 < angle < -30
                    if 0.7 <= ar <= 1.4 and not is_diamond_angle:
                        is_candidate = True
                        shape_type = "square"

            if not is_candidate and peri > 0:
                circularity = 4 * np.pi * area / (peri * peri)
                if circularity > 0.8:
                    is_candidate = True
                    shape_type = "circle"

            if is_candidate:
                child_idx = hierarchy[0][i][2]
                valid_internal = False
                found_cX_c, found_cY_c = None, None

                cX_p, cY_p = self._get_center(contour)[1]
                marker_size = np.sqrt(area)

                while child_idx != -1:
                    child_area = cv2.contourArea(contours[child_idx])
                    ratio = child_area / area

                    if 0.005 < ratio < 0.2:
                        ok, cX_c, cY_c = self._is_valid_internal(
                            contours[child_idx], cX_p, cY_p, marker_size
                        )
                        if ok:
                            valid_internal = True
                            found_cX_c, found_cY_c = cX_c, cY_c
                            break
                    elif ratio >= 0.2:
                        grandchild_idx = hierarchy[0][child_idx][2]
                        while grandchild_idx != -1:
                            grandchild_area = cv2.contourArea(contours[grandchild_idx])
                            g_ratio = grandchild_area / area
                            if 0.005 < g_ratio < 0.2:
                                ok, cX_c, cY_c = self._is_valid_internal(
                                    contours[grandchild_idx], cX_p, cY_p, marker_size
                                )
                                if ok:
                                    valid_internal = True
                                    found_cX_c, found_cY_c = cX_c, cY_c
                                    break
                            grandchild_idx = hierarchy[0][grandchild_idx][0]
                        if valid_internal:
                            break
                    child_idx = hierarchy[0][child_idx][0]

                if valid_internal:
                    # AICODE-NOTE: angle from parent center to internal centroid; 0° = east, 90° = south (image coords)
                    angle_deg = math.degrees(
                        math.atan2(found_cY_c - cY_p, found_cX_c - cX_p)
                    )
                    found_markers.append(((cX_p, cY_p), shape_type, angle_deg))

        if not found_markers:
            return False, None, None, None

        # AICODE-NOTE: prefer_shape='circle' for navigation/CONFIRM_M2 so M2 is
        # found even when M1 (square) is still visible. Default (None) prefers
        # squares so IDLE→CONFIRM_M1 triggers when both markers are in frame.
        preferred = prefer_shape if prefer_shape else "square"
        for center, shape_type, angle_deg in found_markers:
            if shape_type == preferred:
                return True, center, shape_type, angle_deg
        center, shape_type, angle_deg = found_markers[0]
        return True, center, shape_type, angle_deg

    def _is_valid_internal(self, contour, cX_p, cY_p, marker_size):
        """Returns (valid, cX_c, cY_c)."""
        M_c = cv2.moments(contour)
        if M_c["m00"] != 0:
            cX_c = int(M_c["m10"] / M_c["m00"])
            cY_c = int(M_c["m01"] / M_c["m00"])

            dist = np.sqrt((cX_c - cX_p) ** 2 + (cY_c - cY_p) ** 2)
            if dist < marker_size * 0.6:
                return True, cX_c, cY_c
        return False, None, None

    def _get_center(self, contour):
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            return True, (cX, cY)
        return False, None
