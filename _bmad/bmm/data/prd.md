# Product Requirements Document (PRD): Manufacturing Performance Assistant

## 1. Goals and Background Context
### Goals
*   **Reduce Analysis Latency:** Empower Plant Managers to move from T+24h retroactive reporting to T+15m near-real-time situational awareness.
*   **Synthesize Actionable Intelligence:** Move beyond simple "reporting" to generating a prioritized **Daily Action List** using GenAI that synthesizes Production, Labor, Quality, and Financial data.
*   **Zero-Incident Visibility:** Ensure 100% of recorded "Safety Issue" downtime codes are flagged immediately.
*   **Democratize Data Access:** Enable non-technical staff to query complex factory data using natural language.

### Background Context
The facility operates with rich data in SQL Server but lacks a unified view. Data on Output, Downtime, Quality, and Labor exists but is siloed. Leadership needs a "Morning Report" that doesn't just show charts but explains *why* targets were missed and *what* to do about it, backed by financial impact analysis. Additionally, a "Live Pulse" is needed to catch issues as they happen during the shift.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2026-01-05 | 1.0 | Initial MVP Draft | PM Agent |

## 2. Requirements
### Functional
*   **FR1 (Data Ingestion):** Ingest T-1 (Yesterday) and T-15m (Live) data from SQL Server for Output, OEE, Downtime, Quality, and Labor.
*   **FR2 (Plant Object Model):** Maintain a relational model linking Assets to Cost Centers to Staffing Lines to enable cross-domain analysis.
*   **FR3 (Action Engine):** Generate a natural-language "Daily Action List" prioritizing issues based on Financial Impact and Safety Risk.
*   **FR4 (Safety Alerting):** Immediately visual "Red" alerting for any "Safety Issue" reason code.
*   **FR5 (Financial Context):** Translate operational losses (waste, downtime) into estimated dollar values using standard costs.
*   **FR6 (AI Chat with Memory):** Provide a chat interface that remembers past context (via Mem0) to answer specific queries.

### Non-Functional
*   **NFR1 (Accuracy):** AI must cite specific data points for every recommendation to prevent hallucination.
*   **NFR2 (Latency):** "Live" views must reflect SQL data within 60 seconds of ingestion.
*   **NFR3 (Read-Only):** System must strictly observe Read-Only permissions on source manufacturing databases.

## 3. User Interface Design Goals
*   **"Industrial Clarity":** High-contrast, legible design suitable for factory floor lighting.
*   **Contextual Separation:** Clear visual distinction between "Yesterday's Analysis" (Static) and "Live Pulse" (Dynamic).
*   **Action-First:** The "Daily Action List" should be the primary view on login, before detailed charts.

## 4. Technical Assumptions
*   **Frontend:** Next.js (React)
*   **Backend:** Python (FastAPI) for robust AI/Data processing.
*   **Database:** Supabase (PostgreSQL) for App DB; Connection to existing MSSQL for Source.
*   **AI/Memory:** LangChain + **Mem0** for long-term memory and user context.
*   **Deployment:** Dockerized containers.

## 5. Epic List
*   **Epic 1: Foundation & "Morning Report" Core:** Supabase setup, Plant Object Model, Data Pipelines.
*   **Epic 2: Production & Downtime Intelligence:** Throughput, OEE, and Granular Downtime analysis.
*   **Epic 3: Resource & Reliability Intelligence:** Quality, Labor/Staffing, and Maintenance/Reliability modules.
*   **Epic 4: Business Context (Financials & Inventory):** Financial impact translation and Material Flow risk.
*   **Epic 5: The "Action Engine" (AI Synthesis):** Mem0 integration, Anomaly Synthesis, and Daily Action List generation.

## 6. Epic Details
### Epic 1: Foundation & "Morning Report" Core
*   **Goal:** Establish the semantic data layer.
*   **Stories:**
    *   1.1 Project Scaffold & Supabase Setup
    *   1.2 SQL Ingestion Pipelines (Batch + Polling)
    *   1.3 Plant Object Model Schema Definition
    *   1.4 Morning Report UI Shell

### Epic 2: Production & Downtime Intelligence
*   **Goal:** Visualize operational metrics.
*   **Stories:**
    *   2.1 Throughput Visualizer (Actual vs Target)
    *   2.2 Granular Downtime Pareto & Analysis
    *   2.3 Asset Drill-Down Views
    *   2.4 "Live Pulse" 15-min Ticker

### Epic 3: Resource & Reliability Intelligence
*   **Goal:** Contextualize with resource data.
*   **Stories:**
    *   3.1 Quality & Scrap Analysis Module
    *   3.2 Labor & Staffing Correlation View
    *   3.3 Reliability "Red Zone" Monitor

### Epic 4: Business Context
*   **Goal:** Translate to business value.
*   **Stories:**
    *   4.1 Financial Impact Calculator
    *   4.2 Inventory & Material Flow Risk Monitor
    *   4.3 Cost of Loss Widget

### Epic 5: The "Action Engine"
*   **Goal:** Synthesize insights into actions.
*   **Stories:**
    *   5.1 Mem0 Vector Memory Integration
    *   5.2 Anomaly Synthesis Agent Logic
    *   5.3 Daily Action List Generator UI
    *   5.4 Plant Analyst Chatbot
