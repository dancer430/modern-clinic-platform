## ADDED Requirements

### Requirement: Production startup shall fail loudly when required env vars are missing
The backend SHALL refuse to start in production (`ENV=production`) when any of the variables `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` is unset, and SHALL refuse to start when `DJANGO_SECRET_KEY` equals the development default value.

#### Scenario: Production startup with missing POSTGRES_PASSWORD
- **WHEN** the backend starts with `ENV=production` and no `POSTGRES_PASSWORD` set
- **THEN** Django SHALL raise `ImproperlyConfigured` listing `POSTGRES_PASSWORD` (along with any other missing required variables) and process startup MUST fail

#### Scenario: Production startup with the dev-default secret key
- **WHEN** the backend starts with `ENV=production` and `DJANGO_SECRET_KEY` equal to `dev-insecure-key-change-in-production`
- **THEN** startup MUST fail with `ImproperlyConfigured`

### Requirement: Logging shall use a structured format in production
The backend SHALL emit logs to stdout using a JSON formatter when `ENV=production` and a human-readable console formatter otherwise.

#### Scenario: A request error is logged in production
- **WHEN** the backend logs at WARNING or higher in production
- **THEN** the emitted record MUST be parseable as JSON and MUST contain at least the keys `ts`, `level`, `logger`, `msg`

### Requirement: An env-presence check command shall be available
The backend SHALL expose a `python manage.py check_env` management command that prints presence/absence of every required production variable and exits with a non-zero status if any are missing.

#### Scenario: All required vars are set
- **WHEN** an operator runs `manage.py check_env` with all required production variables set
- **THEN** the command MUST exit 0 and MUST print one line per checked variable

#### Scenario: A required var is missing
- **WHEN** an operator runs `manage.py check_env` with `POSTGRES_PASSWORD` unset
- **THEN** the command MUST exit non-zero and MUST list `POSTGRES_PASSWORD` as missing
