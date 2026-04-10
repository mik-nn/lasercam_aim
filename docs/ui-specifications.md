# UI/UX Specifications

## 1. Overview

The LaserCam UI provides a graphical interface for marker detection, approval/cancellation workflow, calibration, and movement control. The MVP uses Tkinter; the final tool uses Qt.

---

## 2. Layout

### 2.1 Main Window

```
┌─────────────────────────────────────────────────────┐
│ LaserCam                                    [─][□][×]│
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────────┐  ┌───────────────────────┐   │
│  │                   │  │                       │   │
│  │                   │  │    Workspace Overview  │   │
│  │   Camera View     │  │    (simulation only)   │   │
│  │                   │  │                       │   │
│  │                   │  │                       │   │
│  └───────────────────┘  └───────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ State: IDLE                                         │
├─────────────────────────────────────────────────────┤
│  [↑]                                                │
│  [←] [→]  0.5 mm/step    [Confirm M1] [Cancel]     │
│  [↓]                                                │
└─────────────────────────────────────────────────────┘
```

### 2.2 Camera View
- Displays live camera feed (real or emulated)
- Overlays detected markers with:
  - Circle outline around detected marker
  - Crosshair at marker center
  - Direction arrow showing angle to next marker
  - Confidence score
- In CONFIRM states: shows zoomed view (~3×) centered on marker

### 2.3 Workspace Overview (Simulation Mode Only)
- Shows full workspace with sample/artwork
- Red rectangle indicates current camera FOV position
- Orange arrow shows navigation direction during M1→M2 movement
- Updates in real-time as gantry moves

---

## 3. State Machine & UI Behaviour

### 3.1 States

| State | Description | Controls Shown |
|-------|-------------|----------------|
| `IDLE` | Waiting for marker detection | Nav arrows (coarse 0.5mm/step) |
| `CONFIRM_M1` | M1 detected, awaiting approval | Nav arrows (fine 0.1mm/step), Confirm M1, Cancel |
| `NAVIGATE_TO_M2` | Auto-moving toward M2 | Cancel only |
| `SEARCH_M2` | M2 not found after navigation | Nav arrows (coarse), Cancel |
| `CONFIRM_M2` | M2 detected, awaiting approval | Nav arrows (fine 0.1mm/step), Confirm M2, Cancel |
| `DONE` | Alignment complete | None (auto-resets to IDLE after 2s) |

### 3.2 State Transitions

```
IDLE ──(M1 detected)──▶ CONFIRM_M1
CONFIRM_M1 ──(user confirms)──▶ NAVIGATE_TO_M2
CONFIRM_M1 ──(user cancels)──▶ IDLE
NAVIGATE_TO_M2 ──(M2 found)──▶ CONFIRM_M2
NAVIGATE_TO_M2 ──(max steps reached)──▶ SEARCH_M2
NAVIGATE_TO_M2 ──(user cancels)──▶ IDLE
SEARCH_M2 ──(M2 detected)──▶ CONFIRM_M2
SEARCH_M2 ──(user cancels)──▶ IDLE
CONFIRM_M2 ──(user confirms)──▶ DONE
CONFIRM_M2 ──(user cancels)──▶ IDLE
DONE ──(2 second delay)──▶ IDLE
```

---

## 4. Visual Overlays

### 4.1 Marker Detection Overlay (IDLE state)
- Green circle (12px radius) around detected marker center
- "Marker Found" text label next to circle

### 4.2 Confirmation Overlay (CONFIRM_M1, CONFIRM_M2)
- **Zoomed view**: ~3× crop centered on marker
- **Shape indicator**: Green circle or rectangle outline matching marker shape
- **Crosshair**: Center lines at marker center
- **Direction arrow**: Orange arrowedLine from center showing direction to next marker
- **Info text**: Direction angle and zoom factor (e.g., "Dir: 157deg [3.0x zoom]")

### 4.3 Navigation Arrow (Overview Canvas)
- Orange arrow from M1 camera position in the direction of M2
- Length: 60px on overview canvas
- Visible only during NAVIGATE_TO_M2 state

---

## 5. Controls

### 5.1 Navigation Arrows
- Four directional buttons: ↑ ↓ ← →
- Step size varies by state:
  - IDLE/SEARCH_M2: 0.5 mm/step (coarse scanning)
  - CONFIRM_M1/CONFIRM_M2: 0.1 mm/step (fine adjustment)
- Each click sends a relative move command to the controller

### 5.2 Confirm Buttons
- **Confirm M1**: Green button, triggers M1→M2 navigation
- **Confirm M2**: Green button, completes alignment
- Only visible in respective CONFIRM states

### 5.3 Cancel Button
- Red button with white text
- Available in all states except IDLE and DONE
- Returns to IDLE state, clears all detection data

---

## 6. Status Display

- Text label showing current state: "State: IDLE"
- Updates immediately on state transitions
- Position: Below camera view, above controls

---

## 7. Calibration Interface (Future)

### 7.1 Calibration Panel
- "Start Calibration" button
- Displays current offset values (dx, dy in mm)
- Shows calibration validity status
- Last calibration timestamp
- Threshold setting (mm)

### 7.2 Calibration Workflow
1. User clicks "Start Calibration"
2. System moves camera to calibration marker
3. Detects marker center
4. Moves laser to same position
5. Calculates and displays offset
6. User confirms or repeats

---

## 8. Error Display

- Error messages shown in status label (red text)
- Examples:
  - "No marker detected"
  - "Movement failed: out of bounds"
  - "Controller disconnected"
  - "Calibration failed: offset change > threshold"

---

## 9. Configuration UI (Future)

- Controller type selection (Simulated / GRBL / RUIDA)
- Camera settings (resolution, FOV)
- Emulator connection settings (host, port)
- Recognizer parameters (min/max area, circularity threshold)
- Calibration settings (threshold, verification interval)

---

## 10. Responsive Design

### 10.1 Camera View Dimensions
- Display canvas: 620×360px (half of 1240×720 sensor, preserves 1.722:1 aspect ratio)
- Overview canvas: 400×400px (square, for workspace visualization)

### 10.2 Minimum Window Size
- Width: 1100px (camera + overview side by side)
- Height: 600px (camera + controls + status)

---

## 11. Accessibility

- All controls have keyboard shortcuts (arrow keys for navigation, Enter for confirm, Escape for cancel)
- High contrast colors for overlays (green, orange, red on dark/light backgrounds)
- Status changes announced via label text updates
