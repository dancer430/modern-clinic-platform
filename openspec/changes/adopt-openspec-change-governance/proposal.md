# Adopt OpenSpec Change Governance

## Why

This repository currently has working application code, but it does not yet have a clear change-governance layer.

Non-trivial work can begin directly from code edits, which makes architecture evolution harder to reason about. Scope can expand implicitly, rationale gets buried inside diffs, and later contributors must infer intent from implementation instead of reading an explicit change definition.

This repository needs a default rule that design comes before implementation.

## What Changes

Introduce OpenSpec as the required entry point for all non-trivial changes in this repository.

This change defines:
- which changes must create an OpenSpec change first
- which micro-changes may bypass OpenSpec
- what `proposal.md`, `design.md`, and `tasks.md` must contain
- what quality gate a change must satisfy before implementation begins
- how OpenSpec governs AI-assisted workflows using superpowers / OMO

## Scope

In scope:
- repository-level change governance rules
- a balanced architecture decision template
- implementation readiness criteria
- OpenSpec-to-AI workflow rules

Out of scope:
- refactoring application code
- changing frontend/backend architecture directly
- introducing new product features
- replacing existing `.opencode/` prompt assets

## Expected Outcome

After this change, all non-trivial work starts from explicit change artifacts rather than ad hoc code edits.
