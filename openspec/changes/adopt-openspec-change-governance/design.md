# Design: OpenSpec as the Default Change Entry Point

## Boundary

This design governs how changes are proposed, reasoned about, and prepared for implementation in this repository.

It does not directly change runtime architecture. It changes the decision process that must exist before runtime architecture is changed.

## Core Rule

All non-trivial changes must begin as an OpenSpec change.

Only the following may bypass OpenSpec:
- text/comment edits
- typo and minor style-only adjustments
- purely mechanical renames with no behavior change

Any change affecting behavior, APIs, data structures, permissions, page flow, component responsibilities, directory structure, or architecture must create a change first.

## Change Naming

Naming follows a mixed convention:
- business-facing changes use business capability names
- governance/architecture/process changes use technical-topic names

Examples:
- `improve-appointment-workflow`
- `clarify-medical-record-access`
- `adopt-openspec-change-governance`
- `standardize-frontend-feature-boundaries`

## Artifact Responsibilities

### proposal.md

Defines why the change exists.

It must state:
- the current problem
- the intended outcome
- the scope
- the non-goals

### design.md

Defines how the change is reasoned about.

It must answer:
- what boundary is being changed
- why the change is needed now
- what alternatives were considered
- what the main risks are
- how the change will be verified
- how the change can be rolled back

### tasks.md

Defines how work will be executed.

Tasks must be small, independently verifiable, and clear enough that implementation does not require rediscovering the original intent from source code.

## Readiness Gate

A change is implementation-ready only when:
- `proposal.md` clearly states goal, scope, and non-goals
- `design.md` answers the required architectural questions
- `tasks.md` is concrete and verifiable
- change naming follows repository convention
- scope does not mix unrelated concerns

Implementation must not start when:
- boundaries are vague
- alternatives were not considered
- risks or verification are generic
- tasks are too large or ambiguous
- implementers must infer the true goal from source code alone

## Relationship to superpowers / OMO

OpenSpec is the governing layer.
superpowers / OMO are execution and analysis tools.

Rules:
- without a change, AI may explore, clarify, or propose, but must not default to implementation
- exploration findings should flow back into `proposal.md`, `design.md`, and `tasks.md`
- implementation work should map back to explicit tasks
- verification must provide evidence, not confidence language
- newly discovered unrelated work should open a new change rather than silently expanding scope

## Alternatives Considered

### Option A: Keep the current lightweight approach

Rejected because it preserves speed of starting, but weakens long-term architecture clarity and scope control.

### Option B: Require OpenSpec only for large changes

Rejected because boundary ambiguity would gradually erode the process.

### Option C: Require OpenSpec for all non-trivial changes

Chosen because it creates a stable default and reduces case-by-case negotiation.

## Risks

- the process may feel heavy at first
- contributors may over-document trivial changes
- AI agents may still drift into implementation without explicit gating

## Mitigations

- define a narrow micro-change exemption list
- keep the architecture decision template balanced rather than exhaustive
- treat OpenSpec as the single authoritative pre-implementation boundary

## Verification

This design is successful when:
- future non-trivial work begins with an OpenSpec change
- `proposal.md`, `design.md`, and `tasks.md` have consistent roles
- implementation discussions refer back to change artifacts
- governance and architecture decisions can be understood without reading diffs first

## Rollback

If this process proves too heavy, rollback should relax only the entry threshold, not remove artifact discipline entirely.

The first fallback is:
- require OpenSpec for all medium and large changes

The fallback should not be:
- return to code-first change behavior
