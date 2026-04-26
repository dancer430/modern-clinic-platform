## ADDED Requirements

### Requirement: The appointments route page shall become a thin feature container
The appointments route page SHALL act as a composition entry point for the appointments feature and MUST NOT remain the default location for all appointment workflow logic.

#### Scenario: Appointments page composes feature modules
- **WHEN** the appointments route screen is structured under the feature boundary model
- **THEN** it MUST primarily coordinate sections, dialogs, and route-specific orchestration instead of directly owning all calculations and workflow state

#### Scenario: New appointment workflow logic is added
- **WHEN** new stateful appointment workflow logic is introduced
- **THEN** it MUST default to feature-local modules instead of being appended directly to the page container

### Requirement: Appointment business logic shall be split into feature-local modules
The appointments feature SHALL separate page rendering, workflow state, API access, and feature-specific types into explicit feature-local modules.

#### Scenario: Appointment endpoints are used
- **WHEN** the appointments flow performs list queries or appointment mutations
- **THEN** those business endpoints MUST be defined in `features/appointments/api` and consume shared transport infrastructure rather than raw page-local client calls

#### Scenario: Appointment types are reused within the feature
- **WHEN** appointment item shapes, attachment payloads, or slot option structures are needed across the appointments feature
- **THEN** they MUST be defined in feature-local types rather than duplicated inside the page component

### Requirement: Appointment workflows shall be modeled as feature-local behavior
The appointments feature SHALL model create, confirm, complete, cancel, upload, and slot-derivation behavior as feature-local workflow modules rather than leaving them embedded inside a single page file.

#### Scenario: Dialog workflow is extracted
- **WHEN** confirm, complete, or cancel behavior is split from the page
- **THEN** the extracted module MUST own the corresponding workflow state and validation behavior needed by that dialog flow

#### Scenario: Slot availability behavior is reused within appointments
- **WHEN** slot option calculations or attachment preparation logic is needed by multiple page sections or dialogs
- **THEN** the behavior MUST live in feature-local composables or equivalent workflow modules rather than inline page logic

### Requirement: The appointments pilot shall preserve behavior during structural migration
The appointments pilot MUST be implementable incrementally and SHALL preserve current runtime behavior while ownership and placement are being changed.

#### Scenario: First migration batch is executed
- **WHEN** the first appointments implementation batch is chosen
- **THEN** it MUST be scoped so that behavior stays stable while only a limited set of feature boundaries is introduced

#### Scenario: Pilot proves too disruptive
- **WHEN** a full appointments split is found to be too disruptive for one batch
- **THEN** the migration MAY fall back to extracting API, types, and the heaviest workflows first while keeping the feature ownership model intact
