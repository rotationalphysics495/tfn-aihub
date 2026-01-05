---
epic: 2
title: "Data Pipelines & Production Intelligence"
status: draft
frs_covered: ["FR1", "FR4", "FR5"]
story_count: 9
---

# Epic 2: Data Pipelines & Production Intelligence

**Goal:** Plant Managers can view near-real-time production status with OEE, throughput vs target, downtime analysis, AND immediate safety alerts - with financial context integrated from the start.

**FRs Covered:** FR1 (Data Ingestion - complete), FR4 (Safety Alerting), FR5 (Financial Context)

**Relevant NFRs:** NFR2 (Latency - 60 seconds), NFR3 (Read-Only MSSQL)

---

## Stories

### Story 2.1: Batch Data Pipeline (T-1)

Morning Report pipeline via Railway Cron fetching yesterday's data from MSSQL.

---

### Story 2.2: Polling Data Pipeline (T-15m)

Live Pulse polling via Python Background Scheduler for near-real-time updates.

---

### Story 2.3: Throughput Dashboard

Actual vs Target production visualization for Plant Managers.

---

### Story 2.4: OEE Metrics View

Overall Equipment Effectiveness display with calculations from ingested data.

---

### Story 2.5: Downtime Pareto Analysis

Granular downtime breakdown and pareto charts by reason code.

---

### Story 2.6: Safety Alert System

Immediate "Red" alerting for any "Safety Issue" reason code detected.

---

### Story 2.7: Financial Impact Calculator

Translate downtime and waste into dollar values using cost_centers data.

---

### Story 2.8: Cost of Loss Widget

Financial loss display widget integrated into production views.

---

### Story 2.9: Live Pulse Ticker

15-minute real-time status ticker with integrated financial context.

---

## Dependencies

- Epic 1: Project Foundation & Infrastructure (monorepo, auth, schemas, MSSQL connection)

## Enables

- Epic 3: Action Engine & AI Synthesis (uses daily_summaries, safety_events, financial data)
- Epic 4: AI Chat & Memory (queries production and financial data)
