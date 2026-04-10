# mvp/app.py
import os
import sys

# Add the project root to the Python path to support direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from mvp.bridge import get_bridge
from mvp.camera_simulator import CameraSimulator
from mvp.config import Config
from mvp.controller import GRBLController, RuidaController
from mvp.ui import App


class Application:
    def __init__(self):
        cfg = Config.load()
        controller = None

        if cfg.controller == "grbl":
            print(f"Connecting to GRBL on {cfg.grbl_port} at {cfg.grbl_baudrate} baud...")
            controller = GRBLController(
                port=cfg.grbl_port,
                baudrate=cfg.grbl_baudrate,
                timeout=1.0,
                retries=3,
            )
            print(f"GRBL connected. Position: {controller.position}")
        elif cfg.controller == "ruida":
            print(f"Connecting to Ruida at {cfg.ruida_host}:{cfg.ruida_port}...")
            controller = RuidaController(
                host=cfg.ruida_host,
                port=cfg.ruida_port,
                timeout=1.0,
                retries=3,
            )
            print(f"Ruida connected. Position: {controller.position}")
        else:
            print(f"Using simulated controller (config: '{cfg.controller}')")

        # The camera is always a simulator in this version of the MVP.
        # A real camera implementation would be chosen here based on config.
        self.camera = CameraSimulator(
            controller=controller,
            workspace_image_path=cfg.workspace_image,
            camera_fov=cfg.camera_fov_mm,
            workspace_pixels_per_mm=cfg.workspace_pixels_per_mm,
            camera_resolution_px=cfg.camera_resolution,
        )

        if controller is None:
            controller = self.camera.controller

        # Overlay new-design markers on top of the workspace image.
        # Both M1 and M2 are identical solid circles with white direction lines.
        # M1 — circle marker; direction line points toward M2.
        self.camera.add_marker(
            cfg.m1_x_mm, cfg.m1_y_mm, "circle", cfg.m1_angle_deg
        )
        # M2 — circle marker; direction line points toward M1.
        self.camera.add_marker(
            cfg.m2_x_mm, cfg.m2_y_mm, "circle", cfg.m2_angle_deg
        )

        # AICODE-NOTE: Initialize position from controller if it can report
        # its position on startup, otherwise use configured home position.
        try:
            pos = controller.position
            start_x, start_y = pos
            print(f"Controller reported position: ({start_x:.1f}, {start_y:.1f}) mm")
        except Exception:
            start_x, start_y = cfg.home_x_mm, cfg.home_y_mm
            print(
                f"Could not query controller position. "
                f"Using configured home: ({start_x:.1f}, {start_y:.1f}) mm"
            )

        self.camera.move_to(start_x, start_y)

        self.bridge = get_bridge()
        self.ui = App(
            camera=self.camera,
            controller=controller,
            fine_step_mm=cfg.fine_step_mm,
            coarse_step_mm=cfg.coarse_step_mm,
            large_step_mm=cfg.large_step_mm,
            laser_offset_x=cfg.laser_offset_x,
            laser_offset_y=cfg.laser_offset_y,
            controller_type=cfg.controller,
        )

    def run(self):
        self.ui.mainloop()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
