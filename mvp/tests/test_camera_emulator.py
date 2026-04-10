import json
import time

import numpy as np
import pytest

from mvp.plugins.camera_emulator import (
    CameraEmulatorServer,
    CameraState,
)


@pytest.fixture
def server():
    """Start a camera emulator server for testing."""
    srv = CameraEmulatorServer(port=18081)
    srv.camera_state.workspace_image = np.ones(
        (1000, 1000, 3), dtype=np.uint8
    ) * 255
    srv.start()
    time.sleep(0.1)
    yield srv
    srv.stop()


def test_camera_state_init():
    cs = CameraState()
    assert cs.fov_mm == (50.0, 37.5)
    assert cs.resolution == (1920, 1080)
    assert cs.fps == 30


def test_camera_state_set_position():
    cs = CameraState()
    cs.set_position(100.0, 50.0)
    pos = cs.get_position()
    assert pos["x"] == 100.0
    assert pos["y"] == 50.0


def test_camera_state_set_config():
    cs = CameraState()
    cs.set_config(fov_mm=(60.0, 45.0), resolution=(1280, 720))
    config = cs.get_config()
    assert config["fov_mm"] == [60.0, 45.0]
    assert config["resolution"] == [1280, 720]


def test_camera_state_render_frame():
    cs = CameraState(
        fov_mm=(100, 100),
        resolution=(640, 480),
    )
    cs.workspace_image = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    cs.workspace_pixels_per_mm = 10.0
    cs.set_position(50.0, 50.0)

    frame = cs.render_frame()
    assert frame is not None
    assert frame.shape == (480, 640, 3)


def test_camera_emulator_health(server):
    import urllib.request

    resp = urllib.request.urlopen("http://127.0.0.1:18081/health")
    data = json.loads(resp.read())
    assert data["status"] == "ok"


def test_camera_emulator_get_position(server):
    import urllib.request

    server.camera_state.set_position(75.0, 25.0)
    resp = urllib.request.urlopen("http://127.0.0.1:18081/position")
    data = json.loads(resp.read())
    assert data["x"] == 75.0
    assert data["y"] == 25.0


def test_camera_emulator_get_config(server):
    import urllib.request

    resp = urllib.request.urlopen("http://127.0.0.1:18081/config")
    data = json.loads(resp.read())
    assert "fov_mm" in data
    assert "resolution" in data
    assert "fps" in data


def test_camera_emulator_set_config(server):
    import urllib.request

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
    assert data["status"] == "updated"

    # Verify config updated
    resp = urllib.request.urlopen("http://127.0.0.1:18081/config")
    config = json.loads(resp.read())
    assert config["fov_mm"] == [60.0, 45.0]


def test_camera_emulator_get_frame(server):
    import urllib.request

    resp = urllib.request.urlopen("http://127.0.0.1:18081/frame")
    assert resp.headers["Content-Type"] == "image/jpeg"
    data = resp.read()
    assert len(data) > 0
