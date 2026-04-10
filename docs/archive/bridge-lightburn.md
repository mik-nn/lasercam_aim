# bridge-lightburn.md — LightBurn Integration and WinAPI Bridge

This document describes how the Marker Alignment Tool integrates with LightBurn during the Print & Cut workflow. The bridge is responsible for detecting LightBurn, tracking its state, and intercepting Print & Cut hotkeys.

## 1. Purpose of the Bridge

The bridge ensures that:
- the tool knows when LightBurn is active,
- the tool can detect Print & Cut hotkeys,
- the tool can synchronize marker confirmation with LightBurn.

The bridge does not modify LightBurn; it only observes and reacts.

## 2. Detecting LightBurn

The bridge identifies the LightBurn main window by:
- enumerating all top-level windows,
- matching the process name LightBurn.exe,
- verifying visibility and window class.

This detection method is stable across LightBurn versions.

## 3. Window Focus Tracking

The bridge monitors:
- whether LightBurn is the active window,
- whether the user switches away during alignment,
- whether hotkeys should be intercepted or ignored.

If LightBurn is not active, the bridge waits.

## 4. Hotkey Interception

The bridge intercepts:
- Alt+F1 (first Print & Cut point),
- any additional Print & Cut hotkeys if needed.

In the MVP, this is done via Python WinAPI bindings.  
In the final tool, this is implemented using native WinAPI hooks.

## 5. State Machine

The bridge maintains a simple state machine:

- idle  
- first_marker_detected  
- first_marker_confirmed  
- second_marker_detected  
- second_marker_confirmed  
- ready  

The state machine ensures correct sequencing of user actions.

## 6. Interaction with the Tool

When a hotkey is detected:
- the bridge checks the current state,
- validates that the marker has been detected and confirmed,
- transitions to the next state,
- notifies the rest of the system.

Incorrect hotkey usage is ignored.

## 7. Error Handling

The bridge handles:
- missing LightBurn window,
- unexpected hotkey sequences,
- loss of window focus,
- user cancellation.

Errors do not crash the tool; they reset the state machine if needed.

## 8. Behaviour Consistency

The bridge must behave identically in:
- MVP (Python),
- final tool (C/C++/Qt).

Only the internal implementation differs.