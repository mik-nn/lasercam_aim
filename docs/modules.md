# Modules

This document describes all major modules of the LaserCam application, covering both the **MVP implementation (Python)** and the **final implementation (C++/Qt)**.

---

## 1. Camera Module

### Purpose
Provide real-time video frames from the camera, abstracted behind a stable API.

### Responsibilities
- Open the camera device (DirectShow, GigE, or emulator)
- Deliver frames at a stable FPS
- Expose resolution, FOV, and camera parameters
- In MVP: Camera emulator plugin via MeerK40t IPC
- In final tool: Direct camera capture or emulated feed

### Inputs
- Camera device index or emulator connection parameters
- Optional configuration (resolution, exposure, gain)

### Outputs
- Raw frames (RGB or grayscale)
- Camera metadata (resolution, FPS, FOV)

---

## 2. Marker Recognizer

### Purpose
Detect solid circle markers with direction lines in the camera frame and compute their geometric properties.

### Responsibilities
- Locate circle candidates in the image
- Validate circle shape and size
- Detect the white direction line within the circle
- Compute marker center in image coordinates
- Extract direction angle from the line
- Compute confidence score
- Provide stable API: `(found: bool, center: (x, y), angle: float, confidence: float)`

### Inputs
- Current camera frame

### Outputs
- `found: bool`
- `center: (x, y)` in image coordinates
- `angle: float` — direction angle in degrees (0° = east, 90° = south in image coords)
- `confidence: float` — detection confidence score

### Notes
- MVP uses Python + OpenCV for rapid iteration
- Final tool re-implements the stable algorithm in C++ + OpenCV
- Both M1 and M2 use the same marker shape; differentiation is by context

---

## 3. Direction Detection Module

### Purpose
Extract the direction angle from the marker's white line indicator.

### Responsibilities
- Detect the white line within the detected circle
- Calculate the line's angle relative to the circle center
- Convert angle to machine coordinate system
- Validate angle confidence

### Inputs
- Camera frame with detected circle center
- Circle radius and bounding region

### Outputs
- `angle: float` — direction angle in degrees
- `confidence: float` — angle detection confidence

---

## 4. Controller Module

### Purpose
Abstract the control of the laser gantry, whether real or simulated.

### Responsibilities
- Provide a common interface (`BaseController`) for moving the gantry
- `move_to(x, y)`: Move to an absolute position
- `move_by(dx, dy)`: Move by a relative amount
- `move_in_direction(angle, distance)`: Move along a vector
- `position`: Get the current gantry position
- Implement concrete controller classes:
  - `SimulatedController`: Wraps the MeerK40t laser emulator
  - `GRBLController`: Sends G-code commands over serial
  - `RuidaController`: Sends commands over UDP

### Inputs
- For real controllers: port, baud rate, host, etc.
- For simulated controller: MeerK40t emulator connection

### Outputs
- Movement commands to the hardware or emulator
- Position feedback from the hardware or emulator

---

## 5. Calibration Manager

### Purpose
Calibrate and monitor the offset between laser and camera.

### Responsibilities
- Calculate laser-camera offset
- Detect offset changes during carriage movement
- Trigger recalibration when offset changes exceed threshold
- Store and persist calibration data
- Validate calibration accuracy

### Inputs
- Camera position and laser position readings
- Movement history
- Calibration marker detections

### Outputs
- Offset vector (dx, dy) in mm
- Offset change alerts
- Calibration validity status

---

## 6. LightBurn Bridge

### Purpose
Communicate with LightBurn to register marker positions during Print&Cut workflow.

### Responsibilities
- Detect LightBurn window and bring it to focus
- Simulate Alt+1 hotkey to register M1 position
- Simulate Alt+2 hotkey to register M2 position
- In MVP: Fake bridge for development (stdin-based simulation)
- In final tool: WinAPI-based hotkey injection (SendInput)

### Inputs
- Hotkey simulation commands (Alt+1, Alt+2)

### Outputs
- Hotkey events sent to LightBurn window

---

## 7. UI Module

### Purpose
Provide a graphical user interface for camera view, marker detection, and control.

### Responsibilities
- Display the live camera feed (real or emulated)
- Show detected markers with overlays (green circle, zoomed view)
- Display current system state
- Provide approval/cancellation workflow for marker detection
- Show calibration interface
- Provide manual jogging controls (arrows, step size, Go To)
- Display workspace overview (in simulation mode)

### Inputs
- Camera frames
- System state
- Detected marker information (center, angle, confidence)

### Outputs
- User commands (start, confirm, cancel, jog, calibrate, Go To)

### Notes
- MVP uses Tkinter for simplicity
- Final tool uses Qt for a professional UI

### Key UI Elements
- **Camera view**: Live feed with marker overlays
- **Zoomed view**: ~3× crop centered on detected marker with green circle
- **Green circle**: Visual indicator showing detected marker boundary
- **Direction arrow**: Orange arrow showing direction to next marker
- **Jog controls**: Arrow buttons with configurable step size (fine/coarse/large)
- **Go To**: Entry fields for absolute X,Y coordinates
- **Status label**: Current state display
- **Start/Reset buttons**: Begin and reset the workflow

---

## 8. Application Core (State Machine)

### Purpose
Orchestrate the LightBurn Print&Cut workflow: detection → confirmation → registration → navigation.

### Responsibilities
- Manage application state machine
- Coordinate between recognizer, controller, LightBurn bridge, and calibration
- Handle approval/cancellation workflow
- Manage emulator lifecycle
- Error handling and recovery

### State Machine

```
START → SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE → (auto) → START
```

| State | Description | Actions |
|-------|-------------|---------|
| `START` | Initial state, waiting for operator | Show "Start" button |
| `SEARCH_M1` | Reading camera, scanning for M1 | Continuous frame capture, marker detection |
| `CONFIRM_M1` | M1 detected, awaiting approval | Zoomed view, green circle, fine-tune, confirm/cancel |
| `REGISTER_M1` | Move laser to M1 centre, register in LightBurn | Apply offset, move laser, send Alt+1 |
| `SEARCH_M2` | Move toward M2 using direction angle | Autonomous movement, continuous detection |
| `CONFIRM_M2` | M2 detected, awaiting approval | Zoomed view, green circle, fine-tune, confirm/cancel |
| `REGISTER_M2` | Move laser to M2 centre, register in LightBurn | Apply offset, move laser, send Alt+2 |
| `DONE` | Both markers registered | Auto-reset to START |
