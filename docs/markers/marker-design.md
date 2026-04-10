# Marker Design

## 1. Overview

LaserCam uses a unified marker design for both M1 and M2 markers. Both markers are identical in shape and are differentiated only by position and context within the workflow.

---

## 2. Marker Specification

### 2.1 Shape
- **Form**: Solid black circle
- **Diameter**: 4-6mm (5mm recommended)
- **Fill**: 100% black (CMYK: 0, 0, 0, 100)
- **Stroke**: None

### 2.2 Direction Indicator
- **Form**: White line (solid rectangle) originating from circle center
- **Length**: 1.5-2.0mm (from center to endpoint)
- **Width**: 0.6-0.8mm
- **Color**: 100% white (CMYK: 0, 0, 0, 0)
- **Direction**: Points towards the next marker in the sequence

### 2.3 Canvas
- **Size**: 12x12mm minimum bounding box
- **Background**: White (to ensure contrast with the black circle)
- **Purpose**: Provides clean background for reliable detection

---

## 3. Detection Requirements

### 3.1 Circle Detection
- Must be detectable at camera resolutions from 640x480 to 1920x1080
- Must tolerate up to 15° perspective distortion
- Must be robust to lighting variations and minor print imperfections
- Minimum detectable size: 20 pixels diameter in camera frame

### 3.2 Line Detection
- Must be detectable within the circle region
- Must tolerate partial occlusion (up to 20%)
- Must provide angle accuracy within ±3°
- Line-to-circle area ratio: approximately 0.05-0.10

### 3.3 Robustness
The marker must remain detectable under:
- Uneven lighting
- Slight blur (Gaussian blur σ ≤ 2)
- Minor print distortions (up to 5% size variation)
- Camera noise
- Perspective distortion within reasonable limits

---

## 4. Recognition Output

The recognizer outputs:

```python
(
    found: bool,        # True if marker detected
    center: (x, y),     # Circle center in image coordinates (pixels)
    angle: float,       # Direction angle in degrees (0° = east, 90° = south)
    confidence: float   # Detection confidence (0.0 - 1.0)
)
```

---

## 5. Marker Placement

### 5.1 M1 Marker
- Placed at the first alignment point (typically top-right of artwork)
- Direction line points towards M2

### 5.2 M2 Marker
- Placed at the second alignment point (typically bottom-left of artwork)
- Direction line points towards M1

### 5.3 Placement Guidelines
- Minimum distance from artwork edge: 8mm
- Minimum distance between markers: 50mm
- Both markers must be within camera FOV during detection

---

## 6. Generation

Markers are generated using the `LaserMark.jsx` Adobe Illustrator script:
- Select artwork
- Run script
- Script places M1 and M2 markers at artwork corners with direction lines

See `LaserMark.jsx` for implementation.

---

## 7. Validation

### 7.1 Test Criteria
- Detection rate: ≥ 95% under normal lighting
- False positive rate: ≤ 1%
- Angle accuracy: ±3°
- Center accuracy: ±1 pixel

### 7.2 Test Conditions
- Various lighting conditions (bright, dim, uneven)
- Various print qualities (high, medium, low)
- Various camera distances and angles
- Various background patterns
