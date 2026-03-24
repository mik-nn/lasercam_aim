import cv2
import pytest

from mvp.camera_simulator import CameraSimulator


def test_camera_simulator_init():
    sim = CameraSimulator(camera_fov=(100, 100), workspace_pixels_per_mm=5)
    assert sim.simulator is not None
    assert sim.recognizer is not None


def test_camera_simulator_move():
    sim = CameraSimulator()
    sim.move_to(50, 50)
    assert sim.simulator.gantry_x == 50
    assert sim.simulator.gantry_y == 50


def test_camera_simulator_get_frame():
    sim = CameraSimulator(camera_resolution_px=(640, 480))
    frame = sim.get_frame()
    assert frame.shape == (480, 640, 3)


def test_camera_simulator_find_marker():
    workspace_pixels_per_mm = 5
    res_w, res_h = 640, 480
    sim = CameraSimulator(
        camera_fov=(100, 100),
        workspace_pixels_per_mm=workspace_pixels_per_mm,
        camera_resolution_px=(res_w, res_h),
    )
    sim.move_to(50, 50)

    # Manually draw a marker that we KNOW should be recognized
    # Camera center at (50, 50)mm is (250, 250)px in workspace
    wa = sim.simulator.work_area
    wa[:] = 255
    cv2.rectangle(wa, (240, 240), (260, 260), (0, 0, 0), 2)
    cv2.rectangle(wa, (248, 248), (252, 252), (0, 0, 0), -1)

    found, center, shape, angle = sim.find_marker()
    assert found
    # Center should be in the middle of the resized camera frame
    assert abs(center[0] - res_w / 2) <= 5
    assert abs(center[1] - res_h / 2) <= 5


def test_camera_simulator_move_laser_to_marker():
    sim = CameraSimulator(camera_resolution_px=(500, 500), workspace_pixels_per_mm=5)
    sim.move_to(0, 0)

    # Marker at center of current FOV (500x500 pixels)
    marker_center_px = (250, 250)

    sim.move_laser_to_marker(marker_center_px)

    # marker abs pos (0, 0), laser_offset (10, 10)
    # gantry must move to (-10, -10)
    assert sim.simulator.gantry_x == pytest.approx(-10)
    assert sim.simulator.gantry_y == pytest.approx(-10)
