# Standardize Frontend Feature Boundaries

## Why

The frontend currently follows a mostly layer-oriented structure built around folders such as `views/`, `stores/`, `utils/`, `components/`, and `composables/`. That structure works for small modules, but it becomes harder to reason about as feature complexity grows.

Business logic, page logic, API calls, feature-specific state, and reusable utilities can become separated by technical type rather than grouped by business capability. This increases the cost of change, makes ownership less clear, and encourages large page files to absorb more responsibility over time.

The repository needs a clearer rule for where frontend code belongs before more UI and workflow changes accumulate.

## What Changes

Define a standard frontend module boundary model based on a hybrid structure:
- `app/` for application-level composition
- `shared/` for cross-feature reusable foundations
- `features/` for business-capability modules

This change defines:
- what kinds of code belong in each layer
- where route pages should live
- where Pinia stores should live
- how API code should be split between shared and feature layers
- how cross-feature dependencies are allowed to work
- how migration should proceed incrementally instead of as a rewrite

## Scope

In scope:
- frontend structural standards
- feature boundary rules
- dependency rules between frontend modules
- migration principles for existing code

Out of scope:
- immediate code movement across the frontend
- backend architecture changes
- UI redesign
- runtime behavior changes unrelated to structure

## Expected Outcome

After this change, future frontend work should have a clear default placement model, and existing hotspot areas should have an agreed migration direction instead of ad hoc file-by-file restructuring.
