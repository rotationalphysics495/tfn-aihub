---
epic: 3
title: "Action Engine & AI Synthesis"
status: draft
frs_covered: ["FR3"]
story_count: 5
---

# Epic 3: Action Engine & AI Synthesis

**Goal:** Plant Managers see a prioritized "Daily Action List" on login that synthesizes Production, Quality, and Financial data into actionable recommendations backed by evidence.

**FRs Covered:** FR3 (Action Engine)

**Relevant NFRs:** NFR1 (Accuracy - AI must cite specific data points)

---

## Stories

### Story 3.1: Action Engine Logic

Filter/sort algorithm prioritizing by Safety first, then OEE below target, then Financial Loss above threshold.

---

### Story 3.2: Daily Action List API

Backend endpoint generating prioritized action items from daily_summaries, safety_events, and financial data.

---

### Story 3.3: Action List Primary View

Morning Report UI with Action List as the landing page view on login.

---

### Story 3.4: Insight + Evidence Cards

Card design linking each recommendation to supporting metric/chart evidence.

---

### Story 3.5: Smart Summary Generator

LLM-powered natural language summary explaining why targets were missed and what to do about it.

---

## Dependencies

- Epic 1: Project Foundation & Infrastructure (schemas, UI shell)
- Epic 2: Data Pipelines & Production Intelligence (daily_summaries, safety_events, financial calculations)

## Enables

- Epic 4: AI Chat & Memory (can reference action items in conversational queries)
