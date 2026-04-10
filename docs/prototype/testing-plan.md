# Integration Testing Plan

## 1. Overview

This document defines the testing strategy for the LaserCam prototype system, including unit tests for individual components, integration tests between plugins and the main application, and end-to-end workflow tests.

---

## 2. Test Environment

### 2.1 Requirements

- Python 3.8+ for plugin testing
- MeerK40t installed and configured
- pytest for test execution
- OpenCV for image comparison
- HTTP client library for API testing

### 2.2 Test Configuration

```json
{
    "test": {
        "laser_emulator": {
            "host": "127.0.0.1",
            "port": 8080
        },
        "camera_emulator": {
            "host": "127.0.0.1",
            "port": 8081
        },
        "timeouts": {
            "request_ms": 1000,
            "movement_ms": 5000,
            "frame_ms": 500
        }
    }
}
```

---

## 3. Unit Tests

### 3.1 Laser Emulator Plugin

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_initial_position` | Verify laser starts at origin | Position is (0, 0) |
| `test_move_to_position` | Move to absolute position | Position matches target |
| `test_move_relative` | Move by relative amount | Position changes by delta |
| `test_move_out_of_bounds` | Move outside workspace | Error returned, position unchanged |
| `test_draw_path` | Draw a multi-point path | Path recorded, workspace updated |
| `test_stop_movement` | Stop during movement | Movement halts immediately |
| `test_position_broadcast` | Verify WebSocket updates | Clients receive position updates |
| `test_workspace_rendering` | Render workspace image | Image contains expected elements |

### 3.2 Camera Emulator Plugin

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_frame_generation` | Generate frame at default position | Valid JPEG image returned |
| `test_frame_at_bounds` | Generate frame at workspace edge | Frame shows partial workspace |
| `test_frame_out_of_bounds` | Generate frame outside workspace | Blank or error frame returned |
| `test_marker_rendering` | Verify markers in frame | Markers visible at correct positions |
| `test_marker_direction_line` | Verify direction line angle | Line angle matches configuration |
| `test_config_update` | Change camera FOV | Subsequent frames reflect new FOV |
| `test_resolution_change` | Change output resolution | Frame dimensions match config |
| `test_mjpeg_stream` | Connect to MJPEG stream | Continuous frames received |

### 3.3 Main Application

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_plugin_connection` | Connect to both plugins | Connections established |
| `test_position_query` | Query laser position | Valid position returned |
| `test_frame_request` | Request camera frame | Valid frame received |
| `test_movement_command` | Send movement command | Laser moves to target |
| `test_marker_detection` | Detect marker in frame | Marker center and angle returned |
| `test_calibration` | Run calibration routine | Offset calculated correctly |

---

## 4. Integration Tests

### 4.1 Plugin Communication

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_laser_position_sync` | Move laser, verify position update | Main app receives update within 50ms |
| `test_frame_position_correlation` | Request frame with position | Frame matches laser position |
| `test_marker_sync` | Update markers in camera emulator | Laser emulator workspace updated |
| `test_error_propagation` | Plugin error occurs | Main app handles error gracefully |

### 4.2 Workflow Integration

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_full_detection_flow` | Detect marker, approve, move | Laser moves to marker center |
| `test_calibration_workflow` | Run full calibration | Offset calculated and stored |
| `test_movement_with_calibration` | Move with active calibration | Movement accounts for offset |
| `test_error_recovery` | Plugin disconnects during operation | System recovers or fails safely |

---

## 5. End-to-End Tests

### 5.1 Complete Workflow

| Test | Steps | Expected Result |
|------|-------|-----------------|
| `test_m1_detection_and_movement` | 1. Start plugins<br>2. Move camera to M1<br>3. Detect M1<br>4. Approve detection<br>5. Move laser to M1 | Laser at M1 center |
| `test_m1_to_m2_navigation` | 1. Detect M1<br>2. Get direction angle<br>3. Move toward M2<br>4. Detect M2<br>5. Approve detection<br>6. Move laser to M2 | Laser at M2 center |
| `test_calibration_check` | 1. Run calibration<br>2. Verify offset<br>3. Move laser<br>4. Verify position accuracy | Offset accurate within 0.1mm |
| `test_full_alignment_workflow` | Complete M1→M2 workflow with calibration | All steps complete successfully |

### 5.2 Error Scenarios

| Test | Scenario | Expected Result |
|------|----------|-----------------|
| `test_plugin_crash_recovery` | Laser emulator crashes during operation | Main app detects crash, attempts restart |
| `test_network_timeout` | Network delay causes timeout | Operation retries or fails gracefully |
| `test_invalid_marker` | No marker in frame | System reports no detection, waits |
| `test_out_of_bounds_movement` | Movement command outside workspace | Command rejected, error reported |

---

## 6. Performance Tests

### 6.1 Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Frame generation latency | < 50ms | Time from request to frame receipt |
| Position update latency | < 10ms | Time from movement to update receipt |
| Movement simulation speed | Real-time | Compare simulated vs expected time |
| API response time | < 100ms | Time from request to response |
| Memory usage | < 500MB | Monitor process memory during operation |
| CPU usage | < 50% | Monitor CPU during active operation |

### 6.2 Stress Tests

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| `test_continuous_movement` | Send 1000 movement commands | All commands complete, no errors |
| `test_high_frequency_frames` | Request frames at 60 FPS for 60 seconds | No dropped frames, stable performance |
| `test_concurrent_clients` | 5 clients connected simultaneously | All clients receive updates correctly |

---

## 7. Test Execution

### 7.1 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -v

# Run with coverage
pytest tests/ --cov=mvp --cov-report=html
```

### 7.2 Test Fixtures

```python
@pytest.fixture
def laser_emulator():
    """Start laser emulator plugin for testing."""
    plugin = LaserEmulatorPlugin(...)
    yield plugin
    plugin.shutdown()

@pytest.fixture
def camera_emulator():
    """Start camera emulator plugin for testing."""
    plugin = CameraEmulatorPlugin(...)
    yield plugin
    plugin.shutdown()

@pytest.fixture
def connected_app(laser_emulator, camera_emulator):
    """Main application connected to both plugins."""
    app = LaserCamApp(...)
    app.connect_plugins()
    yield app
    app.disconnect_plugins()
```

---

## 8. Validation Criteria

### 8.1 Acceptance Criteria

- All unit tests pass (100%)
- All integration tests pass (≥ 95%)
- End-to-end workflow completes successfully
- Performance benchmarks met
- Error scenarios handled gracefully

### 8.2 Continuous Integration

- Tests run on every commit
- Performance benchmarks tracked over time
- Test coverage ≥ 80%
- No regressions in detection accuracy

---

## 9. Test Data

### 9.1 Test Workspace

- Size: 900x600mm
- Background: White with optional grid
- Markers: 2 circle markers at known positions
- Resolution: 10 pixels/mm

### 9.2 Test Markers

| Marker | Position (mm) | Angle (°) |
|--------|---------------|-----------|
| M1 | (809.2, 480.3) | 157.0 |
| M2 | (751.0, 506.0) | 337.0 |

### 9.3 Test Scenarios

1. **Normal Operation**: Both markers visible, good lighting
2. **Edge Cases**: Markers at workspace edges
3. **Error Conditions**: No markers, invalid positions
4. **Performance**: High-frequency operations
