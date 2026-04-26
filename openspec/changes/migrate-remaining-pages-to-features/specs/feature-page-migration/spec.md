## ADDED Requirements

### Requirement: Frontend route guards shall reject role-mismatched navigation
The frontend router SHALL examine each route's `meta.roles` array and reject navigation by users whose role is not listed.

#### Scenario: Patient navigates to a doctor-only page
- **WHEN** a user whose `user_type` is `patient` tries to navigate to a route with `meta.roles = ['doctor', 'admin']`
- **THEN** the router MUST redirect to `/dashboard` and surface a toast indicating the access is denied

#### Scenario: Role match passes through
- **WHEN** a user whose `user_type` matches one of the listed roles navigates
- **THEN** the navigation MUST resolve normally to the target route

### Requirement: Frontend sidebar shall hide role-gated items the current user cannot reach
The application shell SHALL filter sidebar navigation items so users see only items their role is permitted to navigate to.

#### Scenario: Doctor logs in
- **WHEN** a doctor user signs in
- **THEN** the sidebar MUST hide patient-only items and SHOULD show doctor-and-admin items such as `/timeslots`

#### Scenario: User object not yet restored
- **WHEN** the application shell renders before the auth feature has restored a user from storage
- **THEN** the sidebar MUST default to hiding role-gated items (no flash of items that will disappear)

### Requirement: Business-capability pages shall live under their owning feature directory
The frontend SHALL place every business-capability page under `features/<name>/pages/<Name>Page.vue` rather than under the layer-oriented `views/` folder.

#### Scenario: A new business page is added
- **WHEN** a contributor introduces a new business-capability page
- **THEN** it MUST be placed under `features/<name>/pages/` and the router MUST import it from there
