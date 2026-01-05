# Project Brief: Manufacturing Performance Assistant

## 1. Executive Summary
The **Manufacturing Performance Assistant** is a GenAI-powered analytics platform designed to provide Plant Managers and Line Supervisors with both deep retrospective analysis and near-real-time operational awareness. Integrating directly with facility SQL databases, the platform ingests granular production data (Output, OEE, Downtime, ManHours) to deliver a "zero-latency" understanding of performance. It features a hybrid data pipeline that analyzes the previous day's operations (T-1) for root cause discovery while simultaneously polling the last 15 minutes to provide immediate situational awareness. Through a natural language chat interface and automated "Smart Summaries," the system democratizes access to complex data, surfacing critical insights regarding OEE, Safety, Waste, and Schedule Adherence without requiring manual data crunching.

## 2. Problem Statement
**Current State:**
Plant leadership currently relies on fragmented reports and static dashboards to understand performance. While data exists in SQL servers, it is often siloed or requires significant manual effort to correlate "Minutes Lost" with specific reasons (e.g., "Carton Former" vs. "Lid Feeder").
**Pain Points:**
- **Analysis Latency:** Managers often don't understand *why* a shift failed until hours or days later.
- **Reactive Safety Culture:** Safety incidents are buried in row-level data rather than being flagged immediately.
- **Opaque Performance:** Non-technical staff struggle to query specific details (e.g., "Which Rychiger line had the most downtime?") without asking data analysts.
**Impact:**
Operational inefficiency persists because decisions are made based on outdated or incomplete pictures of the factory floor.

## 3. Proposed Solution
**Core Concept:**
A responsive web application acting as an intelligent layer on top of existing SQL infrastructure.
**Key Capabilities:**
*   **Hybrid Data Engine:** Combines a daily batch process for deep historical analysis with a high-frequency (15-minute) polling engine for current status.
*   **GenAI Analyst:** An embedded chat interface allowing users to query data in natural language (e.g., "Show me the top 3 downtime reasons for Grinder 5 yesterday").
*   **Business Logic Layer:** Automatically calculates standard metrics (OEE, Schedule Adherence) while applying business rules to flag anomalies.
*   **Safety First Alerting:** Prominent, immediate visualization of any "Safety Issue" downtime codes detected in the data stream.

## 4. Target Users
*   **Primary: Plant Manager**
    *   Needs high-level summaries, "Red/Green" status of the plant, and immediate awareness of safety/waste issues.
*   **Secondary: Line Supervisors / Area Leads**
    *   Needs tactical details for specific assets (e.g., "Why is CAMA 800-2 down right now?") to direct maintenance resources effectively.

## 5. Goals & Success Metrics
**Business Objectives:**
1.  **Reduce Analysis Latency:** Shift from T+24h understanding to T+15m awareness.
2.  **Zero-Incident Visibility:** Ensure 100% of recorded Safety Issues are flagged to leadership immediately.
3.  **Efficiency:** Improve Schedule Adherence by identifying chronic micro-stoppages (e.g., "Waiting on Supplies").

**Key Performance Indicators (KPIs):**
*   **OEE Improvement:** Track week-over-week trends in Overall Equipment Effectiveness.
*   **Response Time:** Time from "Safety Issue" log to Platform Alert (Target: < 15 mins).
*   **User Engagement:** Daily Active Users (DAU) and number of GenAI queries per session.

## 6. MVP Scope
**In Scope:**
*   **Data Sources:** Ingestion of specific tables/views (Area, Location/Asset, Output, Target, OEE, Downtime Reason Codes) from SQL Server.
*   **Timeframes:**
    *   **T-1 (Yesterday):** Full aggregated analysis, root cause summaries, and "Day in Review."
    *   **T-Now (Last 15 Mins):** Rolling snapshot of current Output vs. Target and active Downtime status.
*   **Dashboard:** Visualizing the 4 Core Metrics:
    1.  OEE (Availability, Performance, Quality)
    2.  Safety Incidents (Count & specific reason codes)
    3.  Waste Produced (Gap between Input/Output or Scrap counts)
    4.  Performance to KPI (Schedule Adherence, T-max Output)
*   **AI Chat:** RAG (Retrieval-Augmented Generation) or Text-to-SQL interface for querying performance data.
*   **Mobile Support:** Responsive design for viewing summaries and alerts on the floor.

**Out of Scope:**
*   **Sub-Second Real-Time:** Streaming websockets are not required for MVP; 15-minute polling is sufficient.
*   **Write-Back:** Users cannot control machines or edit data records via the app.
*   **Predictive Modeling:** No forecasting of future breakdowns (Phase 2).

## 7. Technical Considerations
*   **Infrastructure:** Web Platform (React/Next.js recommended) with a robust backend (Node/Python) to handle SQL querying and AI orchestration.
*   **Data Quality:** System must handle "NaN", "0", and missing values (observed in sample data) gracefully to prevent AI hallucinations.
*   **Performance:** 15-minute polling must be optimized to prevent locking the production SQL database.

## 8. Risks & Assumptions
*   **Risk:** "Last 15 Minutes" data might be noisy or incomplete if the SCADA system buffers data before writing to SQL.
*   **Assumption:** "Safety Issue" and "Waste" data points are explicitly logged in the `problemTypeName` or similar columns as seen in the sample PDF.
