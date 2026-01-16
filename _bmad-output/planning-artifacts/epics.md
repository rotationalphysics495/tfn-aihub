---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad/bmm/data/prd/prd-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-non-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-epics.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/architecture/voice-briefing.md"
  - "_bmad/bmm/data/ux-design.md"
lastUpdated: "2026-01-16"
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
- **FR7 (AI Agent Tools):** Provide specialized tools for common plant manager queries (Asset Lookup, OEE Query, Downtime Analysis, Production Status, Safety Events, Financial Impact, Cost of Loss, Trend Analysis, Memory Recall, Comparative Analysis, Action List, Alert Check, Recommendation Engine).

### NonFunctional Requirements

- **NFR1 (Accuracy):** AI must cite specific data points for every recommendation to prevent hallucination.
- **NFR2 (Latency):** "Live" views must reflect SQL data within 60 seconds of ingestion.
- **NFR3 (Read-Only):** System must strictly observe Read-Only permissions on source manufacturing databases.
- **NFR4 (Agent Honesty):** AI Agent must never fabricate data; clearly state when information is unavailable.
- **NFR5 (Tool Extensibility):** Tool architecture must support adding new data sources (MSSQL) without modifying existing tools.
- **NFR6 (Response Structure):** All tool responses must include citations, structured data, and optional follow-ups.
- **NFR7 (Tool Response Caching):** Tool responses must be cached with tiered TTLs (60s live, 15m daily, 1h static).

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
| FR7.1 | Epic 5 | Core Operations Tools (Asset, OEE, Downtime, Production) |
| FR7.2 | Epic 6 | Safety & Financial Tools |
| FR7.3 | Epic 6 + Epic 7 | Intelligence Tools (Trend Analysis in E6, Memory/Comparison in E7) |
| FR7.4 | Epic 7 | Proactive Action Tools (Action List, Alerts, Recommendations) |
| FR8-FR13 | Epic 8 | Voice & Briefing Delivery (TTS, STT, transcript) |
| FR14-FR20 | Epic 8 | Morning Briefing Workflow |
| FR35-FR45 | Epic 8 | User Preferences & Onboarding |
| FR21-FR30 | Epic 9 | Shift Handoff Workflow |
| FR31-FR34 | Epic 9 | End of Day Summary |
| FR46-FR50 | Epic 9 | Admin & Configuration |
| FR51-FR57 | Epic 9 | Data Citations & Audit |

## Epic List

| Epic | Title | User Value | FRs | Status |
|------|-------|------------|-----|--------|
| 1 | Project Foundation & Infrastructure | Auth + UI shell + design system | FR2, partial FR1 | ✅ Complete |
| 2 | Data Pipelines & Production Intelligence | Live monitoring + safety + financials | FR1, FR4, FR5 | ✅ Complete |
| 3 | Action Engine & AI Synthesis | Prioritized Daily Action List | FR3 | ✅ Complete |
| 4 | AI Chat & Memory | Natural language queries with context | FR6 | ✅ Complete |
| 5 | Agent Foundation & Core Tools | Reliable, fast responses to common questions | FR7.1, NFR4-7 | ✅ Complete |
| 6 | Safety & Financial Intelligence Tools | Safety visibility + financial context via chat | FR7.2, FR7.3 | ✅ Complete |
| 7 | Proactive Agent Capabilities | Memory, comparison, recommendations | FR7.3, FR7.4 | ✅ Complete |
| 8 | Voice Briefing Foundation | Hands-free morning briefings with voice | FR8-FR20, FR35-FR45 | Ready |
| 9 | Shift Handoff & EOD Summary | Persistent handoffs + accountability loop | FR21-FR34, FR46-FR57 | Ready |

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

---

## Epic 5: Agent Foundation & Core Tools

**Goal:** Plant Managers can ask natural language questions about assets, OEE, downtime, and production status and receive fast, reliable, cited responses.

**FRs Covered:** FR7.1 (Core Operations Tools), NFR4-7

**Dependencies:** Epic 4 (AI Chat & Memory) - completed

**Scope:**
- LangChain Agent Framework with tool registration pattern
- Data Access Abstraction Layer (Supabase now, MSSQL future)
- Asset Lookup Tool (metadata, status, 7-day performance)
- OEE Query Tool (with component breakdown)
- Downtime Analysis Tool (Pareto, patterns)
- Production Status Tool (real-time output vs target)
- Agent Chat Integration (wire to existing UI)
- Tool Response Caching (tiered TTLs)

**Stories:** 8 | **Details:** See [epic-5.md](epic-5.md)

---

## Epic 6: Safety & Financial Intelligence Tools

**Goal:** Plant Managers can query safety incidents and understand the financial impact of operational issues.

**FRs Covered:** FR7.2 (Safety & Financial Tools), FR7.3 (Trend Analysis)

**Dependencies:** Epic 5 (Agent Foundation & Core Tools)

**Scope:**
- Safety Events Tool (incidents with severity, resolution status)
- Financial Impact Tool (cost calculation by asset/area)
- Cost of Loss Tool (ranked financial losses)
- Trend Analysis Tool (7-90 day performance trends)

**Stories:** 4 | **Details:** See [epic-6.md](epic-6.md)

---

## Epic 7: Proactive Agent Capabilities

**Goal:** The AI Agent proactively helps plant managers by recalling context, comparing assets, and suggesting actions.

**FRs Covered:** FR7.3 (Memory Recall, Comparative Analysis), FR7.4 (Proactive Action Tools)

**Dependencies:** Epic 6 (Safety & Financial Intelligence Tools)

**Scope:**
- Memory Recall Tool (conversation history by topic/asset)
- Comparative Analysis Tool (side-by-side asset comparison)
- Action List Tool (prioritized daily actions)
- Alert Check Tool (active warnings and issues)
- Recommendation Engine (pattern-based suggestions)

**Stories:** 5 | **Details:** See [epic-7.md](epic-7.md)

---

## Epic 8: Voice Briefing Foundation

**Goal:** Enable voice-first operations with Morning Briefing workflow, allowing Plant Managers and Supervisors to receive synthesized briefings hands-free.

**FRs Covered:** FR8-FR13 (Voice & Briefing Delivery), FR14-FR20 (Morning Briefing Workflow), FR35-FR45 (User Preferences & Onboarding)

**Dependencies:** Epic 7 (Proactive Agent Capabilities)

**Scope:**
- ElevenLabs TTS integration (Flash v2.5)
- Push-to-talk STT integration (Scribe v2)
- Briefing Synthesis Engine (tool orchestration)
- Morning Briefing Workflow (all areas for PM)
- Supervisor Scoped Briefings (assigned assets only)
- Voice Number Formatting ("2.1 million" not "2,130,500")
- Area-by-Area Delivery UI with pause points
- User Preference Onboarding flow
- Mem0 Preference Storage and sync

**Stories:** 9 | **Details:** See [epic-8.md](epic-8.md)

---

## Epic 9: Shift Handoff & EOD Summary

**Goal:** Enable persistent shift handoffs and close the accountability loop with End of Day summaries, ensuring knowledge doesn't walk out the door when shifts change.

**FRs Covered:** FR21-FR30 (Shift Handoff), FR31-FR34 (EOD Summary), FR46-FR50 (Admin), FR51-FR57 (Citations & Audit)

**Dependencies:** Epic 8 (Voice Briefing Foundation)

**Scope:**
- Shift Handoff Trigger and Workflow
- Shift Data Synthesis via LangChain tools
- Voice Note Attachment for handoffs
- Persistent Handoff Records (immutable)
- Handoff Review UI for incoming supervisors
- Handoff Q&A with AI assistance
- Acknowledgment Flow with audit trail
- Handoff Notifications (in-app + push)
- Offline Handoff Caching (Service Worker + IndexedDB)
- End of Day Summary with prediction comparison
- EOD Push Notification Reminders
- Admin UI for Asset Assignment
- Admin UI for Role Management
- Admin Audit Logging (90-day retention)

**Stories:** 15 | **Details:** See [epic-9.md](epic-9.md)
