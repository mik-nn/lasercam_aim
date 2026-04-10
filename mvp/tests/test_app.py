import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mvp.app import Application

# Mock tkinter before it's imported by mvp.app
mock_tk = MagicMock()
sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()

# Path to the config file
_CFG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "lasercam.json")


@pytest.fixture(autouse=True)
def _clean_config():
    """Remove any persisted config before each test so defaults are used."""
    if os.path.exists(_CFG_PATH):
        os.remove(_CFG_PATH)
    yield
    if os.path.exists(_CFG_PATH):
        os.remove(_CFG_PATH)


def imread_side_effect(path, *args, **kwargs):
    if "HoneyComb.jpg" in path:
        return np.zeros((2000, 2000, 3), dtype=np.uint8)
    else:  # marker.png
        return np.zeros((50, 50, 3), dtype=np.uint8)


@patch("mvp.app.App")
@patch("mvp.app.get_bridge")
@patch("cv2.imread")
def test_app_init_simulator(mock_imread, mock_get_bridge, mock_ui_app):
    mock_imread.side_effect = imread_side_effect

    app = Application()

    assert app.camera is not None
    assert app.bridge is not None
    assert app.ui is not None
    mock_ui_app.assert_called_once()


@patch("mvp.app.App")
@patch("mvp.app.get_bridge")
def test_app_run(mock_get_bridge, mock_ui_app):
    app = Application()
    app.run()
    app.ui.mainloop.assert_called_once()  # type: ignore
