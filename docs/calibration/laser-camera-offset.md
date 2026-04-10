# Laser-Camera Offset Calibration

## 1. Overview

The laser and camera are physically offset on the gantry. This offset must be calibrated to ensure accurate alignment between what the camera sees and where the laser cuts.

---

## 2. Material Area

For calibration, a **200×150 mm piece of material** is placed in the center of the workspace. The simulator displays this as a light brown rectangle with a border.

- **Center**: Workspace center (450.0, 300.0) mm for 900×600 mm workspace
- **Size**: 200 × 150 mm
- **Bounds**: (350.0, 225.0) to (550.0, 375.0) mm

---

## 3. Calibration Marker

The calibration uses a dedicated marker different from the workflow markers:

- **Shape**: Black circle with white cross (plus sign) inside
- **Size**: 3mm radius circle, 5mm cross arms
- **Purpose**: Easy to detect and provides precise center point
- **Creation**: Drawn by the laser at a known position on the material

---

## 4. Calibration Procedure

### 4.1 Step-by-Step Process

1. **Move Laser to Material**: Click "Move Laser to Material" — laser moves to the material area
2. **Draw Calibration Marker**: Click "Draw Marker" — laser draws a circle with cross at current position
3. **Record Laser Position**: System automatically records the laser's center position `(lx, ly)`
4. **Move Camera**: User manually jogs the camera until the calibration marker enters the camera's field of view
5. **Detect Marker**: Click "Detect Marker" — system reads the calibration marker position `(cx, cy)`
6. **Calculate Offset**: System calculates:
   ```
   offset_x = lx - cx
   offset_y = ly - cy
   ```
7. **Confirm Calibration**: Review the calculated offset and click "Confirm" to save
8. **Save and Close**: Offset is saved to `lasercam.json` and calibration window closes

### 4.2 UI Flow

```
┌─────────────────────────────────────────┐
│        Calibrate Laser-Camera Offset     │
├─────────────────────────────────────────┤
│                                         │
│  1. Move laser to material area         │
│     [Move Laser to Material]            │
│                                         │
│  2. Draw calibration marker             │
│     [Draw Marker]                       │
│                                         │
│  Laser position: (400.0, 300.0) mm      │
│                                         │
│  3. Move camera until marker visible    │
│     [Detect Marker]                     │
│                                         │
│  Camera position: (400.0, 300.0) mm     │
│                                         │
│  ─────────────────────────────────────  │
│  Calculated Offset:                     │
│  X: 0.0 mm  |  Y: 0.0 mm               │
│                                         │
│  [Confirm]          [Cancel]            │
└─────────────────────────────────────────┘
```

---

## 5. Offset Calculation

### 5.1 Formula

```
offset_x = laser_x - camera_x
offset_y = laser_y - camera_y
```

Where:
- `laser_x, laser_y` = Laser position when calibration marker was drawn
- `camera_x, camera_y` = Camera position when calibration marker was detected

### 5.2 Application

When the camera detects a marker at position `(cx, cy)`, the laser must move to:
```
laser_target_x = cx + offset_x
laser_target_y = cy + offset_y
```

---

## 6. Offset Storage

- Stored in `lasercam.json` as `laser_offset_x` and `laser_offset_y`
- Loaded on application startup
- Applied when moving laser to marker centers during registration
- Displayed on the START screen

---

## 7. Controller Type Configuration

### 7.1 Configuration

The controller type is specified in `lasercam.json`:

```json
{
  "controller": "simulated",
  "grbl_port": "COM3",
  "grbl_baudrate": 115200,
  "ruida_host": "192.168.1.100",
  "ruida_port": 50200,
  "laser_offset_x": 10.0,
  "laser_offset_y": 10.0
}
```

### 7.2 Supported Controller Types

| Type | Description | Connection |
|------|-------------|------------|
| `simulated` | Internal Python simulator | None (in-process) |
| `grbl` | GRBL laser controller | USB Serial (COM port) |
| `ruida` | Ruida laser controller | UDP Network |

### 7.3 Controller Selection

The controller type is displayed on the START screen. To change it:
1. Edit `lasercam.json` manually
2. Set `"controller"` to `"simulated"`, `"grbl"`, or `"ruida"`
3. Restart the application

---

## 8. Validation

### 8.1 Verification Procedure
1. Detect a known marker
2. Move laser to marker center using stored offset
3. Verify laser is at marker center (within tolerance)
4. Report validation result

### 8.2 Acceptance Criteria
- Laser position accuracy: ±0.1mm
- Validation pass rate: ≥ 99%

---

## 9. Configuration

```json
{
  "controller": "simulated",
  "grbl_port": "COM3",
  "grbl_baudrate": 115200,
  "ruida_host": "192.168.1.100",
  "ruida_port": 50200,
  "laser_offset_x": 10.0,
  "laser_offset_y": 10.0,
  "camera_resolution": [1240, 720],
  "camera_fov_mm": [210.0, 122.0],
  "workspace_image": "Workspace90x60cm+sample.png",
  "workspace_pixels_per_mm": 7.874
}
```
