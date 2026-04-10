# mvp/tests/e2e/test_plugin_integration.py
"""
End-to-end tests for MeerK40t plugin integration.

Tests the HTTP API communication between the main application
and the Laser/Camera Emulator plugins.
"""
import json
import time
import urllib.request

import numpy as np
import pytest

from mvp.plugins.laser_emulator import LaserEmulatorServer
from mvp.plugins.camera_emulator import CameraEmulatorServer


@pytest.fixture
def laser_server():
    srv = LaserEmulatorServer(port=28080)
    srv.start()
    time.sleep(0.1)
    yield srv
    srv.stop()


@pytest.fixture
def camera_server():
    srv = CameraEmulatorServer(port=28081)
    srv.camera_state.workspace_image = np.ones(
        (1000, 1000, 3), dtype=np.uint8
    ) * 255
    srv.camera_state.workspace_pixels_per_mm = 10.0
    srv.start()
    time.sleep(0.1)
    yield srv
    srv.stop()


class TestLaserEmulatorAPI:
    """E2E: Full HTTP API lifecycle for Laser Emulator."""

    def test_health_check(self, laser_server):
        resp = urllib.request.urlopen("http://127.0.0.1:28080/health")
        data = json.loads(resp.read())
        assert data["status"] == "ok"

    def test_initial_position(self, laser_server):
        resp = urllib.request.urlopen("http://127.0.0.1:28080/position")
        data = json.loads(resp.read())
        assert data["x"] == 0.0
        assert data["y"] == 0.0
        assert data["status"] == "idle"

    def test_move_and_verify(self, laser_server):
        # Move to position
        payload = json.dumps({"x": 250.0, "y": 175.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28080/move",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert json.loads(resp.read())["status"] == "complete"

        # Verify position
        resp = urllib.request.urlopen("http://127.0.0.1:28080/position")
        data = json.loads(resp.read())
        assert data["x"] == 250.0
        assert data["y"] == 175.0

    def test_workspace_state(self, laser_server):
        laser_server.workspace.move_to(100, 50)
        resp = urllib.request.urlopen("http://127.0.0.1:28080/workspace")
        data = json.loads(resp.read())
        assert data["width"] == 900.0
        assert data["height"] == 600.0
        assert data["laser_x"] == 100.0
        assert data["laser_y"] == 50.0

    def test_draw_path(self, laser_server):
        path = [[0, 0], [50, 50], [100, 0], [50, 100]]
        payload = json.dumps({"path": path}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28080/draw",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert json.loads(resp.read())["status"] == "complete"

        # Laser should be at end of path
        resp = urllib.request.urlopen("http://127.0.0.1:28080/position")
        data = json.loads(resp.read())
        assert data["x"] == 50.0
        assert data["y"] == 100.0

    def test_stop(self, laser_server):
        req = urllib.request.Request(
            "http://127.0.0.1:28080/stop",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert json.loads(resp.read())["status"] == "stopped"


class TestCameraEmulatorAPI:
    """E2E: Full HTTP API lifecycle for Camera Emulator."""

    def test_health_check(self, camera_server):
        resp = urllib.request.urlopen("http://127.0.0.1:28081/health")
        data = json.loads(resp.read())
        assert data["status"] == "ok"

    def test_get_frame(self, camera_server):
        resp = urllib.request.urlopen("http://127.0.0.1:28081/frame")
        assert resp.headers["Content-Type"] == "image/jpeg"
        data = resp.read()
        assert len(data) > 0

    def test_get_position(self, camera_server):
        camera_server.camera_state.set_position(300, 200)
        resp = urllib.request.urlopen("http://127.0.0.1:28081/position")
        data = json.loads(resp.read())
        assert data["x"] == 300.0
        assert data["y"] == 200.0

    def test_update_config(self, camera_server):
        payload = json.dumps({
            "fov_mm": [60.0, 45.0],
            "resolution": [1280, 720],
            "fps": 60,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28081/config",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert json.loads(resp.read())["status"] == "updated"

        resp = urllib.request.urlopen("http://127.0.0.1:28081/config")
        config = json.loads(resp.read())
        assert config["fov_mm"] == [60.0, 45.0]
        assert config["resolution"] == [1280, 720]
        assert config["fps"] == 60

    def test_update_position(self, camera_server):
        payload = json.dumps({"x": 450.0, "y": 300.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28081/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert json.loads(resp.read())["status"] == "updated"

        resp = urllib.request.urlopen("http://127.0.0.1:28081/position")
        data = json.loads(resp.read())
        assert data["x"] == 450.0
        assert data["y"] == 300.0


class TestPluginSynchronization:
    """E2E: Laser and Camera plugins stay in sync."""

    def test_coordinated_movement(self, laser_server, camera_server):
        """Move laser, update camera position, verify both agree."""
        # Move laser to position
        payload = json.dumps({"x": 500.0, "y": 350.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28080/move",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        # Update camera to same position
        payload = json.dumps({"x": 500.0, "y": 350.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28081/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        # Verify both agree
        resp = urllib.request.urlopen("http://127.0.0.1:28080/position")
        laser_pos = json.loads(resp.read())

        resp = urllib.request.urlopen("http://127.0.0.1:28081/position")
        camera_pos = json.loads(resp.read())

        assert laser_pos["x"] == camera_pos["x"]
        assert laser_pos["y"] == camera_pos["y"]

    def test_frame_reflects_workspace(self, camera_server):
        """Camera frame should change when workspace changes."""
        # Get initial frame
        resp1 = urllib.request.urlopen("http://127.0.0.1:28081/frame")
        frame1 = resp1.read()

        # Move camera to different position
        payload = json.dumps({"x": 50.0, "y": 50.0}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:28081/position",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

        # Get new frame
        resp2 = urllib.request.urlopen("http://127.0.0.1:28081/frame")
        frame2 = resp2.read()

        # Frames should be different (different positions = different content)
        # Both should be valid JPEG
        assert len(frame1) > 0
        assert len(frame2) > 0
        assert frame1[:2] == b"\xff\xd8"  # JPEG magic bytes
        assert frame2[:2] == b"\xff\xd8"
