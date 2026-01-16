# PRD: Technical Architecture

**Parent Document:** [prd.md](../prd.md)

---

## Architecture Overview

```
User Message
    │
    ▼
┌─────────────────────────────────────────────┐
│           Manufacturing Agent                │
│     (LangChain AgentExecutor + GPT-4)       │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         Tool Selection              │    │
│  │  (Based on intent classification)   │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
    │
    ▼ selects tool(s)
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Asset   │ OEE     │ Safety  │ Memory  │ Action  │
│ Lookup  │ Query   │ Events  │ Recall  │ List    │
│  ...    │  ...    │  ...    │  ...    │  ...    │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │         │
     ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────┐
│           Data Access Layer                      │
│  ┌──────────────┐    ┌──────────────┐           │
│  │   Supabase   │    │    MSSQL     │           │
│  │   Adapter    │    │   Adapter    │           │
│  │   (Active)   │    │   (Future)   │           │
│  └──────────────┘    └──────────────┘           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│         Citation & Grounding Layer              │
│   (Validates claims, attaches source refs)      │
└─────────────────────────────────────────────────┘
    │
    ▼
Response with Citations
```

---

## Data Access Abstraction

Tools SHALL NOT query databases directly. Instead, they use a data access abstraction layer:

```python
class DataSource(Protocol):
    async def get_asset(self, asset_id: str) -> Asset | None
    async def get_oee(self, asset_id: str, start: datetime, end: datetime) -> OEEMetrics
    async def get_downtime(self, asset_id: str, start: datetime, end: datetime) -> list[DowntimeEvent]

class SupabaseDataSource(DataSource):
    # Current implementation - queries Supabase tables

class MSSQLDataSource(DataSource):
    # Future implementation - queries source MSSQL (read-only)

class CompositeDataSource(DataSource):
    # Routes queries to appropriate source based on data type/freshness
```

---

## Tool Registration Pattern

Tools are self-describing for automatic registration:

```python
class ManufacturingTool(BaseTool):
    name: str
    description: str  # Used by agent for tool selection
    args_schema: Type[BaseModel]  # Pydantic model for input validation
    citations_required: bool = True

    async def _arun(self, **kwargs) -> ToolResult:
        # Returns structured data + citations
        pass
```

---

## Supabase Tables Used

| Tool | Primary Tables | Join Tables |
|------|---------------|-------------|
| Asset Lookup | `assets`, `live_snapshots` | `cost_centers`, `daily_summaries` |
| OEE Query | `daily_summaries` | `assets`, `shift_targets` |
| Downtime Analysis | `daily_summaries` | `assets` |
| Production Status | `live_snapshots` | `assets`, `shift_targets` |
| Safety Events | `safety_events` | `assets` |
| Financial Impact | `daily_summaries` | `cost_centers` |
| Trend Analysis | `daily_summaries` | `assets` |
| Memory Recall | `memories` | - |
| Action List | (Action Engine output) | Multiple |

---

## Infrastructure Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+ with App Router |
| Backend | Python (FastAPI) |
| App Database | Supabase (PostgreSQL) |
| Source Database | MSSQL (read-only connection) |
| AI/Memory | LangChain + Mem0 |
| Voice | ElevenLabs (TTS + STT) |
| Deployment | Dockerized containers on Railway |

---

## Voice Integration Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│  ┌───────────────┐    ┌───────────────┐         │
│  │ Push-to-Talk  │    │   Audio       │         │
│  │   Button      │    │   Player      │         │
│  └───────┬───────┘    └───────▲───────┘         │
│          │                    │                  │
│          ▼                    │                  │
│  ┌───────────────┐    ┌───────────────┐         │
│  │   Record      │    │   Play TTS    │         │
│  │   Audio       │    │   Response    │         │
│  └───────┬───────┘    └───────▲───────┘         │
└──────────┼────────────────────┼─────────────────┘
           │                    │
           ▼                    │
┌─────────────────────────────────────────────────┐
│                   Backend                        │
│  ┌───────────────┐    ┌───────────────┐         │
│  │  ElevenLabs   │    │  ElevenLabs   │         │
│  │     STT       │    │     TTS       │         │
│  └───────┬───────┘    └───────▲───────┘         │
│          │                    │                  │
│          ▼                    │                  │
│  ┌───────────────────────────────────────┐      │
│  │         Manufacturing Agent            │      │
│  │   (Process query, generate response)   │      │
│  └───────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

---

## Offline Caching Strategy

For shift handoff records on tablets:

1. **Service Worker** - Intercepts fetch requests for handoff data
2. **IndexedDB** - Stores handoff records locally (last 24-48 hours)
3. **Sync Queue** - Queues acknowledgments for upload when online
4. **Background Sync** - Automatically syncs when connectivity restored

```
┌─────────────────────────────────────────────────┐
│                   Tablet                         │
│  ┌───────────────┐    ┌───────────────┐         │
│  │   Handoff     │◄───│   IndexedDB   │         │
│  │   Review UI   │    │   (Cache)     │         │
│  └───────┬───────┘    └───────▲───────┘         │
│          │                    │                  │
│          ▼                    │                  │
│  ┌───────────────┐    ┌───────────────┐         │
│  │  Acknowledge  │───►│  Sync Queue   │         │
│  └───────────────┘    └───────┬───────┘         │
└───────────────────────────────┼─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Background Sync     │
                    │   (When Online)       │
                    └───────────────────────┘
```
