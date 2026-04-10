# Migration Strategy: To LightBurn Print&Cut Workflow

## 1. Current State

The current MVP has:
- Basic marker detection (circle + line)
- Simulated camera and controller
- Tkinter UI with jog controls
- Fake LightBurn bridge (stdin-based)
- State machine: START → SEARCH_M1 → CONFIRM_M1 → ... → DONE

## 2. Target State

The production application integrates with LightBurn's Print&Cut workflow:
- Real camera captures live frames
- Real controller (GRBL/RUIDA) moves the laser
- WinAPI hotkey injection (Alt+1 / Alt+2) registers markers in LightBurn
- Full state machine: SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE
- Calibration system accounts for camera-laser offset

## 3. Feature Mapping

| Current MVP Feature | Production Feature | Notes |
|---------------------|-------------------|-------|
| Camera simulator | Real camera (DirectShow/GigE) | Same API, different backend |
| Simulated controller | GRBL/RUIDA controller | Same BaseController interface |
| Fake LightBurn bridge | WinAPI hotkey injection | Alt+1 / Alt+2 via SendInput |
| Tkinter UI | Qt UI | Same workflow, professional look |
| Emulated markers | Real printed markers | Same marker design |
| Ground-truth detection | OpenCV detection | Same algorithm, real images |

## 4. Migration Steps

### Step 1: Implement Real Camera Backend
- Add DirectShow camera capture (Windows)
- Add GigE camera support (if applicable)
- Keep same `CameraInterface` API
- Test with real printed markers

### Step 2: Implement Real Controller Backends
- Complete GRBL serial communication
- Complete RUIDA UDP communication
- Keep same `BaseController` interface
- Test movement commands with real hardware

### Step 3: Implement WinAPI LightBurn Bridge
- Detect LightBurn window by class name/title
- Bring LightBurn to foreground
- Send Alt+1 via SendInput (register M1)
- Send Alt+2 via SendInput (register M2)
- Handle focus restoration

### Step 4: Implement REGISTER_M1 and REGISTER_M2 States
- REGISTER_M1: Move laser to marker centre (apply offset), send Alt+1
- REGISTER_M2: Move laser to marker centre (apply offset), send Alt+2
- Handle errors (movement failed, LightBurn not found)

### Step 5: Port UI to Qt
- Recreate Tkinter UI in Qt
- Maintain same layout and behaviour
- Add professional styling
- Keep same state machine logic

### Step 6: Port Recognizer to C++
- Reimplement OpenCV detection in C++
- Maintain same API and behaviour
- Optimise for real-time performance

## 5. Backward Compatibility

- Keep emulation system for testing without hardware
- Emulation can be toggled via config (`controller: "simulated"` vs `"grbl"` / `"ruida"`)
- Same marker design across emulation and production
- Same state machine across emulation and production

## 6. Testing During Migration

| Phase | Test |
|-------|------|
| Emulation | Full workflow with simulated camera and controller |
| Real camera | Marker detection with printed markers |
| Real controller | Movement commands and position feedback |
| LightBurn bridge | Alt+1 / Alt+2 registration in LightBurn |
| Full integration | Complete Print&Cut workflow with real hardware |

## 7. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LightBurn window detection fails | Support multiple window titles, manual window selection |
| Hotkey injection blocked | Alternative: clipboard-based coordinate transfer |
| Real camera performance | Optimise detection pipeline, reduce frame resolution |
| Controller communication errors | Retry logic, timeout handling, user notification |
| Calibration drift | Periodic verification, recalibration prompts |
