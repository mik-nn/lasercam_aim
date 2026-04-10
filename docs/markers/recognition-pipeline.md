# Recognition Pipeline

## 1. Overview

The recognition pipeline processes camera frames to detect solid circle markers with direction lines and outputs structured detection results.

---

## 2. Pipeline Stages

```
Camera Frame → Preprocessing → Circle Detection → Line Detection → Angle Calculation → Output
```

---

## 3. Stage 1: Preprocessing

### 3.1 Input
- Raw camera frame (BGR, any resolution)

### 3.2 Processing
1. **Resize** (if needed) to processing resolution
   - Target: frame width where 5mm marker ≈ 30-50 pixels
2. **Convert to grayscale**
3. **Gaussian blur** (5x5 kernel, σ=1) to reduce noise
4. **Adaptive thresholding**
   - Method: ADAPTIVE_THRESH_GAUSSIAN_C
   - Type: THRESH_BINARY_INV
   - Block size: 11
   - C: 2

### 3.3 Output
- Binary image (thresholded)
- Original grayscale image (for later stages)

---

## 4. Stage 2: Circle Detection

### 4.1 Method: Contour-Based Detection

1. **Find contours** in the thresholded image
   - Mode: RETR_TREE (nested contours for internal structure)
   - Method: CHAIN_APPROX_SIMPLE

2. **Filter contours** by area
   - Minimum area: (1.5mm × pixels_per_mm)²
   - Maximum area: (6.0mm × pixels_per_mm)²

3. **Check circularity**
   - `circularity = 4π × area / perimeter²`
   - Accept if circularity > 0.8

4. **Validate internal structure**
   - Check for child contours (the white line creates internal contours)
   - Valid marker has at least one child contour within the circle

### 4.2 Alternative Method: Hough Circles

1. Apply HoughCircles with parameters tuned for 4-6mm markers
2. Filter results by radius range
3. Validate each candidate by checking for the white line

### 4.3 Output
- List of detected circles: `[(center_x, center_y, radius), ...]`

---

## 5. Stage 3: Line Detection

For each detected circle:

### 5.1 Extract ROI
- Crop square region: center ± radius
- Add 20% margin for line detection

### 5.2 Preprocess ROI
- Convert to grayscale (if not already)
- Apply thresholding to isolate white line

### 5.3 Detect Line
- Use Hough Line Transform or contour analysis
- Filter lines:
  - Must pass near circle center (within radius/3)
  - Must extend outward from center
  - Must be within circle boundary

### 5.4 Output
- For each circle: `(line_angle, line_confidence)` or `None`

---

## 6. Stage 4: Angle Calculation

### 6.1 Processing
- For each circle with a detected line:
  - Calculate angle from circle center to line endpoint
  - `angle = atan2(dy, dx)` in image coordinates
  - Convert to degrees
  - Normalize to 0-360° range

### 6.2 Confidence Calculation
- Based on:
  - Circle detection confidence (circularity score)
  - Line detection confidence (line strength, proximity to center)
  - Combined: `confidence = circle_conf × line_conf`

---

## 7. Stage 5: Output

### 7.1 Format
```python
(
    found: bool,        # True if at least one marker detected
    center: (x, y),     # Best marker center in image coordinates
    angle: float,       # Direction angle in degrees
    confidence: float   # Combined confidence score (0.0 - 1.0)
)
```

### 7.2 Multiple Markers
- If multiple markers are detected, return the one with highest confidence
- Optionally return all detections for debugging

---

## 8. Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_area_px` | Calculated | Minimum contour area in pixels |
| `max_area_px` | Calculated | Maximum contour area in pixels |
| `circularity_threshold` | 0.8 | Minimum circularity score |
| `line_length_min` | 0.5 × radius | Minimum detected line length |
| `line_center_tolerance` | radius / 3 | Max distance from center to line |
| `blur_kernel` | (5, 5) | Gaussian blur kernel size |
| `threshold_block` | 11 | Adaptive threshold block size |
| `threshold_c` | 2 | Adaptive threshold constant |

---

## 9. Performance

- Target: < 50ms per frame at 1920x1080
- Memory: < 100MB
- CPU: Single-threaded processing

---

## 10. Error Handling

| Error | Response |
|-------|----------|
| No circles detected | Return `(False, None, None, 0.0)` |
| Circle detected but no line | Return `(True, center, None, circle_conf)` |
| Multiple markers | Return highest confidence marker |
| Low confidence (< 0.5) | Flag for user review |
| Frame is None/empty | Return `(False, None, None, 0.0)` |
