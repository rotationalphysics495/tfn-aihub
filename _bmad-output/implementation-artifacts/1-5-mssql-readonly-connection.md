# Story 1.5: MSSQL Read-Only Connection

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **backend system**,
I want **a secure read-only connection to the source manufacturing MSSQL database**,
so that **I can safely query production data without risking any data modifications to the legacy system**.

## Acceptance Criteria

1. **Connection Configuration**
   - GIVEN the FastAPI backend is running
   - WHEN I attempt to connect to the MSSQL database
   - THEN the connection uses pyodbc with SQLAlchemy ORM
   - AND the connection is established using environment variables (not hardcoded credentials)

2. **Read-Only Enforcement**
   - GIVEN an active MSSQL connection
   - WHEN any database operation is attempted
   - THEN only SELECT queries are permitted
   - AND any INSERT, UPDATE, DELETE, or DDL operations are blocked at the database user level

3. **Connection Health Check**
   - GIVEN the API is running
   - WHEN the `/health` or `/api/health` endpoint is called
   - THEN it includes MSSQL connection status
   - AND returns appropriate error if connection fails

4. **Environment Variable Configuration**
   - GIVEN the application is deployed
   - WHEN the MSSQL connection is initialized
   - THEN it reads from these environment variables:
     - `MSSQL_SERVER` (hostname/IP)
     - `MSSQL_DATABASE` (database name)
     - `MSSQL_USER` (read-only user)
     - `MSSQL_PASSWORD` (password)
     - `MSSQL_PORT` (optional, default 1433)
     - `MSSQL_DRIVER` (optional, default "ODBC Driver 18 for SQL Server")

5. **Connection Pooling**
   - GIVEN multiple concurrent API requests
   - WHEN database queries are executed
   - THEN connection pooling is properly configured via SQLAlchemy
   - AND connections are reused efficiently

6. **Error Handling**
   - GIVEN a database connection attempt
   - WHEN the connection fails (timeout, auth failure, network issue)
   - THEN meaningful error messages are logged
   - AND the API returns appropriate HTTP error responses (503 Service Unavailable)
   - AND no sensitive credentials are exposed in logs or responses

## Tasks / Subtasks

- [ ] Task 1: Install MSSQL Dependencies (AC: #1, #2)
  - [ ] Add pyodbc to requirements.txt
  - [ ] Add SQLAlchemy to requirements.txt
  - [ ] Document ODBC driver installation for local dev (Linux/macOS/Windows)

- [ ] Task 2: Create Database Configuration Module (AC: #4)
  - [ ] Create `apps/api/app/core/database.py` for MSSQL config
  - [ ] Implement Pydantic settings class for MSSQL env vars
  - [ ] Add connection string builder with proper escaping

- [ ] Task 3: Implement SQLAlchemy Engine with Connection Pool (AC: #1, #5)
  - [ ] Create SQLAlchemy engine with pyodbc dialect
  - [ ] Configure connection pool settings (pool_size, max_overflow, pool_timeout)
  - [ ] Create session factory/dependency for FastAPI

- [ ] Task 4: Implement Health Check Endpoint (AC: #3)
  - [ ] Add MSSQL connectivity check to existing health endpoint
  - [ ] Return structured health response with database status
  - [ ] Handle connection timeout gracefully

- [ ] Task 5: Implement Error Handling and Logging (AC: #6)
  - [ ] Create custom exceptions for database errors
  - [ ] Implement connection retry logic with backoff
  - [ ] Configure structured logging (no credentials in logs)

- [ ] Task 6: Add Environment Configuration (AC: #4)
  - [ ] Update `.env.example` with MSSQL variables
  - [ ] Document Railway Secrets configuration
  - [ ] Add validation for required environment variables

- [ ] Task 7: Write Tests (AC: All)
  - [ ] Unit tests for configuration parsing
  - [ ] Integration test for connection (mock or test DB)
  - [ ] Test error handling scenarios

## Dev Notes

### Architecture Compliance

This story aligns with the Fullstack Architecture document:

- **Location:** `apps/api/` (Python FastAPI Backend)
- **Module:** `app/core/` for configuration and security-related code
- **Pattern:** Dependency injection via FastAPI for database sessions

### Technical Requirements

**Database Driver Stack:**
```
Python -> SQLAlchemy -> pyodbc -> ODBC Driver 18 -> MSSQL Server
```

**Connection String Format:**
```python
mssql+pyodbc://{user}:{password}@{server}:{port}/{database}?driver={driver}
```

**Required SQLAlchemy Configuration:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    connection_string,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,  # Verify connections before use
    echo=False  # Set True for SQL logging in dev
)
```

### Security Requirements (NFR3)

**CRITICAL:** The MSSQL user MUST be configured with read-only permissions at the database level:

```sql
-- Example SQL Server permission setup (for DBA reference)
CREATE LOGIN RO_User WITH PASSWORD = '...';
CREATE USER RO_User FOR LOGIN RO_User;
GRANT SELECT ON SCHEMA::dbo TO RO_User;
DENY INSERT, UPDATE, DELETE ON SCHEMA::dbo TO RO_User;
```

The application code should NOT attempt to enforce read-only at the application layer alone - database-level enforcement is required.

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MSSQL_SERVER` | Database server hostname or IP | Yes | - |
| `MSSQL_DATABASE` | Target database name | Yes | - |
| `MSSQL_USER` | Read-only database user | Yes | - |
| `MSSQL_PASSWORD` | Database user password | Yes | - |
| `MSSQL_PORT` | Database port | No | 1433 |
| `MSSQL_DRIVER` | ODBC driver name | No | "ODBC Driver 18 for SQL Server" |

### Project Structure Notes

Files to create/modify:
```
apps/api/
├── app/
│   ├── core/
│   │   ├── config.py        # Add MSSQL settings to existing config
│   │   └── database.py      # NEW: MSSQL connection module
│   ├── api/
│   │   └── health.py        # Add/update health check endpoint
│   └── main.py              # Import database module
├── requirements.txt         # Add pyodbc, SQLAlchemy
└── .env.example             # Add MSSQL env vars
```

### ODBC Driver Installation

**macOS (Homebrew):**
```bash
brew tap microsoft/mssql-release https://github.com/microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

**Ubuntu/Debian:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**Docker (for Railway deployment):**
```dockerfile
# Add to Dockerfile
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
```

### Dependencies

**Story Dependencies:**
- Story 1.1 (TurboRepo Monorepo Scaffold) - Must be complete for `apps/api/` structure
- Supabase Auth is NOT required for this story (Story 1.2)

**Blocked By:** Story 1.1 must provide the basic FastAPI project structure

**Enables:**
- Story 1.3 (Plant Object Model Schema) - Will use this connection for data migration
- Epic 2 (Data Pipelines) - All data ingestion depends on this connection

### Testing Strategy

1. **Unit Tests:**
   - Test configuration parsing with various env var combinations
   - Test connection string building with special characters in password
   - Test error handling for missing required vars

2. **Integration Tests:**
   - Use a mock MSSQL or Docker container for CI
   - Test actual connection establishment
   - Test connection pool behavior under load

3. **Manual Testing:**
   - Verify connection to actual dev MSSQL server
   - Confirm read-only by attempting INSERT (should fail)
   - Test health endpoint reports correct status

### References

- [Source: _bmad/bmm/data/architecture.md#3. Tech Stack] - pyodbc/SQLAlchemy specified
- [Source: _bmad/bmm/data/architecture.md#8. Security & Constraints] - RO_User requirement
- [Source: _bmad/bmm/data/prd.md#Non-Functional] - NFR3 Read-Only requirement
- [Source: _bmad-output/planning-artifacts/epic-1.md#Story 1.5] - Story definition

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
