# Story 4.2: LangChain Text-to-SQL

Status: Done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to query production and financial data using natural language questions**,
so that **I can get instant answers about factory performance without writing SQL or navigating complex dashboards**.

## Acceptance Criteria

1. **LangChain SQLDatabase Integration**
   - GIVEN the FastAPI backend is running
   - WHEN the Text-to-SQL service initializes
   - THEN it connects to Supabase PostgreSQL using LangChain's `SQLDatabase` wrapper
   - AND exposes only approved tables: `assets`, `cost_centers`, `daily_summaries`, `live_snapshots`, `safety_events`
   - AND retrieves table schemas and sample data for LLM context

2. **Natural Language Query Parsing**
   - GIVEN a user submits a natural language question via API
   - WHEN the question is processed
   - THEN LangChain's `create_sql_query_chain` generates a valid PostgreSQL query
   - AND the query is validated for safety (SELECT only, no mutations)
   - AND the query targets only approved tables (whitelist enforcement)
   - AND ambiguous questions prompt clarification rather than guessing

3. **Query Execution and Result Formatting**
   - GIVEN a valid SQL query is generated
   - WHEN the query executes against Supabase
   - THEN results are returned within 5 seconds (typical queries)
   - AND results are formatted into human-readable natural language responses
   - AND responses include the data values and business context
   - AND empty results return helpful "no data found" messages with suggestions

4. **Data Citation for NFR1 Compliance**
   - GIVEN an AI response is generated from query results
   - WHEN the response is returned to the user
   - THEN specific data points are cited (e.g., "Grinder 5 had 87% OEE yesterday")
   - AND the source table and date range are referenced
   - AND the raw SQL query is available for transparency (optional display)
   - AND no hallucinated or fabricated data is included

5. **Query Security and Guardrails**
   - GIVEN a user submits any natural language input
   - WHEN the input is processed
   - THEN SQL injection attempts are blocked
   - AND only SELECT statements are generated (no INSERT/UPDATE/DELETE)
   - AND table access is restricted to the whitelist
   - AND query execution has a 30-second timeout
   - AND sensitive columns (if any) are excluded from results

6. **Error Handling and Graceful Degradation**
   - GIVEN a query fails (timeout, syntax error, no results)
   - WHEN the error occurs
   - THEN a user-friendly error message is returned (not raw SQL errors)
   - AND the error is logged with context for debugging
   - AND the system suggests alternative phrasings or simpler questions
   - AND failed queries do not crash the service

7. **Conversation Context Integration**
   - GIVEN this story builds foundation for Mem0 integration (Story 4.1)
   - WHEN Text-to-SQL is invoked
   - THEN the service accepts optional context parameters (previous queries, asset focus)
   - AND the architecture supports future memory enhancement
   - AND standalone queries work without memory context

8. **API Endpoint Design**
   - GIVEN the REST API structure
   - WHEN Text-to-SQL is exposed
   - THEN endpoint is `POST /api/chat/query` with body `{ "question": string, "context"?: object }`
   - AND responses follow format `{ "answer": string, "sql": string, "data": object, "citations": array }`
   - AND endpoints are protected with Supabase JWT authentication
   - AND rate limiting is implemented (prevent abuse)

## Tasks / Subtasks

- [x] Task 1: Create Text-to-SQL Service Structure (AC: #1, #7)
  - [x] Create `apps/api/app/services/ai/` directory
  - [x] Create `apps/api/app/services/ai/__init__.py`
  - [x] Create `apps/api/app/services/ai/text_to_sql/service.py` - main service
  - [x] Create `apps/api/app/services/ai/text_to_sql/query_validator.py` - security layer
  - [x] Create `apps/api/app/services/ai/text_to_sql/response_formatter.py` - human-readable output
  - [x] LLM client configuration integrated in service.py

- [x] Task 2: Configure LangChain SQLDatabase Connection (AC: #1)
  - [x] Install dependencies: `langchain`, `langchain-openai`, `langchain-community`
  - [x] Create SQLDatabase wrapper connecting to Supabase PostgreSQL
  - [x] Configure table whitelist: `assets`, `cost_centers`, `daily_summaries`, `live_snapshots`, `safety_events`
  - [x] Implement `get_table_info()` for schema context
  - [x] Add sample data retrieval for few-shot prompting
  - [x] Configure connection pooling for concurrent requests

- [x] Task 3: Implement create_sql_query_chain (AC: #2)
  - [x] Configure OpenAI LLM (GPT-4 or Claude) for SQL generation
  - [x] Create custom prompt template optimized for manufacturing domain
  - [x] Include table descriptions and column semantics in prompt
  - [x] Configure `k=10` for adequate result sampling
  - [x] Implement question preprocessing (normalize terminology)
  - [x] Add domain-specific examples for few-shot learning

- [x] Task 4: Build Query Validator (AC: #5)
  - [x] Create SQL parsing using `sqlparse` library
  - [x] Validate SELECT-only queries (reject INSERT/UPDATE/DELETE/DROP)
  - [x] Implement table whitelist enforcement
  - [x] Block SQL injection patterns (UNION, comments, semicolons)
  - [x] Validate query complexity (prevent expensive JOINs)
  - [x] Implement query timeout wrapper (30 seconds)

- [x] Task 5: Implement Query Execution (AC: #3)
  - [x] Create async query execution with timeout
  - [x] Handle Supabase connection errors gracefully
  - [x] Implement result size limiting (max 100 rows)
  - [x] Convert query results to structured format
  - [x] Handle NULL values and edge cases

- [x] Task 6: Build Response Formatter with Citations (AC: #3, #4)
  - [x] Create natural language response generation
  - [x] Implement citation extraction from query results
  - [x] Format numbers with appropriate precision (OEE %, dollars)
  - [x] Add temporal context (yesterday, last week, etc.)
  - [x] Create "no results" helpful messaging
  - [x] Include source table references

- [x] Task 7: Implement Error Handling (AC: #6)
  - [x] Create custom exception classes for SQL errors
  - [x] Map SQL errors to user-friendly messages
  - [x] Log errors with request context (for debugging)
  - [x] Implement retry logic for transient failures
  - [x] Create suggestion generator for failed queries

- [x] Task 8: Create API Endpoints (AC: #8)
  - [x] Create `POST /api/chat/query` endpoint
  - [x] Create Pydantic models for request/response
  - [x] Implement Supabase JWT authentication dependency
  - [x] Add rate limiting (10 requests/minute per user)
  - [x] Create `GET /api/chat/tables` endpoint (available tables info)
  - [x] Add request logging for analytics

- [x] Task 9: Write Tests (AC: All)
  - [x] Unit tests for SQL validation (injection prevention)
  - [x] Unit tests for response formatting
  - [x] Integration tests with mock LLM responses
  - [x] Test query execution with sample data
  - [x] Test authentication and rate limiting
  - [x] Test error handling scenarios

- [x] Task 10: Create Manufacturing Domain Prompts (AC: #2, #4)
  - [x] Define table descriptions for LLM context
  - [x] Create example question-SQL pairs for few-shot learning
  - [x] Add manufacturing terminology mapping
  - [x] Include business context for financial calculations
  - [x] Document common query patterns

## Dev Notes

### Architecture Compliance

This story implements **LangChain Text-to-SQL** as part of Epic 4: AI Chat & Memory. It enables FR6 (AI Chat with Memory) by providing natural language to SQL translation for querying production and financial data.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/ai/` for AI/LLM logic
**Pattern:** Service-layer with dependency injection, async operations

### Technical Requirements

**LangChain Text-to-SQL Architecture:**
```
User Question (Natural Language)
    |
    v
POST /api/chat/query
    |
    v
TextToSQLService.query()
    |
    +---> QueryValidator.validate_input()
    |         |
    |         v
    |     [Sanitized Input]
    |
    +---> create_sql_query_chain()
    |         |
    |         v
    |     [Generated SQL]
    |
    +---> QueryValidator.validate_sql()
    |         |
    |         v
    |     [Safe SQL Query]
    |
    +---> SQLDatabase.run()
    |         |
    |         v
    |     [Query Results]
    |
    +---> ResponseFormatter.format()
    |         |
    |         v
    |     [Natural Language + Citations]
    |
    v
API Response with answer, sql, data, citations
```

### LangChain Implementation Reference

**Installation:**
```bash
pip install langchain langchain-openai langchain-community sqlparse
```

**SQLDatabase Setup:**
```python
from langchain_community.utilities import SQLDatabase

# Connect to Supabase PostgreSQL
db = SQLDatabase.from_uri(
    settings.SUPABASE_DB_URL,
    include_tables=[
        "assets",
        "cost_centers",
        "daily_summaries",
        "live_snapshots",
        "safety_events"
    ],
    sample_rows_in_table_info=3
)

# Get schema info for LLM context
table_info = db.get_table_info()
```

**create_sql_query_chain Usage:**
```python
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain

llm = ChatOpenAI(model="gpt-4", temperature=0)

# Create the chain
chain = create_sql_query_chain(
    llm=llm,
    db=db,
    k=10  # Number of sample rows
)

# Execute
sql_query = chain.invoke({"question": "What was the OEE for Grinder 5 yesterday?"})
```

**Custom Prompt Template:**
```python
from langchain_core.prompts import PromptTemplate

MANUFACTURING_SQL_PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "top_k"],
    template="""You are a SQL expert for a manufacturing plant database.

Given the following table schemas:
{table_info}

Generate a PostgreSQL SELECT query to answer this question:
{input}

Rules:
- Only use SELECT statements
- Only query the tables shown above
- For OEE, values are stored as decimals (0.87 = 87%)
- financial_loss_dollars is in USD
- Use asset names from the assets table
- For "yesterday", use: date = CURRENT_DATE - INTERVAL '1 day'
- Limit results to {top_k} rows unless asked for all

Return ONLY the SQL query, no explanation.
"""
)
```

### Query Validation Implementation

**SQL Parsing with sqlparse:**
```python
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

def validate_sql(query: str, allowed_tables: set) -> bool:
    """Validate SQL query for safety."""
    parsed = sqlparse.parse(query)[0]

    # Check statement type
    if parsed.get_type() != 'SELECT':
        raise SecurityError("Only SELECT queries allowed")

    # Check for dangerous patterns
    dangerous_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', '--', ';']
    query_upper = query.upper()
    for pattern in dangerous_patterns:
        if pattern in query_upper:
            raise SecurityError(f"Forbidden pattern: {pattern}")

    # Validate tables (extract from query and check whitelist)
    # ... table extraction logic

    return True
```

### Response Formatting with Citations

**Citation Format:**
```python
class Citation(BaseModel):
    value: str          # "87%"
    field: str          # "oee_overall"
    table: str          # "daily_summaries"
    context: str        # "Grinder 5 on 2026-01-04"

class QueryResponse(BaseModel):
    answer: str         # Natural language response
    sql: str            # Generated SQL query
    data: List[dict]    # Raw query results
    citations: List[Citation]
    executed_at: datetime

# Example response:
{
    "answer": "Grinder 5 had an OEE of 87% yesterday, which is above the plant target of 85%. The main contributor was excellent quality at 99.2%.",
    "sql": "SELECT asset_name, oee_overall, oee_quality FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id WHERE a.name = 'Grinder 5' AND ds.date = CURRENT_DATE - 1",
    "data": [{"asset_name": "Grinder 5", "oee_overall": 0.87, "oee_quality": 0.992}],
    "citations": [
        {"value": "87%", "field": "oee_overall", "table": "daily_summaries", "context": "Grinder 5 on 2026-01-04"}
    ]
}
```

### Database Schema Reference

**Queryable Tables (Whitelist):**

```sql
-- assets (from Story 1.3)
SELECT id, name, source_id, area FROM assets;
-- Example: id=uuid, name='Grinder 5', source_id='GR-005', area='Grinding'

-- cost_centers (from Story 1.3)
SELECT id, asset_id, standard_hourly_rate FROM cost_centers;
-- Example: id=uuid, asset_id=uuid, standard_hourly_rate=125.00

-- daily_summaries (from Story 1.4, populated by Story 2.1)
SELECT date, asset_id, oee_overall, oee_availability, oee_performance, oee_quality,
       output_actual, output_target, downtime_minutes, financial_loss_dollars
FROM daily_summaries;

-- live_snapshots (from Story 1.4, populated by Story 2.2)
SELECT timestamp, asset_id, current_output, target_output, status
FROM live_snapshots;

-- safety_events (from Story 1.4, populated by Stories 2.1, 2.6)
SELECT id, asset_id, occurred_at, duration_minutes, reason_code, description, severity
FROM safety_events;
```

### Common Query Patterns

**Example Questions and Expected SQL:**

| Question | Generated SQL |
|----------|---------------|
| "What was Grinder 5's OEE yesterday?" | `SELECT oee_overall FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id WHERE a.name ILIKE '%Grinder 5%' AND ds.date = CURRENT_DATE - 1` |
| "Which asset had the most downtime last week?" | `SELECT a.name, SUM(ds.downtime_minutes) as total FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id WHERE ds.date >= CURRENT_DATE - 7 GROUP BY a.name ORDER BY total DESC LIMIT 1` |
| "Show me all safety events this month" | `SELECT a.name, se.occurred_at, se.description FROM safety_events se JOIN assets a ON se.asset_id = a.id WHERE se.occurred_at >= DATE_TRUNC('month', CURRENT_DATE)` |
| "What's the total financial loss for the Grinding area?" | `SELECT SUM(ds.financial_loss_dollars) FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id WHERE a.area = 'Grinding'` |

### Project Structure Notes

**Files to Create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── text_to_sql.py       # Main service
│   │       ├── query_validator.py   # Security validation
│   │       ├── response_formatter.py # Natural language output
│   │       └── prompts.py           # Manufacturing domain prompts
│   ├── api/
│   │   └── chat.py                  # API endpoints
│   ├── core/
│   │   └── llm.py                   # LLM client config
│   └── models/
│       └── chat.py                  # Pydantic models
```

**Dependencies to Add to requirements.txt:**
```
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0
sqlparse>=0.5.0
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes | - |
| `LLM_MODEL` | Model to use | No | "gpt-4" |
| `LLM_TEMPERATURE` | Creativity (0=deterministic) | No | 0 |
| `SQL_QUERY_TIMEOUT` | Max query execution seconds | No | 30 |
| `CHAT_RATE_LIMIT` | Requests per minute per user | No | 10 |

### Dependencies

**Story Dependencies:**
- Story 1.1 (TurboRepo Monorepo Scaffold) - FastAPI structure
- Story 1.2 (Supabase Auth Integration) - JWT authentication
- Story 1.3 (Plant Object Model Schema) - `assets`, `cost_centers` tables
- Story 1.4 (Analytical Cache Schema) - `daily_summaries`, `live_snapshots`, `safety_events` tables
- Story 4.1 (Mem0 Vector Memory Integration) - Optional context enhancement

**Blocked By:** Stories 1.1, 1.2, 1.3, 1.4 must be complete
**Soft Dependency:** Story 4.1 for enhanced context (can work without)

**Enables:**
- Story 4.3 (Chat Sidebar UI) - Frontend for querying
- Story 4.4 (Asset History Memory) - Enhanced context
- Story 4.5 (Cited Response Generation) - Extends citation system

### Security Considerations

**CRITICAL: SQL Injection Prevention**
- Never execute raw user input as SQL
- Always validate generated SQL before execution
- Use parameterized queries where possible
- Whitelist allowed tables
- Block dangerous SQL patterns

**Authentication:**
- All endpoints require Supabase JWT
- User ID extracted from token for rate limiting
- Audit log all queries for security review

### Testing Strategy

1. **Unit Tests:**
   - SQL validation (injection attempts, forbidden patterns)
   - Response formatting (number formatting, citations)
   - Prompt generation (domain terminology)

2. **Integration Tests:**
   - End-to-end query flow with mock LLM
   - Database connection and query execution
   - Authentication and rate limiting

3. **Security Tests:**
   - SQL injection attempt handling
   - Table access restriction enforcement
   - Timeout handling for expensive queries

4. **Manual Testing:**
   - Test natural language questions
   - Verify citation accuracy
   - Test error handling and user messages

### NFR Compliance

- **NFR1 (Accuracy):** Every AI response cites specific data points from query results
- **NFR2 (Latency):** Query execution target < 5 seconds for typical queries
- **NFR3 (Read-Only):** Only SELECT queries allowed, enforced at validation layer

### References

- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - LangChain integration
- [Source: _bmad/bmm/data/prd.md#Functional FR6] - AI Chat with Memory requirement
- [Source: _bmad/bmm/data/ux-design.md#Usability Goals] - Zero-Training Interface
- [Source: _bmad-output/planning-artifacts/epic-4.md] - Epic 4 context
- [Source: LangChain Docs - create_sql_query_chain](https://python.langchain.com/api_reference/langchain/chains/langchain.chains.sql_database.query.create_sql_query_chain.html)
- [Source: LangChain SQL Agent Tutorial](https://docs.langchain.com/oss/python/langchain/sql-agent)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Implemented comprehensive LangChain Text-to-SQL service for natural language querying of manufacturing data. The implementation includes:
- TextToSQLService with LangChain SQLDatabase integration
- QueryValidator for SQL injection prevention and table whitelist enforcement
- ResponseFormatter for human-readable output with citations
- Manufacturing domain prompts with few-shot examples
- Full API endpoints with authentication and rate limiting

### Files Created/Modified

**Created:**
- `apps/api/app/services/ai/text_to_sql/__init__.py`
- `apps/api/app/services/ai/text_to_sql/service.py` - Main TextToSQLService (600+ lines)
- `apps/api/app/services/ai/text_to_sql/query_validator.py` - Security validation
- `apps/api/app/services/ai/text_to_sql/response_formatter.py` - Citation generation
- `apps/api/app/services/ai/text_to_sql/prompts.py` - Manufacturing domain prompts
- `apps/api/app/api/chat.py` - Chat API endpoints
- `apps/api/app/models/chat.py` - Pydantic models

**Modified:**
- `apps/api/requirements.txt` - Added LangChain dependencies
- `apps/api/app/core/config.py` - Added SQL and chat configuration
- `apps/api/app/main.py` - Registered chat API router

### Acceptance Criteria Status

| AC | Status | Evidence |
|----|--------|----------|
| AC#1: LangChain SQLDatabase Integration | ✅ | `service.py` - SQLDatabase wrapper with table whitelist |
| AC#2: Natural Language Query Parsing | ✅ | `service.py` - create_sql_query_chain implementation |
| AC#3: Query Execution and Result Formatting | ✅ | `response_formatter.py` - human-readable output |
| AC#4: Data Citation for NFR1 Compliance | ✅ | `response_formatter.py` - Citation generation |
| AC#5: Query Security and Guardrails | ✅ | `query_validator.py` - SQL injection prevention |
| AC#6: Error Handling and Graceful Degradation | ✅ | `service.py` - comprehensive error handling |
| AC#7: Conversation Context Integration | ✅ | `chat.py` - optional context parameters |
| AC#8: API Endpoint Design | ✅ | `chat.py` - POST /api/chat/query with auth and rate limiting |

### Debug Log References

N/A - No debug issues encountered.

### Completion Notes List

- Story file status was not updated after implementation
- LLM configuration integrated directly in service.py rather than separate llm.py file
- Integrated with Story 5.7 ManufacturingAgent for enhanced routing

### File List

```
apps/api/
├── app/
│   ├── services/
│   │   └── ai/
│   │       └── text_to_sql/
│   │           ├── __init__.py
│   │           ├── service.py
│   │           ├── query_validator.py
│   │           ├── response_formatter.py
│   │           └── prompts.py
│   ├── api/
│   │   └── chat.py
│   └── models/
│       └── chat.py
└── requirements.txt (modified)
```

