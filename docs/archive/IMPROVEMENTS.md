# Documentation Improvements for the Marker Alignment Tool

The following improvements are proposed for `AGENTS.md` and the `docs/` directory to enhance the documentation-driven development and agent coordination:

## 1. Centralized State Machine (`docs/state-machine.md`)
The Print & Cut workflow's state machine (`idle → first_marker → second_marker → ready`) is referenced in several documents (`architecture.md`, `modules.md`, `bridge-lightburn.md`).  
**Proposal**: Create a dedicated `docs/state-machine.md` describing all states, transitions, and expected side effects to ensure consistency across the MVP and final tool implementations.

## 2. Agent Handover Protocol
Currently, `ROLES.md` states agents work independently.  
**Proposal**: Define a formal "handover" process in `AGENTS.md` for tasks that cross module boundaries (e.g., when the Vision Agent finishes a new marker algorithm, the UI Agent must be notified to update the overlay).

## 3. Role-Specific Validation Checklists
Each role in `ROLES.md` has responsibilities, but no concrete verification steps.  
**Proposal**: Add a "Validation Checklist" section for each role in `ROLES.md`. For example, the Vision Agent's checklist would include verifying detection robustness against lighting changes.

## 4. C/C++ Porting & Parity Tracking (`docs/porting-status.md`)
The transition from MVP (Python) to the final tool (C/C++) is a core project goal.  
**Proposal**: Create `docs/porting-status.md` to track which MVP features have been ported to the final tool and record the results of parity testing.

## 5. Explicit Parity Testing Requirement
**Proposal**: Update `AGENTS.md` (Section 5 or 6) to mandate that for any logic changes in the MVP, the Agent must consider if a corresponding change is needed in the final tool and how parity will be verified.
