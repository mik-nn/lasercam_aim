# evaluator.md — Evaluation Rules for Autonomous Agents

This document defines how all autonomous and semi‑autonomous agents in the Marker Alignment Tool project are evaluated. The evaluator ensures that every agent action is safe, correct, reversible, and aligned with the documentation-driven development model defined in AGENTS.md.

## 1. Purpose of the Evaluator

The evaluator enforces:
- correctness of agent output,
- adherence to documentation,
- compliance with module boundaries,
- safe and reversible changes,
- consistency between MVP and final tool behaviour,
- proper use of Plan Mode for complex tasks.

The evaluator is the final authority on whether an agent’s contribution is accepted.

## 2. Evaluation Criteria

The evaluator checks each agent action against the following criteria:

### Documentation Consistency
- All changes must match the behaviour described in docs/.
- Any behavioural change must include documentation updates.
- No undocumented assumptions or hidden logic are allowed.

### Module Boundary Compliance
- Agents must modify only the modules they own.
- Cross-module changes require Architecture Agent approval.
- Violations result in rejection.

### Behavioural Consistency
- External behaviour must match the MVP reference.
- Marker detection semantics must remain stable.
- Print & Cut workflow must remain unchanged unless explicitly approved.

### Code Quality
- Code must be clean, maintainable, and follow project conventions.
- Inline memory anchors (AICODE-*) must be used where required.
- No dead code, no commented-out blocks, no unexplained hacks.

### Safety and Reversibility
- All changes must be small and reversible.
- Large diffs without justification are rejected.
- Risky behaviour (hardware movement, WinAPI hooks) must be guarded.

### Testing Requirements
- Complex tasks require full test execution.
- Test results must be written to docs/test-summary.md.
- New features must include tests when applicable.

## 3. Plan Mode Enforcement

The evaluator ensures that:
- complex tasks always use Plan Mode,
- plan files follow the required structure,
- implementation begins only after explicit approval,
- the final implementation matches the approved plan.

If an agent skips Plan Mode for a complex task, the evaluator rejects the contribution.

## 4. Documentation-Driven Development Enforcement

The evaluator verifies that:
- agents read all documentation before acting,
- changes do not contradict existing docs,
- new behaviour is documented immediately,
- outdated documentation is updated or removed.

Documentation is treated as the single source of truth.

## 5. Inline Memory Anchor Enforcement

The evaluator checks that:
- AICODE-NOTE is used for non-obvious logic,
- AICODE-TODO is used for deferred work,
- AICODE-QUESTION is used for uncertainties,
- anchors are placed in the correct locations,
- anchors are meaningful and not generic.

Missing anchors in complex logic results in rejection.

## 6. Behaviour Contract Validation

The evaluator ensures that:
- MVP and final tool share identical external behaviour,
- coordinate mapping logic remains consistent,
- marker detection outputs remain stable,
- LightBurn integration follows the documented workflow,
- the state machine transitions are correct.

Any deviation must be documented and approved.

## 7. Error Categories

The evaluator classifies errors into:

### Critical Errors (automatic rejection)
- breaking external behaviour contract,
- modifying multiple modules without approval,
- missing documentation updates,
- unsafe hardware-related changes,
- skipping Plan Mode for complex tasks.

### Major Errors (requires revision)
- missing inline anchors,
- incomplete tests,
- inconsistent naming or structure,
- unclear logic or missing comments.

### Minor Errors (fix-on-commit)
- formatting issues,
- small style inconsistencies,
- trivial documentation typos.

## 8. Acceptance Conditions

A contribution is accepted only if:
- it passes all evaluator checks,
- documentation is updated,
- tests pass or failures are documented,
- behaviour remains consistent,
- changes are reversible,
- module boundaries are respected.

## 9. Evaluator Authority

The evaluator has the authority to:
- reject contributions,
- request revisions,
- require additional documentation,
- require additional tests,
- escalate architectural issues to the Architecture Agent.

The evaluator cannot modify code directly; it only approves or rejects.

## 10. Long-Term Stability

The evaluator ensures:
- no drift between MVP and final tool,
- no undocumented behaviour changes,
- no silent regressions,
- no architectural erosion,
- no accumulation of technical debt.

The evaluator is the guardian of project integrity.