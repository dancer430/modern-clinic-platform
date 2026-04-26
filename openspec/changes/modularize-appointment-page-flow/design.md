# Design: Appointments Feature Pilot Under Hybrid Frontend Boundaries

## Boundary

This design defines how the existing appointments page flow should be decomposed into a feature-oriented structure under `features/appointments`.

It does not redesign appointment behavior. It reorganizes responsibilities so that the appointments capability can become the first concrete pilot of the standardized frontend boundary model.

## Motivation

The current appointments page is handling too many concerns in one place. The page owns list loading, server-side filtering, pagination, user option loading, schedule slot loading, route-driven prefill behavior, create/confirm/complete/cancel dialog state, attachment upload logic, role-sensitive actions, and helper calculations for slot availability.

This makes the appointments flow a strong pilot candidate because it already demonstrates the exact failure mode the boundary standard is trying to address: business capability logic is present, but not yet grouped into a business-capability module.

## Target Feature Shape

The appointments capability should move toward a feature-local structure such as:

```text
frontend/src/features/appointments/
  pages/
  components/
  composables/
  api/
  types/
```

If local state later proves necessary beyond composables, a feature-local store may be added, but the pilot should not introduce a store unless the flow genuinely needs shared state across multiple appointments screens.

## Page Responsibility

The route page should remain the composition entry point for the appointments feature, but it should become a thin container.

Its responsibilities should be limited to:
- coordinating top-level appointments page sections
- wiring route concerns to feature modules
- composing feature dialogs and list sections
- handling cross-module orchestration that is still page-specific

The page should no longer be the default home for calculations, endpoint calls, upload handling, or dialog-specific workflow logic.

## Feature Modules to Extract

### Appointments API module

`features/appointments/api` should own business endpoints related to:
- appointments list and mutation requests
- doctor and patient option loading for this workflow
- schedule-slot reads required by the appointments booking experience

It should consume the shared HTTP client from the shared API layer rather than owning transport infrastructure.

### Appointments types

`features/appointments/types` should own domain-facing frontend types for appointment items, pagination shapes, form payloads, attachment payloads, and slot option structures that are specific to this capability.

### Appointments composables

Feature composables should own localized business behavior such as:
- list querying and filter state
- create appointment form state and slot option derivation
- confirm/complete/cancel workflow state
- attachment preparation and validation composition
- route-prefill interpretation specific to the appointments flow

These composables should separate stateful page logic from rendering concerns without forcing everything into a global store.

### Appointments components

Feature components should own the visual sections and dialogs that currently live as one large page template, such as:
- filters and pagination controls
- appointment table or list rendering
- create appointment dialog
- confirm appointment dialog
- complete appointment dialog
- cancel confirmation dialog

Components should receive explicit inputs and callbacks rather than directly re-creating business logic internally.

## Shared and Cross-Feature Boundaries

The appointments pilot should obey the broader frontend boundary rules.

### Shared dependencies

Appointments may consume from `shared/` only for truly cross-feature concerns such as:
- HTTP transport infrastructure
- shared UI primitives
- generic utility functions that are not appointment-specific

### Auth dependency

Appointments may depend on auth only through auth's public surface. Role checks and current-user context that are needed for appointment actions should not require direct coupling to auth internals beyond the exposed interface already intended for feature use.

For this pilot, that means the appointments feature may read current-user and role state through the existing auth store entry point that is already consumed by route-level feature code, but it should not reach into token-refresh logic, raw storage helpers, or transport internals.

### Shared versus appointments-local ownership

The pilot should make the shared-versus-local split explicit:

- `shared` continues to own transport setup, generic UI primitives, and cross-feature utilities
- `features/appointments/api` owns appointments-specific endpoint wrappers built on top of shared transport
- `features/appointments/types` owns appointments workflow types, form shapes, attachment payloads, and slot-option structures
- `features/appointments/composables` owns appointments-specific page workflows and orchestration state
- `features/appointments/components` owns appointments-specific visual sections and dialogs

Code should move to `shared` only when another feature would reasonably consume the same abstraction without bringing appointments language or assumptions with it.

### Cross-feature import rule

The appointments pilot should not import other features' internals directly.

Allowed dependency direction for this pilot is:

- feature page/components/composables -> appointments-local modules
- appointments-local modules -> shared modules
- appointments-local modules -> public auth surface already intended for app-wide feature use

Avoided dependency direction for this pilot is:

- appointments modules -> another feature's internal files
- appointments modules -> auth transport/refresh implementation details
- appointments components -> raw shared transport clients

## Migration Strategy

Migration should happen incrementally, not as a single move.

Recommended sequence:
1. define feature-local types and API boundaries
2. extract dialog and workflow logic into feature composables
3. split visual sections into feature components
4. reduce the route page into a composition shell

The first implementation batch is considered successful when:

- the router points at the feature-owned appointments page
- the legacy view no longer acts as the runtime entry point
- appointment endpoint calls live behind `features/appointments/api`
- appointments-specific types are no longer declared inline inside the page
- the route page mainly wires filters, table, pagination, and dialog sections together

Behavior should be preserved by changing one ownership layer at a time, verifying the app after each extraction, and avoiding concurrent behavior redesign while structure is in motion.

The pilot should preserve behavior while changing ownership and placement.

## Alternatives Considered

### Option A: Leave the page intact and only document it as a hotspot

Rejected because it does not test whether the new feature-boundary model is actually actionable.

### Option B: Move the entire appointments page in one step

Rejected because it creates unnecessary migration risk and makes it harder to verify where the new boundaries are helping.

### Option C: Use appointments as an incremental pilot

Chosen because it provides a real, high-value example while still keeping migration scope controlled.

## Risks

- the pilot could over-split logic into too many files without improving comprehension
- feature-local API and composable boundaries could overlap if not stated clearly
- temporary duplication may appear during migration
- the page container could remain too large if orchestration is not constrained deliberately

## Mitigations

- only extract modules with clear ownership
- keep transport in shared and business endpoints in feature API files
- prefer composables for page-local business behavior before adding a store
- treat the route page as a composition shell, not a fallback business-logic bucket

## Verification

This design is successful when:
- the appointments capability has a clear target module map
- the route page becomes thinner and more compositional
- workflow-specific logic is no longer concentrated in one file
- appointments can serve as a repeatable example for later feature migrations

## Rollback

If the pilot proves too granular or too disruptive, rollback should preserve the feature-boundary model while reducing extraction depth.

The first fallback is:
- keep the page under the appointments feature but extract only API, types, and the heaviest dialog/workflow logic first

The fallback should not be:
- abandon feature ownership and return the pilot to generic global layer folders
