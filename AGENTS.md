# AGENTS.md — Coding-Agent Playbook for the Marker Alignment Tool

This document defines the workflow, guard‑rails, and conventions for any autonomous or semi‑autonomous coding agent (“Agent”) contributing to the Marker Alignment Tool project. The project consists of two layers:

- MVP layer: Python + OpenCV + DirectShow + simple UI, used for rapid experimentation with marker detection and simulation.
- Final layer: Standalone C (or C++/Qt) tool with identical external behaviour, used in production.

Agents must follow this playbook to ensure consistent, safe, reversible, documentation‑driven development.

## 1. Core Principles

1. Documentation‑Driven Development  
Every Agent run begins by reading all Markdown files under docs/ to understand architecture, modules, workflows, and constraints.

2. Instruction‑First, Best Practices  
For simple tasks, follow human instructions directly while writing clean, maintainable code.

3. Conditional Planning and Verification  
For complex tasks, produce a plan file and wait for approval before implementation.

4. Greppable Inline Memory  
Use AICODE-* anchors to leave rationale and breadcrumbs for future Agents.

5. Small, Safe, Reversible Commits  
Prefer multiple focused commits over large diffs.

## 2. Task Execution Protocol

A human triggers an Agent with a natural‑language instruction (example: “add marker orientation detection”).

1. Read Documentation  
Agents must read all files in docs/:  
architecture.md  
modules.md  
workflow-print-and-cut.md  
markers.md  
simulator.md  
bridge-lightburn.md

2. Analyse the Request  
Determine dependencies, affected modules, and whether the task is simple or complex.

3. If Complex → Plan Mode  
Create a plan file under plans/ and wait for explicit approval.

4. If Simple → Implement  
Implement directly, keeping edits minimal and aligned with documentation.

5. After Implementation  
For complex tasks: run full tests and update docs/test-summary.md.  
For simple tasks: run only necessary checks.  
Commit with a clear message.

## 2.1 Determining Task Complexity

A task is complex if it involves:

- Multiple modules (camera, recognizer, simulator, bridge, UI)
- Significant algorithmic logic (marker detection, coordinate transforms)
- Integration with external systems (LightBurn, WinAPI hooks)
- Performance‑critical code (real‑time camera processing)
- Architectural changes or cross‑cutting concerns

If uncertain, default to Plan Mode.

## 3. Plan Mode (Complex Tasks Only)

Plans live in plans/ and follow the naming pattern:

###-objective-description.md

A plan must include:

- Objective — the human request verbatim  
- Proposed Steps — short, actionable, numbered  
- Risks / Open Questions — bullet list  
- Rollback Strategy — how to revert safely  

Implementation begins only after explicit approval.

## 4. Inline Memory — AICODE-* Anchors

Use language‑appropriate comment tokens (#, //, etc.).

Anchors:

- AICODE-NOTE: rationale linking new to existing logic  
- AICODE-TODO: follow‑ups not in current scope  
- AICODE-QUESTION: uncertainty requiring human review  

Anchors are mandatory when:

- Logic is non‑obvious  
- Code interacts with legacy or simulator components  
- Marker detection or coordinate transforms are involved  
- Bridge logic touches WinAPI or LightBurn behaviour  

## 5. Test Summary Automation

After running tests for a complex task, the Agent must overwrite docs/test-summary.md with:



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

All Python commands must use the project’s environment:

- Tests: pytest  
- Formatting: black  
- Sorting: isort  
- Style: flake8  
- Type checking: pyright  

## 8. Documentation Maintenance

Agents must update documentation whenever behaviour changes:

- architecture.md — architecture or stage changes  
- modules.md — new modules or API changes  
- workflow-print-and-cut.md — LightBurn integration changes  
- markers.md — marker format or detection logic changes  
- simulator.md — simulation model changes  
- bridge-lightburn.md — WinAPI hook or state machine changes  

Documentation must always reflect the current system.

## 9. Fallback Behaviour

If uncertain:

1. Add an AICODE-QUESTION anchor.  
2. Push work behind a feature flag or draft PR.  

## 10. Project‑Specific Notes

- The MVP layer (Python) is used for rapid iteration on marker detection and simulation.  
- The final tool (C/C++/Qt) must replicate the MVP’s external behaviour exactly.  
- The LightBurn bridge relies on WinAPI window detection and Alt+F1 interception.  
- Marker detection logic must remain consistent across MVP and final tool.  
- Simulation is mandatory in MVP and optional in the final tool.