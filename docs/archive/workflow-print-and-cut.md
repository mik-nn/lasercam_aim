# workflow-print-and-cut.md — LightBurn Print & Cut Integration Workflow

This document describes the complete workflow for integrating the Marker Alignment Tool with LightBurn’s Print & Cut feature. The workflow is identical for both the MVP (Python) and the final tool (C/C++/Qt). The internal implementation differs, but the external behaviour must remain consistent.

## 1. Purpose of the Workflow

The goal is to automate and stabilize the Print & Cut alignment process by using a camera to detect printed markers and by moving the laser head precisely to the marker centers. The tool assists the user through the two-point alignment process required by LightBurn.

## 2. High-Level Flow

1. The user prints artwork with two markers.
2. The user places the printed sheet on the laser bed.
3. The tool uses the camera to detect each marker.
4. The tool moves the laser to the exact center of each marker.
5. The user confirms each point in LightBurn using the Print & Cut hotkeys.
6. LightBurn computes the affine transform and aligns the cut to the print.

The tool ensures that the laser is positioned accurately before each LightBurn confirmation.

## 3. System Roles

- The camera module provides real-time frames.
- The marker recognizer detects markers and computes their centers.
- The motion simulator or hardware driver moves the camera and laser.
- The LightBurn bridge tracks window focus and intercepts Print & Cut hotkeys.
- The UI guides the user through the process.

## 4. Detailed Step-by-Step Workflow

### Step 1 — User positions the camera over the first printed marker
The user manually jogs the gantry until the first marker appears in the camera’s field of view. The tool continuously processes frames and waits for a valid marker detection.

### Step 2 — Tool detects the first marker
When the marker recognizer identifies a valid marker, the UI displays a confirmation prompt. The user confirms that the detected marker is correct.

### Step 3 — Tool moves the laser to the marker center
The tool computes the marker center in machine coordinates using the coordinate mapping module. It then moves the laser head to that exact position. In the MVP, this movement is simulated; in the final tool, it is executed on real hardware.

### Step 4 — User confirms the first point in LightBurn
The user selects the corresponding marker in LightBurn and presses the Print & Cut hotkey (Alt+F1 by default).  
The LightBurn bridge detects this event and transitions the internal state machine to “first marker confirmed”.

### Step 5 — Tool guides the user to the second marker
The tool instructs the user to move the camera to the second printed marker. The process repeats: the camera module streams frames, and the recognizer waits for a valid detection.

### Step 6 — Tool detects the second marker
Once detected, the UI again asks the user to confirm the marker. After confirmation, the tool moves the laser to the second marker center.

### Step 7 — User confirms the second point in LightBurn
The user selects the second marker in LightBurn and presses the corresponding Print & Cut hotkey.  
The LightBurn bridge detects the event and transitions the state machine to “second marker confirmed”.

### Step 8 — LightBurn computes the alignment
With both points confirmed, LightBurn calculates the affine transform needed to align the cut path to the printed artwork.  
The tool’s job is complete at this stage.

## 5. State Machine

The LightBurn bridge maintains a simple state machine:

- idle  
- first_marker_detected  
- first_marker_confirmed  
- second_marker_detected  
- second_marker_confirmed  
- ready  

The tool transitions between these states based on marker detection and LightBurn hotkey events.

## 6. Error Handling

- If the marker is not detected, the UI instructs the user to adjust the camera position.
- If the wrong marker is detected, the user can cancel and retry.
- If LightBurn is not the active window, the bridge waits until focus returns.
- If the user presses the hotkey out of order, the tool ignores the event.

## 7. Behaviour Consistency Between MVP and Final Tool

The following behaviours must remain identical:

- Marker detection semantics  
- Confirmation prompts  
- Movement to marker center  
- LightBurn hotkey handling  
- State machine transitions  
- User-facing workflow  

Only internal implementation details differ between MVP and final tool.

## 8. Summary

This workflow defines the exact sequence of interactions between the user, the tool, and LightBurn during Print & Cut alignment. It ensures predictable, repeatable behaviour and provides a stable foundation for both MVP experimentation and final production implementation.