# Plan: Advanced Marker Recognition and Directional Navigation

## Objective
Implement specialized marker recognition (circles and rectangles with directional arrows) and automated camera navigation between markers to assist in LightBurn's Print & Cut workflow.

## Proposed Steps

### 1. Advanced Marker Recognition
- **Update `MarkerRecognizer`**: 
    - Implement circle detection (Hough Circles or contour-based).
    - Implement rectangle detection.
    - Implement arrow detection and orientation estimation.
    - Implement ID recognition (based on shape or internal pattern).
- **Marker Specs**:
    - Mark 1: Circle with an arrow pointing to Mark 2.
    - Mark 2: Rectangle with an arrow pointing to Mark 1.

### 2. Directional Navigation Logic
- **Update `MotionSimulator` / `CameraSimulator`**:
    - Add `move_in_direction(angle_deg, distance_mm)` method.
    - Add a "search" mode that moves the camera along a vector until a marker is found.
- **Navigation State Machine**:
    - `IDLE` -> `SEARCH_M1` (Manual or automated)
    - `CONFIRM_M1` -> User confirms Mark 1.
    - `NAVIGATE_TO_M2` -> Camera moves in direction detected from Mark 1's arrow.
    - `SEARCH_M2` -> Camera enters FOV-based search for Mark 2.
    - `CONFIRM_M2` -> User confirms Mark 2.

### 3. UI Integration
- **Overlay Enhancements**:
    - Draw detected arrows and IDs.
    - Show navigation vector.
- **Workflow Controls**:
    - Button to "Start Navigation to next marker" after M1 confirmation.

### 4. Verification
- Create synthetic test images with the new marker designs.
- Add unit tests in `mvp/tests/test_recognizer.py` for new shapes and orientations.
- Add integration tests for the full navigation flow.

## Risks / Open Questions
- **Arrow Accuracy**: How precisely can we determine the arrow's angle? Small errors in angle can lead to missing the second marker if it's far away.
- **Search Strategy**: If M2 is not immediately found after moving, what search pattern (spiral, lawnmower) should be used?
- **Lighting/Noise**: Robustness of arrow detection in varying workspace conditions.

## Rollback Strategy
- Revert `recognizer.py` and `simulator.py` to previous git commits.
- Maintain the simple square detection as a fallback mode.
