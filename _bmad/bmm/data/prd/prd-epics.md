# PRD: Epic Definitions

**Parent Document:** [prd.md](../prd.md)

---

## Epic Summary

| Epic | Title | Stories | Focus |
|------|-------|---------|-------|
| 1 | Foundation & "Morning Report" Core | 4 | Supabase setup, Plant Object Model, Data Pipelines |
| 2 | Production & Downtime Intelligence | 4 | Throughput, OEE, and Granular Downtime analysis |
| 3 | Resource & Reliability Intelligence | 3 | Quality, Labor/Staffing, and Maintenance/Reliability |
| 4 | Business Context (Financials & Inventory) | 3 | Financial impact translation and Material Flow risk |
| 5 | The "Action Engine" & AI Agent Tools | 12 | Agent Framework, 13 Tools, Mem0, Action List Generation |
| 6 | Safety & Financial Intelligence Tools | 4 | Safety Events, Financial Impact, Cost of Loss, Trend Analysis |
| 7 | Proactive Agent Capabilities | 5 | Memory Recall, Comparative Analysis, Recommendations |
| 8 | Voice Briefing Foundation | 9 | ElevenLabs integration, Morning Briefing workflow |
| 9 | Shift Handoff & EOD Summary | 15 | Handoff workflow, EOD comparison, Admin UI |

**Total:** 59 stories across 9 epics

---

## Epic 1: Foundation & "Morning Report" Core

**Goal:** Establish the semantic data layer.

**Stories:**
- 1.1 Project Scaffold & Supabase Setup
- 1.2 SQL Ingestion Pipelines (Batch + Polling)
- 1.3 Plant Object Model Schema Definition
- 1.4 Morning Report UI Shell

---

## Epic 2: Production & Downtime Intelligence

**Goal:** Visualize operational metrics.

**Stories:**
- 2.1 Throughput Visualizer (Actual vs Target)
- 2.2 Granular Downtime Pareto & Analysis
- 2.3 Asset Drill-Down Views
- 2.4 "Live Pulse" 15-min Ticker

---

## Epic 3: Resource & Reliability Intelligence

**Goal:** Contextualize with resource data.

**Stories:**
- 3.1 Quality & Scrap Analysis Module
- 3.2 Labor & Staffing Correlation View
- 3.3 Reliability "Red Zone" Monitor

---

## Epic 4: Business Context

**Goal:** Translate to business value.

**Stories:**
- 4.1 Financial Impact Calculator
- 4.2 Inventory & Material Flow Risk Monitor
- 4.3 Cost of Loss Widget

---

## Epic 5: The "Action Engine" & AI Agent Tools

**Goal:** Build the intelligent agent framework with specialized tools and synthesize insights into prioritized actions.

**Dependencies:** Epics 1-4 (Foundation, Production, Resource, Business Context)

**User Value:** Plant managers can ask natural language questions about assets, OEE, downtime, and production status and receive fast, reliable, cited responses. The most common questions ("How is Grinder 5 doing?", "What's our OEE?", "Why were we down?", "What should I focus on today?") work reliably with consistent, cited responses.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 5.1 | Agent Framework & Tool Registry | LangChain agent setup with tool registration pattern |
| 5.2 | Data Access Abstraction Layer | Supabase adapter with interface for future MSSQL |
| 5.3 | Asset Lookup Tool | Asset metadata, status, recent performance |
| 5.4 | OEE Query Tool | OEE calculation with component breakdown |
| 5.5 | Downtime Analysis Tool | Downtime reasons, Pareto, patterns |
| 5.6 | Production Status Tool | Real-time output vs target |
| 5.7 | Agent Chat Integration | Wire agent into existing chat UI |
| 5.8 | Tool Response Caching | Tiered caching with TTL and invalidation |
| 5.9 | Mem0 Vector Memory Integration | Long-term memory and user context |
| 5.10 | Anomaly Synthesis Agent Logic | Cross-domain pattern detection |
| 5.11 | Daily Action List Generator | Prioritized action items with evidence |
| 5.12 | Plant Analyst Chatbot UI | Enhanced chat experience |

**Acceptance Criteria:**
- [ ] Agent framework operational with tool selection
- [ ] All 4 core tools (Asset, OEE, Downtime, Production) implemented and tested
- [ ] Agent correctly selects tools based on user intent (>90% accuracy)
- [ ] All responses include citations with source and timestamp
- [ ] Response time < 2 seconds (p95)
- [ ] Agent gracefully handles unknown queries ("I don't have data for...")
- [ ] Data access layer abstraction in place for future MSSQL
- [ ] Tool response caching implemented with appropriate TTLs
- [ ] Mem0 integration operational for memory persistence
- [ ] Daily Action List generated with financial and safety prioritization
- [ ] Chat UI connected to new agent

---

## Epic 6: Safety & Financial Intelligence Tools

**Goal:** Plant Managers can query safety incidents and understand the financial impact of operational issues.

**Dependencies:** Epic 5 (Action Engine & AI Agent Tools)

**User Value:** Safety-first visibility ("Any safety incidents?") and financial context ("What's this costing us?") are critical for prioritization decisions.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 6.1 | Safety Events Tool | Safety incident queries with severity and resolution status |
| 6.2 | Financial Impact Tool | Cost of downtime/waste calculation by asset or area |
| 6.3 | Cost of Loss Tool | Ranked financial losses with root causes |
| 6.4 | Trend Analysis Tool | Time-series analysis, anomaly detection, baseline comparison |

**Acceptance Criteria:**
- [ ] Safety Events tool returns incidents with severity, status, affected assets
- [ ] Financial Impact tool calculates dollar losses using cost_centers data
- [ ] Cost of Loss tool ranks issues by financial impact
- [ ] Trend Analysis tool shows performance over 7-90 day windows
- [ ] All tools include citations
- [ ] Response time < 2 seconds (p95)

---

## Epic 7: Proactive Agent Capabilities

**Goal:** The AI Agent proactively helps plant managers by recalling context, comparing assets, and suggesting actions.

**Dependencies:** Epic 6 (Safety & Financial Intelligence Tools)

**User Value:** The agent becomes a true assistant—remembering past conversations, helping compare options, and proactively suggesting what to focus on.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 7.1 | Memory Recall Tool | Retrieve relevant conversation history by topic or asset |
| 7.2 | Comparative Analysis Tool | Side-by-side asset/area comparison with variance highlighting |
| 7.3 | Action List Tool | Get prioritized daily actions from Action Engine |
| 7.4 | Alert Check Tool | Query active warnings and issues with severity filter |
| 7.5 | Recommendation Engine | Pattern-based suggestions with supporting evidence |

**Acceptance Criteria:**
- [ ] Memory Recall retrieves relevant past conversations via Mem0
- [ ] Comparative Analysis shows side-by-side metrics for 2+ assets
- [ ] Action List tool surfaces prioritized daily actions with evidence
- [ ] Alert Check returns active warnings with recommended responses
- [ ] Recommendation Engine suggests improvements based on patterns
- [ ] All tools include citations where applicable
- [ ] Response time < 3 seconds (p95) for intelligence tools

---

## Epic 8: Voice Briefing Foundation

**Goal:** Enable voice-first operations with Morning Briefing workflow.

**Dependencies:** Epic 7 (Proactive Agent Capabilities)

**User Value:** Plant Managers can receive a synthesized morning briefing hands-free while walking to their office or pouring coffee. Supervisors receive focused briefings on their assigned assets only.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 8.1 | ElevenLabs TTS Integration | Text-to-speech for briefing delivery |
| 8.2 | Push-to-Talk STT Integration | Speech-to-text for Q&A during briefings |
| 8.3 | Briefing Synthesis Engine | Compose existing tools into narrative briefings |
| 8.4 | Morning Briefing Workflow | Plant-wide synthesis for Plant Managers |
| 8.5 | Supervisor Scoped Briefings | Filter briefings to assigned assets only |
| 8.6 | Voice Number Formatting | Format numbers for natural voice delivery |
| 8.7 | Area-by-Area Delivery UI | Sequential delivery with pause points |
| 8.8 | User Preference Onboarding | First-time setup flow for role, area order, detail level |
| 8.9 | Mem0 Preference Storage | Store and apply user preferences |

**Acceptance Criteria:**
- [ ] ElevenLabs TTS begins playback within 2 seconds
- [ ] Push-to-talk transcription completes within 2 seconds
- [ ] Briefing generation completes within 30 seconds
- [ ] Plant Managers see all areas; Supervisors see assigned assets only
- [ ] Numbers formatted for voice (e.g., "2.1 million" not "2,130,500")
- [ ] Users can pause and ask follow-up questions with cited answers
- [ ] Onboarding completes in under 2 minutes
- [ ] Preferences persist across sessions via Mem0

---

## Epic 9: Shift Handoff & EOD Summary

**Goal:** Enable persistent shift handoffs and close the accountability loop with End of Day summaries.

**Dependencies:** Epic 8 (Voice Briefing Foundation)

**User Value:** Outgoing supervisors can create comprehensive handoff records that incoming supervisors can review, question, and acknowledge. Plant Managers can compare morning predictions against actual outcomes.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 9.1 | Shift Handoff Trigger | Outgoing supervisor initiates handoff |
| 9.2 | Shift Data Synthesis | System synthesizes shift data via LangChain tools |
| 9.3 | Voice Note Attachment | Outgoing supervisor adds voice notes |
| 9.4 | Persistent Handoff Records | Store handoff for incoming supervisor |
| 9.5 | Handoff Review UI | Incoming supervisor views/listens to handoff |
| 9.6 | Handoff Q&A | Incoming supervisor asks follow-up questions |
| 9.7 | Acknowledgment Flow | Incoming supervisor acknowledges with notes |
| 9.8 | Handoff Notifications | Notify outgoing supervisor of acknowledgment |
| 9.9 | Offline Handoff Caching | Service worker caches handoffs for floor access |
| 9.10 | End of Day Summary Trigger | Plant Manager initiates EOD summary |
| 9.11 | Morning vs Actual Comparison | Compare morning predictions to outcomes |
| 9.12 | EOD Push Notification Reminders | Optional reminder for EOD summary |
| 9.13 | Admin UI - Asset Assignment | Assign supervisors to assets/areas |
| 9.14 | Admin UI - Role Management | Assign user roles |
| 9.15 | Admin Audit Logging | Log all configuration changes |

**Acceptance Criteria:**
- [ ] Outgoing supervisors can trigger handoff and add voice notes
- [ ] Handoff records persist and are viewable by incoming supervisor
- [ ] Incoming supervisors can ask follow-up questions with cited answers
- [ ] Acknowledgment creates audit trail; outgoing supervisor notified
- [ ] Handoffs cached locally for offline review
- [ ] EOD summary compares morning briefing to actual outcomes
- [ ] Push notification reminders delivered within 60 seconds
- [ ] Admins can assign supervisors to assets with preview
- [ ] All admin changes logged with audit trail
- [ ] 99.9% uptime during shift change windows (5-7 AM, 5-7 PM)
