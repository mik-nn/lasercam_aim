import cv2
import numpy as np
import pytest

from mvp.recognizer import MarkerRecognizer


@pytest.fixture
def recognizer():
    return MarkerRecognizer()


def _draw_solid_circle_marker(
    img, cx, cy, radius_px, angle_deg, line_len_px=15, line_w_px=5
):
    """
    Draw a new-design marker: solid black circle + white direction line.

    angle_deg: 0 = east, 90 = south (image coordinates, clockwise).
    """
    # Solid black circle
    cv2.circle(img, (cx, cy), radius_px, (0, 0, 0), -1)

    # White direction line
    angle_rad = np.radians(angle_deg)
    end_x = int(cx + line_len_px * np.cos(angle_rad))
    end_y = int(cy + line_len_px * np.sin(angle_rad))
    cv2.line(img, (cx, cy), (end_x, end_y), (255, 255, 255), line_w_px)


def test_find_marker_positive(recognizer):
    # Solid black circle with white line pointing east (0°)
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 0)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(center[0] - 100) <= 3
    assert abs(center[1] - 100) <= 3


def test_find_marker_negative(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255

    found, center, shape, angle = recognizer.find_marker(img)
    assert not found
    assert center is None


def test_find_marker_no_line(recognizer):
    # Solid circle without white line — should not detect as valid marker
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    cv2.circle(img, (100, 100), 25, (0, 0, 0), -1)

    found, center, shape, angle = recognizer.find_marker(img)
    assert not found


def test_find_marker_circle_east(recognizer):
    # White line pointing east (0°)
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 0)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"
    assert abs(center[0] - 100) <= 3
    assert abs(center[1] - 100) <= 3
    assert abs(angle) <= 20.0 or abs(angle - 360) <= 20.0


def test_find_marker_circle_south(recognizer):
    # White line pointing south (90°)
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 90)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"
    assert abs(center[0] - 100) <= 3
    assert abs(center[1] - 100) <= 3
    assert abs(angle - 90.0) <= 20.0


def test_find_marker_circle_west(recognizer):
    # White line pointing west (180°)
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 180)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"
    assert abs(angle - 180.0) <= 20.0


def test_find_marker_circle_north(recognizer):
    # White line pointing north (270°)
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 270)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"
    assert abs(angle - 270.0) <= 20.0


def test_find_marker_solid_circle_with_line(recognizer):
    # Full new-design marker: solid black circle + white direction line
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 20, 90)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"
    assert abs(center[0] - 100) <= 3
    assert abs(center[1] - 100) <= 3
    assert abs(angle - 90.0) <= 20.0


def test_find_marker_angle_45(recognizer):
    # White line at 45°
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 45)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(angle - 45.0) <= 20.0


def test_find_marker_angle_135(recognizer):
    # White line at 135°
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 135)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(angle - 135.0) <= 20.0


def test_find_marker_angle_225(recognizer):
    # White line at 225°
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 225)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(angle - 225.0) <= 20.0


def test_find_marker_angle_315(recognizer):
    # White line at 315°
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 315)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(angle - 315.0) <= 20.0


def test_find_marker_multiple_returns_best(recognizer):
    # Two markers — should return the one with highest confidence
    img = np.ones((400, 400, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 25, 0)
    _draw_solid_circle_marker(img, 300, 300, 25, 90)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    # Should return one of the two markers
    assert shape == "circle"


def test_find_marker_small_circle(recognizer):
    # Smaller circle — should still detect
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 100, 100, 15, 0, line_len_px=10, line_w_px=3)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert shape == "circle"


def test_find_marker_off_center(recognizer):
    # Marker not at image center
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    _draw_solid_circle_marker(img, 50, 150, 20, 45)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(center[0] - 50) <= 3
    assert abs(center[1] - 150) <= 3
