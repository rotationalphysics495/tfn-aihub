---
epic: 1
title: "Project Foundation & Infrastructure"
status: draft
frs_covered: ["FR1 (partial)", "FR2"]
story_count: 7
---

# Epic 1: Project Foundation & Infrastructure

**Goal:** Development team has a fully scaffolded monorepo with authentication, database schemas, and basic UI shell ready for feature development.

**FRs Covered:** Partial FR1 (infrastructure only), FR2 (Plant Object Model schema)

**Relevant NFRs:** NFR3 (Read-Only MSSQL access)

---

## Stories

### Story 1.1: TurboRepo Monorepo Scaffold

Set up the monorepo with apps/web (Next.js) and apps/api (Python FastAPI).

---

### Story 1.2: Supabase Auth Integration

User login/logout with Supabase Auth and JWT validation in FastAPI.

---

### Story 1.3: Plant Object Model Schema

Create assets, cost_centers, shift_targets tables in Supabase PostgreSQL.

---

### Story 1.4: Analytical Cache Schema

Create daily_summaries, live_snapshots, safety_events tables in Supabase PostgreSQL.

---

### Story 1.5: MSSQL Read-Only Connection

Configure secure read-only connection to source manufacturing database via pyodbc/SQLAlchemy.

---

### Story 1.6: Industrial Clarity Design System

Establish Tailwind CSS + Shadcn/UI foundation with high-contrast theme for factory floor visibility.

---

### Story 1.7: Command Center UI Shell

Create dashboard layout with placeholder sections for Action List, Live Pulse, and Financial widgets.

---

## Dependencies

- None (this is the foundational epic)

## Enables

- Epic 2: Data Pipelines & Production Intelligence
- Epic 3: Action Engine & AI Synthesis
- Epic 4: AI Chat & Memory
