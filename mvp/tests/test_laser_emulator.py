import json
import time

import pytest

from mvp.plugins.laser_emulator import (
    LaserEmulatorServer,
    WorkspaceState,
)


@pytest.fixture
def server():
    """Start a laser emulator server for testing."""
    srv = LaserEmulatorServer(port=18080)
    srv.start()
    time.sleep(0.1)  # Let server start
    yield srv
    srv.stop()


def test_workspace_state_init():
    ws = WorkspaceState()
    assert ws.laser_x == 0.0
    assert ws.laser_y == 0.0
    assert ws.is_moving is False


def test_workspace_state_move_to():
    ws = WorkspaceState()
    ws.move_to(100.0, 50.0)
    assert ws.laser_x == 100.0
    assert ws.laser_y == 50.0


def test_workspace_state_move_to_clamped():
    ws = WorkspaceState(width_mm=900, height_mm=600)
    ws.move_to(1000.0, -10.0)
    assert ws.laser_x == 900.0
    assert ws.laser_y == 0.0


def test_workspace_state_get_position():
    ws = WorkspaceState()
    ws.move_to(42.0, 17.0)
    pos = ws.get_position()
    assert pos["x"] == 42.0
    assert pos["y"] == 17.0
    assert pos["status"] == "idle"


def test_workspace_state_add_draw_path():
    ws = WorkspaceState()
    path = [(0.0, 0.0), (10.0, 10.0), (20.0, 0.0)]
    ws.add_draw_path(path)
    assert len(ws.draw_paths) == 1
    assert ws.draw_paths[0] == path


def test_laser_emulator_health(server):
    import urllib.request

    resp = urllib.request.urlopen("http://127.0.0.1:18080/health")
    data = json.loads(resp.read())
    assert data["status"] == "ok"


def test_laser_emulator_get_position(server):
    import urllib.request

    server.workspace.move_to(100.0, 50.0)
    resp = urllib.request.urlopen("http://127.0.0.1:18080/position")
    data = json.loads(resp.read())
    assert data["x"] == 100.0
    assert data["y"] == 50.0


def test_laser_emulator_move_to(server):
    import urllib.request

    payload = json.dumps({"x": 200.0, "y": 150.0}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:18080/move",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    assert data["status"] == "complete"

    # Verify position updated
    resp = urllib.request.urlopen("http://127.0.0.1:18080/position")
    pos = json.loads(resp.read())
    assert pos["x"] == 200.0
    assert pos["y"] == 150.0


def test_laser_emulator_get_workspace(server):
    import urllib.request

    server.workspace.move_to(50.0, 30.0)
    resp = urllib.request.urlopen("http://127.0.0.1:18080/workspace")
    data = json.loads(resp.read())
    assert data["width"] == 900.0
    assert data["height"] == 600.0
    assert data["laser_x"] == 50.0
    assert data["laser_y"] == 30.0


def test_laser_emulator_stop(server):
    import urllib.request

    req = urllib.request.Request(
        "http://127.0.0.1:18080/stop",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    assert data["status"] == "stopped"
