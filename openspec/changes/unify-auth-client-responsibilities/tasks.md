# Tasks

## Task 1: Define auth target structure
- [x] Define the target `features/auth` structure (`api/`, `services/`, `store/`, `types/`, `index.ts`)
- [x] Define the purpose of `api/`, `services/`, `store/`, and `types/` within auth
- [x] Define the shared transport responsibilities that remain outside the auth feature (`shared/http/{client,auth-bridge}.ts`)

## Task 2: Define store and service boundaries
- [x] Auth store owns: user, token, refreshToken, tokenExpireTime + role getters + login/logout/scheduleRefresh actions
- [x] Auth services own: token persistence (services/session.ts) and refresh coordination (services/refresh.ts)
- [x] Timer, storage, and refresh lifecycle logic no longer live directly in the store: only the *high-level* schedule/cancel calls do; the actual storage I/O is in services/session.ts and the singleton refresh promise lives in services/refresh.ts

## Task 3: Define shared client responsibilities
- [x] Single shared HTTP client `shared/http/client.ts` with one request interceptor (token attach) and one response interceptor (401 retry via injected callback)
- [x] No auth-specific behavior in shared/http: tokens are obtained via the registered `getAccessToken` callback, refresh is delegated via `refreshAccessToken`, and post-failure cleanup is delegated via `onAuthFailure`
- [x] Authenticated requests obtain access tokens through the auth-bridge registry, not by directly importing the auth feature

## Task 4: Define auth API and public interface boundaries
- [x] `features/auth/api/index.ts` owns login/logout/refresh endpoint wrappers; consumes shared HTTP client
- [x] `features/auth/index.ts` is the only public surface: exports `useAuthStore`, `setupAuth`, and the `User`/`Role`/`LoginCredentials` types
- [x] Imports targeting `features/auth/services/*` or `features/auth/store/*` from outside the auth feature are treated as boundary violations (none exist after this change)

## Task 5: Define migration sequencing
- [x] Build new structure additively (shared/http + features/auth) before removing old files
- [x] Re-wire all consumers (App.vue, router, views/*, composables, features/appointments) to the new public surface
- [x] Delete legacy files: `frontend/src/utils/{axios,apiClient,tokenRefresh}.ts`, `frontend/src/stores/auth.ts`, `frontend/src/api/images.ts` (orphaned)
- [x] Move and rewrite the deduplication contract test from `utils/__tests__/tokenRefresh.spec.ts` to `features/auth/services/__tests__/refresh.spec.ts` so the test moved with the code
- [x] Add `shared/http/__tests__/client.spec.ts` for the auth-bridge registration contract

## Task 6: Future implementation alignment
- [x] Aligned with `standardize-frontend-feature-boundaries`: `app/` (router + main.ts) → `shared/http` → `features/auth`
- [x] `setupAuth()` is the only side-effecting call from `main.ts`; future feature additions hook the HTTP client by registering their own behaviors (none required for now)
- [x] Documented as the second boundary pilot after appointments

## Verification
- [x] `vitest` 4 files / 15 tests green
- [x] `vue-tsc -b --noEmit` clean
- [x] `vite build` succeeds
- [x] No grep for the legacy paths (`@/utils/{axios,apiClient,tokenRefresh}`, `@/stores/auth`, `@/api/images`) returns any matches under `frontend/src/`
