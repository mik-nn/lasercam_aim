# Architecture

## 1. Overview

LaserCam is a marker-based laser alignment application that automates the Print&Cut workflow for laser cutters. It:

- Automatically locates printed markers and determines the direction to the next marker
- Displays detected markers in a zoomed view with a green circle overlay for visual verification
- Allows the user to fine-tune position, confirm, or cancel marker detection
- Moves the laser to the centre of each confirmed marker (accounting for camera-laser offset)
- Registers marker positions in LightBurn by simulating Alt+1 / Alt+2 hotkeys
- Navigates autonomously from M1 to M2 using the direction line on the marker
- Calibrates and monitors the offset between laser and camera

The system is developed in two stages:

- **MVP (Python):** Rapid experimentation using a simulated workspace and camera emulator
- **Final tool (C++/Qt):** Production-ready standalone application with identical external behaviour

---

## 2. LightBurn Print&Cut Workflow

### 2.1 Operator Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Operator Workflow                           │
│                                                                 │
│  1. Operator positions camera over M1 (via jog / LightBurn)     │
│  2. Selects "Register M1" in LightBurn Print&Cut                │
│  3. LaserCam detects marker, shows zoomed view + green circle   │
│  4. Operator fine-tunes position if needed                      │
│  5. Operator confirms → LaserCam moves laser to marker centre   │
│  6. LaserCam sends Alt+1 to LightBurn (registers M1)            │
│                                                                 │
│  7. Operator selects "Register M2" in LightBurn Print&Cut       │
│  8. LaserCam determines direction from M1's marker line         │
│  9. LaserCam moves camera toward M2 autonomously                │
│ 10. M2 enters FOV → LaserCam detects, shows zoomed view         │
│ 11. Operator fine-tunes, confirms                              │
│ 12. LaserCam moves laser to M2 centre, sends Alt+2 to LightBurn │
│                                                                 │
│  13. LightBurn now has both registration points → ready to cut  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. State Machine

```
                         ┌──────────────┐
                         │    START     │  ← Initial state, controller connected
                         └──────┬───────┘
                                │ operator clicks "Connect & Start"
                                ▼
                         ┌──────────────┐
               ┌────────│  SEARCH_M1   │  ← Find M1 marker in camera FOV
               │        └──────┬───────┘
               │               │ marker detected → camera auto-centers
               │               ▼
               │        ┌──────────────┐
               │        │  CONFIRM_M1  │  ← Zoomed view, green circle overlay
               │        │              │     Operator fine-tunes with arrow keys
               │        └──────┬───────┘
               │               │ confirmed
               │               ▼
               │        ┌──────────────┐
               │        │  REGISTER_M1 │  ← Move laser to M1 center
               │        │              │     Send Alt+1 to LightBurn
               │        └──────┬───────┘
               │               │ registered
               │               ▼
               │        ┌──────────────┐
               │        │  SEARCH_M2   │  ← Navigate toward M2 using direction
               │        │              │     Camera auto-centers when M2 found
               │        └──────┬───────┘
               │               │ M2 detected → camera auto-centers
               │               ▼
               │        ┌──────────────┐
               │        │  CONFIRM_M2  │  ← Zoomed view, green circle overlay
               │        │              │     Operator fine-tunes with arrow keys
               │        └──────┬───────┘
               │               │ confirmed
               │               ▼
               │        ┌──────────────┐
               │        │  REGISTER_M2 │  ← Move laser to M2 center
               │        │              │     Send Alt+2 to LightBurn
               │        └──────┬───────┘
               │               │ registered
               │               ▼
               │        ┌──────────────┐
               │        │    DONE       │  ← Both markers registered
               │        └──────┬───────┘
               │               │ auto-reset
               └───────────────┘
```

---

## 4. Staged Architecture

### 4.1 MVP Architecture (Python)

**Goals:**
- Rapid experimentation with marker design and detection algorithms
- Validate the full LightBurn Print&Cut workflow with emulation
- Test controller communication and LightBurn hotkey simulation

**Main components:**

- **Marker Recognizer (Python + OpenCV):**
  - Detects solid circle markers with direction lines
  - Computes marker center and direction angle
  - API: `(found: bool, center: (x, y), angle: float, confidence: float)`

- **Camera Emulator:**
  - Simulates a camera moving over a workspace image
  - Returns the camera's field of view for current coordinates
  - Renders markers at known positions in the workspace

- **Laser/Controller Emulator:**
  - Simulates laser movement and position reporting
  - Tracks gantry position in machine coordinates
  - Provides movement commands (absolute, relative, direction-based)

- **LightBurn Bridge:**
  - Simulates Alt+1 / Alt+2 hotkey injection into LightBurn
  - On Windows: uses WinAPI (win32gui, SendInput)
  - During development: fake bridge for testing

- **Calibration Manager:**
  - Laser-camera offset calculation
  - Offset change detection during movement
  - Recalibration triggers

- **UI (Tkinter → Qt):**
  - Camera preview with marker overlays
  - Zoomed view with green circle on detection
  - Direction indicators
  - Approve/Cancel workflow
  - Movement controls (jog arrows, step size, Go To)

---

### 4.2 Final Architecture (C++/Qt)

**Goals:**
- High performance and robustness
- Standalone tool with stable external contract
- Same behaviour as MVP, implemented in native code

**Main components:**

- **Core Recognizer (C++ + OpenCV):**
  - Circle detection + line angle extraction
  - Same detection semantics as MVP
  - Real-time camera frame processing

- **Controller Layer:**
  - RUIDA UDP protocol implementation
  - GRBL serial protocol implementation
  - Common abstraction interface

- **LightBurn Integration:**
  - WinAPI hotkey injection (Alt+1 / Alt+2)
  - LightBurn window detection and focus management

- **Calibration System:**
  - Offset calculation and storage
  - Change detection during carriage movement
  - Validation procedures

- **UI (Qt):**
  - Modern camera preview with overlays
  - Zoomed view with green circle on detection
  - Direction indicators and approval workflow
  - Calibration interface
  - Movement controls

---

## 5. Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    LightBurn Print&Cut                        │
│                                                               │
│  Operator selects "Register M1" in LightBurn                  │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐                                              │
│  │  SEARCH_M1  │  ← LaserCam reads camera frames continuously │
│  └──────┬──────┘                                              │
│         │ marker detected                                     │
│         ▼                                                     │
│  ┌──────────────┐                                             │
│  │  CONFIRM_M1  │  ← Zoomed view, green circle, fine-tune     │
│  └──────┬───────┘                                             │
│         │ operator confirms                                   │
│         ▼                                                     │
│  ┌───────────────┐                                            │
│  │  REGISTER_M1  │  ← Move laser to marker centre             │
│  │               │     Apply camera-laser offset              │
│  │               │     Send Alt+1 to LightBurn                │
│  └──────┬────────┘                                            │
│         │                                                     │
│         ▼                                                     │
│  Operator selects "Register M2" in LightBurn                  │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐                                             │
│  │  SEARCH_M2   │  ← Move toward M2 using direction angle     │
│  │              │     Read camera until M2 enters FOV          │
│  └──────┬───────┘                                             │
│         │ M2 detected                                         │
│         ▼                                                     │
│  ┌──────────────┐                                             │
│  │  CONFIRM_M2  │  ← Zoomed view, green circle, fine-tune     │
│  └──────┬───────┘                                             │
│         │ operator confirms                                   │
│         ▼                                                     │
│  ┌───────────────┐                                            │
│  │  REGISTER_M2  │  ← Move laser to marker centre             │
│  │               │     Apply camera-laser offset              │
│  │               │     Send Alt+2 to LightBurn                │
│  └───────────────┘                                            │
│                                                               │
│  LightBurn has both registration points → ready to cut        │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         UI Layer                             │
│  Camera Preview | Zoomed View | Green Circle | Approve/Cancel│
│  Jog Controls | Step Size | Go To | Status                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Application Core                          │
│  State Machine: SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 →       │
│                SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE   │
└───────┬──────────────────────┬──────────────────────────────┘
        │                      │
┌───────▼──────┐    ┌──────────▼──────────┐
│  Recognizer  │    │  Calibration Manager │
│  Circle+Line │    │  Offset Detection    │
└───────┬──────┘    └──────────┬──────────┘
        │                      │
┌───────▼──────┐    ┌──────────▼──────────┐
│    Camera    │    │    Controller Layer  │
│  (Real/Emu)  │    │  RUIDA | GRBL | Sim  │
└──────────────┘    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   LightBurn Bridge   │
                    │  Alt+1 / Alt+2 (Win) │
                    └─────────────────────┘
```

---

## 7. Marker Design

- **Shape**: Solid black circle (4-6mm diameter)
- **Direction indicator**: White line from center pointing towards the next marker
- **Recognition**: Circle detection + line angle extraction
- **Output**: `(found: bool, center: (x, y), angle: float, confidence: float)`

Both M1 and M2 markers use the same shape. Differentiation is by position/context, not shape.

See `markers/marker-design.md` for full specification.

---

## 8. Emulation System

The MVP uses two emulators for development without physical hardware:

1. **Camera Emulator**: Simulates a camera moving over a workspace image, returning the FOV for current coordinates
2. **Laser/Controller Emulator**: Simulates laser movement, position reporting, and gantry control

The camera emulator renders markers at known positions in the workspace and returns the appropriate FOV image based on the current gantry position.

See `prototype/meerk40t-integration.md` for full specification.

---

## 9. Controller Support

- **RUIDA**: UDP-based protocol for Ruida controllers
- **GRBL**: Serial-based protocol for GRBL controllers
- Both share a common `BaseController` abstraction interface

See `controllers/ruida-protocol.md` and `controllers/grbl-protocol.md`.

---

## 10. Calibration System

The application calibrates and monitors the offset between laser and camera:

- Offset calculation algorithm
- Offset change detection during carriage movement
- Recalibration triggers
- Validation and verification methods

This is critical because the camera and laser are physically offset — when the camera sees a marker at position (x, y), the laser must move to (x + offset_x, y + offset_y) to be at the same physical location.

See `calibration/laser-camera-offset.md` for full specification.

---

## 11. M1/M2 Marker Exclusion

### Problem
Both M1 and M2 markers are identical solid black circles with white direction lines. When the camera moves toward M2 after registering M1, both markers may be in the field of view simultaneously. Without proper exclusion, the system may detect M1 and mistakenly treat it as M2.

### Solution
The system tracks the **actual world position** of M1 when it is confirmed, then excludes any marker within 15mm of that position during M2 search.

### How It Works

1. **M1 Confirmation**: When the user confirms M1, the system:
   - Stores the camera position (`m1_camera_pos`)
   - Calculates the **actual M1 marker position in world coordinates** (`m1_marker_pos`) using:
     - Camera position
     - Camera FOV dimensions
     - Marker center in image coordinates (pixels)
     - Pixels-per-mm conversion

2. **M2 Search**: During navigation toward M2, the `find_marker()` method:
   - Receives `exclude_position=m1_marker_pos`
   - Calculates Euclidean distance from each detected marker to M1's world position
   - Excludes any marker within **15mm** of M1
   - Returns the closest non-excluded marker (M2)

3. **Distance Threshold**: 15mm is chosen because:
   - M1 and M2 are typically 50-100mm apart
   - 15mm is larger than the marker diameter (5mm) plus tolerance
   - Small enough to not accidentally exclude M2

### Code Flow
```
confirm_m1() → calculates m1_marker_pos from image coords → world coords
_register_m1() → moves laser, sends Alt+1
_nav_step() → moves camera, calls find_marker(exclude_position=m1_marker_pos)
find_marker() → excludes markers within 15mm of m1_marker_pos → returns M2
```

### Edge Cases
- **Both markers in FOV**: M1 excluded by distance, M2 detected
- **Only M1 in FOV**: M1 excluded, no marker found → continue navigation
- **Only M2 in FOV**: M2 detected (distance to M1 > 15mm)
- **M1 position unknown**: Falls back to camera position for exclusion
