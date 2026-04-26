# Tasks

## Task 1: Define target frontend structure
- [ ] Define the purpose of `app/`
- [ ] Define the purpose of `shared/`
- [ ] Define the purpose of `features/`
- [ ] Add one example feature shape showing pages, components, composables, api, store, and types

## Task 2: Define placement rules
- [ ] Define that route page components live in their owning feature
- [ ] Define that router registration stays in `app/router`
- [ ] Define that Pinia stores default to features
- [ ] Define which state is allowed to live in `app/`

## Task 3: Define API boundary rules
- [ ] Define what belongs in `shared/api`
- [ ] Define what belongs in `features/*/api`
- [ ] Define how feature APIs should consume the shared client
- [ ] Define what should not be centralized globally

## Task 4: Define dependency rules
- [ ] Define allowed cross-feature dependencies through public interfaces only
- [ ] Define what counts as a feature internal implementation detail
- [ ] Define what kinds of direct imports should be treated as violations

## Task 5: Define migration approach
- [ ] Define incremental migration as the default strategy
- [ ] Define when existing code should be moved versus left in place temporarily
- [ ] Define how new work should follow the target boundary model immediately
- [ ] Define how hotspot-driven migration should be justified

## Task 6: Prepare for future implementation
- [ ] Identify the first likely pilot area for this structure
- [ ] Confirm that the pilot can be executed without a frontend rewrite
- [ ] Ensure future implementation tasks can reference this boundary model directly
