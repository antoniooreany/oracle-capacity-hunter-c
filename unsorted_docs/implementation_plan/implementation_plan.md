# Implementation Plan - Full-Application Integration Testing

This plan outlines the implementation of a dedicated integration test suite for the SQEVAL platform, verifying that the entire multi-container environment builds and runs successfully via Docker Compose.

## User Review Required

> [!IMPORTANT]
> - A local Docker daemon must be running to execute this integration test.
> - The integration test is strictly isolated and does not contain or duplicate any of the AI-worker development code, ensuring a clear PR focus.

## Proposed Changes

We will introduce a clean integration testing script and wire it to the project's build commands.

---

### [Component: Configuration & Makefiles]

#### [MODIFY] [Makefile](file:///C:/Users/anton/Projects/sqeval-test-2/Makefile)
- Registered the `.PHONY` target `test-integration`.
- Added the `test-integration` recipe to run the python integration script.

---

### [Component: Testing & Scripts]

#### [NEW] [test_integration.py](file:///C:/Users/anton/Projects/sqeval-test-2/scripts/test_integration.py)
- Created a standalone Python script to validate the complete platform end-to-end:
  1. Executes `docker compose down -v` to ensure clean environment states.
  2. Executes `docker compose up --build -d` to build and launch all containers.
  3. Polls the API's `/health` endpoint until a 200 OK state is detected.
  4. Resolves and lists container states, verifying all 11 core application containers are running successfully.
  5. Performs an integration task creation POST request to `/api/v1/analyses`, verifying the database and message broker loop.
  6. Tears down the Docker stack via `docker compose down -v`.

---

## Verification Plan

### Automated Tests
- Run the new integration test via Makefile:
  ```bash
  make test-integration
  ```
