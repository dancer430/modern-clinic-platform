# Design: Page Migration + Role-Aware Routing

## Boundary

This change moves five existing page components from `frontend/src/views/` into their respective `frontend/src/features/<name>/pages/` modules and adds role-aware route guards. It does not add features, change UX, or rework backend behavior.

## Migration template

Every migrated page follows the appointments pattern:

```text
features/<name>/
  api/index.ts          # HTTP calls (consume @/shared/http)
  types/index.ts        # response & form types
  composables/use<Name>Page.ts  # stateful workflow
  components/*.vue      # dialogs / table cards split out where the page is large
  pages/<Name>Page.vue  # thin composition shell
```

Mechanical rules per page:
1. Identify the page's HTTP calls. Move them to `features/<name>/api/index.ts` (each one a named exported async function).
2. Identify the response/form types. Move them to `features/<name>/types/index.ts`.
3. Identify the stateful workflow (refs, computed, dialog open/close, request orchestration). Move it to a single `composables/use<Name>Page.ts`.
4. Identify the visual sections. If the page is small (< 200 lines), keep them inline; if larger, split into `components/`.
5. The `pages/<Name>Page.vue` becomes ~50–150 lines of template plus a thin script that calls the composable.
6. Update `router/index.ts` to import from the feature path.
7. Delete the old `views/<Name>Page.vue`.

## Role-aware routing

```ts
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: Array<'admin' | 'doctor' | 'patient'>
  }
}
```

Each route gains `meta.roles`. The shell guard becomes:

```ts
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/dashboard'
  const allowed = to.meta.roles
  if (allowed?.length && auth.user && !allowed.includes(auth.user.user_type)) {
    ElMessage.warning('You do not have access to that page')
    return '/dashboard'
  }
  return true
})
```

The sidebar filters identically:

```ts
const visibleNavItems = computed(() =>
  navItems.filter((item) => !item.roles || item.roles.includes(authStore.userType ?? 'patient')),
)
```

## Role assignments (initial cut)

| Path | Roles |
|---|---|
| `/login` | (none — open to anonymous) |
| `/dashboard` | all |
| `/doctors` | all (admin can edit; others read) |
| `/patients` | all (doctor/admin can edit; patients see filtered list) |
| `/appointments` | all |
| `/timeslots` | doctor + admin |
| `/records` | doctor + admin (patients see their records via /appointments completed list) |
| `/profile` | all |

Backend permissions remain the source of truth; the frontend guard is a UX courtesy that reduces 403 round-trips, not a security boundary.

## Migration sequencing

We migrate each page in a separate commit so review and rollback are surgical:
1. Add role-aware routing meta + guard + sidebar filtering. Delete orphan views (`ImageUploadPage`, `StatisticsPage`).
2. Migrate `DashboardPage` (smallest, cleanest).
3. Migrate `RecordsPage`.
4. Migrate `TimeSlotsPage`.
5. Migrate `DoctorsPage`.
6. Migrate `PatientsPage`.
7. Migrate `ProfilePage`.

If time pressure cuts the program short, steps 1 + 2 alone deliver: role guards, orphan removal, and a second page on the new template.

## Risks

- **Sidebar role default.** When the user object is missing (initial load, race), `userType` is null. The sidebar must default to "show nothing role-gated" rather than "show everything", to avoid flashing items that disappear after auth restore.
- **Backend ↔ frontend role parity drift.** Adding role-aware routing in the frontend creates a second source of role policy. Mitigate by having the frontend mirror what the backend already enforces (no new policies invented client-side) and by leaving an integration test that exercises one role/page mismatch end-to-end after the migration.
- **Test churn.** Each migrated page that has unit tests today (none — only appointments) gains a test target during migration. Expect new tests as part of the migration commits, not separate-PRed.

## Verification

- vitest green
- vue-tsc green
- vite build green
- a manual smoke check (or Playwright if added later) confirms a patient cannot navigate to `/timeslots`

## Rollback

Each step ships as one commit. Roll back step N by reverting commit N. The role-guard step is independent of any individual page migration.
