# ROLES.md — Agent Roles in the Marker Alignment Tool Project

This document defines the autonomous and semi‑autonomous agent roles used in the project. Each role has a clear responsibility boundary, decision authority, and interaction model. All agents operate under the AGENTS.md playbook and must follow documentation‑driven development.

## 1. Overview of Agent Roles

The project uses several specialized agents, each responsible for a specific domain:

- Architecture Agent  
- Vision Agent  
- Simulator Agent  
- Bridge Agent  
- UI Agent  
- Core Logic Agent  
- Documentation Agent  
- Testing Agent  

Each agent works independently but follows the same workflow rules.

## 2. Architecture Agent

Responsible for maintaining the overall system structure.

Responsibilities:
- Maintain architecture.md and structure.md  
- Ensure consistency between MVP and final tool  
- Validate module boundaries  
- Approve or reject architectural changes  
- Ensure external behaviour contract remains stable  

The Architecture Agent has veto power over cross‑module changes.

## 3. Vision Agent

Responsible for marker detection logic and visual algorithms.

Responsibilities:
- Maintain vision.md and markers.md  
- Develop and refine marker detection algorithms  
- Validate robustness across lighting and distortion conditions  
- Ensure consistent detection semantics across MVP and final tool  
- Provide reference implementations for C/C++ porting  

The Vision Agent owns the marker format and detection pipeline.

## 4. Simulator Agent

Responsible for the MVP simulation environment.

Responsibilities:
- Maintain simulator.md  
- Implement and update gantry, camera, and laser simulation  
- Validate coordinate mapping logic  
- Provide synthetic test cases for the Vision Agent  
- Ensure simulator behaviour matches real hardware expectations  

The Simulator Agent is MVP‑only but defines behaviour required by the final tool.

## 5. Bridge Agent

Responsible for LightBurn integration and WinAPI interaction.

Responsibilities:
- Maintain bridge-lightburn.md  
- Implement LightBurn window detection  
- Implement hotkey interception logic  
- Maintain Print & Cut state machine  
- Ensure identical behaviour across MVP and final tool  

The Bridge Agent owns all OS‑level integration logic.

## 6. UI Agent

Responsible for user interface behaviour.

Responsibilities:
- Maintain UI-related documentation  
- Implement camera preview overlays  
- Implement marker confirmation dialogs  
- Ensure consistent user workflow across MVP and final tool  
- Coordinate with Vision and Bridge Agents for UI events  

The UI Agent ensures the tool remains intuitive and predictable.

## 7. Core Logic Agent

Responsible for the internal logic that connects modules.

Responsibilities:
- Maintain coordinate mapping logic  
- Maintain movement logic (simulated or real)  
- Ensure correct sequencing of operations  
- Guarantee external behaviour contract  
- Validate consistency between MVP and final tool  

The Core Logic Agent ensures the system behaves as a unified whole.

## 8. Documentation Agent

Responsible for maintaining all documentation.

Responsibilities:
- Maintain all files under docs/  
- Ensure documentation reflects current behaviour  
- Update docs after any behavioural change  
- Enforce documentation-driven development  
- Validate consistency across all documents  

The Documentation Agent is the final authority on written specifications.

## 9. Testing Agent

Responsible for automated and manual testing.

Responsibilities:
- Maintain testing.md and test-summary.md  
- Create and update automated tests  
- Validate behaviour across MVP and final tool  
- Ensure regression prevention  
- Maintain reproducible test environments  

The Testing Agent ensures long-term stability and correctness.

## 10. Collaboration Rules

- Each agent must respect module boundaries.  
- Cross-module changes require Architecture Agent approval.  
- Documentation updates are mandatory for behavioural changes.  
- Testing Agent must validate all complex changes.  
- All agents must follow AGENTS.md workflow rules.

This role system ensures clarity, modularity, and safe evolution of the project.