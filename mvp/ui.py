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

from mvp.camera import Camera
from mvp.controller import BaseController

# Display canvas dimensions — half of the 1240×720 sensor resolution,
# preserving the aspect ratio (≈ 1.722 : 1).
_DISPLAY_W = 620
_DISPLAY_H = 360


class App(tk.Tk):
    NAV_STEP_MM = 20.0
    NAV_MAX_STEPS = 20

    def __init__(
        self, camera=None, controller: BaseController | None = None, *args, **kwargs
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
            self.controller = self.camera.controller
        else:
            from mvp.controller import SimulatedController
            from mvp.simulator import MotionSimulator

            self.controller = SimulatedController(MotionSimulator())

        self.state = "IDLE"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None
        self.nav_steps_done = 0

        # Main layout
        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        # FOV canvas — sized to match camera aspect ratio
        self.canvas = tk.Canvas(self.main_frame, width=_DISPLAY_W, height=_DISPLAY_H)
        self.canvas.pack(side=tk.LEFT)

        # Overview canvas
        self.overview_canvas = tk.Canvas(self.main_frame, width=400, height=400)
        self.overview_canvas.pack(side=tk.RIGHT)

        # Control panel
        self.control_panel = tk.Frame(self)
        self.control_panel.pack()

        # Status label (always visible)
        self.status_label = tk.Label(self, text=f"State: {self.state}")
        self.status_label.pack()

        self.add_controls()

        self.delay = 15
        self.update()

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def add_controls(self):
        self.status_label.config(text=f"State: {self.state}")

        if hasattr(self.control_panel, "winfo_children"):
            for child in self.control_panel.winfo_children():
                child.destroy()

        btn_frame = tk.Frame(self.control_panel)
        btn_frame.pack()

        # AICODE-NOTE: coarse step for scanning, fine step when zoomed on a marker.
        if self.state in ("CONFIRM_M1", "CONFIRM_M2"):
            step = 0.1  # mm — fine adjustment while zoomed on detected marker
        else:
            step = 0.5  # mm — coarse scan step

        def _nav_buttons(row_offset=0):
            tk.Button(
                btn_frame, text="↑", command=lambda: self.move_gantry(0, -step)
            ).grid(row=row_offset + 0, column=1)
            tk.Button(
                btn_frame, text="←", command=lambda: self.move_gantry(-step, 0)
            ).grid(row=row_offset + 1, column=0)
            tk.Button(
                btn_frame, text="→", command=lambda: self.move_gantry(step, 0)
            ).grid(row=row_offset + 1, column=2)
            tk.Button(
                btn_frame, text="↓", command=lambda: self.move_gantry(0, step)
            ).grid(row=row_offset + 2, column=1)
            tk.Label(btn_frame, text=f"{step} mm/step").grid(
                row=row_offset + 1, column=3, padx=6
            )

        if self.state in ("IDLE", "SEARCH_M2"):
            _nav_buttons()
            if self.state == "SEARCH_M2":
                tk.Button(
                    btn_frame,
                    text="Cancel",
                    command=self.cancel_to_idle,
                    bg="red",
                    fg="white",
                ).grid(row=1, column=4, padx=10)

        elif self.state == "CONFIRM_M1":
            # AICODE-NOTE: fine nav arrows + step label; camera shows 3× zoom.
            _nav_buttons()
            tk.Button(
                btn_frame,
                text="Confirm M1",
                command=self.confirm_m1,
                bg="green",
                fg="white",
            ).grid(row=1, column=4, padx=10)
            tk.Button(
                btn_frame,
                text="Cancel",
                command=self.cancel_to_idle,
                bg="red",
                fg="white",
            ).grid(row=1, column=5, padx=5)

        elif self.state == "NAVIGATE_TO_M2":
            tk.Button(
                btn_frame,
                text="Cancel",
                command=self.cancel_to_idle,
                bg="red",
                fg="white",
            ).grid(row=0, column=0, padx=5)

        elif self.state == "CONFIRM_M2":
            # AICODE-NOTE: fine nav arrows for M2 position tuning; zoomed view.
            _nav_buttons()
            tk.Button(
                btn_frame,
                text="Confirm M2",
                command=self.confirm_m2,
                bg="green",
                fg="white",
            ).grid(row=1, column=4, padx=10)
            tk.Button(
                btn_frame,
                text="Cancel",
                command=self.cancel_to_idle,
                bg="red",
                fg="white",
            ).grid(row=1, column=5, padx=5)
        # DONE: no buttons — auto-resets via _reset_to_idle

    # ------------------------------------------------------------------
    # Movement — always via controller, never touching the simulator directly
    # ------------------------------------------------------------------

    def move_gantry(self, dx: float, dy: float) -> None:
        self.controller.move_by(dx, dy)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def confirm_m1(self) -> None:
        if self.detected_marker is None:
            return
        _center, _shape_type, angle_deg = self.detected_marker
        if angle_deg is None:
            return  # direction is required for autonomous M2 navigation
        self.m1_angle_deg = angle_deg
        self.m1_camera_pos = self.controller.position
        self.nav_steps_done = 0
        self.state = "NAVIGATE_TO_M2"
        self.add_controls()
        self.after(self.delay, self._nav_step)

    def confirm_m2(self) -> None:
        self.state = "DONE"
        self.add_controls()
        self.after(2000, self._reset_to_idle)

    def cancel_to_idle(self) -> None:
        self.state = "IDLE"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None
        self.nav_steps_done = 0
        self.add_controls()

    def _reset_to_idle(self) -> None:
        self.state = "IDLE"
        self.detected_marker = None
        self.m1_angle_deg = None
        self.m1_camera_pos = None
        self.nav_steps_done = 0
        self.add_controls()

    # ------------------------------------------------------------------
    # Autonomous navigation to M2
    # ------------------------------------------------------------------

    def _nav_step(self) -> None:
        if self.state != "NAVIGATE_TO_M2":
            return

        # Workspace boundary check — only available for SimulatedController
        from mvp.controller import SimulatedController

        if isinstance(self.controller, SimulatedController):
            sim = self.controller._simulator
            dx = self.NAV_STEP_MM * math.cos(math.radians(self.m1_angle_deg))
            dy = self.NAV_STEP_MM * math.sin(math.radians(self.m1_angle_deg))
            cx, cy = self.controller.position
            new_x, new_y = cx + dx, cy + dy

            # workspace dimensions are in pixels, need to convert to mm
            wa_h_px, wa_w_px = sim.work_area.shape[:2]
            wa_w_mm = wa_w_px / sim.workspace_pixels_per_mm
            wa_h_mm = wa_h_px / sim.workspace_pixels_per_mm

            hfx, hfy = sim.camera_fov_mm[0] / 2, sim.camera_fov_mm[1] / 2
            if (
                new_x < hfx
                or new_x > wa_w_mm - hfx
                or new_y < hfy
                or new_y > wa_h_mm - hfy
            ):
                self.state = "SEARCH_M2"
                self.add_controls()
                return

        self.controller.move_in_direction(self.m1_angle_deg, self.NAV_STEP_MM)
        self.nav_steps_done += 1

        found, center, shape_type, angle_deg = self.camera.find_marker(
            prefer_shape="circle"
        )
        if found and shape_type == "circle":
            self.state = "CONFIRM_M2"
            self.detected_marker = (center, shape_type, angle_deg)
            self.add_controls()
            return

        if self.nav_steps_done >= self.NAV_MAX_STEPS:
            self.state = "SEARCH_M2"
            self.add_controls()
            return

        self.after(self.delay, self._nav_step)

    # ------------------------------------------------------------------
    # Main update loop
    # ------------------------------------------------------------------

    def update(self) -> None:
        frame = self.camera.get_frame()
        if frame is not None:
            found: bool = False
            center = None

            if self.state != "NAVIGATE_TO_M2":
                found, center, shape_type, angle_deg = self.camera.find_marker()

                if found and shape_type == "square" and self.state == "IDLE":
                    self.state = "CONFIRM_M1"
                    self.detected_marker = (center, shape_type, angle_deg)
                    self.add_controls()

                elif (
                    found and shape_type == "square" and self.state == "CONFIRM_M1"
                ):
                    # Refresh detected marker every frame so arrow tracks the marker.
                    self.detected_marker = (center, shape_type, angle_deg)

                elif self.state == "CONFIRM_M1" and not found:
                    # Marker left the FOV — drop stale data, show unzoomed view.
                    self.detected_marker = None

                elif self.state in ("SEARCH_M2", "CONFIRM_M2"):
                    # AICODE-NOTE: prefer_shape='circle' so M2 is detected even
                    # if M1 (square) is still partially visible in the same FOV.
                    found, center, shape_type, angle_deg = self.camera.find_marker(
                        prefer_shape="circle"
                    )
                    if found and shape_type == "circle":
                        if self.state == "SEARCH_M2":
                            self.state = "CONFIRM_M2"
                            self.add_controls()
                        self.detected_marker = (center, shape_type, angle_deg)
                    else:
                        self.detected_marker = None

            # Draw confirm-state overlays (zoom + crosshair + direction arrow)
            if self.state in ("CONFIRM_M1", "CONFIRM_M2") and self.detected_marker:
                det_center, shape_type, angle_deg = self.detected_marker
                if det_center is not None:
                    fh, fw = frame.shape[:2]

                    # AICODE-NOTE: crop preserving the original frame aspect ratio
                    # (fw:fh) around the marker centre. crop_half_h = fh//6 gives
                    # ~3× zoom.  The centre is clamped away from frame edges so
                    # the crop is always symmetric and the marker stays centred.
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
                    zoom = cv2.resize(zoom, (fw, fh), interpolation=cv2.INTER_LINEAR)

                    ocx, ocy = fw // 2, fh // 2
                    colour = (0, 255, 0)
                    r = min(fw, fh) // 6
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
                cv2.circle(frame, center, 12, (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    "Marker Found",
                    (center[0] + 18, center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            # Resize for display canvas (maintain aspect ratio)
            frame = cv2.resize(frame, (_DISPLAY_W, _DISPLAY_H))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # Overview — only when the camera is a simulator with a visual workspace
        from mvp.camera_simulator import CameraSimulator

        if isinstance(self.camera, CameraSimulator):
            sim = self.camera.simulator
            work_area = sim.work_area

            overview_img = cv2.resize(work_area, (400, 400))
            overview_rgb = cv2.cvtColor(overview_img, cv2.COLOR_BGR2RGB)
            self.overview_photo = ImageTk.PhotoImage(
                image=Image.fromarray(overview_rgb)
            )
            self.overview_canvas.create_image(
                0, 0, image=self.overview_photo, anchor=tk.NW
            )

            wa_h, wa_w = work_area.shape[:2]
            sx = 400 / wa_w
            sy = 400 / wa_h

            cam_x_px = sim.camera_x_mm * sim.workspace_pixels_per_mm
            cam_y_px = sim.camera_y_mm * sim.workspace_pixels_per_mm

            # FOV rectangle in workspace pixels (crop size, not sensor resolution)
            fov_w_px = int(sim.camera_fov_mm[0] * sim.workspace_pixels_per_mm)
            fov_h_px = int(sim.camera_fov_mm[1] * sim.workspace_pixels_per_mm)

            self.overview_canvas.create_rectangle(
                (cam_x_px - fov_w_px / 2) * sx,
                (cam_y_px - fov_h_px / 2) * sy,
                (cam_x_px + fov_w_px / 2) * sx,
                (cam_y_px + fov_h_px / 2) * sy,
                outline="red",
                width=2,
            )

            # Navigation arrow during autonomous scan
            if (
                self.state == "NAVIGATE_TO_M2"
                and self.m1_camera_pos is not None
                and self.m1_angle_deg is not None
            ):
                m1x = self.m1_camera_pos[0] * sim.workspace_pixels_per_mm * sx
                m1y = self.m1_camera_pos[1] * sim.workspace_pixels_per_mm * sy
                ar = math.radians(self.m1_angle_deg)
                arrow_len = 60
                self.overview_canvas.create_line(
                    m1x,
                    m1y,
                    m1x + arrow_len * math.cos(ar),
                    m1y + arrow_len * math.sin(ar),
                    fill="orange",
                    width=2,
                    arrow=tk.LAST,
                )

        self.after(self.delay, self.update)

    def on_closing(self) -> None:
        self.camera.release()
        self.controller.release()
        self.destroy()


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
