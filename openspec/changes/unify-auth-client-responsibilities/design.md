# Design: Auth Feature and Shared Client Responsibility Boundaries

## Boundary

This design defines how frontend authentication responsibilities should be divided between the auth feature and the shared API infrastructure.

It does not change backend auth behavior. It reorganizes frontend ownership so that state, persistence, token lifecycle logic, and HTTP transport concerns no longer overlap awkwardly.

## Motivation

The current auth implementation mixes several kinds of responsibility in one flow:
- auth state and user/session data
- local storage persistence
- token expiry scheduling
- token refresh orchestration
- logout cleanup behavior
- HTTP request and retry behavior

These concerns are currently split across the auth store, a token refresh helper, and two axios clients with overlapping interceptor responsibilities. That structure makes it harder to reason about where auth bugs should be fixed and makes reuse by other features less explicit.

## Target Structure

Auth should become a feature-owned capability under the hybrid frontend model, while transport stays shared.

```text
frontend/src/
  shared/
    api/
  features/
    auth/
      api/
      services/
      store/
      types/
```

## Shared API Responsibility

`shared/api` should own:
- the base HTTP client
- common interceptor wiring
- shared request configuration
- the mechanism by which authenticated requests can obtain the current access token

`shared/api` should not own auth feature business actions such as login, logout, or session restoration workflows.

## Auth Feature Responsibility

`features/auth` should own:
- auth-facing types
- auth endpoint wrappers
- token lifecycle services
- auth store state and derived auth getters
- the public interface through which other features access auth context

The auth feature should be the canonical place for session behavior, while the shared client should only provide transport infrastructure.

## Store Boundary

The auth store should own:
- current user/session state
- derived role and authentication getters
- high-level auth actions exposed to the UI or other app-level composition code

The auth store should not remain the default home for timer management, local-storage mechanics, and low-level refresh implementation details if those concerns can be moved into auth services.

## Service Boundary

Auth services should own:
- token persistence and restoration mechanics
- token expiry calculations and refresh scheduling
- low-level refresh coordination
- logout cleanup orchestration that is not purely store state mutation

This keeps the store focused on state and high-level flows rather than acting as both state container and auth runtime engine.

## API Boundary

`features/auth/api` should define auth business endpoints such as:
- login
- logout
- refresh
- current-user/session fetches where applicable

These endpoint wrappers should consume the shared HTTP client or approved shared transport primitives rather than creating feature-specific transport stacks.

## Public Interface for Other Features

Other features should consume auth only through the auth feature's public surface.

That public surface may include:
- current-user access
- role-aware getters
- authenticated-session state
- high-level auth actions intended for cross-feature use

Other features should not directly import auth internals such as storage helpers, timer logic, or private service implementation files.

## Migration Strategy

Migration should be incremental.

Recommended sequence:
1. define auth types, feature API wrappers, and service boundaries
2. define a single shared client responsibility model
3. move token lifecycle behavior behind auth services
4. reduce the auth store to state plus high-level actions
5. expose a stable public auth interface for other features

The migration should remove duplicated client logic while preserving behavior.

## Alternatives Considered

### Option A: Leave auth as a special-case global implementation

Rejected because it preserves unclear ownership and works against the frontend boundary model.

### Option B: Move everything auth-related into the store

Rejected because it keeps low-level runtime mechanics and transport-coupled concerns bound to state management.

### Option C: Split shared transport from feature-owned auth behavior

Chosen because it matches the hybrid boundary standard and creates a cleaner surface for other features.

## Risks

- auth service boundaries may become over-engineered if split too finely
- migration could temporarily duplicate persistence or refresh logic
- the shared client could still drift into owning auth-specific behavior if not constrained
- consumers may continue to import old auth files directly during transition

## Mitigations

- keep services grouped by responsibility rather than by tiny abstractions
- define one shared client model and one auth public interface clearly
- move low-level mechanics out of the store before widening auth reuse
- treat direct imports of auth internals as transition debt to eliminate

## Verification

This design is successful when:
- auth state, token lifecycle behavior, and transport concerns have distinct owners
- duplicated axios-client behavior is replaced by a single shared client model
- the auth store becomes smaller and more state-focused
- other features can use auth through a stable public interface instead of internal file access

## Rollback

If the auth split proves too disruptive, rollback should reduce extraction depth while preserving the principle of one shared client model.

The first fallback is:
- centralize the HTTP client first and defer some auth service extraction while still reducing store overload

The fallback should not be:
- keep two overlapping axios clients and an ever-growing auth store indefinitely
