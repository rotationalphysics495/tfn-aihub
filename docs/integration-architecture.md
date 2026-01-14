# Integration Architecture

## Overview

TFN AI Hub is a multi-part monorepo with three main components that integrate to deliver a manufacturing intelligence platform.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User Browser                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend (web)                        │
│                        http://localhost:3000                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Dashboard  │  │ AI Chat     │  │ Action List │  │ Reports    │ │
│  │  Pages      │  │ Sidebar     │  │ Components  │  │ Views      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
│         │                │                │               │         │
│         └────────────────┴────────────────┴───────────────┘         │
│                                    │                                 │
│                             REST API calls                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (api)                           │
│                      http://localhost:8000                           │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                        API Layer                                 ││
│  │  /api/agent  /api/chat  /api/oee  /api/safety  /api/actions     ││
│  └─────────────────────────────┬───────────────────────────────────┘│
│                                │                                     │
│  ┌─────────────────────────────┴───────────────────────────────────┐│
│  │                     Service Layer                                ││
│  │  ┌───────────────────────────────────────────────────────────┐  ││
│  │  │              AI Agent Framework (LangChain)                │  ││
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │  ││
│  │  │  │ Asset    │  │ OEE      │  │ Safety   │  │ Financial │  │  ││
│  │  │  │ Lookup   │  │ Query    │  │ Events   │  │ Impact    │  │  ││
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │  ││
│  │  │       └─────────────┴─────────────┴──────────────┘        │  ││
│  │  └──────────────────────────────┬────────────────────────────┘  ││
│  │                                 │                                ││
│  │  ┌──────────────────────────────┴───────────────────────────────┐││
│  │  │                  Data Source Layer                           │││
│  │  │   DataSource Protocol → SupabaseDataSource / MSSQLDataSource │││
│  │  └──────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
           │                                              │
           ▼                                              ▼
┌──────────────────────┐                    ┌──────────────────────┐
│   Supabase (Cloud)   │                    │    MSSQL (On-Prem)   │
│   PostgreSQL         │                    │    Source System     │
│                      │                    │                      │
│  • assets            │                    │  • Production data   │
│  • cost_centers      │                    │  • Downtime events   │
│  • daily_summaries   │                    │  • Quality defects   │
│  • safety_events     │                    │  • Machine states    │
│  • citation_logs     │                    │                      │
└──────────────────────┘                    └──────────────────────┘
```

## Integration Points

### 1. Web → API Integration

**Protocol:** REST over HTTP/HTTPS
**Port:** 8000 (development)

| Frontend Action | API Endpoint | Purpose |
|-----------------|--------------|---------|
| AI Chat Message | `POST /api/agent/query` | Send query to AI agent |
| Load OEE Data | `GET /api/oee` | Fetch OEE metrics |
| Load Downtime | `GET /api/v1/downtime` | Fetch downtime analysis |
| Load Actions | `GET /api/actions` | Fetch prioritized actions |
| Load Safety | `GET /api/safety` | Fetch safety events |
| Auth Login | `POST /api/auth/login` | JWT token exchange |

**CORS Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. API → Supabase Integration

**Protocol:** REST API (supabase-py client)
**Authentication:** Service Role Key

**Data Flow:**
```
API Service → supabase-py → Supabase REST API → PostgreSQL
```

**Tables Accessed:**
- `assets` - Asset metadata
- `cost_centers` - Financial data
- `daily_summaries` - Cached OEE data
- `live_snapshots` - Real-time status
- `safety_events` - Safety incidents
- `citation_logs` - AI response citations

### 3. API → MSSQL Integration

**Protocol:** TDS (Tabular Data Stream) via pyodbc
**Connection:** SQLAlchemy ORM with connection pooling

**Data Flow:**
```
API Service → SQLAlchemy → pyodbc → MSSQL Driver → MSSQL Server
```

**Security:**
- Read-only database user
- Connection pooling with health checks
- Credential sanitization in logs

### 4. AI Agent → Tools Integration

**Pattern:** LangChain Tool Registry

```python
# Tool Discovery
registry = get_tool_registry()
tools = registry.get_all_tools()

# Agent Execution
executor = AgentExecutor(agent=agent, tools=tools)
result = await executor.ainvoke({"input": query})
```

**Tool Chain:**
```
User Query → AgentExecutor → Tool Selection → ManufacturingTool._arun()
    → DataSource.query() → Citation Generation → ToolResult
```

## Data Flow Diagrams

### AI Query Flow

```
User                  Frontend              Backend               Database
  │                      │                     │                      │
  │─── Ask Question ────>│                     │                      │
  │                      │─── POST /api/agent/query ──>│             │
  │                      │                     │                      │
  │                      │                     │── Query Supabase ──>│
  │                      │                     │<── Asset Data ──────│
  │                      │                     │                      │
  │                      │                     │── Query MSSQL ─────>│
  │                      │                     │<── Production Data ─│
  │                      │                     │                      │
  │                      │                     │── Run AI Agent ──>  │
  │                      │                     │   (LangChain)        │
  │                      │                     │                      │
  │                      │<── Response + Citations ─│                │
  │<── Render Response ──│                     │                      │
  │                      │                     │                      │
```

### Real-Time Polling Flow

```
Backend Scheduler           Backend                  MSSQL
       │                       │                        │
       │── Trigger Poll ──────>│                        │
       │   (every 60s)         │                        │
       │                       │── Query live data ────>│
       │                       │<── Production status ──│
       │                       │                        │
       │                       │── Update Supabase ────>│ (live_snapshots)
       │                       │                        │
```

## Authentication Flow

```
User        Frontend          Backend         Supabase Auth
 │              │                 │                  │
 │─── Login ───>│                 │                  │
 │              │── Auth Request ────────────────────>│
 │              │<── Session Token ──────────────────│
 │              │                 │                  │
 │              │── API Request + Token ──>│         │
 │              │                 │── Validate ─────>│
 │              │                 │<── User Info ───│
 │              │<── Protected Data ───────│         │
 │              │                 │                  │
```

## Environment Configuration

### Web (.env)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

### API (.env)
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=service_role_key

# MSSQL (Optional)
MSSQL_SERVER=server.database.windows.net
MSSQL_DATABASE=manufacturing
MSSQL_USER=readonly_user
MSSQL_PASSWORD=***

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Memory
MEM0_API_KEY=...
```

## Deployment Architecture

### Development
```
localhost:3000  →  localhost:8000  →  Supabase Cloud
     (web)            (api)              + MSSQL
```

### Production (Planned)
```
Vercel/Netlify  →  Railway/Render  →  Supabase Cloud
    (web)             (api)              + MSSQL VPN
```

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
