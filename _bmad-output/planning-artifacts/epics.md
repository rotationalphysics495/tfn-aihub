---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/ux-design.md"
---

# Manufacturing Performance Assistant - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Manufacturing Performance Assistant, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR1 (Data Ingestion):** Ingest T-1 (Yesterday) and T-15m (Live) data from SQL Server for Output, OEE, Downtime, Quality, and Labor.
- **FR2 (Plant Object Model):** Maintain a relational model linking Assets to Cost Centers to Staffing Lines to enable cross-domain analysis.
- **FR3 (Action Engine):** Generate a natural-language "Daily Action List" prioritizing issues based on Financial Impact and Safety Risk.
- **FR4 (Safety Alerting):** Immediately visual "Red" alerting for any "Safety Issue" reason code.
- **FR5 (Financial Context):** Translate operational losses (waste, downtime) into estimated dollar values using standard costs.
- **FR6 (AI Chat with Memory):** Provide a chat interface that remembers past context (via Mem0) to answer specific queries.

### NonFunctional Requirements

- **NFR1 (Accuracy):** AI must cite specific data points for every recommendation to prevent hallucination.
- **NFR2 (Latency):** "Live" views must reflect SQL data within 60 seconds of ingestion.
- **NFR3 (Read-Only):** System must strictly observe Read-Only permissions on source manufacturing databases.

### Additional Requirements

**From Architecture:**
- TurboRepo monorepo structure with `apps/web` (Next.js) and `apps/api` (Python FastAPI)
- Supabase for App Database, Auth, and Vector Storage
- Railway for backend hosting with background worker capabilities
- Vercel for frontend hosting (recommended)
- Mem0 integration for AI memory/context
- LangChain for AI orchestration and Text-to-SQL
- Plant Object Model schema: `assets`, `cost_centers`, `shift_targets` tables
- Analytical Cache: `daily_summaries`, `live_snapshots`, `safety_events` tables
- Pipeline A (Morning Report): Daily batch at 06:00 AM via Railway Cron
- Pipeline B (Live Pulse): 15-minute polling via Python Background Scheduler
- MSSQL read-only connection via pyodbc/SQLAlchemy
- JWT authentication via Supabase Auth

**From UX Design:**
- "Industrial Clarity" high-contrast design for factory floor visibility
- Action-first landing page with Daily Action List as primary view
- "Glanceability" - status readable from 3 feet away on tablet
- Trust & Transparency - AI recommendations must link to raw data evidence
- Clear visual distinction between Retrospective (cool colors) and Live (vibrant/pulsing) modes
- "Safety Red" reserved exclusively for safety incidents
- AI Analyst Chat as overlay/sidebar
- Asset Detail View with machine history and real-time status
- Responsive design for tablets (primary) and desktop

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 (infra) + Epic 2 (pipelines) | Data Ingestion: connection setup in E1, pipelines in E2 |
| FR2 | Epic 1 | Plant Object Model schema (assets, cost_centers, shift_targets) |
| FR3 | Epic 3 | Action Engine (Daily Action List generation) |
| FR4 | Epic 2 | Safety Alerting (immediate "Red" alerts) |
| FR5 | Epic 2 | Financial Context (integrated with production views) |
| FR6 | Epic 4 | AI Chat with Memory (Mem0 integration) |

## Epic List

| Epic | Title | User Value | FRs |
|------|-------|------------|-----|
| 1 | Project Foundation & Infrastructure | Auth + UI shell + design system | FR2, partial FR1 |
| 2 | Data Pipelines & Production Intelligence | Live monitoring + safety + financials | FR1, FR4, FR5 |
| 3 | Action Engine & AI Synthesis | Prioritized Daily Action List | FR3 |
| 4 | AI Chat & Memory | Natural language queries with context | FR6 |

---

## Epic 1: Project Foundation & Infrastructure

**Goal:** Development team has a fully scaffolded monorepo with authentication, database schemas, and basic UI shell ready for feature development.

**FRs Covered:** Partial FR1 (infrastructure only), FR2 (Plant Object Model schema)

**Scope:**
- TurboRepo monorepo scaffold (Next.js + FastAPI)
- Supabase setup (Auth, PostgreSQL, schemas)
- Plant Object Model tables (assets, cost_centers, shift_targets)
- Analytical Cache tables (daily_summaries, live_snapshots, safety_events)
- MSSQL read-only connection configuration
- "Industrial Clarity" design system foundation (Tailwind + Shadcn/UI)
- Command Center UI shell with placeholder sections

---

## Epic 2: Data Pipelines & Production Intelligence

**Goal:** Plant Managers can view near-real-time production status with OEE, throughput vs target, downtime analysis, AND immediate safety alerts - with financial context integrated from the start.

**FRs Covered:** FR1 (Data Ingestion - complete), FR4 (Safety Alerting), FR5 (Financial Context)

**Scope:**
- Batch pipeline (T-1 "Morning Report" via Railway Cron)
- Polling pipeline (T-15m "Live Pulse" via Background Scheduler)
- Production dashboards (Throughput vs Target, OEE metrics)
- Downtime Pareto & Analysis views
- Safety "Red" alerting for safety incidents
- Financial Impact Calculator (using cost_centers)
- Cost of Loss widget integrated into views
- Live Pulse ticker with financial context

---

## Epic 3: Action Engine & AI Synthesis

**Goal:** Plant Managers see a prioritized "Daily Action List" on login that synthesizes Production, Quality, and Financial data into actionable recommendations backed by evidence.

**FRs Covered:** FR3 (Action Engine)

**Scope:**
- Action Engine logic (filter by Safety > 0, OEE < Target, Financial Loss > Threshold)
- Sort by Safety first, then Financial Impact ($)
- "Morning Report" UI with Action List as primary view
- Insight + Evidence card design (recommendation + supporting data)
- AI recommendations linked to raw data citations (NFR1)
- Smart Summary text generation via LLM

---

## Epic 4: AI Chat & Memory

**Goal:** Plant Managers can query complex factory data using natural language, with the AI remembering past context and providing cited, accurate responses.

**FRs Covered:** FR6 (AI Chat with Memory)

**Scope:**
- Mem0 vector memory integration
- LangChain Text-to-SQL for natural language queries
- Chat sidebar/overlay UI
- Asset history and user session memory
- Responses cite specific data points (NFR1)
- Context-aware follow-up conversations

