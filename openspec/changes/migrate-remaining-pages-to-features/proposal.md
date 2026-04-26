# Migrate Remaining Pages to Features

## Why

Only the appointments page has been migrated into the `features/` boundary model defined in `standardize-frontend-feature-boundaries`. The remaining route pages — Dashboard, Doctors, Patients, TimeSlots, Records, Profile, Login — still live under `views/` as monolithic single-file components. Two more files (`ImageUploadPage.vue`, `StatisticsPage.vue`) are orphaned: neither is registered in the router and neither is imported anywhere.

Cross-cutting gaps the current router exposes:
- routes only check `requiresAuth`; any authenticated user can navigate to any page (e.g. patients can land on `/timeslots` even though that page is doctor-oriented)
- `App.vue`'s sidebar shows the same nav links to every role
- there is no shell-level guard that observes role mismatches

This sub-change finishes the boundary migration and adds role-aware routing in one pass.

## What Changes

For each non-appointments business page:
- create `features/<name>/{api,components,composables,pages,types}` per the standard
- move the page to `features/<name>/pages/<Name>Page.vue`
- extract the page's HTTP calls into `features/<name>/api/index.ts`
- extract dialog state and stateful workflows into `features/<name>/composables/`
- update the router to import from the feature path
- delete the old `views/<Name>Page.vue`

Routing changes:
- add `meta.roles?: Array<'admin' | 'doctor' | 'patient'>` to every route
- the router `beforeEach` guard rejects mismatched roles to `/dashboard` with a toast
- the App shell sidebar filters its nav items by the current user's role

Cleanup:
- delete orphaned `views/ImageUploadPage.vue` and `views/StatisticsPage.vue`

## Scope

In scope:
- migration of Dashboard, Doctors, Patients, TimeSlots, Records, Profile pages to `features/`
- LoginPage stays where it is for now (it's the auth feature page, but moving it requires coordinating with the auth feature's `pages/` directory)
- role-aware routing guards
- role-aware sidebar filtering
- removal of orphaned views

Out of scope:
- redesigning any page UX
- splitting long composables into multiple files (we extract; we do not redesign)
- adding new feature-local stores unless cross-page state is genuinely shared
- LoginPage migration to `features/auth/pages/` (deferred to keep this PR focused)

## Expected Outcome

After this change:
- `frontend/src/views/` is empty or contains only LoginPage
- every business page has a corresponding `features/<name>/` directory
- a patient navigating to `/timeslots` is redirected to `/dashboard` with a toast
- the sidebar hides menu items the current role cannot reach
- the existing 15 frontend tests stay green; new role-guard tests are added
