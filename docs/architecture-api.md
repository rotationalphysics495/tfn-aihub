# Architecture - API (Python FastAPI Backend)

## Overview

The API backend is a Python FastAPI application serving as the intelligence layer of the Manufacturing Performance Assistant. It provides REST APIs for plant data, AI-powered chat, and a suite of 12+ specialized manufacturing tools.

## Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Framework** | FastAPI 0.109+ | Async API framework with OpenAPI docs |
| **Language** | Python 3.11+ | Primary backend language |
| **AI/LLM** | LangChain 0.1+ | Agent orchestration framework |
| **LLM Providers** | OpenAI, Anthropic | Language model providers |
| **Memory** | Mem0 0.1+ | Vector memory for conversation history |
| **Database** | SQLAlchemy 2.0+ | ORM for MSSQL source system |
| **Supabase** | supabase-py 2.0+ | PostgreSQL client |
| **Caching** | cachetools 5.3+ | In-memory TTL caching |

## Directory Structure

```
apps/api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                  # Route handlers (18 routers)
│   │   ├── health.py         # Health check endpoints
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── assets.py         # Asset management
│   │   ├── oee.py            # OEE calculations
│   │   ├── downtime.py       # Downtime analysis
│   │   ├── production.py     # Production status
│   │   ├── safety.py         # Safety events
│   │   ├── financial.py      # Financial impact
│   │   ├── actions.py        # Action engine
│   │   ├── chat.py           # AI chat interface
│   │   ├── agent.py          # LangChain agent API
│   │   ├── memory.py         # Mem0 memory API
│   │   ├── citations.py      # Citation management
│   │   ├── cache.py          # Cache management
│   │   └── ...
│   ├── core/                 # Core infrastructure
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── database.py       # MSSQL connection manager
│   │   └── security.py       # JWT authentication
│   ├── models/               # Pydantic data models
│   │   ├── agent.py          # Agent request/response models
│   │   ├── asset_history.py  # Asset history models
│   │   ├── citation.py       # Citation models
│   │   ├── chat.py           # Chat message models
│   │   ├── safety.py         # Safety event models
│   │   └── ...
│   ├── schemas/              # API schemas
│   │   ├── financial.py      # Financial schemas
│   │   ├── action.py         # Action schemas
│   │   └── summary.py        # Summary schemas
│   └── services/             # Business logic
│       ├── agent/            # AI Agent Framework (Story 5.1+)
│       │   ├── base.py       # ManufacturingTool base class
│       │   ├── registry.py   # ToolRegistry for auto-discovery
│       │   ├── executor.py   # AgentExecutor wrapper
│       │   ├── cache.py      # TTL-based tool caching
│       │   ├── data_source/  # Data access abstraction
│       │   └── tools/        # 12+ Manufacturing tools
│       ├── memory/           # Mem0 integration
│       ├── pipelines/        # Data pipelines
│       └── ...               # Other services
├── tests/                    # Pytest test suite
├── migrations/               # Database migrations
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
└── pytest.ini               # Pytest configuration
```

## Core Architecture Components

### 1. ManufacturingTool Base Class

All AI agent tools inherit from `ManufacturingTool` (Story 5.1):

```python
class ManufacturingTool(BaseTool):
    name: str
    description: str
    args_schema: Type[BaseModel]
    citations_required: bool = True

    async def _arun(self, **kwargs) -> ToolResult:
        # Tool implementation
        pass
```

**Key Features:**
- Structured `ToolResult` responses with data + citations
- Citation support for NFR1 compliance (data source tracking)
- Async execution pattern for FastAPI compatibility
- Helper methods: `_create_citation()`, `_create_error_result()`, `_create_success_result()`

### 2. Tool Registry

Automatic tool discovery and registration (Story 5.1):

```python
from app.services.agent.registry import get_tool_registry

registry = get_tool_registry()
tools = registry.get_all_tools()  # Returns list of instantiated tools
```

### 3. Agent Executor

LangChain AgentExecutor wrapper with:
- Tool orchestration
- Response formatting with citations
- Error handling and recovery

### 4. Manufacturing Tools (12+)

| Tool | Description | Story |
|------|-------------|-------|
| `asset_lookup` | Query asset by name, get status and performance | 5.3 |
| `oee_query` | OEE for asset/area/plant with breakdown | 5.4 |
| `downtime_analysis` | Downtime reasons and Pareto analysis | 5.5 |
| `production_status` | Real-time production across assets | 5.6 |
| `safety_events` | Safety incidents with severity | 6.1 |
| `financial_impact` | Cost of downtime and waste | 6.2 |
| `cost_of_loss` | Ranked losses by financial impact | 6.3 |
| `trend_analysis` | Performance trends over time | 6.4 |
| `memory_recall` | Past conversations about assets | 7.1 |
| `comparative_analysis` | Compare 2+ assets side-by-side | 7.2 |
| `action_list` | Prioritized daily actions | 7.3 |
| `alert_check` | Active alerts and warnings | 7.4 |
| `recommendation_engine` | Improvement suggestions | 7.5 |

### 5. Data Access Layer

**DataSource Protocol** (Story 5.2) abstracts data access:

```python
class DataSource(Protocol):
    async def get_asset_by_name(self, name: str) -> Optional[Asset]: ...
    async def get_oee_data(self, asset_id: str, date_range: DateRange) -> OEEData: ...
```

**Implementations:**
- `SupabaseDataSource` - Supabase PostgreSQL
- `MSSQLDataSource` - Read-only MSSQL source system
- `CompositeDataSource` - Combines multiple sources

### 6. Caching Strategy

TTL-based caching tiers (Story 5.8):

| Tier | TTL | Use Case |
|------|-----|----------|
| **Live** | 60s | Real-time data (production status) |
| **Daily** | 15min | Aggregated metrics (OEE) |
| **Static** | 1hr | Reference data (asset metadata) |

## API Endpoints

### Core Routes

| Prefix | Router | Description |
|--------|--------|-------------|
| `/` | root | API welcome message |
| `/health` | health | Health check |
| `/docs` | OpenAPI | Swagger UI |

### Domain Routes

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/assets` | assets | Asset management |
| `/api/oee` | oee | OEE calculations |
| `/api/v1/downtime` | downtime | Downtime analysis |
| `/api/production` | production | Production status |
| `/api/safety` | safety | Safety events |
| `/api/financial` | financial | Financial impact |
| `/api/actions` | actions | Action engine |
| `/api/v1/actions` | actions | Versioned actions API |

### AI Routes

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/chat` | chat | Text-to-SQL chat |
| `/api/agent` | agent | LangChain agent queries |
| `/api/memory` | memory | Mem0 vector memory |
| `/api/citations` | citations | Citation management |
| `/api/cache` | cache | Cache management |

### Infrastructure Routes

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/auth` | auth | Authentication |
| `/api/pipelines` | pipelines | Data pipelines |
| `/api/live-pulse` | live_pulse | Real-time polling |
| `/api/summaries` | summaries | Report summaries |

## Database Connections

### MSSQL (Source System)
- Read-only connection to manufacturing MSSQL database
- SQLAlchemy ORM with pyodbc driver
- Connection pooling with health checks
- Used for: production data, downtime events, safety incidents

### Supabase (Application Database)
- PostgreSQL via Supabase client
- Used for: assets, cost_centers, shift_targets, analytical cache
- Row Level Security (RLS) enabled

## Application Lifecycle

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_database()  # MSSQL connection
    scheduler = get_scheduler()
    await scheduler.start()  # Live Pulse polling

    yield

    # Shutdown
    await scheduler.shutdown(wait=True)
    shutdown_database()
```

## Security

- **CORS**: Configured for `http://localhost:3000` (Next.js dev)
- **Authentication**: JWT tokens via `/api/auth`
- **Database**: Read-only MSSQL user permissions
- **Error Handling**: Sanitized error messages (no credential exposure)

## Testing

```bash
cd apps/api
pytest                    # Run all tests
pytest tests/services/    # Run service tests
pytest --cov=app          # Coverage report
```

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
