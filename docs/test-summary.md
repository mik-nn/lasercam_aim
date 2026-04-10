# test-summary.md — Test Results Summary

Generated: 2026-04-10

## Overall Results

- **Total tests**: 106
- **Passed**: 106
- **Failed**: 0
- **Pyright errors**: 0
- **Flake8 violations**: 0

## Test Breakdown

### Unit Tests (76)

| Module | Tests | Status |
|--------|-------|--------|
| `test_app.py` | 2 | All passed |
| `test_bridge.py` | 5 | All passed |
| `test_camera.py` | 3 | All passed |
| `test_camera_simulator.py` | 5 | All passed |
| `test_camera_emulator.py` | 9 | All passed |
| `test_controller.py` | 20 | All passed |
| `test_laser_emulator.py` | 10 | All passed |
| `test_recognizer.py` | 15 | All passed |
| `test_simulator.py` | 7 | All passed |
| `test_ui.py` | 5 | All passed |

### End-to-End Tests (30)

| Suite | Tests | Status |
|-------|-------|--------|
| `test_full_workflow.py` | 10 | All passed |
| `test_plugin_integration.py` | 13 | All passed |

#### E2E: Full Workflow (10 tests)
- `test_detect_m1_at_position` — Detects M1 marker at known coordinates
- `test_detect_m2_at_position` — Detects M2 marker at known coordinates
- `test_no_marker_in_empty_area` — Returns not-found in empty workspace
- `test_move_to_and_verify_position` — Absolute movement verification
- `test_move_by_relative` — Relative movement verification
- `test_move_in_direction` — Directional movement (0° = east)
- `test_calculate_and_apply_offset` — Laser-camera offset calculation
- `test_move_laser_to_marker_center` — Laser positioning to detected marker
- `test_idle_to_detected_to_approved` — State machine transitions
- `test_full_m1_m2_workflow` — Complete M1→M2 navigation flow

#### E2E: Plugin Integration (13 tests)
- `test_health_check` (laser) — Plugin health endpoint
- `test_initial_position` (laser) — Default position is (0, 0)
- `test_move_and_verify` (laser) — HTTP move command + position verification
- `test_workspace_state` (laser) — Full workspace state retrieval
- `test_draw_path` (laser) — Path drawing with laser at end position
- `test_stop` (laser) — Stop command
- `test_health_check` (camera) — Plugin health endpoint
- `test_get_frame` (camera) — JPEG frame retrieval
- `test_get_position` (camera) — Camera position query
- `test_update_config` (camera) — FOV, resolution, FPS configuration
- `test_update_position` (camera) — Position update via HTTP
- `test_coordinated_movement` — Laser and camera plugins synchronized
- `test_frame_reflects_workspace` — Camera frame changes with position

## Code Quality

| Check | Result |
|-------|--------|
| `pyright mvp/` | 0 errors, 0 warnings |
| `flake8 mvp/` | 0 violations |
| `pytest mvp/tests/` | 106/106 passed |

## State Machine Workflow

The application implements the following workflow:

1. **START** → Controller connected, operator clicks "Connect & Start"
2. **SEARCH_M1** → Camera finds M1, auto-centers on detection
3. **CONFIRM_M1** → Zoomed view with green circle, operator adjusts with arrow keys, confirms
4. **REGISTER_M1** → Laser moves to M1 center, sends Alt+1 to LightBurn
5. **SEARCH_M2** → Navigate toward M2 using M1 direction, auto-centers on detection
6. **CONFIRM_M2** → Zoomed view with green circle, operator adjusts with arrow keys, confirms
7. **REGISTER_M2** → Laser moves to M2 center, sends Alt+2 to LightBurn
8. **DONE** → Both markers registered, auto-reset to START

## Failed Tests

None.