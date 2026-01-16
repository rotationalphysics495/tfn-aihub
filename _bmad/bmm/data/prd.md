# Product Requirements Document (PRD): Manufacturing Performance Assistant

**Version:** 2.0
**Author:** Caleb
**Date:** 2026-01-15
**Status:** Active

---

## Executive Summary

### The Problem

The facility operates with rich data in SQL Server but lacks a unified view. Data on Output, Downtime, Quality, and Labor exists but is siloed. Plant Managers spend 30-45 minutes each morning clicking through dashboards, cross-referencing reports, and mentally synthesizing overnight production data. Leadership needs a "Morning Report" that doesn't just show charts but explains *why* targets were missed and *what* to do about it, backed by financial impact analysis. Additionally, supervisors hand off shifts through hurried hallway conversations—knowledge that walks out the door when the outgoing shift leaves.

### The Solution

The Manufacturing Performance Assistant is a comprehensive AI-powered platform that:

1. **Synthesizes Actionable Intelligence:** Moves beyond simple "reporting" to generating a prioritized Daily Action List using GenAI that synthesizes Production, Labor, Quality, and Financial data.

2. **Provides Reliable AI Tools:** A LangChain Agent with 13+ specialized tools delivers structured, reliable responses for common plant manager questions while maintaining natural language flexibility.

3. **Enables Voice-First Operations:** Voice-enabled structured briefings transform the platform from a reactive query system into a proactive intelligence partner through Morning Briefings, Shift Handoffs, and End of Day Summaries.

### What Makes This Special

- **From T+24h to T+15m:** Move from retroactive reporting to near-real-time situational awareness
- **From dashboards to dialogue:** Instead of 45 minutes clicking through reports, get a 3-minute synthesized briefing while pouring coffee
- **Knowledge that doesn't walk out the door:** Shift handoffs create persistent, reviewable records with full interaction capability
- **Zero-Incident Visibility:** 100% of recorded "Safety Issue" downtime codes are flagged immediately

### Success Metrics

| Metric | Target |
|--------|--------|
| Analysis Latency | T+24h → T+15m |
| Morning meeting prep time | 50% reduction |
| Shift handoff documentation | 100% consistent coverage |
| Tool Response Time | < 2 seconds (p95) |
| Citation Coverage | 100% of factual claims |

---

## Project Classification

**Technical Type:** web_app (Next.js/FastAPI platform)
**Domain:** Manufacturing/Industrial Operations
**Complexity:** High
**Project Context:** Brownfield - extending existing system

**Infrastructure:**
- Supabase (PostgreSQL) for App DB
- Connection to existing MSSQL for Source (read-only)
- LangChain + Mem0 for AI/Memory
- ElevenLabs for voice (TTS + push-to-talk STT)
- Dockerized containers on Railway

---

## Document Index

This PRD is organized into the following sections:

| Document | Description |
|----------|-------------|
| [prd.md](prd.md) | This file - Executive summary, classification, and index |
| [prd-goals.md](prd/prd-goals.md) | Goals, background context, and UI design principles |
| [prd-functional-requirements.md](prd/prd-functional-requirements.md) | All functional requirements (FR1-FR57) |
| [prd-non-functional-requirements.md](prd/prd-non-functional-requirements.md) | All non-functional requirements (NFR1-NFR26) |
| [prd-user-journeys.md](prd/prd-user-journeys.md) | User personas and journey narratives |
| [prd-architecture.md](prd/prd-architecture.md) | Technical architecture and data access patterns |
| [prd-epics.md](prd/prd-epics.md) | Epic list and detailed epic definitions |

---

## Epic Overview

| Epic | Title | Focus |
|------|-------|-------|
| 1 | Foundation & "Morning Report" Core | Supabase setup, Plant Object Model, Data Pipelines |
| 2 | Production & Downtime Intelligence | Throughput, OEE, and Granular Downtime analysis |
| 3 | Resource & Reliability Intelligence | Quality, Labor/Staffing, and Maintenance/Reliability |
| 4 | Business Context (Financials & Inventory) | Financial impact translation and Material Flow risk |
| 5 | The "Action Engine" & AI Agent Tools | Agent Framework, 13 Tools, Mem0, Action List Generation |
| 6 | Safety & Financial Intelligence Tools | Safety Events, Financial Impact, Cost of Loss, Trend Analysis |
| 7 | Proactive Agent Capabilities | Memory Recall, Comparative Analysis, Recommendations |
| 8 | Voice Briefing Foundation | ElevenLabs integration, Morning Briefing workflow |
| 9 | Shift Handoff & EOD Summary | Handoff workflow, EOD comparison, Admin UI |

---

## Decisions & Resolved Questions

| # | Question | Decision |
|---|----------|----------|
| 1 | Should tools support batch queries? | Not required for MVP - single asset/area queries sufficient |
| 2 | Rate limiting per user for expensive tools? | Not required - can be added later if needed |
| 3 | Should recommendations require human approval? | No - display directly to user |
| 4 | Cache strategy for tool results? | Yes - tiered TTLs (see NFR18) |
| 5 | Epic 5 scope conflict? | Combined Agent Foundation + Action Engine into single epic |
| 6 | Voice features epic placement? | New Epic 8 (Voice Foundation) and Epic 9 (Handoff/EOD) |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-05 | 1.0 | Initial MVP Draft | PM Agent |
| 2026-01-09 | 1.1 | AI Agent Tools Addendum | Caleb + PM Agent |
| 2026-01-15 | 1.2 | Voice Morning Report PRD | Caleb + PM Agent |
| 2026-01-15 | 2.0 | Unified PRD - consolidated all requirements | Caleb + PM Agent |
| 2026-01-15 | 2.1 | Sharded PRD into section files | Caleb + PM Agent |
