# Plan: Camera Simulator

## Objective

Create a camera simulator that takes a picture of the laser workspace as input and shows the camera view in a window. The simulator will be integrated with the existing LightBurn workflow.

## Proposed Steps

1.  **Create a new module for the camera simulator:** This module will be located in the `mvp/` directory and will be named `camera_simulator.py`.
2.  **Load a static image:** The simulator will load a static image of the laser workspace from the `simulator/` directory. A placeholder image will be used initially.
3.  **Display the image in a UI window:** A simple UI window will be created using `wxPython` to display the camera view.
4.  **Simulate gantry movements:** The simulator will subscribe to gantry movement events and update the camera view by cropping and displaying the relevant part of the workspace image.
5.  **Integrate with LightBurn bridge:** The simulator will be integrated with the LightBurn bridge to react to Print & Cut events. For example, when a marker is detected, the simulator will show the laser position on the camera view.

## Risks / Open Questions

- **Ruida Controller:** The role of the Ruida controller mentioned by the user is still unclear. The current plan focuses on the documented LightBurn integration. Further clarification is needed to understand if the Ruida controller replaces or complements LightBurn.
- **Workspace Image:** The exact format and source of the "picture of the laser workspace" is not specified. The plan assumes a static image file for now. The implementation should be flexible to accommodate other sources in the future.

## Rollback Strategy

The new camera simulator will be a self-contained module. To roll back, the `mvp/camera_simulator.py` file and any related UI components can be safely removed without affecting the rest of the application.
