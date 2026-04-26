## ADDED Requirements

### Requirement: Frontend code shall follow a hybrid boundary model
The frontend SHALL organize code around a hybrid structure consisting of `app/`, `shared/`, and `features/`, with each layer having distinct ownership responsibilities.

#### Scenario: New frontend capability is added
- **WHEN** a contributor introduces a new business-facing frontend capability
- **THEN** the capability MUST be modeled under `features/` rather than as a new top-level technical-type folder

#### Scenario: Application-wide composition logic is added
- **WHEN** code is responsible for router registration, app shell composition, or cross-feature orchestration
- **THEN** it MUST belong to `app/`

### Requirement: Route pages shall belong to their owning feature
The frontend SHALL keep route registration in the app layer while colocating page-level route components with the business feature that owns them.

#### Scenario: Router registers a business screen
- **WHEN** `app/router` registers a route for a business capability
- **THEN** the referenced page component MUST come from that feature's `pages/` area

#### Scenario: Feature screen is reorganized
- **WHEN** page-specific dialogs, rendering sections, or page-local workflows are split out from a route screen
- **THEN** they MUST remain within the owning feature boundary rather than moving back to generic global folders by default

### Requirement: Feature state and feature APIs shall default to feature ownership
The frontend SHALL default Pinia stores, feature-specific API modules, and feature-specific types to the owning feature unless they are clearly application-wide or cross-feature foundational.

#### Scenario: New state is introduced for one business capability
- **WHEN** state is needed only for a single capability such as appointments, auth, patients, or doctors
- **THEN** that state MUST default to the owning feature instead of a global shared store area

#### Scenario: Shared transport infrastructure is needed
- **WHEN** HTTP client wiring, interceptor setup, or common request configuration is required
- **THEN** that transport infrastructure MUST live in `shared/api` while business endpoint definitions remain feature-scoped

### Requirement: Cross-feature dependencies shall use public interfaces only
The frontend SHALL allow cross-feature dependency only through explicit public interfaces and MUST NOT allow features to reach into another feature's internal implementation files by default.

#### Scenario: One feature consumes another feature's capability
- **WHEN** a feature needs auth context or another feature-owned capability
- **THEN** it MUST consume the other feature through the exposed public surface rather than private internals

#### Scenario: Direct import targets feature internals
- **WHEN** a change introduces a direct import into another feature's private store, helper, or component implementation
- **THEN** that import MUST be treated as a boundary violation unless explicitly promoted to the public surface
