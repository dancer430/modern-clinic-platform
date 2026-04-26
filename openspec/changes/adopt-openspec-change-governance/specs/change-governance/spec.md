## ADDED Requirements

### Requirement: Non-trivial changes require OpenSpec artifacts
The repository SHALL require all non-trivial changes to begin with an OpenSpec change that defines proposal, design, and tasks artifacts before implementation starts.

#### Scenario: Non-trivial frontend change is proposed
- **WHEN** a contributor wants to change application behavior, architecture, API shape, permissions, page flow, or component responsibilities
- **THEN** the contributor MUST create an OpenSpec change with `proposal.md`, `design.md`, and `tasks.md` before implementation begins

#### Scenario: Non-trivial backend or process change is proposed
- **WHEN** a contributor wants to change backend behavior, data structures, workflow rules, repository governance, or architecture conventions
- **THEN** the contributor MUST create an OpenSpec change with `proposal.md`, `design.md`, and `tasks.md` before implementation begins

### Requirement: Micro-changes may bypass OpenSpec only under narrow conditions
The repository SHALL allow bypassing OpenSpec only for text or comment edits, typo fixes and minor style-only adjustments, and purely mechanical renames with no behavior change.

#### Scenario: Typo-only change is made
- **WHEN** a contributor fixes a spelling mistake or adjusts comments without changing behavior
- **THEN** the change MAY proceed without a new OpenSpec change

#### Scenario: Structural or behavioral change is proposed
- **WHEN** a change goes beyond the allowed micro-change categories
- **THEN** it MUST be treated as non-trivial and enter the OpenSpec workflow

### Requirement: Change readiness must be explicit before implementation
The repository SHALL treat a change as implementation-ready only when scope, design reasoning, and executable tasks are explicit enough that implementers do not need to infer the true intent from source code alone.

#### Scenario: Change has complete artifacts
- **WHEN** `proposal.md` defines goal, scope, and non-goals, `design.md` defines boundary, alternatives, risks, verification, and rollback, and `tasks.md` defines concrete work items
- **THEN** the change MAY enter implementation

#### Scenario: Change is underspecified
- **WHEN** boundaries are vague, alternatives are missing, verification is generic, or tasks remain too large
- **THEN** implementation MUST NOT begin

### Requirement: OpenSpec governs AI-assisted execution
The repository SHALL use OpenSpec as the governing layer for AI-assisted work, and AI-assisted implementation MUST map back to explicit change artifacts and explicit tasks.

#### Scenario: AI is used before a change exists
- **WHEN** AI tools are used without an OpenSpec change
- **THEN** they MAY explore, clarify, and draft artifacts but MUST NOT default to implementation

#### Scenario: AI discovers new unrelated work
- **WHEN** exploration or implementation reveals unrelated scope outside the current change
- **THEN** the new work MUST be captured in a separate change instead of being silently folded into the current one
