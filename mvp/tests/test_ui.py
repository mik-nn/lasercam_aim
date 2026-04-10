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

    def config(self, **kwargs):
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
        self._width = 400
        self._height = 400

    def pack(self, *args, **kwargs):
        pass

    def create_image(self, *args, **kwargs):
        pass

    def create_rectangle(self, *args, **kwargs):
        pass

    def create_line(self, *args, **kwargs):
        pass

    def create_oval(self, *args, **kwargs):
        pass

    def create_text(self, *args, **kwargs):
        pass

    def itemconfig(self, item, **kwargs):
        pass

    def winfo_width(self):
        return self._width

    def winfo_height(self):
        return self._height

    def delete(self, *args, **kwargs):
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
        "mvp.ui", "mvp.app", "mvp.camera", "mvp.camera_simulator", "mvp.controller",
        "mvp.bridge",
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
    mock_controller.move_to.return_value = None
    mock_controller.move_in_direction.return_value = None
    mock_controller.release.return_value = None
    # Add a mock simulator for tests that need it
    mock_sim = MagicMock()
    mock_sim.work_area = np.ones((500, 500, 3), dtype=np.uint8)
    mock_sim.camera_x_mm = 0
    mock_sim.camera_y_mm = 0
    mock_sim.workspace_pixels_per_mm = 5
    mock_sim.camera_fov_mm = (20, 20)
    mock_sim.camera_fov_px = (100, 100)
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
    """When update() detects a circle marker in SEARCH_M1, state → CONFIRM_M1."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (True, (50, 50), "circle", 45.0)

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after"):
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(camera=mock_camera, controller=mock_controller)
                    # Start process to transition from START → SEARCH_M1
                    app.start_process()
                    # Run update to trigger detection → CONFIRM_M1
                    app.update()

    assert app.state == "CONFIRM_M1"


def test_ui_state_register_m1():
    """After confirm_m1(), state → REGISTER_M1, then Alt+1 sent, then SEARCH_M2."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (False, None, None, None)

    mock_bridge = MagicMock()
    mock_bridge.send_alt_1.return_value = True

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after") as mock_after:
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(
                        camera=mock_camera,
                        controller=mock_controller,
                        bridge=mock_bridge,
                    )
                    # Set workspace bounds large enough for the test
                    app.workspace_w_mm = 1000.0
                    app.workspace_h_mm = 1000.0
                    app.state = "CONFIRM_M1"
                    app.detected_marker = ((50, 50), "circle", 45.0)
                    app.confirm_m1()

    # confirm_m1 transitions to REGISTER_M1
    assert app.state == "REGISTER_M1"
    mock_after.assert_called_with(app.delay, app._register_m1)

    # Call _register_m1 to move laser to position
    app.m1_marker_pos = (100.0, 50.0)
    app._register_m1()

    # Should have moved laser to position
    mock_controller.move_to.assert_called()

    # Now call _next_after_m1 to send Alt+1 and go to SEARCH_M2
    app._next_after_m1()

    # Should have sent Alt+1
    mock_bridge.send_alt_1.assert_called_once()
    # Should transition to SEARCH_M2
    assert app.state == "SEARCH_M2"


def test_ui_state_navigate_to_m2():
    """After REGISTER_M1, _nav_step navigates toward M2 using direction angle."""
    import mvp.ui

    mock_controller = _make_mock_controller()
    mock_camera = _make_sim_camera(mock_controller)
    mock_camera.find_marker.return_value = (False, None, None, None)

    mock_bridge = MagicMock()
    mock_bridge.send_alt_1.return_value = True
    mock_bridge.send_alt_2.return_value = True

    with _patch_as_camera_sim(mock_camera):
        with patch("mvp.ui.App.after"):
            with patch("mvp.ui.ImageTk.PhotoImage"):
                with patch("mvp.ui.Image.fromarray"):
                    app = mvp.ui.App(
                        camera=mock_camera,
                        controller=mock_controller,
                        bridge=mock_bridge,
                    )
                    app.workspace_w_mm = 1000.0
                    app.workspace_h_mm = 1000.0
                    app.state = "SEARCH_M2"
                    app.m1_angle_deg = 45.0
                    app.m1_camera_pos = (0, 0)
                    app.nav_steps_done = 0

    # Call _nav_step manually — moves by HALF FOV
    app._nav_step()
    half_fov = app._fov_step() / 2.0
    mock_controller.move_in_direction.assert_called_once_with(45.0, half_fov)
    # The state should remain SEARCH_M2 after one step (no M2 found yet)
    assert app.state == "SEARCH_M2"


def test_ui_reset_to_start():
    """reset_to_start() from any state resets state to START."""
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
                    app.detected_marker = ((50, 50), "circle", 45.0)
                    app.reset_to_start()

    assert app.state == "START"
    assert app.detected_marker is None
    assert app.m1_angle_deg is None
