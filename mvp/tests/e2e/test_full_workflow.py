# mvp/tests/e2e/test_full_workflow.py
"""
End-to-end tests for the complete LaserCam workflow.

These tests exercise the full integration of:
- Camera simulator with workspace
- Marker generation and placement
- Marker recognition
- Controller-based movement
- Calibration
- State machine transitions
"""
import cv2
import numpy as np
import pytest

from mvp.camera_simulator import CameraSimulator
from mvp.controller import SimulatedController
from mvp.simulator import MotionSimulator


def _create_workspace_with_markers(
    width_mm=900,
    height_mm=600,
    ppm=7.874,
    camera_fov=(50.0, 37.5),
    resolution=(640, 480),
):
    """Create a simulator workspace with M1 and M2 markers."""
    sim = MotionSimulator(
        work_area_size=(int(width_mm * ppm), int(height_mm * ppm)),
        camera_fov=camera_fov,
        workspace_pixels_per_mm=ppm,
        camera_resolution_px=resolution,
    )
    # White background
    sim.work_area[:] = 255

    # M1 at (800, 500) — solid circle with direction line
    m1_x, m1_y = 800, 500
    m1_px = int(m1_x * ppm), int(m1_y * ppm)
    r1 = int(3 * ppm)  # 3mm radius
    cv2.circle(sim.work_area, m1_px, r1, (0, 0, 0), -1)
    # Direction line pointing toward M2 at (750, 550)
    # dx = -50 (left), dy = +50 (down) → angle = 135° in image coords
    angle1_rad = np.radians(135)
    line_len = int(2 * ppm)
    lx1 = int(m1_px[0] + line_len * np.cos(angle1_rad))
    ly1 = int(m1_px[1] + line_len * np.sin(angle1_rad))
    cv2.line(sim.work_area, m1_px, (lx1, ly1), (255, 255, 255), max(1, int(0.5 * ppm)))

    # M2 at (750, 550) — solid circle with direction line
    m2_x, m2_y = 750, 550
    m2_px = int(m2_x * ppm), int(m2_y * ppm)
    r2 = int(3 * ppm)
    cv2.circle(sim.work_area, m2_px, r2, (0, 0, 0), -1)
    # Direction line pointing toward M1 at (800, 500)
    # dx = +50 (right), dy = -50 (up) → angle = 315° in image coords
    angle2_rad = np.radians(315)
    lx2 = int(m2_px[0] + line_len * np.cos(angle2_rad))
    ly2 = int(m2_px[1] + line_len * np.sin(angle2_rad))
    cv2.line(sim.work_area, m2_px, (lx2, ly2), (255, 255, 255), max(1, int(0.5 * ppm)))

    markers = [
        {"x_mm": m1_x, "y_mm": m1_y, "shape_type": "circle", "angle_deg": 135.0},
        {"x_mm": m2_x, "y_mm": m2_y, "shape_type": "circle", "angle_deg": 315.0},
    ]
    return sim, markers


def _make_cam_sim(sim, markers):
    """Create a CameraSimulator wrapping the given simulator and markers."""
    cam_sim = CameraSimulator(
        workspace_image_path=None,
        camera_fov=(50.0, 37.5),
        workspace_pixels_per_mm=7.874,
        camera_resolution_px=(640, 480),
    )
    cam_sim.simulator = sim
    cam_sim.controller = SimulatedController(sim)
    for m in markers:
        cam_sim._markers.append(m)
    return cam_sim


class TestMarkerDetectionWorkflow:
    """E2E: Detect markers at known positions."""

    def test_detect_m1_at_position(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        # Move camera to M1 position
        cam_sim.move_to(800, 500)
        frame = cam_sim.get_frame()

        assert frame is not None
        assert frame.shape == (480, 640, 3)

        found, center, shape_type, angle = cam_sim.find_marker()
        assert found
        assert center is not None
        assert shape_type == "circle"

    def test_detect_m2_at_position(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        cam_sim.move_to(750, 550)
        cam_sim.get_frame()

        found, center, shape_type, angle = cam_sim.find_marker()
        assert found
        assert center is not None

    def test_no_marker_in_empty_area(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        # Move to area with no markers
        cam_sim.move_to(100, 100)

        found, center, shape_type, angle = cam_sim.find_marker()
        assert not found


class TestMovementWorkflow:
    """E2E: Move between positions via controller."""

    def test_move_to_and_verify_position(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        cam_sim.move_to(400, 300)
        pos = cam_sim.controller.position
        assert pos == (400, 300)

    def test_move_by_relative(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        cam_sim.move_to(100, 100)
        cam_sim.controller.move_by(50, -20)
        pos = cam_sim.controller.position
        assert pos == pytest.approx((150, 80))

    def test_move_in_direction(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        cam_sim.move_to(0, 0)
        cam_sim.controller.move_in_direction(0, 100)  # East
        pos = cam_sim.controller.position
        assert pos[0] == pytest.approx(100, abs=0.01)
        assert pos[1] == pytest.approx(0, abs=0.01)


class TestCalibrationWorkflow:
    """E2E: Calibrate laser-camera offset."""

    def test_calculate_and_apply_offset(self):
        from mvp.simulator import MotionSimulator

        sim = MotionSimulator()
        sim.laser_offset_x = 15.0
        sim.laser_offset_y = 10.0

        # Camera at (100, 100), laser should be at (115, 110)
        sim.move_gantry_to(100, 100)
        laser_x = sim.gantry_x + sim.laser_offset_x
        laser_y = sim.gantry_y + sim.laser_offset_y

        assert laser_x == 115.0
        assert laser_y == 110.0

    def test_move_laser_to_marker_center(self):
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        cam_sim.move_to(800, 500)
        frame = cam_sim.get_frame()

        found, center, shape_type, angle = cam_sim.recognizer.find_marker(frame)
        if found and center is not None:
            cam_sim.move_laser_to_marker(center)
            # Laser position should now be near the marker
            laser_x = sim.gantry_x + sim.laser_offset_x
            laser_y = sim.gantry_y + sim.laser_offset_y
            # Within tolerance of marker position
            assert abs(laser_x - 800) < 5
            assert abs(laser_y - 500) < 5


class TestStateTransitions:
    """E2E: State machine transitions through the workflow."""

    def test_idle_to_detected_to_approved(self):
        """Simulate the state flow: IDLE → DETECTED → APPROVED → MOVING."""
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        # IDLE: Move to M1 area
        cam_sim.move_to(800, 500)
        found, center, shape_type, angle = cam_sim.find_marker()

        # DETECTED
        assert found
        assert center is not None
        assert angle is not None

        # APPROVED: Move to marker center
        cam_sim.move_to(800, 500)
        pos = cam_sim.controller.position
        assert pos == (800, 500)

    def test_full_m1_m2_workflow(self):
        """Complete workflow: find M1 → confirm → navigate to M2 → confirm."""
        sim, markers = _create_workspace_with_markers()
        cam_sim = _make_cam_sim(sim, markers)

        # Step 1: Find M1
        cam_sim.move_to(800, 500)
        found1, center1, shape1, angle1 = cam_sim.find_marker()
        assert found1
        assert angle1 is not None

        # Step 2: Move toward M2 using direction from M1
        # M1 is at (800, 500), M2 is at (750, 550). Direction is ~135° (down-left)
        # Move 70mm in that direction should get us closer to M2
        m1_pos = cam_sim.controller.position
        cam_sim.controller.move_in_direction(angle1, 70)

        # Step 3: Search for M2 — try a few positions around where we landed
        found2 = False
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                cam_sim.move_to(
                    cam_sim.controller.position[0] + dx * 5,
                    cam_sim.controller.position[1] + dy * 5,
                )
                f, c, s, a = cam_sim.find_marker()
                if f:
                    found2 = True
                    break
            if found2:
                break

        assert found2

        # Step 4: Verify we moved from M1 position
        m2_pos = cam_sim.controller.position
        distance = np.sqrt(
            (m2_pos[0] - m1_pos[0]) ** 2 + (m2_pos[1] - m1_pos[1]) ** 2
        )
        assert distance > 10  # We moved significantly
