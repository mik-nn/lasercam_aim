# recognizer.py
"""
Marker Recognizer for LaserCam — Unified Circle + Direction Line Design

Detects solid black circle markers with a white direction line pointing
towards the next marker.

Output: (found: bool, center: (x, y), angle: float, confidence: float)

AICODE-NOTE: Uses inverted threshold + contour detection to find solid
black circles. The white line creates a hole in the black circle, but
the outer contour remains highly circular.
"""
import math
from typing import Optional

import cv2
import numpy as np


class MarkerRecognizer:
    # AICODE-NOTE: area limits are in camera-frame pixels. Calibrate via
    # px_per_mm from camera FOV so mesh holes (>>marker size) are rejected.
    def __init__(
        self,
        min_area_px: float = 50,
        max_area_px: float = 50000,
        circularity_threshold: float = 0.7,
        line_length_min_ratio: float = 0.28,
        line_center_tolerance_ratio: float = 0.4,
    ):
        self._min_area = min_area_px
        self._max_area = max_area_px
        self._circularity_threshold = circularity_threshold
        self._line_length_min_ratio = line_length_min_ratio
        self._line_center_tolerance_ratio = line_center_tolerance_ratio

    def find_marker(self, frame, prefer_shape: Optional[str] = None, exclude_center: Optional[tuple[float, float]] = None, exclude_radius: float = 15.0):
        """
        Finds a circle marker with a direction line in the frame.

        Returns (found, center, shape_type, angle_deg).
        - found: bool
        - center: (x, y) in image coordinates
        - shape_type: always "circle" for the new design
        - angle_deg: direction angle from the white line (0° = east, 90° = south)

        prefer_shape: retained for backward compatibility; always prefers circles.
        exclude_center: (x, y) in image coordinates to ignore.
        exclude_radius: radius in pixels around exclude_center to ignore.
        """
        if frame is None or frame.size == 0:
            return False, None, None, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # AICODE-NOTE: Adaptive thresholding isolates dark features (black
        # circles) from their local background. THRESH_BINARY_INV makes dark
        # regions white in the output. The white direction line becomes a
        # black cut through the white blob, but the outer contour remains
        # highly circular. This works on complex backgrounds (sample cards)
        # where global thresholding would merge the marker with dark areas.
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2,
        )

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        found_markers = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self._min_area or area > self._max_area:
                continue

            peri = cv2.arcLength(contour, True)
            if peri == 0:
                continue

            circularity = 4 * np.pi * area / (peri * peri)
            if circularity < self._circularity_threshold:
                continue

            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]

            # Exclude marker if it's too close to the excluded center
            if exclude_center is not None:
                ex, ey = exclude_center
                if math.sqrt((cx - ex)**2 + (cy - ey)**2) < exclude_radius:
                    continue
            radius = math.sqrt(area / math.pi)

            # Detect the white direction line within this circle
            angle_deg, line_confidence = self._detect_line(
                frame, cx, cy, radius
            )

            if angle_deg is not None:
                # AICODE-NOTE: confidence combines circularity with line
                # detection confidence for overall marker quality score.
                confidence = circularity * line_confidence
                found_markers.append(
                    ((cx, cy), "circle", angle_deg, confidence)
                )

        if not found_markers:
            return False, None, None, None

        # Return the marker with highest confidence
        found_markers.sort(key=lambda m: m[3], reverse=True)
        center, shape_type, angle_deg, confidence = found_markers[0]
        return True, center, shape_type, angle_deg

    def _detect_line(self, frame, cx, cy, radius):
        """
        Detect the white direction line within a detected circle.

        Returns (angle_deg, confidence).
        - angle_deg: direction angle (0° = east, 90° = south)
        - confidence: line detection confidence (0.0 - 1.0)
        """
        if frame is None:
            return None, 0.0

        h, w = frame.shape[:2]

        # Extract ROI around the circle with margin
        margin = int(radius * 0.3)
        x1 = max(0, int(cx - radius - margin))
        y1 = max(0, int(cy - radius - margin))
        x2 = min(w, int(cx + radius + margin))
        y2 = min(h, int(cy + radius + margin))

        if x2 <= x1 or y2 <= y1:
            return None, 0.0

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None, 0.0

        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Threshold to find white regions (the direction line)
        _, white_mask = cv2.threshold(roi_gray, 200, 255, cv2.THRESH_BINARY)

        # Mask to only consider white pixels within the circle
        circle_mask = np.zeros(white_mask.shape[:2], dtype=np.uint8)
        cx_roi = int(cx - x1)
        cy_roi = int(cy - y1)
        cv2.circle(circle_mask, (cx_roi, cy_roi), int(radius), 255, -1)
        white_mask = cv2.bitwise_and(white_mask, white_mask, mask=circle_mask)

        white_contours, _ = cv2.findContours(
            white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not white_contours:
            return None, 0.0

        best_angle = None
        best_confidence = 0.0

        for wc in white_contours:
            wc_area = cv2.contourArea(wc)
            if wc_area < 3:
                continue

            M = cv2.moments(wc)
            if M["m00"] == 0:
                continue

            wc_cx = M["m10"] / M["m00"]
            wc_cy = M["m01"] / M["m00"]

            dx = wc_cx - cx_roi
            dy = wc_cy - cy_roi
            dist = math.sqrt(dx * dx + dy * dy)

            min_dist = radius * self._line_length_min_ratio
            max_dist = radius * 1.1

            if min_dist <= dist <= max_dist:
                angle = math.atan2(dy, dx)
                angle_deg = math.degrees(angle)
                if angle_deg < 0:
                    angle_deg += 360

                optimal_dist = radius * 0.65
                dist_score = 1.0 - abs(dist - optimal_dist) / optimal_dist
                dist_score = max(0.0, min(1.0, dist_score))

                expected_line_area = radius * radius * 0.06
                area_score = min(1.0, wc_area / expected_line_area)

                confidence = dist_score * area_score
                confidence = max(0.0, min(1.0, confidence))

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_angle = angle_deg

        if best_angle is not None and best_confidence > 0.05:
            return best_angle, best_confidence

        return None, 0.0
