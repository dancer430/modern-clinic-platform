# Change Roadmap

This document explains how the current OpenSpec changes fit together and in what order they should be read or implemented.

## Recommended Reading Order

1. `openspec/changes/adopt-openspec-change-governance/`
2. `openspec/changes/standardize-frontend-feature-boundaries/`
3. `openspec/changes/modularize-appointment-page-flow/`
4. `openspec/changes/unify-auth-client-responsibilities/`

This order matters because each later change assumes the rules established by the previous one.

## Change Roles

### 1. Governance layer

`adopt-openspec-change-governance`

This change defines the repository rule that all non-trivial work starts as an OpenSpec change. It also defines artifact expectations, readiness gates, and how AI-assisted work is controlled by OpenSpec rather than replacing it.

Read this first if you want to understand how change design works in this repository.

### 2. Boundary standard layer

`standardize-frontend-feature-boundaries`

This change defines the frontend target model:
- `app/` for application composition
- `shared/` for cross-feature foundations
- `features/` for business-capability modules

It also defines route-page ownership, feature-local store defaults, shared-versus-feature API responsibilities, and cross-feature dependency rules.

Read this second if you want to understand the architectural standard that future frontend refactors are expected to follow.

### 3. Pilot change: appointments

`modularize-appointment-page-flow`

This is the first concrete pilot for the frontend boundary standard. It takes the appointments hotspot and defines how that page flow should be decomposed into feature-local pages, components, composables, API modules, and types.

Read this third if you want to see how the boundary standard applies to a large page-based workflow.

### 4. Pilot change: auth

`unify-auth-client-responsibilities`

This is the second concrete pilot. It defines how auth state, token lifecycle behavior, and shared HTTP-client behavior should be separated under the same frontend boundary standard.

Read this fourth if you want to see how the boundary standard applies to shared infrastructure and cross-feature concerns.

## Recommended Implementation Order

If these changes are later implemented, the recommended order is:

1. Treat `adopt-openspec-change-governance` as already established repository workflow
2. Use `standardize-frontend-feature-boundaries` as the architecture reference
3. Implement `modularize-appointment-page-flow` as the first concrete frontend pilot
4. Implement `unify-auth-client-responsibilities` as the second frontend pilot

The appointments pilot is the better first implementation target because it is feature-local and easier to contain. The auth pilot should follow once the repository has one successful example of the feature-boundary model in motion.

## Current State

All four changes currently have complete OpenSpec artifacts:
- proposal
- design
- specs
- tasks

That means the repository now has:
- a governance model
- a frontend boundary standard
- two real pilot changes that apply the standard

The next phase is no longer discovery. The next phase is choosing when to implement the pilot changes.
