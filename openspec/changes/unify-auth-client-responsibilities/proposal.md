# Unify Auth Client Responsibilities

## Why

The frontend auth flow currently spreads responsibility across multiple modules: `frontend/src/stores/auth.ts`, `frontend/src/utils/tokenRefresh.ts`, `frontend/src/utils/apiClient.ts`, and `frontend/src/utils/axios.ts`.

This creates unclear ownership over authentication state, persistence, token refresh orchestration, logout behavior, and HTTP retry rules. It also duplicates transport behavior across two axios clients with overlapping interceptors and slightly different request rules.

The repository needs a clearer auth boundary model so that the frontend boundary standard can be applied consistently to a second hotspot after the appointments pilot.

## What Changes

Define a feature-oriented responsibility split for frontend auth and HTTP client behavior.

This change defines:
- what belongs in the auth feature versus the shared API layer
- what the auth store should own versus what should move into services
- how token lifecycle behavior should be organized
- how login, logout, refresh, and retry behavior should be modeled without duplicated client logic
- how the auth capability should expose a public interface to other features

## Scope

In scope:
- frontend auth structure and responsibility boundaries
- auth feature modules and public interface design
- shared HTTP client responsibilities
- migration direction for existing auth-related files

Out of scope:
- backend authentication changes
- role and permission redesign
- immediate implementation of the restructure
- unrelated frontend feature refactors

## Expected Outcome

After this change, auth and HTTP-client responsibilities should have a clear target design that reduces duplication, clarifies ownership, and gives other features a stable public interface for authentication-related needs.
