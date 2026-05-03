# Change Governance

This repository uses OpenSpec as the default entry point for non-trivial change design.

The goal is to make architecture and workflow changes explicit before implementation begins. We do not want important decisions to live only inside diffs or code comments.

## Default Rule

All non-trivial changes must begin with an OpenSpec change under:

```text
openspec/changes/<change-name>/
```

Each change should include:
- `proposal.md` — why the change exists
- `design.md` — how the change is reasoned about
- `tasks.md` — how the change will be executed

## Micro-Change Exceptions

The following may bypass OpenSpec:
- text or comment edits
- typo fixes and minor style-only adjustments
- purely mechanical renames with no behavior change

If a change affects behavior, APIs, data structures, permissions, page flow, component responsibilities, directory structure, or architecture, it must start as an OpenSpec change.

## Artifact Responsibilities

### proposal.md

Use `proposal.md` to define:
- the current problem
- the intended outcome
- the scope
- the non-goals

### design.md

Use `design.md` to define:
- the boundary being changed
- why the change is needed now
- alternatives considered
- main risks
- verification strategy
- rollback strategy

### tasks.md

Use `tasks.md` to define:
- small, verifiable work items
- sequencing where needed
- a clear path from design to implementation

Tasks should be concrete enough that implementers do not need to rediscover the original intent from source code alone.

## Readiness Gate

A change is ready to implement only when:
- `proposal.md` clearly defines goal, scope, and non-goals
- `design.md` answers the required architectural questions
- `tasks.md` is concrete and verifiable
- the change name matches repository naming rules
- the change does not mix unrelated concerns

Implementation should not begin when boundaries are vague, alternatives are missing, verification is generic, or the tasks are still too large.

## Naming Convention

This repository uses mixed change naming:
- business-facing changes use business capability names
- governance, architecture, and process changes use technical-topic names

Examples:
- `improve-appointment-workflow`
- `clarify-medical-record-access`
- `adopt-openspec-change-governance`
- `standardize-frontend-feature-boundaries`

## AI Workflow Rule

OpenSpec is the governing layer.

AI tools such as superpowers and OMO are execution and analysis tools. They may explore, clarify, and help draft artifacts, but implementation work should map back to an explicit change and explicit tasks.

Exploration findings should flow back into the change artifacts rather than silently turning into implementation scope.

## Current Change Chain

The current repository change chain is:

1. `openspec/changes/adopt-openspec-change-governance/`
2. `openspec/changes/standardize-frontend-feature-boundaries/`
3. `openspec/changes/modularize-appointment-page-flow/`
4. `openspec/changes/unify-auth-client-responsibilities/`

Read them in order if you want to understand how governance, frontend boundaries, and the first frontend pilot changes fit together.

For the recommended reading and future implementation order, see:
- `change-roadmap.md`
