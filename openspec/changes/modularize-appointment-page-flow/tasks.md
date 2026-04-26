# Tasks

## Task 1: Define the appointments feature target shape
- [x] Define the target `features/appointments` structure
- [x] Define which modules are required for the pilot
- [x] Define whether a local store is necessary or optional

## Task 2: Define page-container boundaries
- [x] Define what the appointments route page should continue to own
- [x] Define what must move out of the page into components or composables
- [x] Define what should explicitly not remain in the page container

## Task 3: Define feature API and type boundaries
- [x] Define the responsibilities of `features/appointments/api`
- [x] Define the responsibilities of `features/appointments/types`
- [x] Define how appointments API modules consume the shared HTTP client
- [x] Define which data shapes remain feature-specific

## Task 4: Define composable and component boundaries
- [x] Define which stateful workflows should become composables
- [x] Define which visual sections should become feature components
- [x] Define how dialogs should receive data and callbacks
- [x] Define where slot calculations and attachment-handling logic should live

## Task 5: Define cross-boundary rules for the pilot
- [x] Define how the appointments feature may consume auth context
- [x] Define what belongs in shared versus appointments-local modules
- [x] Define what kinds of direct imports into other feature internals should be avoided

## Task 6: Define migration sequencing
- [x] Define the recommended order of extraction for the pilot
- [x] Define how to preserve behavior during structural migration
- [x] Define what a successful first implementation batch should cover
- [x] Ensure future implementation tasks can reference this pilot design directly
