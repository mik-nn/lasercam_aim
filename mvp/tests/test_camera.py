from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mvp.camera import Camera


@patch("cv2.VideoCapture")
def test_camera_init(mock_video_capture):
    mock_cap = MagicMock()
    mock_video_capture.return_value = mock_cap

    cam = Camera(camera_index=1)

    mock_video_capture.assert_called_with(1, 700)  # cv2.CAP_DSHOW = 700
    assert cam.cap == mock_cap


@patch("cv2.VideoCapture")
def test_camera_get_frame(mock_video_capture):
    mock_cap = MagicMock()
    mock_video_capture.return_value = mock_cap

    # Mock cap.read()
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, frame)

    cam = Camera()
    returned_frame = cam.get_frame()

    assert returned_frame is frame


@patch("cv2.VideoCapture")
def test_camera_release(mock_video_capture):
    mock_cap = MagicMock()
    mock_video_capture.return_value = mock_cap

    cam = Camera()
    cam.release()

    mock_cap.release.assert_called_once()
