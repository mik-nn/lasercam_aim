# mvp/plugins/test_plugins_standalone.py
"""
Standalone verification script for LaserCam plugins.
Tests the HTTP API without requiring MeerK40t to be running.
"""
import json
import sys
import time
import urllib.request

import numpy as np

sys.path.insert(0, ".")

from mvp.plugins.laser_emulator import LaserEmulatorServer  # noqa: E402
from mvp.plugins.camera_emulator import CameraEmulatorServer  # noqa: E402


def test_laser_emulator():
    print("Testing Laser Emulator HTTP API...")
    server = LaserEmulatorServer(port=18080)
    server.start()
    time.sleep(0.5)

    try:
        # Test health
        resp = urllib.request.urlopen("http://127.0.0.1:18080/health")
        data = json.loads(resp.read())
        assert data["status"] == "ok", "Health check failed"
        print("  Health check: PASS")

        # Test move
        payload = json.dumps({"x": 100.0, "y": 50.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18080/move",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "complete", "Move failed"
        print("  Move command: PASS")

        # Test position
        resp = urllib.request.urlopen("http://127.0.0.1:18080/position")
        data = json.loads(resp.read())
        assert data["x"] == 100.0 and data["y"] == 50.0, "Position mismatch"
        print("  Position query: PASS")

        # Test workspace
        resp = urllib.request.urlopen("http://127.0.0.1:18080/workspace")
        data = json.loads(resp.read())
        assert data["width"] == 900.0, "Workspace width mismatch"
        assert data["laser_x"] == 100.0, "Laser X mismatch"
        print("  Workspace state: PASS")

        # Test draw path
        path = [[0, 0], [50, 50], [100, 0]]
        payload = json.dumps({"path": path}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18080/draw",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "complete", "Draw failed"
        print("  Draw path: PASS")

        # Test stop
        req = urllib.request.Request(
            "http://127.0.0.1:18080/stop",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "stopped", "Stop failed"
        print("  Stop command: PASS")

        print()
        print("  Laser Emulator: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        server.stop()


def test_camera_emulator():
    print("Testing Camera Emulator HTTP API...")
    server = CameraEmulatorServer(port=18081)
    server.camera_state.workspace_image = np.ones(
        (1000, 1000, 3), dtype=np.uint8
    ) * 255
    server.camera_state.workspace_pixels_per_mm = 10.0
    server.start()
    time.sleep(0.5)

    try:
        # Test health
        resp = urllib.request.urlopen("http://127.0.0.1:18081/health")
        data = json.loads(resp.read())
        assert data["status"] == "ok", "Health check failed"
        print("  Health check: PASS")

        # Test frame
        resp = urllib.request.urlopen("http://127.0.0.1:18081/frame")
        assert resp.headers["Content-Type"] == "image/jpeg", "Wrong content type"
        frame_data = resp.read()
        assert len(frame_data) > 0, "Empty frame"
        print("  Frame streaming: PASS")

        # Test position
        server.camera_state.set_position(200.0, 150.0)
        resp = urllib.request.urlopen("http://127.0.0.1:18081/position")
        data = json.loads(resp.read())
        assert data["x"] == 200.0 and data["y"] == 150.0, "Position mismatch"
        print("  Position query: PASS")

        # Test config
        payload = json.dumps({
            "fov_mm": [60.0, 45.0],
            "resolution": [1280, 720],
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18081/config",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "updated", "Config update failed"
        print("  Config update: PASS")

        # Test position update via POST
        payload = json.dumps({"x": 300.0, "y": 200.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18081/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "updated", "Position update failed"
        print("  Position update: PASS")

        print()
        print("  Camera Emulator: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        server.stop()


def test_plugin_synchronization():
    print("Testing Plugin Synchronization...")
    laser = LaserEmulatorServer(port=18082)
    camera = CameraEmulatorServer(port=18083)
    camera.camera_state.workspace_image = np.ones(
        (1000, 1000, 3), dtype=np.uint8
    ) * 255
    camera.camera_state.workspace_pixels_per_mm = 10.0
    laser.start()
    camera.start()
    time.sleep(0.5)

    try:
        # Move laser
        payload = json.dumps({"x": 500.0, "y": 350.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18082/move",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        # Update camera to same position
        payload = json.dumps({"x": 500.0, "y": 350.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18083/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        # Verify both agree
        resp = urllib.request.urlopen("http://127.0.0.1:18082/position")
        laser_pos = json.loads(resp.read())

        resp = urllib.request.urlopen("http://127.0.0.1:18083/position")
        camera_pos = json.loads(resp.read())

        assert laser_pos["x"] == camera_pos["x"], "X position mismatch"
        assert laser_pos["y"] == camera_pos["y"], "Y position mismatch"
        print("  Coordinated movement: PASS")

        # Verify frames are valid JPEG (move camera to center of workspace first)
        payload = json.dumps({"x": 50.0, "y": 50.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18083/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        resp = urllib.request.urlopen("http://127.0.0.1:18083/frame")
        frame = resp.read()
        assert frame[:2] == b"\xff\xd8", "Not a valid JPEG"
        print("  Frame integrity: PASS")

        print()
        print("  Plugin Synchronization: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        laser.stop()
        camera.stop()


if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  LaserCam Plugin Standalone Verification")
    print("=" * 50)
    print()

    results = []
    results.append(("Laser Emulator", test_laser_emulator()))
    print()
    results.append(("Camera Emulator", test_camera_emulator()))
    print()
    results.append(("Plugin Sync", test_plugin_synchronization()))

    print()
    print("=" * 50)
    print("  Results Summary")
    print("=" * 50)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  ALL TESTS PASSED - Plugins are working correctly!")
    else:
        print("  SOME TESTS FAILED - Check errors above.")
    print("=" * 50)
    print()
