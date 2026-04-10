import numpy as np
import pytest

from mvp.simulator import MotionSimulator


def test_simulator_init():
    sim = MotionSimulator(
        work_area_size=(500, 500),
        camera_fov=(50, 50),
        workspace_pixels_per_mm=2,
        camera_resolution_px=(640, 480),
    )
    assert sim.gantry_x == 0
    assert sim.gantry_y == 0
    assert sim.camera_fov_px == (640, 480)
    assert sim.work_area.shape == (500, 500, 3)
    assert sim.workspace_pixels_per_mm == 2


def test_simulator_move():
    sim = MotionSimulator()
    sim.move_gantry_to(10, 20)
    assert sim.gantry_x == 10
    assert sim.gantry_y == 20
    assert sim.camera_x_mm == 10
    assert sim.camera_y_mm == 20


def test_simulator_set_work_area():
    sim = MotionSimulator()
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    sim.set_work_area_image(img)
    assert sim.work_area.shape == (200, 200, 3)


def test_simulator_get_camera_view():
    sim = MotionSimulator(
        work_area_size=(100, 100),
        camera_fov=(20, 20),
        workspace_pixels_per_mm=1,
        camera_resolution_px=(320, 240),
    )
    # Fill work area with a pattern
    sim.work_area[:] = 0
    sim.work_area[40:60, 40:60] = 255  # White square in the middle

    sim.move_gantry_to(50, 50)
    view = sim.get_camera_view()

    # View should be resized to camera_resolution_px
    assert view.shape == (240, 320, 3)
    # Center of view should be white
    assert np.mean(view) > 250


def test_move_in_direction_east():
    sim = MotionSimulator()
    sim.move_gantry_to(0, 0)
    sim.move_in_direction(0, 10)
    assert sim.gantry_x == pytest.approx(10, abs=1e-6)
    assert sim.gantry_y == pytest.approx(0, abs=1e-6)


def test_move_in_direction_south():
    sim = MotionSimulator()
    sim.move_gantry_to(0, 0)
    sim.move_in_direction(90, 10)
    assert sim.gantry_x == pytest.approx(0, abs=1e-6)
    assert sim.gantry_y == pytest.approx(10, abs=1e-6)


def test_simulator_move_laser_to_marker():
    sim = MotionSimulator(
        camera_fov=(20, 20),
        workspace_pixels_per_mm=5,
        camera_resolution_px=(500, 500),
    )
    sim.move_gantry_to(0, 0)

    # Marker is at center of camera view (250, 250) in pixels
    marker_center_px = (250, 250)

    sim.move_laser_to_marker_center(marker_center_px)

    # Marker absolute position should be (0, 0) mm
    # To place laser at (0, 0), gantry must be at (0 - 65, 0 - 15) = (-65, -15)
    assert sim.gantry_x == -65
    assert sim.gantry_y == -15
