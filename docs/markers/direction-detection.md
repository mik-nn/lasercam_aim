# Direction Detection

## 1. Overview

The direction detection module extracts the angle of the white direction line within a detected circle marker. This angle indicates the direction from the current marker to the next marker in the sequence.

---

## 2. Algorithm

### 2.1 Input
- Camera frame (BGR)
- Detected circle center (cx, cy)
- Detected circle radius r

### 2.2 Processing Steps

1. **Extract Region of Interest (ROI)**
   - Crop a square region centered on the circle with side length = 2r
   - This isolates the marker from the rest of the frame

2. **Preprocess ROI**
   - Convert to grayscale
   - Apply adaptive thresholding (binary inverse)
   - The white line becomes a bright region on a dark background

3. **Detect Line**
   - Use morphological operations to enhance the line:
     - Apply a line-shaped kernel oriented at multiple angles
     - Or use Hough Line Transform on the thresholded ROI
   - Filter detected lines:
     - Must pass near the circle center (within r/3)
     - Must extend outward from center (length > r/2)
     - Must be within the circle boundary

4. **Calculate Angle**
   - From the best-fit line, compute the angle from circle center to line endpoint
   - `angle = atan2(y_endpoint - cy, x_endpoint - cx)`
   - Convert to degrees: `angle_deg = degrees(angle)`
   - Normalize to 0-360° range

### 2.3 Output
- `angle: float` — Direction angle in degrees
  - 0° = east (right)
  - 90° = south (down)
  - 180° = west (left)
  - 270° = north (up)
- `confidence: float` — Line detection confidence (0.0 - 1.0)

---

## 3. Coordinate Systems

### 3.1 Image Coordinates
- Origin: Top-left corner of frame
- X-axis: Rightward (increasing column index)
- Y-axis: Downward (increasing row index)
- Angle: 0° = east, increasing clockwise

### 3.2 Machine Coordinates
- Origin: Machine home position
- X-axis: Rightward
- Y-axis: Forward (away from machine)
- Angle: 0° = machine X+, increasing counter-clockwise

### 3.3 Conversion
- Image angle → Machine angle requires calibration
- Account for camera orientation relative to machine axes
- Store conversion matrix in calibration data

---

## 4. Error Handling

### 4.1 No Line Detected
- Return `angle: None, confidence: 0.0`
- Log warning with frame snapshot
- Retry with adjusted parameters

### 4.2 Multiple Lines Detected
- Select the line closest to the expected direction
- Use previous angle as hint (if available)
- Return the most confident detection

### 4.3 Low Confidence
- If confidence < 0.5, flag for user review
- Suggest manual angle input as fallback

---

## 5. Performance Requirements

- Processing time: < 10ms per frame
- Memory: Minimal (ROI is small)
- Accuracy: ±3° under normal conditions

---

## 6. Validation

### 6.1 Test Cases
- Line at 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°
- Various line lengths (1.5mm, 2.0mm, 2.5mm)
- Various line widths (0.6mm, 0.8mm, 1.0mm)
- Partial occlusion (10%, 20%, 30%)
- Lighting variations (bright, dim, uneven)

### 6.2 Acceptance Criteria
- Angle accuracy: ±3° for 95% of detections
- Detection rate: ≥ 95% under normal conditions
- False positive rate: ≤ 2%
