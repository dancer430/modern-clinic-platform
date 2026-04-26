# Tasks

## Task 1: Routing meta + guard + sidebar
- [x] Extend `RouteMeta` declaration with `roles?: Array<Role>`
- [x] Add `meta.roles` to every existing route in `frontend/src/router/index.ts`
- [x] Update `router.beforeEach` to reject mismatched roles back to `/dashboard` with a toast
- [x] Update `App.vue` sidebar to filter `navItems` by current `auth.userType`
- [x] Add `frontend/src/router/__tests__/guard.spec.ts` covering: unauthenticated redirect, role mismatch redirect, role match passes through

## Task 2: Orphan cleanup
- [x] Delete `frontend/src/views/ImageUploadPage.vue` (unrouted, unimported)
- [x] Delete `frontend/src/views/StatisticsPage.vue` (unrouted, unimported)

## Task 3: Migrate Dashboard page
- [ ] Create `features/dashboard/{api,types,composables,pages}` skeleton
- [ ] Move page contents; thin to a composition shell
- [ ] Update router import; delete `views/DashboardPage.vue`

## Task 4: Migrate Records page
- [ ] Create `features/records/{api,types,composables,pages}`
- [ ] Move page contents; delete old view

## Task 5: Migrate TimeSlots page
- [ ] Create `features/timeslots/{api,types,composables,components,pages}`
- [ ] Move page contents; delete old view

## Task 6: Migrate Doctors page
- [ ] Create `features/doctors/{api,types,composables,components,pages}`
- [ ] Move page contents; delete old view

## Task 7: Migrate Patients page
- [ ] Create `features/patients/{api,types,composables,components,pages}`
- [ ] Move page contents; delete old view

## Task 8: Migrate Profile page
- [ ] Create `features/profile/{api,types,composables,pages}`
- [ ] Move page contents; delete old view

## Task 9: Verification
- [x] vitest green after Task 1+2 (guard tests added)
- [ ] vitest green after each subsequent migration commit
- [ ] vue-tsc + vite build green after each commit
- [ ] `frontend/src/views/` contains only LoginPage.vue (or is empty if Login is moved later)

Notes: Tasks 3–8 are scoped per-page and intentionally not implemented in this commit so each migration can land as its own reviewable diff.
