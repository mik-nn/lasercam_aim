import cv2
import numpy as np
import pytest

from mvp.recognizer import MarkerRecognizer


@pytest.fixture
def recognizer():
    return MarkerRecognizer()


def test_find_marker_positive(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (40, 40), (60, 60), (0, 0, 0), 2)
    cv2.rectangle(img, (48, 48), (52, 52), (0, 0, 0), -1)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(center[0] - 50) <= 1
    assert abs(center[1] - 50) <= 1


def test_find_marker_negative(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255

    found, center, shape, angle = recognizer.find_marker(img)
    assert not found
    assert center is None


def test_find_marker_no_internal(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (40, 40), (60, 60), (0, 0, 0), 2)

    found, center, shape, angle = recognizer.find_marker(img)
    assert not found


def test_find_marker_circle(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.circle(img, (50, 50), 10, (0, 0, 0), 2)
    cv2.circle(img, (50, 50), 3, (0, 0, 0), -1)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(center[0] - 50) <= 1
    assert abs(center[1] - 50) <= 1


def test_find_marker_hollow_with_arrow(recognizer):
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (40, 40), (60, 60), (0, 0, 0), 2)
    cv2.circle(img, (50, 50), 3, (0, 0, 0), -1)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(center[0] - 50) <= 1
    assert abs(center[1] - 50) <= 1


def test_find_marker_angle_direction(recognizer):
    # AICODE-NOTE: internal feature displaced to the right of parent center → angle ~0°
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    # Large square centered at (100, 100): (60,60)-(140,140), marker_size ~80, max_dist ~48
    cv2.rectangle(img, (60, 60), (140, 140), (0, 0, 0), 2)
    # Internal feature 20px to the right of center: centered at (120, 100)
    cv2.rectangle(img, (117, 97), (123, 103), (0, 0, 0), -1)

    found, center, shape, angle = recognizer.find_marker(img)
    assert found
    assert abs(angle) <= 10.0
