# ImplementationPlan.md — LaserCam Cleanup & LightBurn Print&Cut Implementation

## Objective

1. Clean up ambiguous, debug, and obsolete files from the project
2. Implement the full LightBurn Print&Cut workflow with REGISTER_M1/REGISTER_M2 states
3. Add WinAPI hotkey injection (Alt+1 / Alt+2) for LightBurn integration
4. Complete the calibration system for camera-laser offset

---

## Phase 1: Cleanup

### Step 1.1: Remove Debug/Diagnostic Files
Delete from root:
- `debug_frame.png`, `debug_thresh.png`
- `diag.py`, `diag2.py`, `diag3.py`, `diag4.py`, `diag_final.py`, `diag5_m2.py`
- `diag_bl_corner.png`, `diag_candidates.png`, `diag_frame.png`, `diag_thresh_card.png`, `diag_thresh_ci.png`, `diag_tr_corner.png`, `diag5_m2_center_crop.png`, `diag5_m2_frame.png`
- `ui_diff.txt`
- `0` (orphaned file)

### Step 1.2: Remove Test Artifacts & Duplicates
Delete from root:
- `test_m1_square.png`, `test_m2_circle.png`, `TestPrint.png`
- `honeycomb.jpeg`, `HoneyComb.jpg` (duplicates)

Delete from mvp/:
- `manual_test_recognizer.py`, `manual_test_simulator.py`

### Step 1.3: Remove Empty/Build Artifact Directories
- `simulator/` — empty directory
- `lasercam.egg-info/` — build artifact
- `mvp/plugins/meerk40t_plugin/lasercam_meerk40t_plugins.egg-info/` — build artifact
- All `__pycache__/` directories
- `.pytest_cache/`

### Step 1.4: Archive Completed Plans
Move `plans/*.md` to `docs/archive/` (they are completed plans)

### Step 1.5: Review Superseded Documentation
Review and either merge or archive:
- `docs/product.md` — likely superseded by `architecture.md`
- `docs/structure.md` — likely superseded by `architecture.md`
- `docs/tech.md` — likely superseded by `architecture.md`
- `docs/vision.md` — likely superseded by `AGENTS.md`
- `docs/simulator.md` — likely superseded by `prototype/meerk40t-integration.md`

---

## Phase 2: LightBurn Print&Cut Workflow Implementation

### Step 2.1: Implement WinAPI LightBurn Bridge
**Target**: `mvp/bridge.py`
**Actions**:
- Implement real WinAPI hotkey injection using `win32gui` + `SendInput`
- Detect LightBurn window by title/class
- Methods: `send_alt_1()`, `send_alt_2()`, `focus_lightburn()`
- Keep FakeLightBurnBridge for development without LightBurn

### Step 2.2: Implement REGISTER_M1 State
**Target**: `mvp/ui.py`
**Actions**:
- Add `REGISTER_M1` state to state machine
- On entry: move laser to marker centre (apply camera-laser offset)
- Send Alt+1 to LightBurn via bridge
- Transition to SEARCH_M2

### Step 2.3: Implement REGISTER_M2 State
**Target**: `mvp/ui.py`
**Actions**:
- Add `REGISTER_M2` state to state machine
- On entry: move laser to marker centre (apply camera-laser offset)
- Send Alt+2 to LightBurn via bridge
- Transition to DONE

### Step 2.4: Update State Machine Transitions
**Target**: `mvp/ui.py`
**New flow**:
```
START → SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE → START
```

### Step 2.5: Add Calibration Offset to Movement
**Target**: `mvp/ui.py`, `mvp/app.py`
**Actions**:
- Store camera-laser offset in application
- When moving laser to marker centre: `laser_pos = camera_pos + offset`
- Add offset configuration to `config.py`

---

## Phase 3: UI Updates for Full Workflow

### Step 3.1: Update State Labels and Controls
**Target**: `mvp/ui.py`
**Actions**:
- Add status text for REGISTER_M1 and REGISTER_M2 states
- Show "Registering M1..." / "Registering M2..." during registration
- Add LightBurn connection status indicator

### Step 3.2: Add Calibration UI
**Target**: `mvp/ui.py`
**Actions**:
- Add "Calibrate" button
- Show current offset values
- Show calibration validity status

---

## Verification

After each phase:
1. `python -m pyright mvp/` — 0 errors
2. `python -m flake8 mvp/` — clean
3. `python -m pytest mvp/tests/ -v` — all pass
4. Manual test: run full workflow with emulator

---

**Status**: Ready for execution
**Next Step**: Phase 1, Step 1.1 — Remove Debug/Diagnostic Files
