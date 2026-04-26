# Modularize Appointment Page Flow

## Why

The appointments area is the clearest frontend hotspot for structural drift. The legacy `frontend/src/views/AppointmentsPage.vue` grew into a large page component that combined list loading, filters, pagination, route-driven prefill behavior, form state, confirmation and completion workflows, attachment handling, role-sensitive UI rules, and slot availability calculations.

That concentration of responsibilities makes the page harder to understand, harder to change safely, and harder to use as a model for future feature work.

This change creates a design-first pilot for applying the new frontend boundary model to one real capability without requiring a broad frontend rewrite.

## What Changes

Define how the appointments area should be split into a feature-oriented structure under the standardized frontend boundary model.

This change defines:
- the target substructure for the appointments feature
- what remains in the feature page container versus what moves into local modules
- how appointment APIs, page flows, dialogs, upload behavior, and supporting calculations should be separated
- how the appointments feature should interact with shared and cross-feature concerns
- how migration should proceed incrementally rather than through a single large rewrite

## Scope

In scope:
- the appointments feature as the first pilot area
- modular boundaries for appointments pages, components, composables, API modules, types, and optional local state
- integration boundaries with auth and shared API infrastructure
- migration sequencing for the pilot

Out of scope:
- immediate implementation of the split
- backend appointment workflow changes
- redesign of appointment UX
- unrelated frontend feature migration

## Expected Outcome

After this change, the appointments area should have a defined target shape and migration plan that can be implemented incrementally while also serving as the reference example for future feature-oriented frontend refactors.
