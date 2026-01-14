# Data Models

## Overview

TFN AI Hub uses a dual-database architecture:
1. **Supabase (PostgreSQL)** - Application database with Plant Object Model
2. **MSSQL** - Read-only source system for manufacturing data

## Supabase Schema (Plant Object Model)

### Core Tables

#### `assets`
Physical equipment/machines in the manufacturing plant.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `name` | VARCHAR(255) | Human-readable asset name (e.g., "Grinder 5") |
| `source_id` | VARCHAR(255) | Maps to MSSQL locationName for data sync |
| `area` | VARCHAR(100) | Plant area (e.g., "Grinding") |
| `created_at` | TIMESTAMPTZ | Auto-generated timestamp |
| `updated_at` | TIMESTAMPTZ | Auto-updated on changes |

**Indexes:** `idx_assets_source_id`

#### `cost_centers`
Financial cost center information linked to assets.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` (CASCADE DELETE) |
| `standard_hourly_rate` | DECIMAL(10,2) | Cost per hour for financial calculations |
| `created_at` | TIMESTAMPTZ | Auto-generated |
| `updated_at` | TIMESTAMPTZ | Auto-updated |

**Indexes:** `idx_cost_centers_asset_id`

#### `shift_targets`
Production targets per shift for each asset.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` |
| `shift` | VARCHAR(50) | Shift identifier |
| `target_units` | INTEGER | Target production units |
| `created_at` | TIMESTAMPTZ | Auto-generated |
| `updated_at` | TIMESTAMPTZ | Auto-updated |

### Analytical Cache Tables

#### `daily_summaries`
Cached daily performance summaries.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` |
| `date` | DATE | Summary date |
| `oee` | DECIMAL(5,2) | Overall Equipment Effectiveness |
| `availability` | DECIMAL(5,2) | Availability component |
| `performance` | DECIMAL(5,2) | Performance component |
| `quality` | DECIMAL(5,2) | Quality component |
| `downtime_minutes` | INTEGER | Total downtime |
| `units_produced` | INTEGER | Production count |
| `created_at` | TIMESTAMPTZ | Cache timestamp |

#### `live_snapshots`
Real-time production snapshots.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` |
| `snapshot_time` | TIMESTAMPTZ | Snapshot timestamp |
| `status` | VARCHAR(50) | Current asset status |
| `current_rate` | DECIMAL(10,2) | Current production rate |
| `shift_target` | INTEGER | Shift target |
| `shift_actual` | INTEGER | Actual production |

### Safety & Alert Tables

#### `safety_events`
Safety incident records.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` (nullable) |
| `area` | VARCHAR(100) | Plant area |
| `severity` | VARCHAR(20) | critical, high, medium, low |
| `status` | VARCHAR(20) | open, investigating, resolved |
| `description` | TEXT | Incident description |
| `occurred_at` | TIMESTAMPTZ | When incident occurred |
| `resolved_at` | TIMESTAMPTZ | When resolved (nullable) |
| `created_at` | TIMESTAMPTZ | Record creation |

#### `alerts`
System alerts and warnings.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` (nullable) |
| `type` | VARCHAR(50) | Alert type |
| `severity` | VARCHAR(20) | Severity level |
| `message` | TEXT | Alert message |
| `acknowledged` | BOOLEAN | Whether acknowledged |
| `created_at` | TIMESTAMPTZ | Alert creation |

### Asset History Tables

#### `asset_history`
Historical asset performance records.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `asset_id` | UUID | FK to `assets.id` |
| `metric_type` | VARCHAR(50) | Type of metric |
| `value` | DECIMAL(15,4) | Metric value |
| `recorded_at` | TIMESTAMPTZ | When recorded |
| `metadata` | JSONB | Additional context |

### Citation & Memory Tables

#### `citation_logs`
Audit trail for AI response citations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `conversation_id` | UUID | Conversation identifier |
| `source` | VARCHAR(100) | Data source name |
| `query` | TEXT | Query that retrieved data |
| `table_name` | VARCHAR(100) | Database table |
| `record_id` | VARCHAR(255) | Specific record |
| `asset_id` | UUID | Related asset |
| `confidence` | DECIMAL(3,2) | Confidence score |
| `created_at` | TIMESTAMPTZ | Citation creation |

## Entity Relationships

```
┌─────────────┐       ┌──────────────────┐
│   assets    │───────│   cost_centers   │
│             │   1:1 │                  │
└──────┬──────┘       └──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│  shift_targets   │
└──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│ daily_summaries  │
└──────────────────┘

┌─────────────┐       ┌──────────────────┐
│   assets    │───────│  safety_events   │
│             │   1:N │                  │
└─────────────┘       └──────────────────┘

┌─────────────┐       ┌──────────────────┐
│   assets    │───────│  asset_history   │
│             │   1:N │                  │
└─────────────┘       └──────────────────┘
```

## MSSQL Source Tables

The API connects to the source MSSQL database (read-only) for:
- Real-time production data
- Downtime events with reasons
- Quality defect records
- Machine state changes

**Note:** MSSQL connection is optional and gracefully degraded if not configured.

## Pydantic Models (API)

### Agent Models (`app/models/agent.py`)

```python
class ToolResult(BaseModel):
    data: Any
    citations: List[Citation]
    metadata: Dict[str, Any]
    cached_at: Optional[datetime]
    success: bool
    error_message: Optional[str]

class Citation(BaseModel):
    source: str
    query: str
    timestamp: datetime
    table: Optional[str]
    record_id: Optional[str]
    asset_id: Optional[str]
    confidence: float
```

### Safety Models (`app/models/safety.py`)

```python
class SafetyEvent(BaseModel):
    id: UUID
    asset_id: Optional[UUID]
    area: str
    severity: Literal["critical", "high", "medium", "low"]
    status: Literal["open", "investigating", "resolved"]
    description: str
    occurred_at: datetime
```

### Chat Models (`app/models/chat.py`)

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: Optional[List[Citation]]
    follow_up_questions: Optional[List[str]]
```

## Migrations

Migrations are located in `supabase/migrations/`:

| Migration | Description |
|-----------|-------------|
| `20260106000000_plant_object_model.sql` | Core assets, cost_centers, shift_targets |
| `20260106000001_analytical_cache.sql` | Daily summaries, live snapshots |
| `20260106000002_safety_alert_enhancements.sql` | Safety events, alerts |
| `20260106000003_asset_history.sql` | Asset history tracking |
| `20260107000001_citation_logs.sql` | Citation audit trail |

## Row Level Security (RLS)

All Supabase tables have RLS enabled with policies for:
- Authenticated user access
- Service role bypass for API operations

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
