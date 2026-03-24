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
            controller = GRBLController(port=cfg.grbl_port, baudrate=cfg.grbl_baudrate)
        elif cfg.controller == "ruida":
            controller = RuidaController(host=cfg.ruida_host, port=cfg.ruida_port)

        # The camera is always a simulator in this version of the MVP.
        # A real camera implementation would be chosen here based on config.
        self.camera = CameraSimulator(
            controller=controller,
            workspace_image_path=cfg.workspace_image,
            camera_fov=cfg.camera_fov_mm,
            workspace_pixels_per_mm=cfg.workspace_pixels_per_mm,
            camera_resolution_px=cfg.camera_resolution,
        )

        # If no hardware controller was specified, the camera created a default
        # simulated one. We use that for the UI.
        if controller is None:
            controller = self.camera.controller

        # Overlay new-design markers on top of the workspace image.
        # The workspace already contains the sample card; the new markers
        # are placed at the card corners to overwrite the old embedded ones.
        # M1 — square marker; internal dot points toward M2.
        self.camera.add_marker(
            cfg.m1_x_mm, cfg.m1_y_mm, "square", cfg.m1_angle_deg
        )
        # M2 — circle marker; internal dot points toward M1.
        self.camera.add_marker(
            cfg.m2_x_mm, cfg.m2_y_mm, "circle", cfg.m2_angle_deg
        )

        # Set initial camera position from config
        self.camera.move_to(cfg.camera_start_x_mm, cfg.camera_start_y_mm)
        print(
            f"Camera started at ({cfg.camera_start_x_mm:.1f}, "
            f"{cfg.camera_start_y_mm:.1f}) mm"
        )

        self.bridge = get_bridge()
        self.ui = App(camera=self.camera, controller=controller)

    def run(self):
        self.ui.mainloop()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
