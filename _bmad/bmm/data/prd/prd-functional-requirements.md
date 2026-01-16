# PRD: Functional Requirements

**Parent Document:** [prd.md](../prd.md)

---

## Data & Foundation (FR1-FR5)

| ID | Requirement |
|----|-------------|
| FR1 | Ingest T-1 (Yesterday) and T-15m (Live) data from SQL Server for Output, OEE, Downtime, Quality, and Labor |
| FR2 | Maintain a relational Plant Object Model linking Assets to Cost Centers to Staffing Lines |
| FR3 | Generate a natural-language Daily Action List prioritizing issues based on Financial Impact and Safety Risk |
| FR4 | Immediate visual "Red" alerting for any "Safety Issue" reason code |
| FR5 | Translate operational losses (waste, downtime) into estimated dollar values using standard costs |

---

## AI Chat & Memory (FR6)

| ID | Requirement |
|----|-------------|
| FR6 | Provide a chat interface that remembers past context (via Mem0) to answer specific queries |

---

## AI Agent Tools (FR7)

The AI Chat interface SHALL provide specialized tools for common plant manager queries:

### FR7.1: Core Operations Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Asset Lookup | Retrieve asset metadata, current status, and recent performance | Asset name or ID | Asset details, current state, 7-day performance summary |
| OEE Query | Calculate OEE with breakdown by component | Area, asset, or plant-wide; time range | OEE percentage, availability, performance, quality breakdown |
| Downtime Analysis | Investigate downtime reasons and patterns | Asset or area; time range | Downtime reasons ranked by duration, Pareto distribution |
| Production Status | Real-time output vs target across assets | Area filter (optional) | Current output, target, variance, status per asset |

### FR7.2: Safety & Financial Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Safety Events | Query safety incidents | Time range; severity filter (optional) | Events with severity, resolution status, affected assets |
| Financial Impact | Calculate cost of downtime/waste | Asset or area; time range | Dollar loss breakdown by category |
| Cost of Loss | Rank issues by financial impact | Time range | Prioritized list of losses with root causes |

### FR7.3: Intelligence & Memory Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Trend Analysis | Time-series performance analysis | Asset; metric; time range (7-90 days) | Trend direction, anomalies, comparison to baseline |
| Memory Recall | Retrieve relevant conversation history | Topic or asset reference | Previous discussions, decisions, context |
| Comparative Analysis | Side-by-side asset/area comparison | Two or more assets/areas; metrics | Comparison table with variance highlighting |

### FR7.4: Proactive Action Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Action List | Get prioritized daily actions | Date (default: today) | Ranked action items with evidence and impact |
| Alert Check | Query active warnings/issues | Severity filter (optional) | Active alerts with status and recommended response |
| Recommendation Engine | Suggest improvements based on patterns | Asset or area; focus area (OEE, safety, cost) | Specific recommendations with supporting evidence |

---

## Voice & Briefing Delivery (FR8-FR13)

| ID | Requirement |
|----|-------------|
| FR8 | Users can receive briefings via voice (ElevenLabs TTS) or text display based on preference |
| FR9 | Users can use push-to-talk to ask follow-up questions during briefings |
| FR10 | System can convert voice input to text for processing (STT) |
| FR11 | System can deliver briefings in area-by-area sequential format with pause points |
| FR12 | Users can continue to next area via voice command, button, or silence detection (3-4 seconds) |
| FR13 | System can display text transcript alongside voice delivery |

---

## Morning Briefing Workflow (FR14-FR20)

| ID | Requirement |
|----|-------------|
| FR14 | Plant Managers can trigger a morning briefing that covers all plant areas |
| FR15 | Supervisors can trigger a morning briefing that covers only their assigned assets |
| FR16 | System can synthesize overnight production data into a narrative briefing |
| FR17 | System can identify and highlight top wins (areas exceeding targets) |
| FR18 | System can identify and highlight top concerns (areas with gaps or issues) |
| FR19 | System can format numbers for voice delivery (e.g., "2.1 million" not "2,130,500") |
| FR20 | Users can ask follow-up questions during briefings and receive cited answers |

---

## Shift Handoff Workflow (FR21-FR30)

| ID | Requirement |
|----|-------------|
| FR21 | Outgoing supervisors can trigger a shift handoff |
| FR22 | System can synthesize shift data into a handoff summary via LangChain tools |
| FR23 | Outgoing supervisors can add voice notes to handoff records |
| FR24 | System can create persistent handoff records for incoming supervisors |
| FR25 | Incoming supervisors can review handoff records (view, listen) |
| FR26 | Incoming supervisors can ask follow-up questions about handoff content |
| FR27 | Incoming supervisors can acknowledge receipt of handoff |
| FR28 | System can notify outgoing supervisors when handoff is acknowledged |
| FR29 | Incoming supervisors can add notes to acknowledgment |
| FR30 | System can cache handoff records for offline review on tablets |

---

## End of Day Summary Workflow (FR31-FR34)

| ID | Requirement |
|----|-------------|
| FR31 | Plant Managers can trigger an end of day summary |
| FR32 | System can compare morning briefing predictions against actual day outcomes |
| FR33 | System can generate feedback on prediction accuracy (flagged concerns that materialized) |
| FR34 | System can send push notification reminders for EOD summary |

---

## User Preferences & Personalization (FR35-FR41)

| ID | Requirement |
|----|-------------|
| FR35 | Users can set their role (Plant Manager or Supervisor) |
| FR36 | Users can set their preferred area order for briefings |
| FR37 | Users can set their preferred detail level (Summary or Detailed) |
| FR38 | Users can enable or disable voice delivery |
| FR39 | Supervisors can set their preferred asset order within assigned areas |
| FR40 | System can store user preferences in Mem0 |
| FR41 | System can apply stored preferences to all future briefings |

---

## User Onboarding (FR42-FR45)

| ID | Requirement |
|----|-------------|
| FR42 | System can detect first-time users and trigger onboarding flow |
| FR43 | Users can complete onboarding in under 2 minutes |
| FR44 | System can guide users through role, area order, detail level, and voice preferences |
| FR45 | Users can modify preferences after onboarding via Settings |

---

## Admin & Configuration (FR46-FR50)

| ID | Requirement |
|----|-------------|
| FR46 | Admins can assign supervisors to specific assets/areas |
| FR47 | Admins can assign user roles (Plant Manager, Supervisor, Admin) |
| FR48 | Admins can preview assignment impact ("User will see X assets across Y areas") |
| FR49 | Admins can temporarily reassign assets for coverage changes |
| FR50 | System can maintain audit log of all assignment changes |

---

## Data & Citations (FR51-FR54)

| ID | Requirement |
|----|-------------|
| FR51 | All briefing content must cite source data with timestamps |
| FR52 | All Q&A responses must include citations to source tables and queries |
| FR53 | System can aggregate data from all 7 production areas |
| FR54 | System can scope data to supervisor's assigned assets only |

---

## Audit & Compliance (FR55-FR57)

| ID | Requirement |
|----|-------------|
| FR55 | System can maintain audit trail of shift handoffs with acknowledgments |
| FR56 | System can log all admin configuration changes |
| FR57 | System can track morning prediction accuracy via EOD feedback loop |
