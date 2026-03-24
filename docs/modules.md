# Modules

This document describes all major modules of the Marker Alignment Tool.
It covers both the **MVP implementation (Python)** and the **final implementation (C/C++/Qt)**, while keeping the external behaviour identical across both stages.

---

## 1. Camera Module

### Purpose
Provide real‑time video frames from the GigE camera using DirectShow, abstracted behind a stable API.

### Responsibilities
- Open the camera as a DirectShow video device.
- Deliver frames at a stable FPS.
- Expose resolution, FOV, and camera parameters.
- Provide timestamps for synchronization.
- In MVP: Python `cv2.VideoCapture(..., cv2.CAP_DSHOW)`.
- In final tool: DirectShow or Media Foundation capture in C/C++.

### Inputs
- Device index or DirectShow device name.
- Optional configuration (resolution, exposure, gain).

### Outputs
- Raw frames (RGB or grayscale).
- Camera metadata (resolution, FPS).

---

## 2. Marker Recognizer

### Purpose
Detect custom printed markers in the camera frame and compute their geometric properties.

### Responsibilities
- Locate marker candidates in the image.
- Validate marker shape and pattern.
- Compute marker center in image coordinates.
- Optionally compute orientation and confidence.
- Provide a stable API for “marker found / not found”.

### Inputs
- Current camera frame.

### Outputs
- `found: bool`
- `center: (x, y)` in image coordinates
- `orientation` (optional)
- `confidence` score

### Notes
- MVP uses Python + OpenCV for rapid iteration.
- Final tool re‑implements the stable algorithm in C/C++.

---

## 3. Motion Simulator

### Purpose
Simulate gantry movement, camera position, and laser offset during MVP development.

### Responsibilities
- Represent virtual X/Y coordinates of the gantry.
- Represent camera offset relative to the laser.
- Render camera FOV over a virtual work area.
- Visualize where the laser would cut relative to printed artwork.

### Inputs
- Target coordinates.
- Virtual work area image.
- Camera FOV parameters.

### Outputs
- Updated simulated positions.
- Visualization overlays.

### Notes
- This module provides the "physics" of the simulated world. Movement commands are issued by a `Controller`.

---

## 4. Controller Module

### Purpose
Abstract the control of the machine's gantry, whether real or simulated.

### Responsibilities
- Provide a common interface (`BaseController`) for moving the gantry.
- `move_to(x, y)`: Move to an absolute position.
- `move_by(dx, dy)`: Move by a relative amount.
- `position`: Get the current gantry position.
- Implement concrete controller classes:
    - `SimulatedController`: Wraps the `MotionSimulator` to move the virtual gantry.
    - `GRBLController`: Sends G-code commands over a serial port.
    - `RuidaController`: Sends commands over UDP to a Ruida controller.

### Inputs
- For real controllers: port, baud rate, host, etc.
- For simulated controller: an instance of `MotionSimulator`.

### Outputs
- Movement commands to the hardware or simulator.
- Position feedback from the hardware or simulator.

### Notes
- The UI and other high-level components only interact with the `BaseController` interface, making the application hardware-agnostic.

---

## 5. LightBurn Bridge

### Purpose
Integrate with LightBurn’s Print & Cut workflow by detecting user actions and maintaining alignment state.

### Responsibilities
- Detect LightBurn main window (PID + EnumWindows).
- Track when LightBurn is the active window.
- Intercept Alt+F1 (and other Print & Cut hotkeys).
- Maintain Print & Cut state machine:
- `idle`
- `first_marker`
- `second_marker`
- `ready`
- Notify the rest of the system when the user selects a marker in LightBurn.

### Inputs
- User hotkey presses.
- Window focus events.

### Outputs
- State change notifications.

### Notes
- Requires platform-specific code for window and keyboard monitoring (e.g., `pywin32` on Windows).
- Final tool will use Qt's event handling.

---

## 6. UI Module

### Purpose
Provide a graphical user interface for camera view, status, and manual control.

### Responsibilities
- Display the live camera feed.
- Show the current system state (e.g., "IDLE", "CONFIRM_M1").
- Provide manual jogging controls.
- Display an overview of the workspace (in simulation).
- Allow the user to confirm or cancel marker detection.

### Inputs
- Camera frames.
- System state.
- Detected marker information.

### Outputs
- User commands (e.g., jog, confirm, cancel).

### Notes
- MVP uses Python's `tkinter` for simplicity.
- Final tool will be built with Qt for a more robust and professional UI.
