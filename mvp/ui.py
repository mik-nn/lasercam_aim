# mvp/ui.py
import math
import os
import sys
import tkinter as tk

import cv2
from PIL import Image, ImageTk  # type: ignore[import]

# Add the project root to the Python path to support direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from mvp.bridge import LightBurnBridge
from mvp.camera import Camera
from mvp.controller import BaseController

# Display canvas dimensions — half of the 1240×720 sensor resolution,
# preserving the aspect ratio (≈ 1.722 : 1).
_DISPLAY_W = 620
_DISPLAY_H = 360


class App(tk.Tk):
    NAV_MAX_STEPS = 20

    def __init__(
        self,
        camera=None,
        controller: BaseController | None = None,
        bridge: LightBurnBridge | None = None,
        fine_step_mm: float = 0.1,
        coarse_step_mm: float = 0.5,
        large_step_mm: float = 10.0,
        laser_offset_x: float = 0.0,
        laser_offset_y: float = 0.0,
        controller_type: str = "simulated",
        *args,
        **kwargs,
    ):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("LaserCam MVP")
        self.camera = camera if camera else Camera()

        # AICODE-NOTE: controller is resolved here once. For CameraSimulator
        # we infer it from camera.controller; for real cameras the caller must
        # pass a BaseController explicitly (e.g. RuidaController).
        if controller is not None:
            self.controller: BaseController = controller
        elif hasattr(self.camera, "controller"):
            self.controller = getattr(self.camera, "controller")  # type: ignore
        else:
            from mvp.controller import SimulatedController
            from mvp.simulator import MotionSimulator

            self.controller = SimulatedController(MotionSimulator())

        # AICODE-NOTE: LightBurn bridge for hotkey injection (Alt+1 / Alt+2).
        # If not provided, a fake bridge is used for development.
        if bridge is not None:
            self.bridge: LightBurnBridge = bridge
        else:
            from mvp.bridge import get_bridge

            self.bridge = get_bridge()

        # AICODE-NOTE: configurable step sizes for manual movement.
        self.fine_step_mm = fine_step_mm
        self.coarse_step_mm = coarse_step_mm
        self.large_step_mm = large_step_mm
        self._step_mode = "coarse"  # coarse | fine | large

        # AICODE-NOTE: laser-camera offset in mm. When the camera sees a
        # marker at position (cx, cy), the laser must move to
        # (cx + offset_x, cy + offset_y) to be at the same physical point.
        self.laser_offset_x = laser_offset_x
        self.laser_offset_y = laser_offset_y

        # AICODE-NOTE: controller type for display and calibration
        self.controller_type = controller_type

        # AICODE-NOTE: workspace boundary limits (mm). Set from simulator
        # or config. Movement is clamped to these bounds.
        self.workspace_w_mm = 900.0
        self.workspace_h_mm = 600.0
        self._init_workspace_bounds()

        # AICODE-NOTE: Full LightBurn Print&Cut state machine:
        # START → SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 →
        #         SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE → START
        self.state = "START"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None  # Camera position when M1 was confirmed
        self.m1_marker_pos = None  # Actual M1 marker position in world coords
        self.nav_steps_done = 0

        # Main layout
        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        # Emulator workspace view (left)
        self.emulator_canvas = tk.Canvas(self.main_frame, width=400, height=400)
        self.emulator_canvas.pack(side=tk.LEFT)

        # Camera view (right)
        self.canvas = tk.Canvas(self.main_frame, width=_DISPLAY_W, height=_DISPLAY_H)
        self.canvas.pack(side=tk.RIGHT)

        # Control panel
        self.control_panel = tk.Frame(self)
        self.control_panel.pack()

        # Status label (always visible)
        self.status_label = tk.Label(self, text=f"State: {self.state}")
        self.status_label.pack()

        # Controller status label
        self._controller_status = "unknown"
        self.controller_status_label = tk.Label(
            self, text="Controller: unknown", fg="gray"
        )
        self.controller_status_label.pack()

        self._try_detect_controller()

        # Log label — shows recent actions
        self.log_var = tk.StringVar(value="Ready")
        self.log_label = tk.Label(
            self, textvariable=self.log_var, justify=tk.LEFT, anchor=tk.W
        )
        self.log_label.pack(fill=tk.X, padx=10, pady=5)

        # ── Menu bar ──────────────────────────────────────────────
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Preferences", command=self._show_preferences)
        tools_menu.add_command(label="Calibrate Offset", command=self._show_calibration)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

        self.add_controls()

        self.delay = 15
        self.update()

    def _try_detect_controller(self) -> None:
        """Detect controller type and update status label."""
        try:
            from mvp.controller import GRBLController, RuidaController, SimulatedController

            if isinstance(self.controller, GRBLController):
                self._controller_status = "GRBL"
                self.controller_status_label.config(text="Controller: GRBL", fg="green")
            elif isinstance(self.controller, RuidaController):
                self._controller_status = "Ruida"
                self.controller_status_label.config(text="Controller: Ruida", fg="green")
            elif isinstance(self.controller, SimulatedController):
                self._controller_status = "Simulated"
                self.controller_status_label.config(text="Controller: Simulated", fg="orange")
            else:
                self._controller_status = "Unknown"
                self.controller_status_label.config(text="Controller: Unknown", fg="red")
        except (TypeError, ImportError):
            # During tests with mocked modules, isinstance may fail
            self._controller_status = "Simulated"
            self.controller_status_label.config(text="Controller: Simulated", fg="orange")

    def _reconnect_controller(self, cfg) -> None:
        """Recreate the controller with new config parameters."""
        from mvp.controller import GRBLController, RuidaController, SimulatedController
        from mvp.simulator import MotionSimulator

        # Release old controller
        try:
            self.controller.release()
        except Exception:
            pass

        if cfg.controller == "grbl":
            try:
                self.controller = GRBLController(
                    port=cfg.grbl_port,
                    baudrate=cfg.grbl_baudrate,
                    timeout=1.0,
                    retries=3,
                )
                pos = self.controller.position
                self._log(f"GRBL connected on {cfg.grbl_port}. Position: {pos}")
            except Exception as e:
                self._log(f"GRBL connection failed: {e}. Using simulated.")
                self.controller = SimulatedController(MotionSimulator())
        elif cfg.controller == "ruida":
            try:
                self.controller = RuidaController(
                    host=cfg.ruida_host,
                    port=cfg.ruida_port,
                    timeout=1.0,
                    retries=3,
                )
                pos = self.controller.position
                self._log(f"Ruida connected at {cfg.ruida_host}:{cfg.ruida_port}. Position: {pos}")
            except Exception as e:
                self._log(f"Ruida connection failed: {e}. Using simulated.")
                self.controller = SimulatedController(MotionSimulator())
        else:
            self.controller = SimulatedController(MotionSimulator())
            self._log("Using simulated controller.")

        # AICODE-NOTE: Also update the CameraSimulator's controller so
        # camera view and UI use the same controller.
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            self.camera.controller = self.controller

        self.controller_type = cfg.controller
        self._try_detect_controller()
        self.add_controls()

    def _log(self, message):
        """Append a message to the visible log."""
        self.log_var.set(message)
        if hasattr(self, "update_idletasks"):
            self.update_idletasks()

    # ------------------------------------------------------------------
    # Workspace bounds
    # ------------------------------------------------------------------

    def _init_workspace_bounds(self):
        """Detect workspace size from simulator if available."""
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            sim = self.camera.simulator
            wa_h_px, wa_w_px = sim.work_area.shape[:2]
            self.workspace_w_mm = wa_w_px / sim.workspace_pixels_per_mm
            self.workspace_h_mm = wa_h_px / sim.workspace_pixels_per_mm

    def _clamp_position(self, x: float, y: float) -> tuple[float, float]:
        """Clamp position to workspace bounds, accounting for FOV."""
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            sim = self.camera.simulator
            hfx = sim.camera_fov_mm[0] / 2
            hfy = sim.camera_fov_mm[1] / 2
        else:
            # Default FOV half-size if not a simulator (small for testing)
            hfx, hfy = 10.0, 10.0

        cx = max(hfx, min(self.workspace_w_mm - hfx, x))
        cy = max(hfy, min(self.workspace_h_mm - hfy, y))
        return cx, cy

    def _fov_step(self) -> float:
        """Return the FOV size for navigation steps."""
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            return min(self.camera.simulator.camera_fov_mm)
        return 50.0  # default FOV size

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    @property
    def current_step(self) -> float:
        """Return the current step size based on mode and state."""
        if self.state in ("CONFIRM_M1", "CONFIRM_M2"):
            return self.fine_step_mm
        return {
            "fine": self.fine_step_mm,
            "coarse": self.coarse_step_mm,
            "large": self.large_step_mm,
        }.get(self._step_mode, self.coarse_step_mm)

    def add_controls(self):
        self.status_label.config(text=f"State: {self.state}")

        if hasattr(self.control_panel, "winfo_children"):
            for child in self.control_panel.winfo_children():
                child.destroy()

        btn_frame = tk.Frame(self.control_panel)
        btn_frame.pack()

        # START state: show Connect button
        if self.state == "START":
            tk.Button(
                btn_frame,
                text="▶ Connect & Start",
                command=self._connect_and_start,
                bg="green",
                fg="white",
                font=("", 14),
            ).grid(row=0, column=0, columnspan=2, pady=10)
            # Show current controller type and offset
            info_text = (
                f"Controller: {self.controller_type}\n"
                f"Offset: ({self.laser_offset_x:.1f}, {self.laser_offset_y:.1f}) mm"
            )
            tk.Label(btn_frame, text=info_text, justify=tk.LEFT).grid(
                row=1, column=0, columnspan=2, pady=5
            )
            return

        # REGISTER_M1 and REGISTER_M2: show "Registering..." status, no controls
        if self.state in ("REGISTER_M1", "REGISTER_M2"):
            reg_text = (
                "Registering M1..."
                if self.state == "REGISTER_M1"
                else "Registering M2..."
            )
            tk.Label(
                btn_frame,
                text=reg_text,
                font=("", 12),
            ).grid(row=0, column=0, columnspan=2, pady=10)
            return

        # DONE state: show completion message
        if self.state == "DONE":
            tk.Label(
                btn_frame,
                text="Both markers registered!",
                font=("", 12, "bold"),
                fg="green",
            ).grid(row=0, column=0, columnspan=2, pady=10)
            return

        step = self.current_step

        def _nav_buttons(row_offset=0):
            tk.Button(
                btn_frame, text="↑", command=lambda: self.move_gantry_clamped(0, -step)
            ).grid(row=row_offset + 0, column=1)
            tk.Button(
                btn_frame, text="←", command=lambda: self.move_gantry_clamped(-step, 0)
            ).grid(row=row_offset + 1, column=0)
            tk.Button(
                btn_frame, text="→", command=lambda: self.move_gantry_clamped(step, 0)
            ).grid(row=row_offset + 1, column=2)
            tk.Button(
                btn_frame, text="↓", command=lambda: self.move_gantry_clamped(0, step)
            ).grid(row=row_offset + 2, column=1)
            tk.Label(btn_frame, text=f"{step} mm/step").grid(
                row=row_offset + 1, column=3, padx=6
            )

        def _step_buttons(row_offset=3):
            """Buttons to switch between step sizes."""
            for i, (mode, label) in enumerate(
                [
                    ("fine", "Fine"),
                    ("coarse", "Coarse"),
                    ("large", "Large"),
                ]
            ):
                bg = "lightblue" if self._step_mode == mode else "white"
                tk.Button(
                    btn_frame,
                    text=f"{label}\n({getattr(self, f'{mode}_step_mm')}mm)",
                    command=lambda m=mode: self._set_step_mode(m),
                    bg=bg,
                ).grid(row=row_offset, column=i, padx=2)

        def _goto_buttons(row_offset=4):
            """Entry fields and button for absolute coordinate movement."""
            tk.Label(btn_frame, text="X:").grid(row=row_offset, column=0, sticky=tk.E)
            x_var = tk.StringVar(value=f"{self.controller.position[0]:.1f}")
            x_entry = tk.Entry(btn_frame, textvariable=x_var, width=8)
            x_entry.grid(row=row_offset, column=1)

            tk.Label(btn_frame, text="Y:").grid(row=row_offset, column=2, sticky=tk.E)
            y_var = tk.StringVar(value=f"{self.controller.position[1]:.1f}")
            y_entry = tk.Entry(btn_frame, textvariable=y_var, width=8)
            y_entry.grid(row=row_offset, column=3)

            def _go_to():
                try:
                    x = float(x_var.get())
                    y = float(y_var.get())
                    self.move_gantry_to_clamped(x, y)
                except ValueError:
                    pass

            tk.Button(btn_frame, text="Go To", command=_go_to, bg="lightgreen").grid(
                row=row_offset, column=4, padx=4
            )

        if self.state in ("SEARCH_M1", "SEARCH_M2"):
            _nav_buttons()
            _step_buttons()
            _goto_buttons()
            tk.Button(
                btn_frame,
                text="Reset",
                command=self.reset_to_start,
                bg="red",
                fg="white",
            ).grid(row=5, column=4, padx=10)

        elif self.state == "CONFIRM_M1":
            # AICODE-NOTE: fine nav arrows + step label; camera shows 3× zoom.
            _nav_buttons()
            _step_buttons()
            tk.Button(
                btn_frame,
                text="Confirm M1",
                command=self.confirm_m1,
                bg="green",
                fg="white",
            ).grid(row=1, column=4, padx=10)
            tk.Button(
                btn_frame,
                text="Reset",
                command=self.reset_to_start,
                bg="red",
                fg="white",
            ).grid(row=1, column=5, padx=5)

        elif self.state == "REGISTER_M1":
            tk.Button(
                btn_frame,
                text="Next",
                command=self._next_after_m1,
                bg="green",
                fg="white",
            ).grid(row=0, column=0, padx=5)
            tk.Button(
                btn_frame,
                text="Reset",
                command=self.reset_to_start,
                bg="red",
                fg="white",
            ).grid(row=1, column=0, padx=5)

        elif self.state == "NAVIGATE_TO_M2":
            _step_buttons()
            tk.Button(
                btn_frame,
                text="Cancel",
                command=self.reset_to_start,
                bg="red",
                fg="white",
            ).grid(row=0, column=0, padx=5)

        elif self.state == "CONFIRM_M2":
            # AICODE-NOTE: fine nav arrows for M2 position tuning; zoomed view.
            _nav_buttons()
            _step_buttons()
            tk.Button(
                btn_frame,
                text="Confirm M2",
                command=self.confirm_m2,
                bg="green",
                fg="white",
            ).grid(row=1, column=4, padx=10)
            tk.Button(
                btn_frame,
                text="Reset",
                command=self.reset_to_start,
                bg="red",
                fg="white",
            ).grid(row=1, column=5, padx=5)

    def _set_step_mode(self, mode: str) -> None:
        """Switch the manual step size mode and redraw controls."""
        self._step_mode = mode
        self.add_controls()

    # ------------------------------------------------------------------
    # Movement — always via controller, clamped to workspace bounds
    # ------------------------------------------------------------------

    def move_gantry(self, dx: float, dy: float) -> None:
        """Move by relative amount (no clamping)."""
        self.controller.move_by(dx, dy)

    def move_gantry_clamped(self, dx: float, dy: float) -> None:
        """Move by relative amount, clamped to workspace bounds."""
        cx, cy = self.controller.position
        new_x, new_y = self._clamp_position(cx + dx, cy + dy)
        self.controller.move_to(new_x, new_y)
        # AICODE-NOTE: refresh controls after movement to update position display
        self.add_controls()

    def move_gantry_to(self, x: float, y: float) -> None:
        """Move gantry to absolute coordinates (no clamping)."""
        self.controller.move_to(x, y)
        self.add_controls()

    def move_gantry_to_clamped(self, x: float, y: float) -> None:
        """Move gantry to absolute coordinates, clamped to workspace bounds."""
        cx, cy = self._clamp_position(x, y)
        self.controller.move_to(cx, cy)
        self.add_controls()

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _connect_and_start(self) -> None:
        """Verify controller connection, then begin the alignment process."""
        from mvp.controller import GRBLController, RuidaController

        if isinstance(self.controller, (GRBLController, RuidaController)):
            try:
                pos = self.controller.position
                self._log(f"Controller connected. Position: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            except Exception as e:
                self._log(f"Connection failed: {e}")
                return

        self.start_process()

    def start_process(self) -> None:
        """Begin the alignment process — transition from START to SEARCH_M1."""
        self._log("Starting marker detection. Move camera toward M1 at (809, 480) mm")
        self.state = "SEARCH_M1"
        self.add_controls()

    def reset_to_start(self) -> None:
        """Reset the entire process back to START state."""
        self.state = "START"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None
        self.m1_marker_pos = None
        self.nav_steps_done = 0
        self.add_controls()

    def confirm_m1(self) -> None:
        """User confirmed M1 position. Move to REGISTER_M1 state."""
        if self.detected_marker is None:
            return
        center, shape_type, angle_deg = self.detected_marker
        if angle_deg is None:
            return  # direction is required for autonomous M2 navigation
        self.m1_angle_deg = angle_deg
        self.m1_camera_pos = self.controller.position

        # AICODE-NOTE: Store actual M1 marker position in world coordinates
        # for proper exclusion during M2 search
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator) and center is not None:
            fov_w, fov_h = self.camera.simulator.camera_fov_mm
            res_w, res_h = self.camera.simulator.camera_fov_px
            ppm_x = res_w / fov_w
            ppm_y = res_h / fov_h
            hfx = fov_w / 2
            hfy = fov_h / 2
            self.m1_marker_pos = (
                self.camera.simulator.camera_x_mm - hfx + center[0] / ppm_x,
                self.camera.simulator.camera_y_mm - hfy + center[1] / ppm_y,
            )
        else:
            self.m1_marker_pos = self.controller.position

        self.nav_steps_done = 0
        self.state = "REGISTER_M1"
        self.add_controls()
        self.after(self.delay, self._register_m1)

    def confirm_m2(self) -> None:
        """User confirmed M2 position. Move to REGISTER_M2 state."""
        if self.detected_marker is None:
            return
        self.state = "REGISTER_M2"
        self.add_controls()
        self.after(self.delay, self._register_m2)

    def _reset_to_start(self) -> None:
        """Auto-reset from DONE back to START."""
        self.state = "START"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None
        self.m1_marker_pos = None
        self.nav_steps_done = 0
        self.add_controls()

    # ------------------------------------------------------------------
    # Preferences — Controller and system configuration
    # ------------------------------------------------------------------

    def _show_preferences(self) -> None:
        """Show preferences dialog with controller parameters."""
        from mvp.config import Config

        cfg = Config.load()

        dialog = tk.Toplevel(self)
        dialog.title("Preferences")
        dialog.geometry("500x550")
        dialog.transient(self)
        dialog.grab_set()

        # ── Controller Type ────────────────────────────────────────
        ctrl_frame = tk.LabelFrame(dialog, text="Controller", padx=10, pady=10)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)

        ctrl_type_var = tk.StringVar(value=cfg.controller)
        for i, (val, label) in enumerate(
            [
                ("simulated", "Simulated"),
                ("grbl", "GRBL (Serial)"),
                ("ruida", "Ruida (UDP)"),
            ]
        ):
            tk.Radiobutton(
                ctrl_frame, text=label, variable=ctrl_type_var, value=val
            ).grid(row=0, column=i, sticky=tk.W, padx=5)

        # ── GRBL Parameters ────────────────────────────────────────
        grbl_frame = tk.LabelFrame(dialog, text="GRBL Serial Port", padx=10, pady=10)
        grbl_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(grbl_frame, text="Port:").grid(row=0, column=0, sticky=tk.E, pady=3)
        grbl_port_var = tk.StringVar(value=cfg.grbl_port)
        tk.Entry(grbl_frame, textvariable=grbl_port_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )

        tk.Label(grbl_frame, text="Baud rate:").grid(row=1, column=0, sticky=tk.E, pady=3)
        grbl_baud_var = tk.StringVar(value=str(cfg.grbl_baudrate))
        tk.Entry(grbl_frame, textvariable=grbl_baud_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5
        )

        tk.Label(grbl_frame, text="Timeout (s):").grid(row=2, column=0, sticky=tk.E, pady=3)
        grbl_timeout_var = tk.StringVar(value="1.0")
        tk.Entry(grbl_frame, textvariable=grbl_timeout_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=5
        )

        tk.Label(grbl_frame, text="Retries:").grid(row=3, column=0, sticky=tk.E, pady=3)
        grbl_retries_var = tk.StringVar(value="3")
        tk.Entry(grbl_frame, textvariable=grbl_retries_var, width=20).grid(
            row=3, column=1, sticky=tk.W, padx=5
        )

        # ── Ruida Parameters ───────────────────────────────────────
        ruida_frame = tk.LabelFrame(dialog, text="Ruida UDP", padx=10, pady=10)
        ruida_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(ruida_frame, text="Host:").grid(row=0, column=0, sticky=tk.E, pady=3)
        ruida_host_var = tk.StringVar(value=cfg.ruida_host)
        tk.Entry(ruida_frame, textvariable=ruida_host_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )

        tk.Label(ruida_frame, text="Port:").grid(row=1, column=0, sticky=tk.E, pady=3)
        ruida_port_var = tk.StringVar(value=str(cfg.ruida_port))
        tk.Entry(ruida_frame, textvariable=ruida_port_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5
        )

        tk.Label(ruida_frame, text="Timeout (s):").grid(row=2, column=0, sticky=tk.E, pady=3)
        ruida_timeout_var = tk.StringVar(value="1.0")
        tk.Entry(ruida_frame, textvariable=ruida_timeout_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=5
        )

        tk.Label(ruida_frame, text="Retries:").grid(row=3, column=0, sticky=tk.E, pady=3)
        ruida_retries_var = tk.StringVar(value="3")
        tk.Entry(ruida_frame, textvariable=ruida_retries_var, width=20).grid(
            row=3, column=1, sticky=tk.W, padx=5
        )

        # ── Camera Parameters ──────────────────────────────────────
        cam_frame = tk.LabelFrame(dialog, text="Camera", padx=10, pady=10)
        cam_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cam_frame, text="FOV width (mm):").grid(row=0, column=0, sticky=tk.E, pady=3)
        fov_w_var = tk.StringVar(value=str(cfg.camera_fov_mm[0]))
        tk.Entry(cam_frame, textvariable=fov_w_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )

        tk.Label(cam_frame, text="FOV height (mm):").grid(row=1, column=0, sticky=tk.E, pady=3)
        fov_h_var = tk.StringVar(value=str(cfg.camera_fov_mm[1]))
        tk.Entry(cam_frame, textvariable=fov_h_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5
        )

        tk.Label(cam_frame, text="Resolution W:").grid(row=2, column=0, sticky=tk.E, pady=3)
        res_w_var = tk.StringVar(value=str(cfg.camera_resolution[0]))
        tk.Entry(cam_frame, textvariable=res_w_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=5
        )

        tk.Label(cam_frame, text="Resolution H:").grid(row=3, column=0, sticky=tk.E, pady=3)
        res_h_var = tk.StringVar(value=str(cfg.camera_resolution[1]))
        tk.Entry(cam_frame, textvariable=res_h_var, width=20).grid(
            row=3, column=1, sticky=tk.W, padx=5
        )

        # ── Laser-Camera Offset ────────────────────────────────────
        offset_frame = tk.LabelFrame(dialog, text="Laser-Camera Offset (mm)", padx=10, pady=10)
        offset_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(offset_frame, text="Offset X:").grid(row=0, column=0, sticky=tk.E, pady=3)
        offset_x_var = tk.StringVar(value=str(cfg.laser_offset_x))
        tk.Entry(offset_frame, textvariable=offset_x_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )

        tk.Label(offset_frame, text="Offset Y:").grid(row=1, column=0, sticky=tk.E, pady=3)
        offset_y_var = tk.StringVar(value=str(cfg.laser_offset_y))
        tk.Entry(offset_frame, textvariable=offset_y_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5
        )

        # ── Buttons ────────────────────────────────────────────────
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def _save():
            """Save preferences to config, reconnect controller, and apply."""
            cfg.controller = ctrl_type_var.get()
            cfg.grbl_port = grbl_port_var.get()
            try:
                cfg.grbl_baudrate = int(grbl_baud_var.get())
            except ValueError:
                pass
            cfg.ruida_host = ruida_host_var.get()
            try:
                cfg.ruida_port = int(ruida_port_var.get())
            except ValueError:
                pass
            try:
                cfg.camera_fov_mm = (float(fov_w_var.get()), float(fov_h_var.get()))
            except ValueError:
                pass
            try:
                cfg.camera_resolution = (int(res_w_var.get()), int(res_h_var.get()))
            except ValueError:
                pass
            try:
                cfg.laser_offset_x = float(offset_x_var.get())
                cfg.laser_offset_y = float(offset_y_var.get())
            except ValueError:
                pass

            cfg.save()
            self.laser_offset_x = cfg.laser_offset_x
            self.laser_offset_y = cfg.laser_offset_y

            # Reconnect controller with new parameters
            self._reconnect_controller(cfg)

            dialog.destroy()

        def _test_connection():
            """Test connection using the existing controller (don't create new socket)."""
            from mvp.controller import GRBLController, RuidaController, SimulatedController

            if isinstance(self.controller, SimulatedController):
                self._log("Simulated controller — always connected.")
            elif isinstance(self.controller, (GRBLController, RuidaController)):
                try:
                    pos = self.controller.position
                    ctrl_name = "GRBL" if isinstance(self.controller, GRBLController) else "Ruida"
                    self._log(f"{ctrl_name} connected. Position: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
                except Exception as e:
                    self._log(f"Connection test failed: {e}")
            else:
                self._log(f"Unknown controller type: {type(self.controller).__name__}")

        tk.Button(btn_frame, text="Test Connection", command=_test_connection).grid(
            row=0, column=0, padx=5
        )
        tk.Button(btn_frame, text="Save", command=_save, bg="green", fg="white").grid(
            row=0, column=1, padx=5
        )
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy).grid(
            row=0, column=2, padx=5
        )

    # ------------------------------------------------------------------
    # Calibration — Calculate laser-camera offset
    # ------------------------------------------------------------------

    def _show_calibration(self) -> None:
        """Show calibration dialog with jog controls, zoomed view, and green circle.

        Procedure:
        1. Move laser to material area
        2. Draw calibration marker (circle + cross)
        3. Use jog controls to position marker in camera FOV
        4. When detected, shows zoomed view with green circle overlay
        5. Fine-tune with jog arrows to align circle on marker
        6. Confirm → calculate offset, save, close, return to START
        """
        from mvp.camera_simulator import CameraSimulator

        if not isinstance(self.camera, CameraSimulator):
            self._log("Calibration only available in simulator mode.")
            return

        sim = self.camera.simulator

        # Calibration dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Calibrate Laser-Camera Offset")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()

        # State
        laser_pos = [None, None]
        marker_drawn = [False]

        # Top frame: instructions
        tk.Label(
            dialog,
            text="Calibration Procedure\n"
            "1. Move laser to material area → Draw marker\n"
            "2. Use jog controls to find marker in camera view\n"
            "3. Fine-tune position with green circle overlay\n"
            "4. Confirm to save offset and return to START",
            justify=tk.LEFT,
        ).pack(pady=5)

        # Status displays
        status_frame = tk.Frame(dialog)
        status_frame.pack(fill=tk.X, padx=10)

        laser_pos_var = tk.StringVar(value="Laser: not recorded")
        tk.Label(status_frame, textvariable=laser_pos_var).pack(anchor=tk.W)

        cam_pos_var = tk.StringVar(value="Camera: not recorded")
        tk.Label(status_frame, textvariable=cam_pos_var).pack(anchor=tk.W)

        offset_var = tk.StringVar(value="Offset: (0.0, 0.0) mm")
        tk.Label(status_frame, textvariable=offset_var, font=("", 10, "bold")).pack(
            anchor=tk.W
        )

        # Camera view canvas
        view_frame = tk.Frame(dialog)
        view_frame.pack(pady=5)

        canvas = tk.Canvas(view_frame, width=620, height=360)
        canvas.pack()

        # Jog controls frame
        jog_frame = tk.Frame(dialog)
        jog_frame.pack(pady=5)

        step_var = tk.StringVar(value="0.5")

        def _jog(dx, dy):
            step = float(step_var.get())
            self.controller.move_by(dx * step, dy * step)
            pos = self.controller.position
            cam_pos_var.set(f"Camera: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            _update_view()

        def _update_view():
            """Update camera view with marker detection overlay."""
            frame = self.camera.get_frame()
            if frame is None or frame.size == 0:
                return

            found = False
            center = None

            # Detect calibration marker
            if marker_drawn[0] and sim.calibration_marker_pos is not None:
                mx, my = sim.calibration_marker_pos
                cam_x, cam_y = self.controller.position
                fov_w, fov_h = sim.camera_fov_mm

                # Check if marker is in FOV
                if abs(mx - cam_x) < fov_w / 2 and abs(my - cam_y) < fov_h / 2:
                    found = True
                    # Convert to pixel coordinates
                    fh, fw = frame.shape[:2]
                    ppm_x = fw / fov_w
                    ppm_y = fh / fov_h
                    hfx = fov_w / 2
                    hfy = fov_h / 2
                    px = int((mx - cam_x + hfx) * ppm_x)
                    py = int((my - cam_y + hfy) * ppm_y)
                    center = (px, py)

            # Draw overlay
            if found and center is not None:
                # Zoomed view (~3x)
                fh, fw = frame.shape[:2]
                crop_half_h = fh // 6
                crop_half_w = int(crop_half_h * fw / fh)
                x, y = center
                cx_crop = max(crop_half_w, min(fw - crop_half_w, x))
                cy_crop = max(crop_half_h, min(fh - crop_half_h, y))
                x1 = cx_crop - crop_half_w
                y1 = cy_crop - crop_half_h
                x2 = cx_crop + crop_half_w
                y2 = cy_crop + crop_half_h

                zoom = frame[y1:y2, x1:x2].copy()
                zoom = cv2.resize(zoom, (fw, fh), interpolation=cv2.INTER_LINEAR)

                # Green circle overlay
                ocx, ocy = fw // 2, fh // 2
                r = min(fw, fh) // 6
                cv2.circle(zoom, (ocx, ocy), r, (0, 255, 0), 2)
                cv2.line(
                    zoom, (ocx - r // 3, ocy), (ocx + r // 3, ocy), (0, 255, 0), 1
                )
                cv2.line(
                    zoom, (ocx, ocy - r // 3), (ocx, ocy + r // 3), (0, 255, 0), 1
                )

                cv2.putText(
                    zoom,
                    "Calibration Marker — Fine-tune position",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                frame = zoom
            else:
                cv2.putText(
                    frame,
                    "Move camera to find calibration marker",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )

            # Resize for canvas
            frame = cv2.resize(frame, (620, 360))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            canvas.image = photo  # Keep reference

        # Jog buttons
        tk.Label(jog_frame, text="Jog Controls:").grid(
            row=0, column=0, columnspan=3, pady=5
        )

        tk.Button(
            jog_frame, text="↑", width=3, command=lambda: _jog(0, -1)
        ).grid(row=1, column=1)
        tk.Button(
            jog_frame, text="←", width=3, command=lambda: _jog(-1, 0)
        ).grid(row=2, column=0)
        tk.Button(
            jog_frame, text="→", width=3, command=lambda: _jog(1, 0)
        ).grid(row=2, column=2)
        tk.Button(
            jog_frame, text="↓", width=3, command=lambda: _jog(0, 1)
        ).grid(row=3, column=1)

        # Step size selector
        tk.Label(jog_frame, text="Step (mm):").grid(row=2, column=3, padx=10)
        step_entry = tk.Entry(jog_frame, textvariable=step_var, width=6)
        step_entry.grid(row=2, column=4)

        # Action buttons
        action_frame = tk.Frame(dialog)
        action_frame.pack(pady=10)

        def _move_laser_to_material():
            """Move laser to material area."""
            target_x = sim.material_x_mm - sim.material_w_mm / 4
            target_y = sim.material_y_mm
            self.controller.move_to(target_x, target_y)
            pos = self.controller.position
            laser_pos[0], laser_pos[1] = pos
            laser_pos_var.set(f"Laser: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            cam_pos_var.set(f"Camera: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            self._log(f"Laser moved to ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            _update_view()

        def _draw_marker():
            """Draw calibration marker at laser position."""
            pos = self.controller.position
            laser_pos[0], laser_pos[1] = pos
            laser_pos_var.set(f"Laser: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            sim.draw_calibration_marker(pos[0], pos[1])
            marker_drawn[0] = True
            self._log(f"Marker drawn at ({pos[0]:.1f}, {pos[1]:.1f}) mm")
            _update_view()

        def _confirm_calibration():
            """Calculate offset, save, close dialog, return to START."""
            if laser_pos[0] is None:
                self._log("Draw marker first!")
                return

            # Camera position when marker was detected
            cam_x, cam_y = self.controller.position
            # Laser position when marker was drawn
            lx, ly = laser_pos

            # Calculate offset
            ox = lx - cam_x
            oy = ly - cam_y
            offset_var.set(f"Offset: ({ox:.1f}, {oy:.1f}) mm")
            self.laser_offset_x = ox
            self.laser_offset_y = oy
            self._log(f"Offset calculated: ({ox:.1f}, {oy:.1f}) mm")

            # Save to config
            from mvp.config import Config

            cfg = Config.load()
            cfg.laser_offset_x = ox
            cfg.laser_offset_y = oy
            cfg.save()
            self._log("Offset saved to config.")

            dialog.destroy()
            # Return to START state
            self.reset_to_start()
            self._log("Calibration complete. Ready to begin marker detection.")

        tk.Button(
            action_frame,
            text="Move Laser to Material",
            command=_move_laser_to_material,
        ).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(
            action_frame, text="Draw Marker", command=_draw_marker
        ).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(
            action_frame,
            text="Confirm Calibration",
            command=_confirm_calibration,
            bg="green",
            fg="white",
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

        # Initial view update
        _update_view()

    # ------------------------------------------------------------------
    # REGISTER_M1 — Move laser to marker centre, send Alt+1 to LightBurn
    # ------------------------------------------------------------------

    def _register_m1(self) -> None:
        """
        Step 1: Move LASER to M1 marker centre (applying camera-laser offset)
        Step 2: User clicks "Next" to send Alt+1 and start M2 search
        """
        if self.state != "REGISTER_M1":
            return

        if self.m1_camera_pos is None or self.m1_marker_pos is None:
            self.state = "START"
            self.add_controls()
            return

        marker_x, marker_y = self.m1_marker_pos

        # AICODE-NOTE: To move the LASER to the marker, we must move the GANTRY 
        # to (marker - offset), because Laser = Gantry + offset.
        target_gantry_x = marker_x - self.laser_offset_x
        target_gantry_y = marker_y - self.laser_offset_y

        self._log(f"Moving laser to ({marker_x:.1f}, {marker_y:.1f}) mm")
        self.controller.move_to(target_gantry_x, target_gantry_y)

        self._log("Laser positioned. Click 'Next' to register in LightBurn.")
        self.add_controls()

    def _next_after_m1(self) -> None:
        """User clicks Next after laser is positioned at M1."""
        if self.state != "REGISTER_M1":
            return

        self._log("Sending Alt+1 to LightBurn (register M1)...")
        self.bridge.send_alt_1()

        # Move camera back to M1 to start search for M2
        marker_x, marker_y = self.m1_marker_pos
        self._log("Moving camera back to M1 to start search...")
        self.controller.move_to(marker_x, marker_y)

        self._log("Moving camera toward M2...")
        self.state = "SEARCH_M2"
        self.nav_steps_done = 0
        self.add_controls()
        self._start_nav_loop()

    def _start_nav_loop(self) -> None:
        """Start the autonomous navigation loop toward M2."""
        self._nav_step()

    def _nav_step(self) -> None:
        """
        Move CAMERA toward M2 by half FOV.
        After each move, check if M2 is in view.
        If found → go to CONFIRM_M2 (same detection process as M1).
        If edge reached → manual mode.
        """
        if self.state != "SEARCH_M2":
            return

        if self.m1_angle_deg is None:
            self._log("No direction angle. Use manual controls to find M2.")
            self.add_controls()
            return

        # AICODE-NOTE: Move camera by HALF FOV distance toward M2
        fov_step = self._fov_step() / 2.0

        # Workspace boundary check
        cx, cy = self.controller.position
        dx = fov_step * math.cos(math.radians(self.m1_angle_deg))
        dy = fov_step * math.sin(math.radians(self.m1_angle_deg))
        new_x, new_y = cx + dx, cy + dy

        # Clamp to workspace bounds
        clamped_x, clamped_y = self._clamp_position(new_x, new_y)

        # If clamping changed the target, we've hit the edge → manual mode
        if abs(clamped_x - new_x) > 0.1 or abs(clamped_y - new_y) > 0.1:
            self._log("Edge reached. Use manual controls to find M2.")
            self.add_controls()
            return

        self._log(f"Moving camera to M2 (step {self.nav_steps_done + 1})...")
        self.controller.move_in_direction(self.m1_angle_deg, fov_step)
        self.nav_steps_done += 1

        # Check if M2 is now in view (exclude M1 marker position)
        found, center, shape_type, angle_deg = (
            self.camera.find_marker(  # pyright: ignore[reportAttributeAccessIssue]
                prefer_shape="circle",
                exclude_position=self.m1_marker_pos,
            )
        )
        if found and shape_type == "circle":
            # M2 found — stop navigation, go to CONFIRM_M2
            # Same detection process as M1: zoom, green circle, confirm/cancel
            self._log("M2 found! Fine-tune position and confirm.")
            self.detected_marker = (center, shape_type, angle_deg)
            self.state = "CONFIRM_M2"
            self.add_controls()
            return

        if self.nav_steps_done >= self.NAV_MAX_STEPS:
            # Max steps reached — switch to manual mode
            self._log("Max steps reached. Use manual controls to find M2.")
            self.add_controls()
            return

        # Schedule next navigation step
        self.after(self.delay, self._nav_step)

    # ------------------------------------------------------------------
    # REGISTER_M2 — Move laser to marker centre, send Alt+2 to LightBurn
    # ------------------------------------------------------------------

    def _register_m2(self) -> None:
        """
        Step 1: Move LASER to M2 marker centre (applying camera-laser offset)
        Step 2: Send Alt+2 to LightBurn to register M2
        """
        if self.state != "REGISTER_M2":
            return

        if self.detected_marker is None:
            self.state = "START"
            self.add_controls()
            return

        center, _shape_type, _angle = self.detected_marker
        if center is None:
            self.state = "START"
            self.add_controls()
            return

        # Convert image coordinates to world coordinates
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            fov_w, fov_h = self.camera.simulator.camera_fov_mm
            res_w, res_h = self.camera.simulator.camera_fov_px
            ppm_x = res_w / fov_w
            ppm_y = res_h / fov_h
            hfx = fov_w / 2
            hfy = fov_h / 2
            cam_x = self.camera.simulator.camera_x_mm - hfx + center[0] / ppm_x
            cam_y = self.camera.simulator.camera_y_mm - hfy + center[1] / ppm_y
        else:
            cam_x, cam_y = center

        # AICODE-NOTE: cam_x, cam_y is the absolute position of the M2 marker in the world.
        # To position the LASER over M2, we must move the GANTRY to (M2 - offset).
        laser_x = cam_x
        laser_y = cam_y
        target_gantry_x = laser_x - self.laser_offset_x
        target_gantry_y = laser_y - self.laser_offset_y

        self._log(f"Moving laser to ({laser_x:.1f}, {laser_y:.1f}) mm")
        self.controller.move_to(target_gantry_x, target_gantry_y)

        self._log("Sending Alt+2 to LightBurn (register M2)...")
        self.bridge.send_alt_2()

        self._log("Both markers registered! Done.")
        self.state = "DONE"
        self.add_controls()
        self.after(2000, self._reset_to_start)

    # ------------------------------------------------------------------
    # Zoom helper — reusable crop + resize for any detected marker
    # ------------------------------------------------------------------

    def _draw_zoomed_view(self, frame, det_center):
        """Crop and resize frame to ~3× zoom centered on det_center."""
        fh, fw = frame.shape[:2]
        crop_half_h = fh // 6
        crop_half_w = int(crop_half_h * fw / fh)
        x, y = det_center
        cx_crop = max(crop_half_w, min(fw - crop_half_w, x))
        cy_crop = max(crop_half_h, min(fh - crop_half_h, y))
        x1 = cx_crop - crop_half_w
        y1 = cy_crop - crop_half_h
        x2 = cx_crop + crop_half_w
        y2 = cy_crop + crop_half_h
        zoom = frame[y1:y2, x1:x2].copy()
        return cv2.resize(zoom, (fw, fh), interpolation=cv2.INTER_LINEAR)

    # ------------------------------------------------------------------
    # Main update loop
    # ------------------------------------------------------------------

    def update(self) -> None:
        frame = self.camera.get_frame()

        # AICODE-NOTE: guard against empty frames (camera at workspace edge)
        if frame is None or frame.size == 0:
            self.after(self.delay, self.update)
            return

        found: bool = False
        center = None

        # AICODE-NOTE: Import CameraSimulator once at the top of detection logic
        from mvp.camera_simulator import CameraSimulator

        # AICODE-NOTE: START state = view only, no marker detection.
        # SEARCH_M1 = detect M1, auto-transition to CONFIRM_M1.
        # CONFIRM_M1 = keep detecting to track marker while user fine-tunes.
        # SEARCH_M2 (auto-nav) = detect M2 during navigation, stop when found.
        # CONFIRM_M2 = NO auto-detect, user fine-tunes manually.
        # REGISTER_M1/M2/DONE = no detection.

        if self.state == "SEARCH_M1":
            # AICODE-NOTE: sync simulator with controller before detection
            if isinstance(self.camera, CameraSimulator):
                ctrl_x, ctrl_y = self.controller.position
                self.camera.simulator.camera_x_mm = ctrl_x
                self.camera.simulator.camera_y_mm = ctrl_y

            found, center, shape_type, angle_deg = (
                self.camera.find_marker()  # pyright: ignore[reportAttributeAccessIssue]
            )
            if found and shape_type == "circle":
                # AICODE-NOTE: Auto-move camera to marker center (like M2 navigation)
                # Only do this if we have a real simulator with required numeric attributes
                sim = getattr(self.camera, 'simulator', None)
                if (
                    sim
                    and hasattr(sim, 'fov_width_mm')
                    and hasattr(sim, 'work_area')
                    and isinstance(sim.fov_width_mm, (int, float))
                    and sim.work_area.shape[1] > 0
                ):
                    hfx = sim.fov_width_mm / 2.0
                    hfy = sim.fov_height_mm / 2.0
                    ppm_x = sim.work_area.shape[1] / sim.fov_width_mm
                    ppm_y = sim.work_area.shape[0] / sim.fov_height_mm
                    marker_x = sim.camera_x_mm - hfx + center[0] / ppm_x
                    marker_y = sim.camera_y_mm - hfy + center[1] / ppm_y

                    self._log(f"M1 detected, moving camera to ({marker_x:.1f}, {marker_y:.1f}) mm...")
                    self.controller.move_to(marker_x, marker_y)

                    # Sync again after move
                    ctrl_x, ctrl_y = self.controller.position
                    self.camera.simulator.camera_x_mm = ctrl_x
                    self.camera.simulator.camera_y_mm = ctrl_y

                self._log(f"M1 detected at pixel {center}. Adjust position or confirm.")
                self.state = "CONFIRM_M1"
                self.detected_marker = (center, shape_type, angle_deg)
                self.add_controls()
            else:
                # Show distance to M1 to help user navigate
                ctrl_x, ctrl_y = self.controller.position
                from mvp.config import Config
                cfg = Config.load()
                dist = math.sqrt((cfg.m1_x_mm - ctrl_x)**2 + (cfg.m1_y_mm - ctrl_y)**2)
                cv2.putText(
                    frame,
                    f"Move toward M1: {dist:.0f}mm away (need <60mm)",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )

        elif self.state == "CONFIRM_M1":
            # AICODE-NOTE: Same as CONFIRM_M2 - no auto-detection.
            # User fine-tunes position manually with arrow keys.
            pass

        elif self.state == "SEARCH_M2":
            # AICODE-NOTE: sync simulator with controller before detection
            if isinstance(self.camera, CameraSimulator):
                ctrl_x, ctrl_y = self.controller.position
                self.camera.simulator.camera_x_mm = ctrl_x
                self.camera.simulator.camera_y_mm = ctrl_y

            # AICODE-NOTE: During auto-navigation, or manual navigation if edge hit,
            # detect M2. Once found, stop auto-detecting so user can fine-tune manually.
            found, center, shape_type, angle_deg = (
                self.camera.find_marker(  # pyright: ignore[reportAttributeAccessIssue]
                    prefer_shape="circle",
                    exclude_position=self.m1_marker_pos,
                )
            )
            if found and shape_type == "circle":
                # AICODE-NOTE: Auto-move camera to marker center (same as M1)
                # Only do this if we have a real simulator with required numeric attributes
                sim = getattr(self.camera, 'simulator', None)
                if (
                    sim
                    and hasattr(sim, 'fov_width_mm')
                    and hasattr(sim, 'work_area')
                    and isinstance(sim.fov_width_mm, (int, float))
                    and sim.work_area.shape[1] > 0
                ):
                    hfx = sim.fov_width_mm / 2.0
                    hfy = sim.fov_height_mm / 2.0
                    ppm_x = sim.work_area.shape[1] / sim.fov_width_mm
                    ppm_y = sim.work_area.shape[0] / sim.fov_height_mm
                    marker_x = sim.camera_x_mm - hfx + center[0] / ppm_x
                    marker_y = sim.camera_y_mm - hfy + center[1] / ppm_y

                    self._log(f"M2 detected, moving camera to ({marker_x:.1f}, {marker_y:.1f}) mm...")
                    self.controller.move_to(marker_x, marker_y)

                    # Sync again after move
                    ctrl_x, ctrl_y = self.controller.position
                    self.camera.simulator.camera_x_mm = ctrl_x
                    self.camera.simulator.camera_y_mm = ctrl_y

                self._log("M2 found! Fine-tune position and confirm.")
                self.state = "CONFIRM_M2"
                self.detected_marker = (center, shape_type, angle_deg)
                self.add_controls()

        elif self.state == "CONFIRM_M2":
            # AICODE-NOTE: No auto-detection. User has confirmed M2 was found
            # and is now fine-tuning the position manually.
            pass

        # Draw confirm-state overlays (zoom + crosshair + direction arrow)
        if self.state in ("CONFIRM_M1", "CONFIRM_M2") and self.detected_marker:
            det_center, shape_type, angle_deg = self.detected_marker
            if det_center is not None:
                fh, fw = frame.shape[:2]

                # AICODE-NOTE: crop preserving the original frame aspect ratio
                # (fw:fh) around the marker centre. crop_half_h = fh//10 gives
                # ~5× zoom.  The centre is clamped away from frame edges so
                # the crop is always symmetric and the marker stays centred.
                crop_half_h = fh // 10
                crop_half_w = int(crop_half_h * fw / fh)

                x, y = det_center
                cx_crop = max(crop_half_w, min(fw - crop_half_w, x))
                cy_crop = max(crop_half_h, min(fh - crop_half_h, y))
                x1 = cx_crop - crop_half_w
                y1 = cy_crop - crop_half_h
                x2 = cx_crop + crop_half_w
                y2 = cy_crop + crop_half_h

                zoom = frame[y1:y2, x1:x2].copy()
                zoom = cv2.resize(zoom, (fw, fh), interpolation=cv2.INTER_LINEAR)

                # AICODE-NOTE: Draw crosshair at actual frame center, not hardcoded
                ocx, ocy = fw // 2, fh // 2
                colour = (0, 255, 0)
                r = min(fw, fh) // 12  # Decreased from // 6 to make circle smaller
                
                if shape_type == "circle":
                    cv2.circle(zoom, (ocx, ocy), r, colour, 2)
                else:
                    cv2.rectangle(
                        zoom, (ocx - r, ocy - r), (ocx + r, ocy + r), colour, 2
                    )
                cv2.line(zoom, (ocx - r // 3, ocy), (ocx + r // 3, ocy), colour, 1)
                cv2.line(zoom, (ocx, ocy - r // 3), (ocx, ocy + r // 3), colour, 1)

                if angle_deg is not None:
                    zoom_factor = fh / (2 * crop_half_h)
                    ar = math.radians(angle_deg)
                    ex = int(ocx + r * 1.4 * math.cos(ar))
                    ey = int(ocy + r * 1.4 * math.sin(ar))
                    cv2.arrowedLine(
                        zoom, (ocx, ocy), (ex, ey), (0, 165, 255), 2, tipLength=0.3
                    )
                    cv2.putText(
                        zoom,
                        f"Dir: {angle_deg:.0f}deg  [{zoom_factor:.1f}x zoom]",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 165, 255),
                        2,
                    )

                frame = zoom

        elif found and center is not None:
            # AICODE-NOTE: zoom in on detected marker in SEARCH_M1
            frame = self._draw_zoomed_view(frame, center)
            ocx, ocy = frame.shape[1] // 2, frame.shape[0] // 2
            r = min(frame.shape[1], frame.shape[0]) // 6
            cv2.circle(frame, (ocx, ocy), r, (0, 255, 0), 2)
            cv2.putText(
                frame,
                "Marker Found",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # Resize for display canvas (maintain aspect ratio)
        frame = cv2.resize(frame, (_DISPLAY_W, _DISPLAY_H))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
        
        # Prevent memory leak by updating existing item instead of creating new ones
        if not hasattr(self, "_camera_image_item"):
            self._camera_image_item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        else:
            self.canvas.itemconfig(self._camera_image_item, image=self.photo)

        # Emulator workspace view — shows full workspace with laser/camera positions
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            sim = self.camera.simulator
            work_area = sim.work_area

            # Draw workspace overview
            canvas_w = self.emulator_canvas.winfo_width()
            canvas_h = self.emulator_canvas.winfo_height()
            if canvas_w < 1: canvas_w = 400
            if canvas_h < 1: canvas_h = 400
            
            overview_img = cv2.resize(work_area, (canvas_w, canvas_h))
            overview_rgb = cv2.cvtColor(overview_img, cv2.COLOR_BGR2RGB)
            self.emulator_photo = ImageTk.PhotoImage(
                image=Image.fromarray(overview_rgb)
            )
            
            # Clear emulator canvas to prevent memory leak of drawn shapes
            self.emulator_canvas.delete("all")
            self.emulator_canvas.create_image(
                0, 0, image=self.emulator_photo, anchor=tk.NW
            )

            wa_h, wa_w = work_area.shape[:2]
            sx = canvas_w / wa_w
            sy = canvas_h / wa_h

            # AICODE-NOTE: Use actual controller position, not simulator's internal position
            ctrl_x, ctrl_y = self.controller.position
            sim.camera_x_mm = ctrl_x
            sim.camera_y_mm = ctrl_y

            # Camera position (red dot)
            cam_x_px = ctrl_x * sim.workspace_pixels_per_mm
            cam_y_px = ctrl_y * sim.workspace_pixels_per_mm

            self.emulator_canvas.create_oval(
                cam_x_px * sx - 4, cam_y_px * sy - 4,
                cam_x_px * sx + 4, cam_y_px * sy + 4,
                fill="red", outline="white", width=2,
            )

            # Laser position (blue dot, offset from camera)
            laser_x = ctrl_x + self.laser_offset_x
            laser_y = ctrl_y + self.laser_offset_y
            laser_x_px = laser_x * sim.workspace_pixels_per_mm
            laser_y_px = laser_y * sim.workspace_pixels_per_mm
            self.emulator_canvas.create_oval(
                laser_x_px * sx - 4, laser_y_px * sy - 4,
                laser_x_px * sx + 4, laser_y_px * sy + 4,
                fill="blue", outline="white", width=2,
            )

            # FOV rectangle (yellow)
            fov_w_px = int(sim.camera_fov_mm[0] * sim.workspace_pixels_per_mm)
            fov_h_px = int(sim.camera_fov_mm[1] * sim.workspace_pixels_per_mm)
            self.emulator_canvas.create_rectangle(
                (cam_x_px - fov_w_px / 2) * sx,
                (cam_y_px - fov_h_px / 2) * sy,
                (cam_x_px + fov_w_px / 2) * sx,
                (cam_y_px + fov_h_px / 2) * sy,
                outline="yellow", width=2,
            )

            # Navigation arrow during autonomous scan
            if (
                self.state == "SEARCH_M2"
                and self.m1_marker_pos is not None
                and self.m1_angle_deg is not None
            ):
                m1x = self.m1_marker_pos[0] * sim.workspace_pixels_per_mm * sx
                m1y = self.m1_marker_pos[1] * sim.workspace_pixels_per_mm * sy
                ar = math.radians(self.m1_angle_deg)
                arrow_len = 60
                self.emulator_canvas.create_line(
                    m1x, m1y,
                    m1x + arrow_len * math.cos(ar),
                    m1y + arrow_len * math.sin(ar),
                    fill="orange", width=2, arrow=tk.LAST,
                )

            # Position info label
            info_text = (
                f"Camera: ({ctrl_x:.1f}, {ctrl_y:.1f}) mm\n"
                f"Laser: ({laser_x:.1f}, {laser_y:.1f}) mm"
            )
            self.emulator_canvas.create_text(
                200, 380, text=info_text, fill="white",
                font=("", 9), anchor=tk.S,
            )

        self.after(self.delay, self.update)

    def on_closing(self) -> None:
        self.camera.release()
        self.controller.release()
        self.destroy()

    def _show_about(self) -> None:
        """Show about dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("About LaserCam")
        dialog.geometry("350x200")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="LaserCam MVP\n\n"
            "Automates the LightBurn Print&Cut workflow.\n"
            "Detects markers, navigates between them,\n"
            "and registers positions via Alt+1 / Alt+2.\n\n"
            "Controller: GRBL (Serial) / Ruida (UDP)\n"
            "Marker: Solid circle + white direction line",
            justify=tk.LEFT,
        ).pack(pady=10)

        tk.Button(dialog, text="OK", command=dialog.destroy).pack()


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
