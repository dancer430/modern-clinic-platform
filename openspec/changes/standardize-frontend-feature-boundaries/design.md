# Design: Hybrid Frontend Feature Boundaries

## Boundary

This design defines how frontend code in this repository should be organized and how responsibilities should be divided between application-level composition, shared foundational code, and business-capability modules.

It does not require an immediate rewrite of the existing frontend. It defines the target structure and the rules used to move toward it over time.

## Motivation

The current layer-oriented structure makes simple code easy to place, but it does not scale well when a business capability grows. Large pages can accumulate state, API calls, dialogs, workflow actions, and helper logic because the structure does not naturally gather those pieces into one capability boundary.

This is already visible in hotspot patterns such as large page components, duplicated client responsibilities, and uncertainty around whether logic is global, reusable, or feature-specific.

The goal is to reduce ambiguity about placement and ownership before more frontend restructuring happens.

## Chosen Structure

The frontend should standardize on a hybrid structure:

```text
frontend/src/
  app/
  shared/
  features/
```

### `app/`

`app/` owns application-level composition:
- router registration
- app shell
- top-level providers and initialization
- cross-feature orchestration

`app/` should connect features together, not absorb feature business logic.

### `shared/`

`shared/` owns code that is genuinely cross-feature and not tied to one business capability:
- shared UI primitives
- shared utility libraries
- shared type definitions
- shared HTTP client and request infrastructure

`shared/` should not become a dumping ground for feature logic that merely happens to be reused once.

### `features/`

`features/` owns business-capability modules such as appointments, auth, patients, and doctors.

A feature may contain:
- route page components
- feature-specific components
- feature-specific composables
- feature-specific stores
- feature-specific API modules
- feature-specific types

## Page Placement

Page-level route components should live inside their owning feature.

The router stays in `app/router`, but the page components it registers should be imported from `features/*/pages`. This preserves a single routing entry point while keeping business entry screens inside their business module.

This rule prevents top-level page files from becoming detached from their related dialogs, API calls, and feature state.

## Store Placement

Pinia stores should default to the owning feature.

Only truly application-level state should live in `app/`. That means state that is cross-feature, cross-page, or foundational to the application shell itself.

Feature state should not be promoted to the app layer just because it is long-lived or visible in multiple screens of the same capability.

This rule is intended to prevent a single global store area from becoming an unbounded coordination layer.

## API Placement

API responsibilities should be split across shared and feature layers.

### Shared API layer

`shared/api` should own:
- the HTTP client
- interceptors
- authentication header behavior
- retry and common request configuration

### Feature API layer

`features/*/api` should own:
- business-specific endpoint definitions
- request helpers scoped to one capability
- response typing closely tied to the feature domain

This keeps transport concerns centralized without recreating a single global catalog of business endpoints.

## Cross-Feature Dependencies

Cross-feature dependencies are allowed, but only through explicit public interfaces.

That means a feature may depend on another feature's exported surface, but it must not reach into internal stores, internal components, or internal helper files.

This rule preserves flexibility while protecting feature internals from accidental coupling.

## Migration Strategy

Migration should be incremental.

The goal is not to move every frontend file immediately. The goal is to use this boundary model as the default for:
- all new frontend work
- any touched hotspot during future refactors
- any area already being redesigned for other reasons

Existing modules should be migrated when the expected clarity gain is worth the movement cost.

## Alternatives Considered

### Option A: Pure feature-first structure

Rejected for now because it creates a strong target model but asks for a sharper migration jump than this repository currently needs.

### Option B: Keep the current layer-first structure and add rules

Rejected because it reduces ambiguity only partially and still encourages business logic to remain scattered across global technical folders.

### Option C: Hybrid structure with app/shared/features

Chosen because it improves business-capability cohesion while preserving stable top-level layers for shared and application-wide concerns.

## Risks

- teams may disagree about whether code is truly shared or feature-owned
- `shared/` may become a new dumping ground if the bar is too low
- migration may become inconsistent if not tied to active work
- some existing files may fit the new model only after partial extraction

## Mitigations

- define strong defaults: feature-owned unless clearly app-wide or cross-feature foundational
- require explicit reasoning before moving feature logic into `shared/`
- migrate opportunistically with active changes rather than by mass movement
- use public feature exports to reduce accidental direct coupling

## Verification

This design is successful when:
- new frontend code has a clear default placement
- route pages are colocated with their business modules
- stores are mostly feature-owned instead of globally pooled
- HTTP infrastructure is shared while business endpoints remain feature-scoped
- cross-feature imports become more intentional and easier to review

## Rollback

If the hybrid structure proves too heavy or too ambiguous, the first rollback step should be to simplify the migration expectations, not to abandon the boundary model entirely.

The first fallback is:
- keep the hybrid target but restrict enforcement to new code and obvious hotspots

The fallback should not be:
- return to ad hoc placement based only on technical file type
