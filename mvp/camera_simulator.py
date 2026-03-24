# mvp/camera_simulator.py
import os
import sys

import cv2

# Add the project root to the Python path to support direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from mvp.controller import BaseController, SimulatedController
from mvp.recognizer import MarkerRecognizer
from mvp.simulator import MotionSimulator


class CameraSimulator:
    """
    Simulates a camera looking at a workspace image.

    Movement is delegated to a controller which can be a real hardware
    controller or a simulated one. The controller is exposed as
    ``self.controller`` so the UI can drive movement.
    """

    def __init__(
        self,
        controller: BaseController = None,
        workspace_image_path: str = None,
        camera_fov: tuple[float, float] = (50.0, 37.5),
        workspace_pixels_per_mm: float = 7.874,
        camera_resolution_px: tuple[int, int] = (1920, 1080),
    ):
        self.simulator = MotionSimulator(
            camera_fov=camera_fov,
            workspace_pixels_per_mm=workspace_pixels_per_mm,
            camera_resolution_px=camera_resolution_px,
        )
        if controller:
            self.controller = controller
        else:
            self.controller = SimulatedController(self.simulator)

        # AICODE-NOTE: calibrate area limits so tiny markers (~4mm) pass but large
        # mesh-grid holes (>>4mm) are rejected. px_per_mm converts physical marker
        # size bounds to camera-frame pixel areas.
        px_per_mm = camera_resolution_px[0] / camera_fov[0]
        # AICODE-NOTE: marker shape is 4mm, canvas is 12mm, but outer stroke
        # contour is ~4.5mm. Use 6mm upper bound to reject mesh holes (~8mm)
        # while keeping real markers. Lower bound at 1.5mm for tolerance.
        min_area_px = (1.5 * px_per_mm) ** 2   # marker ≥ 1.5mm effective size
        max_area_px = (6.0 * px_per_mm) ** 2   # marker ≤ 6mm (rejects 8mm mesh holes)
        self.recognizer = MarkerRecognizer(min_area_px=min_area_px, max_area_px=max_area_px)

        if workspace_image_path:
            self.load_workspace(workspace_image_path)

    def load_workspace(self, image_path: str):
        """Loads the workspace image into the simulator."""
        image = cv2.imread(image_path)
        if image is not None:
            self.simulator.set_work_area_image(image)
        else:
            print(f"Warning: Could not load workspace image from {image_path}")

    def add_marker(
        self,
        x_mm: float,
        y_mm: float,
        shape_type: str,
        target_angle_deg: float,
        rotate_deg: float = 0,
    ):
        """Adds a marker to the simulated workspace."""
        self.simulator.add_marker(
            x_mm, y_mm, shape_type, target_angle_deg, rotate_deg=rotate_deg
        )

    def move_to(self, x_mm: float, y_mm: float):
        """Moves the gantry to the specified coordinates via the controller."""
        self.controller.move_to(x_mm, y_mm)

    def get_frame(self):
        """
        Returns the current camera view (frame) by synchronizing the
        simulator's position with the controller's position.
        """
        x, y = self.controller.position
        self.simulator.move_gantry_to(x, y)
        return self.simulator.get_camera_view()

    def find_marker(self, prefer_shape: str = None):
        """
        Returns if a marker is found, its center, its shape type, and its
        angle in degrees.

        prefer_shape: 'square', 'circle', or None (default prefers squares).

        Returns:
            tuple: (
                found: bool,
                center: tuple | None,
                shape_type: str | None,
                angle_deg: float | None,
            )
        """
        frame = self.get_frame()
        if frame is None or frame.size == 0:
            return False, None, None, None
        return self.recognizer.find_marker(frame, prefer_shape=prefer_shape)

    def move_laser_to_marker(self, marker_center_px):
        """Moves the gantry so the laser is at the marker center."""
        self.simulator.move_laser_to_marker_center(marker_center_px)

    def release(self):
        """No-op for simulator."""
        pass


if __name__ == "__main__":
    # Simple standalone verification
    sim = CameraSimulator("Workspace90x60cm+sample.png")
    sim.move_to(50, 50)
    frame = sim.get_frame()
    if frame is not None:
        cv2.imwrite("test_camera_sim_frame.png", frame)
        print("Frame saved to test_camera_sim_frame.png")
    else:
        print("Failed to get frame from simulator.")
