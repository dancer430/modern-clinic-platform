# Tasks

## Task 1: Define auth target structure
- [ ] Define the target `features/auth` structure
- [ ] Define the purpose of `api/`, `services/`, `store/`, and `types/` within auth
- [ ] Define the shared transport responsibilities that remain outside the auth feature

## Task 2: Define store and service boundaries
- [ ] Define what the auth store should own
- [ ] Define what should move into auth services
- [ ] Define what timer, storage, and refresh lifecycle logic should no longer live directly in the store

## Task 3: Define shared client responsibilities
- [ ] Define the responsibilities of the single shared HTTP client model
- [ ] Define what auth-specific behavior must not live in the shared client
- [ ] Define how authenticated requests obtain access tokens without duplicating interceptors

## Task 4: Define auth API and public interface boundaries
- [ ] Define the responsibilities of `features/auth/api`
- [ ] Define the public auth interface that other features may consume
- [ ] Define which imports into auth internals should be treated as violations

## Task 5: Define migration sequencing
- [ ] Define the recommended order for reducing duplicated auth/client logic
- [ ] Define how to preserve current behavior during structural migration
- [ ] Define what a safe first implementation batch should cover

## Task 6: Prepare future implementation alignment
- [ ] Ensure this change aligns with `standardize-frontend-feature-boundaries`
- [ ] Ensure future auth implementation tasks can reference this change directly
- [ ] Document auth as the second boundary pilot after appointments
