# simulator.md — Camera and Gantry Simulation Model

This document describes the simulation environment used during the MVP phase. The simulator allows rapid development and testing of marker detection, coordinate mapping, and Print & Cut workflow without requiring real hardware.

## 1. Purpose of the Simulator

The simulator provides:
- a virtual gantry with X/Y coordinates,
- a virtual camera with a configurable field of view,
- a virtual laser offset relative to the camera,
- a virtual work area containing printed artwork and markers.

It enables testing of the entire workflow before hardware integration.

## 2. Components of the Simulator

The simulator consists of:
- `MotionSimulator`: A class that models the physical environment, including the work area, gantry, and camera/laser positions.
- `CameraSimulator`: A class that simulates a camera, using the `MotionSimulator` to generate frames. It also includes the `MarkerRecognizer`.
- `BaseController`: An abstract base class for controllers.
- `SimulatedController`: A controller that sends movement commands to the `MotionSimulator`.

## 3. Camera Model

The camera model is designed to accurately reflect a real-world camera by decoupling the workspace image resolution from the camera's sensor resolution.

- **`workspace_pixels_per_mm`**: The resolution of the background image of the work area.
- **`camera_fov_mm`**: The physical area (e.g., 50x37.5 mm) that the camera can see.
- **`camera_resolution_px`**: The native sensor resolution of the camera (e.g., 1920x1080 pixels).

When `get_camera_view()` is called, the simulator:
1.  Calculates the region to crop from the workspace image, based on the camera's FOV in mm and the workspace image's resolution.
2.  Crops this region.
3.  **Resizes the cropped image to the camera's native `camera_resolution_px`**.

This ensures that the `MarkerRecognizer` always receives a full-resolution image, just as it would from a real camera, regardless of the resolution of the workspace image.

## 4. Gantry and Controller Model

Movement is handled by a controller abstraction (`BaseController`).
- The `SimulatedController` directly manipulates the `MotionSimulator`'s gantry position.
- Real hardware controllers (like `GRBLController` or `RuidaController`) will send commands to the physical machine.

The `CameraSimulator` can be initialized with any controller that inherits from `BaseController`. If no controller is provided, it creates a `SimulatedController` by default.

When `get_frame()` is called on the `CameraSimulator`, it first queries the controller for the current position, updates the `MotionSimulator`'s gantry position accordingly, and then renders the camera view. This ensures the simulated view always matches the controller's state, whether it's simulated or real.

## 5. Laser Offset

The laser is offset from the camera by a fixed vector.
The simulator applies this offset to compute the laser position when the camera is centered on a marker.

## 6. Visualization

The simulator renders:
- the work area,
- the camera viewport,
- detected markers,
- the laser position,
- movement paths.

This visualization is essential for debugging alignment logic.

## 7. Transition to Real Hardware

To switch to real hardware, the `Application` class is configured to instantiate a real controller (e.g., `GRBLController`) instead of relying on the default `SimulatedController`. The rest of the application, including the UI and the `CameraSimulator`, continues to work through the `BaseController` abstraction. The `CameraSimulator` is still used to provide a visual representation of the workspace, with its position driven by the real controller.
