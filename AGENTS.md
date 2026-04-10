# AGENTS.md — Coding-Agent Playbook for LaserCam

This document defines the workflow, guard‑rails, and conventions for any autonomous or semi‑autonomous coding agent ("Agent") contributing to the LaserCam project.

## Project Vision

LaserCam is an application that automates the LightBurn Print&Cut workflow for laser cutters. It:

- Automatically locates printed markers and determines the direction to the next marker
- Displays detected markers in a zoomed view with a green circle overlay for visual verification
- Allows the user to fine-tune position, confirm, or cancel marker detection
- Moves the laser to the centre of each confirmed marker (accounting for camera-laser offset)
- Registers marker positions in LightBurn by simulating Alt+1 / Alt+2 hotkeys
- Navigates autonomously from M1 to M2 using the direction line on the marker
- Calibrates and monitors the offset between laser and camera

**Prototype**: Python-based emulation with a camera emulator and controller emulator:
1. **Camera Emulator**: Simulates a camera moving over a workspace image, returning the FOV for current coordinates
2. **Controller Emulator**: Simulates laser movement, position reporting, and gantry control

**New Marker Design**: Solid circle with a white line pointing towards the next marker

## Project Layers

- **MVP layer (Python)**: Rapid experimentation with marker detection, emulation, and workflow validation. Uses simulated camera and controller for development.
- **Final layer (C++/Qt)**: Production-ready standalone application with identical external behaviour to the MVP, integrating with real hardware and LightBurn via WinAPI.

Agents must follow this playbook to ensure consistent, safe, reversible, documentation‑driven development.

## 1. Core Principles

1. **Documentation‑Driven Development**  
Every Agent run begins by reading all Markdown files under `docs/` to understand architecture, modules, workflows, and constraints.

2. **Instruction‑First, Best Practices**  
For simple tasks, follow human instructions directly while writing clean, maintainable code.

3. **Conditional Planning and Verification**  
For complex tasks, produce a plan file and wait for approval before implementation.

4. **Greppable Inline Memory**  
Use `AICODE-*` anchors to leave rationale and breadcrumbs for future Agents.

5. **Small, Safe, Reversible Commits**  
Prefer multiple focused commits over large diffs.

## 2. Task Execution Protocol

A human triggers an Agent with a natural‑language instruction.

1. **Read Documentation**  
Agents must read all files in `docs/` relevant to the task:
   - `architecture.md` — system architecture, LightBurn Print&Cut workflow, and component relationships
   - `modules.md` — module responsibilities and APIs
   - `markers/marker-design.md` — marker format and design
   - `markers/direction-detection.md` — direction detection algorithm
   - `markers/recognition-pipeline.md` — detection workflow
   - `prototype/meerk40t-integration.md` — emulation system
   - `controllers/ruida-protocol.md` — RUIDA controller protocol
   - `controllers/grbl-protocol.md` — GRBL controller protocol
   - `calibration/laser-camera-offset.md` — calibration system
   - `migration/lightburn-to-meerk40t.md` — migration strategy to production

2. **Analyse the Request**  
Determine dependencies, affected modules, and whether the task is simple or complex.

3. **If Complex → Plan Mode**  
Create a plan file under `.opencode/plans/` and wait for explicit approval.

4. **If Simple → Implement**  
Implement directly, keeping edits minimal and aligned with documentation.

5. **After Implementation**  
For complex tasks: run full tests and update `docs/test-summary.md`.  
For simple tasks: run only necessary checks.  
Commit with a clear message.

## 2.1 Determining Task Complexity

A task is complex if it involves:

- Multiple modules (camera, recognizer, controller, calibration, UI, LightBurn bridge)
- Significant algorithmic logic (marker detection, direction detection, coordinate transforms)
- Integration with external systems (LightBurn, RUIDA, GRBL, real camera)
- Performance‑critical code (real‑time camera processing)
- Architectural changes or cross‑cutting concerns

If uncertain, default to Plan Mode.

## 3. Plan Mode (Complex Tasks Only)

Plans live in `.opencode/plans/` and follow the naming pattern:

`###-objective-description.md`

A plan must include:

- Objective — the human request verbatim  
- Proposed Steps — short, actionable, numbered  
- Risks / Open Questions — bullet list  
- Rollback Strategy — how to revert safely  

Implementation begins only after explicit approval.

## 4. Inline Memory — AICODE-* Anchors

Use language‑appropriate comment tokens (`#`, `//`, etc.).

Anchors:

- `AICODE-NOTE`: rationale linking new to existing logic  
- `AICODE-TODO`: follow‑ups not in current scope  
- `AICODE-QUESTION`: uncertainty requiring human review  

Anchors are mandatory when:

- Logic is non‑obvious  
- Code interacts with legacy or emulator components  
- Marker detection or coordinate transforms are involved  
- Controller logic touches RUIDA or GRBL protocols  
- Calibration logic is involved  
- LightBurn hotkey injection is implemented  

## 5. Test Summary Automation

After running tests for a complex task, the Agent must overwrite `docs/test-summary.md` with:

- Number of passed tests  
- Number of failed tests  
- List of passed tests  
- List of failed tests with error summaries  

## 6. Code Quality Checks

For complex tasks or when requested:

1. Import sorting  
2. Code formatting  
3. Style/length checking  
4. Type checking  

For simple tasks, perform only what is necessary.

### 6.2 Self‑Verification Checklist

- Tests pass or failures are expected and documented  
- Imports sorted  
- Code formatted  
- No style violations  
- No type errors (warnings acceptable)  
- No TODOs left in scope unless explicitly allowed  

## 7. Python Environment (MVP Layer)

All Python commands must use the project's environment:

- Tests: pytest  
- Formatting: black  
- Sorting: isort  
- Style: flake8  
- Type checking: pyright  

## 8. C++ Environment (Final Layer)

- Build system: CMake  
- UI framework: Qt  
- Image processing: OpenCV  
- Testing: Google Test / Catch2  

## 9. Documentation Maintenance

Agents must update documentation whenever behaviour changes:

- `architecture.md` — architecture or workflow changes  
- `modules.md` — new modules or API changes  
- `markers/marker-design.md` — marker format or design changes  
- `markers/direction-detection.md` — direction detection algorithm changes  
- `markers/recognition-pipeline.md` — detection workflow changes  
- `prototype/meerk40t-integration.md` — emulation system changes  
- `controllers/ruida-protocol.md` — RUIDA protocol changes  
- `controllers/grbl-protocol.md` — GRBL protocol changes  
- `calibration/laser-camera-offset.md` — calibration system changes  
- `migration/lightburn-to-meerk40t.md` — migration strategy changes  

Documentation must always reflect the current system.

## 10. Marker Design

The project uses a unified marker design:

- **Shape**: Solid black circle (4-6mm diameter)
- **Direction indicator**: White line from center pointing towards the next marker
- **Recognition**: Circle detection + line angle extraction
- **Output**: `(found: bool, center: (x, y), angle: float, confidence: float)`

Both M1 and M2 markers use the same shape. Differentiation is by position/context, not shape.

## 11. LightBurn Print&Cut Workflow

The application automates the LightBurn Print&Cut workflow:

1. Operator positions camera over M1 (via jog / LightBurn)
2. Selects "Register M1" in LightBurn Print&Cut
3. LaserCam detects marker, shows zoomed view + green circle
4. Operator fine-tunes position if needed
5. Operator confirms → LaserCam moves laser to marker centre
6. LaserCam sends Alt+1 to LightBurn (registers M1)
7. Operator selects "Register M2" in LightBurn Print&Cut
8. LaserCam determines direction from M1's marker line
9. LaserCam moves camera toward M2 autonomously
10. M2 enters FOV → LaserCam detects, shows zoomed view
11. Operator fine-tunes, confirms
12. LaserCam moves laser to M2 centre, sends Alt+2 to LightBurn
13. LightBurn now has both registration points → ready to cut

## 12. State Machine

```
START → SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE → (auto) → START
```

| State | Description |
|-------|-------------|
| `START` | Initial state, waiting for operator |
| `SEARCH_M1` | Reading camera, scanning for M1 |
| `CONFIRM_M1` | M1 detected, zoomed view, fine-tune, confirm/cancel |
| `REGISTER_M1` | Move laser to M1 centre, send Alt+1 to LightBurn |
| `SEARCH_M2` | Move toward M2 using direction angle |
| `CONFIRM_M2` | M2 detected, zoomed view, fine-tune, confirm/cancel |
| `REGISTER_M2` | Move laser to M2 centre, send Alt+2 to LightBurn |
| `DONE` | Both markers registered, auto-reset |

## 13. Emulation System

The MVP uses two emulators for development without physical hardware:

- **Camera Emulator**: Simulates a camera moving over a workspace image, returning the FOV for current coordinates
- **Controller Emulator**: Simulates laser movement, position reporting, and gantry control

## 14. Controller Support

The application supports two laser controller protocols:

- **RUIDA**: UDP-based protocol for Ruida controllers
- **GRBL**: Serial-based protocol for GRBL controllers

Both share a common controller abstraction interface.

## 15. Calibration System

The application calibrates the offset between laser and camera:

- Offset calculation algorithm
- Offset change detection during carriage movement
- Recalibration triggers
- Validation and verification methods

## 16. Fallback Behaviour

If uncertain:

1. Add an `AICODE-QUESTION` anchor.  
2. Push work behind a feature flag or draft PR.  

## 17. Project‑Specific Notes

- The MVP layer (Python) is used for rapid iteration on marker detection and workflow validation with emulation.  
- The final tool (C++/Qt) must replicate the MVP's external behaviour exactly.  
- Marker detection logic must remain consistent across MVP and final tool.  
- The application must never move hardware without explicit user confirmation.  
- The LightBurn integration is central to the workflow — Alt+1 / Alt+2 hotkey injection is required for production.  
- The emulation system (camera + controller) is used for development and testing without physical hardware.
