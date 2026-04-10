# Emulation System

## 1. Overview

LaserCam uses an emulation system during the MVP phase to test the full LightBurn Print&Cut workflow without physical hardware. The emulation consists of:

1. **Camera Emulator**: Simulates a camera moving over a workspace image, returning the field of view for current coordinates
2. **Laser/Controller Emulator**: Simulates laser movement, position reporting, and gantry control

This allows full workflow testing — marker detection, confirmation, registration, and autonomous navigation — without a real camera or laser controller.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────┐
│                    LaserCam Main App                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ UI Layer │  │ Recognizer│  │ Controller/Calib   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬───────────┘  │
│       │              │                  │              │
│  ┌────▼──────────────▼──────────────────▼───────────┐ │
│  │              Emulation Layer                      │ │
│  └──────────────┬───────────────────┬───────────────┘ │
└─────────────────┼───────────────────┼─────────────────┘
                  │                   │
    ┌─────────────▼─────┐   ┌────────▼──────────────┐
    │ Camera Emulator    │   │ Laser/Controller      │
    │                    │   │ Emulator              │
    │ - Workspace image  │   │ - Gantry position     │
    │ - FOV cropping     │   │ - Movement commands   │
    │ - Marker rendering │   │ - Position feedback   │
    │ - Frame output     │   │ - Laser offset        │
    └────────────────────┘   └───────────────────────┘
```

---

## 3. Camera Emulator

### 3.1 Purpose

Simulates a camera viewing a workspace image. Given the current gantry position, it returns the portion of the workspace image that would be visible through the camera's field of view.

### 3.2 How It Works

1. Load a workspace image (e.g., `Workspace90x60cm+sample.png`)
2. Place markers at known positions in the workspace
3. Given current gantry position (x, y) in mm:
   - Convert to pixel coordinates
   - Crop the workspace image to the camera's FOV
   - Resize to camera resolution
   - Return the frame

### 3.3 API

```python
class CameraSimulator:
    def __init__(self, workspace_image_path, camera_fov, workspace_pixels_per_mm, camera_resolution_px):
        pass

    def get_frame(self):
        """Returns the current camera view based on gantry position."""
        pass

    def find_marker(self, prefer_shape=None):
        """Returns (found, center, shape_type, angle_deg)."""
        pass

    def add_marker(self, x_mm, y_mm, shape_type, target_angle_deg):
        """Adds a marker at the specified workspace position."""
        pass

    def move_to(self, x_mm, y_mm):
        """Moves the gantry to the specified coordinates."""
        pass
```

### 3.4 Configuration

```python
camera_fov=(210.0, 122.0)        # FOV in mm (width, height)
workspace_pixels_per_mm=7.874     # Image resolution
camera_resolution_px=(1240, 720)  # Output frame resolution
```

---

## 4. Laser/Controller Emulator

### 4.1 Purpose

Simulates a laser controller that tracks gantry position and responds to movement commands.

### 4.2 How It Works

1. Maintains current gantry position (x, y) in mm
2. Responds to movement commands:
   - `move_to(x, y)`: Set absolute position
   - `move_by(dx, dy)`: Move relative
   - `move_in_direction(angle, distance)`: Move along a vector
3. Reports current position on request

### 4.3 API

```python
class SimulatedController:
    def __init__(self, simulator):
        pass

    @property
    def position(self):
        """Returns current gantry position (x, y) in mm."""
        pass

    def move_to(self, x_mm, y_mm):
        """Move to absolute position."""
        pass

    def move_by(self, dx_mm, dy_mm):
        """Move by relative amount."""
        pass

    def move_in_direction(self, angle_deg, distance_mm):
        """Move along a vector."""
        pass
```

---

## 5. Synchronization

The camera and controller emulators share the same `MotionSimulator` instance, ensuring:

- Camera FOV is always centred on the current gantry position
- Controller position matches the camera's view centre
- Marker positions are consistent between both emulators
- Laser offset is applied correctly when moving laser to marker centre

---

## 6. Data Formats

### 6.1 Coordinate System
- Origin: Top-left of workspace
- Units: Millimeters
- X-axis: Rightward
- Y-axis: Downward

### 6.2 Frame Format
- Encoding: BGR (OpenCV compatible)
- Resolution: Configurable (default 1240x720)
- Color: BGR

### 6.3 Marker Format
- Solid black circle: 4-6mm diameter
- White direction line: from center pointing to next marker
- Rendered at workspace coordinates

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Camera FOV cropping correctness
- Marker rendering at correct positions
- Position tracking accuracy
- Movement command execution

### 7.2 Integration Tests
- Camera frame matches gantry position
- Marker detection works with emulated frames
- End-to-end workflow: SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2

### 7.3 Performance Tests
- Frame generation latency
- Movement command response time
- Continuous detection performance

---

## 8. Transition to Real Hardware

When transitioning from emulation to real hardware:

1. Replace `CameraSimulator` with a real camera implementation
2. Replace `SimulatedController` with `GRBLController` or `RuidaController`
3. Keep the same API interface — no changes to the application core
4. The LightBurn Bridge remains the same (WinAPI hotkey injection)
