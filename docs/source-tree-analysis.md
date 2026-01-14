# Source Tree Analysis

## Repository Structure

```
tfn-aihub/                           # Turborepo monorepo root
├── apps/                            # Application packages
│   ├── web/                         # Next.js 14 Frontend (Part: web)
│   │   ├── src/
│   │   │   ├── app/                 # App Router pages
│   │   │   │   ├── layout.tsx       # Root layout with ThemeProvider + ChatSidebar
│   │   │   │   ├── page.tsx         # Landing page
│   │   │   │   ├── globals.css      # Global styles
│   │   │   │   ├── (auth)/          # Auth route group
│   │   │   │   │   └── login/       # Login page
│   │   │   │   ├── auth/
│   │   │   │   │   └── callback/    # OAuth callback handler
│   │   │   │   ├── dashboard/       # Main dashboard area
│   │   │   │   │   ├── page.tsx     # Dashboard home
│   │   │   │   │   └── production/  # Production views
│   │   │   │   │       ├── oee/     # OEE dashboard
│   │   │   │   │       ├── downtime/# Downtime analysis
│   │   │   │   │       └── throughput/ # Throughput view
│   │   │   │   ├── morning-report/  # Daily report page
│   │   │   │   └── api/
│   │   │   │       └── health/      # Health check API route
│   │   │   ├── components/          # React components
│   │   │   │   ├── ui/              # Base UI (Shadcn/UI primitives)
│   │   │   │   ├── chat/            # AI Chat sidebar components
│   │   │   │   ├── action-engine/   # Action recommendation UI
│   │   │   │   ├── action-list/     # Daily action list
│   │   │   │   ├── dashboard/       # Dashboard-specific
│   │   │   │   ├── oee/             # OEE visualization
│   │   │   │   ├── downtime/        # Downtime charts
│   │   │   │   ├── production/      # Production status
│   │   │   │   ├── safety/          # Safety indicators
│   │   │   │   ├── financial/       # Financial impact
│   │   │   │   ├── navigation/      # Nav components
│   │   │   │   └── theme-provider.tsx # Dark/light mode
│   │   │   └── lib/
│   │   │       ├── utils.ts         # cn() utility
│   │   │       └── supabase/        # Supabase client setup
│   │   ├── public/                  # Static assets
│   │   ├── tailwind.config.ts       # Tailwind configuration
│   │   ├── tsconfig.json            # TypeScript config
│   │   ├── next.config.js           # Next.js config
│   │   ├── vitest.config.ts         # Test config
│   │   └── package.json             # Frontend dependencies
│   │
│   └── api/                         # Python FastAPI Backend (Part: api)
│       ├── app/
│       │   ├── main.py              # ★ FastAPI entry point
│       │   ├── api/                 # Route handlers (18 routers)
│       │   │   ├── health.py        # Health checks
│       │   │   ├── auth.py          # Authentication
│       │   │   ├── assets.py        # Asset management
│       │   │   ├── oee.py           # OEE calculations
│       │   │   ├── downtime.py      # Downtime analysis
│       │   │   ├── production.py    # Production status
│       │   │   ├── safety.py        # Safety events
│       │   │   ├── financial.py     # Financial impact
│       │   │   ├── actions.py       # Action engine API
│       │   │   ├── chat.py          # Text-to-SQL chat
│       │   │   ├── agent.py         # LangChain agent API
│       │   │   ├── memory.py        # Mem0 memory API
│       │   │   ├── citations.py     # Citation management
│       │   │   ├── cache.py         # Cache management
│       │   │   ├── live_pulse.py    # Real-time polling
│       │   │   ├── summaries.py     # Report summaries
│       │   │   ├── pipelines.py     # Data pipelines
│       │   │   └── asset_history.py # Asset history API
│       │   ├── core/                # Infrastructure
│       │   │   ├── config.py        # Settings (pydantic-settings)
│       │   │   ├── database.py      # ★ MSSQL connection manager
│       │   │   └── security.py      # JWT authentication
│       │   ├── models/              # Pydantic models
│       │   │   ├── agent.py         # Agent models
│       │   │   ├── asset_history.py # History models
│       │   │   ├── citation.py      # Citation models
│       │   │   ├── chat.py          # Chat models
│       │   │   ├── downtime.py      # Downtime models
│       │   │   ├── memory.py        # Memory models
│       │   │   ├── pipeline.py      # Pipeline models
│       │   │   ├── safety.py        # Safety models
│       │   │   └── user.py          # User models
│       │   ├── schemas/             # API schemas
│       │   │   ├── action.py        # Action schemas
│       │   │   ├── financial.py     # Financial schemas
│       │   │   └── summary.py       # Summary schemas
│       │   └── services/            # Business logic
│       │       ├── agent/           # ★ AI Agent Framework
│       │       │   ├── base.py      # ManufacturingTool base class
│       │       │   ├── registry.py  # ToolRegistry
│       │       │   ├── executor.py  # AgentExecutor wrapper
│       │       │   ├── cache.py     # TTL-based caching
│       │       │   ├── data_source/ # Data access abstraction
│       │       │   │   ├── protocol.py   # DataSource protocol
│       │       │   │   ├── supabase.py   # Supabase implementation
│       │       │   │   └── composite.py  # Multi-source
│       │       │   └── tools/       # ★ Manufacturing Tools (12+)
│       │       │       ├── asset_lookup.py
│       │       │       ├── oee_query.py
│       │       │       ├── downtime_analysis.py
│       │       │       ├── production_status.py
│       │       │       ├── safety_events.py
│       │       │       ├── financial_impact.py
│       │       │       ├── cost_of_loss.py
│       │       │       ├── trend_analysis.py
│       │       │       ├── memory_recall.py
│       │       │       ├── comparative_analysis.py
│       │       │       ├── action_list.py
│       │       │       ├── alert_check.py
│       │       │       └── recommendation_engine.py
│       │       ├── memory/          # Mem0 integration
│       │       │   ├── mem0_service.py
│       │       │   └── asset_detector.py
│       │       ├── pipelines/       # Data pipelines
│       │       │   └── live_pulse.py
│       │       ├── ai/              # AI utilities
│       │       ├── action_engine.py # Action prioritization
│       │       ├── ai_context_service.py
│       │       ├── asset_history_service.py
│       │       ├── citation_audit_service.py
│       │       ├── citation_generator.py
│       │       ├── cited_response_service.py
│       │       ├── downtime_analysis.py
│       │       ├── embedding_service.py
│       │       ├── financial.py
│       │       ├── grounding_service.py
│       │       ├── mem0_asset_service.py
│       │       ├── oee_calculator.py
│       │       ├── safety_service.py
│       │       └── scheduler.py     # Background jobs
│       ├── tests/                   # Pytest test suite
│       ├── migrations/              # API-level migrations
│       ├── requirements.txt         # Python dependencies
│       ├── Dockerfile               # Container definition
│       └── pytest.ini               # Test configuration
│
├── supabase/                        # Database layer (Part: supabase)
│   ├── migrations/                  # ★ PostgreSQL migrations
│   │   ├── 20260106000000_plant_object_model.sql    # Core tables
│   │   ├── 20260106000001_analytical_cache.sql      # Cache tables
│   │   ├── 20260106000002_safety_alert_enhancements.sql
│   │   ├── 20260106000003_asset_history.sql
│   │   └── 20260107000001_citation_logs.sql
│   ├── tests/                       # Database tests
│   └── package.json                 # Supabase CLI deps
│
├── packages/                        # Shared packages (placeholder)
│   └── .gitkeep
│
├── scripts/                         # Utility scripts
│   └── epic-chain.sh                # BMAD epic chain runner
│
├── _bmad-output/                    # BMAD workflow outputs
│   ├── planning-artifacts/          # PRD, Architecture docs
│   ├── implementation-artifacts/    # Sprint status, metrics
│   ├── stories/                     # User story files
│   └── uat/                         # UAT documents
│
├── _bmad/                           # BMAD framework (installed)
│   ├── core/                        # Core BMAD workflows
│   └── bmm/                         # BMM module
│
├── .claude/                         # Claude Code configuration
│   └── commands/                    # Slash commands
│
├── turbo.json                       # ★ Turborepo configuration
├── package.json                     # Root workspace config
├── package-lock.json                # Dependency lock
├── README.md                        # Project readme
└── .gitignore                       # Git ignore rules
```

## Critical Directories

### Entry Points (★)

| File | Purpose |
|------|---------|
| `apps/web/src/app/layout.tsx` | Frontend root layout |
| `apps/api/app/main.py` | Backend FastAPI entry |
| `turbo.json` | Monorepo task orchestration |

### AI Agent System

| Path | Purpose |
|------|---------|
| `apps/api/app/services/agent/` | Agent framework root |
| `apps/api/app/services/agent/base.py` | ManufacturingTool base class |
| `apps/api/app/services/agent/tools/` | 12+ manufacturing tools |
| `apps/api/app/services/agent/executor.py` | LangChain AgentExecutor |
| `apps/api/app/services/agent/registry.py` | Auto tool discovery |

### Data Layer

| Path | Purpose |
|------|---------|
| `apps/api/app/core/database.py` | MSSQL connection manager |
| `supabase/migrations/` | PostgreSQL schema |
| `apps/api/app/services/agent/data_source/` | Data access abstraction |

### Frontend UI

| Path | Purpose |
|------|---------|
| `apps/web/src/components/ui/` | Shadcn/UI primitives |
| `apps/web/src/components/chat/` | AI chat interface |
| `apps/web/src/components/action-engine/` | Action recommendations |

## Integration Points

### Web → API

The frontend communicates with the backend via:
- `fetch()` calls to `http://localhost:8000/api/*`
- WebSocket connections (planned for live updates)

### API → Databases

- **Supabase**: `supabase-py` client for PostgreSQL
- **MSSQL**: SQLAlchemy + pyodbc for source system

### Agent → Tools

The AI agent uses the ToolRegistry to discover and execute tools:
```
Agent Query → AgentExecutor → ToolRegistry → ManufacturingTool → Data Source
```

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
