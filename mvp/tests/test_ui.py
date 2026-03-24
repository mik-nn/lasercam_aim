import sys
from unittest.mock import MagicMock, patch

import cv2  # noqa: F401 — pre-load cv2 before any fixture modifies sys.modules
import numpy as np
import pytest


# Dummy classes to avoid MagicMock __init__ issues
class DummyTk:
    def __init__(self, *args, **kwargs):
        pass

    def title(self, title):
        pass

    def after(self, delay, callback):
        pass

    def mainloop(self):
        pass

    def protocol(self, name, func):
        pass

    def destroy(self):
        pass

    def bind(self, name, func):
        pass


class DummyFrame:
    def __init__(self, master=None, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass


class DummyCanvas:
    def __init__(self, master=None, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass

    def create_image(self, *args, **kwargs):
        pass

    def create_rectangle(self, *args, **kwargs):
        pass

    def create_line(self, *args, **kwargs):
        pass


# Use a fixture to mock tkinter and related modules for these tests
@pytest.fixture(autouse=True)
def mock_gui_dependencies():
    mock_tk_mod = MagicMock()
    mock_tk_mod.Tk = DummyTk
    mock_tk_mod.Frame = DummyFrame
    mock_tk_mod.Canvas = DummyCanvas
    mock_tk_mod.LEFT = "left"
    mock_tk_mod.RIGHT = "right"
    mock_tk_mod.NW = "nw"
    mock_tk_mod.LAST = "last"

    # Remove mvp modules from sys.modules to force re-import with mocks
    for mod in [
        "mvp.ui", "mvp.app", "mvp.camera", "mvp.camera_simulator", "mvp.controller"
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    # Protect cv2 and its submodules from being evicted by patch.dict on exit
    cv2_mods = {
        k: v for k, v in sys.modules.items() if k == "cv2" or k.startswith("cv2.")
    }
    with patch.dict(
        sys.modules,
        {
            **cv2_mods,
            "tkinter": mock_tk_mod,
            "tkinter.ttk": MagicMock(),
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
            "PIL.ImageTk": MagicMock(),
        },
    ):
        yield


def _make_mock_controller():
    mock_controller = MagicMock()
    mock_controller.position = (0, 0)
    mock_controller.move_by.return_value = None
    mock_controller.move_in_direction.return_value = None
    mock_controller.release.return_value = None
    # Add a mock simulator for tests that need it
    mock_sim = MagicMock()
    mock_sim.work_area = np.ones((500, 500, 3), dtype=np.uint8)
    mock_sim.camera_x_mm = 0
    mock_sim.camera_y_mm = 0
    mock_sim.workspace_pixels_per_mm = 5
    mock_sim.camera_fov_mm = (20, 20)
    mock_controller._simulator = mock_sim
    return mock_controller


def _make_sim_camera(controller):
    """Create a MagicMock camera with realistic simulator attributes."""
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_camera = MagicMock()
    mock_camera.get_frame.return_value = frame
    mock_camera.find_marker.return_value = (False, None, None, None)
    mock_camera.controller = controller
    mock_camera.simulator = controller._simulator
    return mock_camera


def _patch_as_camera_sim(mock_camera):
    """Patch sys.modules so isinstance(mock_camera, CameraSimulator) is True."""
    mock_cs_mod = MagicMock()
    mock_cs_mod.CameraSimulator = type(mock_camera)
    # also need to patch SimulatedController for the nav step boundary check
    mock_controller_mod = MagicMock()
    mock_controller_mod.SimulatedController = type(mock_camera.controller)
    return patch.dict(
        sys.modules,
        {"mvp.camera_simulator": mock_cs_mod, "mvp.controller": mock_controller_mod},
    )


def test_ui_init():
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    with patch("mvp.ui.App.update"):
        app = mvp.ui.App(camera=mock_camera, controller=mock_controller)
        assert app.camera == mock_camera
        assert app.controller == mock_controller


def test_ui_update():
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_camera.get_frame.return_value = frame
    mock_camera.find_marker.return_value = (False, None, None, None)

    with patch("mvp.ui.App.after"):  # Avoid infinite loop
        with patch("mvp.ui.ImageTk.PhotoImage"):
            with patch("mvp.ui.Image.fromarray"):
                app = mvp.ui.App(camera=mock_camera, controller=mock_controller)
                # Clear mocks because they are called in __init__
                mock_camera.get_frame.reset_mock()

                app.update()

                mock_camera.get_frame.assert_called()


def test_ui_state_confirm_m1():
    """When update() detects a square marker in IDLE, state → CONFIRM_M1."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (True, (50, 50), "square", 45.0)

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after"):
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(camera=mock_camera, controller=mock_controller)

    assert app.state == "CONFIRM_M1"


def test_ui_state_navigate_to_m2():
    """After confirm_m1(), state → NAVIGATE_TO_M2."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (False, None, None, None)

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after") as mock_after:
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(camera=mock_camera, controller=mock_controller)
                    app.state = "CONFIRM_M1"
                    app.detected_marker = ((50, 50), "square", 45.0)
                    app.confirm_m1()

    assert app.state == "NAVIGATE_TO_M2"
    mock_after.assert_called_with(app.delay, app._nav_step)

    # To test _nav_step, we call it manually
    app._nav_step()
    mock_controller.move_in_direction.assert_called_once_with(45.0, app.NAV_STEP_MM)
    # The state should remain NAVIGATE_TO_M2 after one step
    assert app.state == "NAVIGATE_TO_M2"


def test_ui_cancel_returns_to_idle():
    """cancel_to_idle() from any state resets state to IDLE."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (False, None, None, None)

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after"):
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(camera=mock_camera, controller=mock_controller)
                    app.state = "CONFIRM_M1"
                    app.detected_marker = ((50, 50), "square", 45.0)
                    app.cancel_to_idle()

    assert app.state == "IDLE"
