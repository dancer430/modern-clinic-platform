## ADDED Requirements

### Requirement: Shared transport and auth feature behavior shall have separate owners
The frontend SHALL separate shared HTTP transport responsibilities from auth feature behavior so that transport infrastructure and auth business logic do not overlap.

#### Scenario: Shared request infrastructure is needed
- **WHEN** the frontend defines base client configuration, shared interceptor wiring, or common request behavior
- **THEN** that infrastructure MUST belong to the shared API layer rather than an auth feature business module

#### Scenario: Auth business action is modeled
- **WHEN** login, logout, refresh lifecycle behavior, or session restoration is designed
- **THEN** the business behavior MUST belong to the auth feature rather than being scattered across unrelated transport files

### Requirement: Auth state shall be distinct from token lifecycle mechanics
The frontend SHALL keep auth state ownership in the auth store while moving low-level token persistence, scheduling, and refresh coordination into dedicated auth services when those mechanics do not need to remain in the store.

#### Scenario: Auth state is read by UI
- **WHEN** UI code needs current user state, authentication status, or role-aware getters
- **THEN** it MUST obtain them from the auth store or the auth feature's public surface

#### Scenario: Token lifecycle logic is executed
- **WHEN** refresh scheduling, token persistence, or low-level refresh coordination is required
- **THEN** the logic MUST be owned by auth services instead of growing indefinitely inside the store implementation

### Requirement: Auth consumers shall use a public auth interface
Other frontend features SHALL consume authentication context only through the auth feature's public surface and MUST NOT rely on auth internals by default.

#### Scenario: Another feature needs auth context
- **WHEN** a feature needs the current user, authenticated-session state, or role-aware behavior
- **THEN** it MUST consume an exposed auth interface rather than importing private auth implementation files

#### Scenario: Direct import targets auth internals
- **WHEN** a change introduces a dependency on storage helpers, timer logic, or private auth service modules
- **THEN** that dependency MUST be treated as an internal-boundary violation unless promoted deliberately to the auth public surface

### Requirement: Duplicated auth client behavior shall converge on a single shared client model
The frontend SHALL converge duplicated authenticated-client behavior into one shared client responsibility model so that request retry and token attachment behavior are not maintained in overlapping implementations.

#### Scenario: Authenticated request client is defined
- **WHEN** the frontend needs authenticated request handling with token attachment and retry behavior
- **THEN** the behavior MUST be modeled through one shared client responsibility model rather than two overlapping axios client implementations

#### Scenario: Structural migration is staged
- **WHEN** auth/client responsibilities are migrated incrementally
- **THEN** each step MUST reduce duplication while preserving existing behavior and keeping the eventual single-client model intact
