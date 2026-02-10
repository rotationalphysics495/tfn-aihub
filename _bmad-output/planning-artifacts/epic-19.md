---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 19
status: "ready"
---

# Epic 19: Conversational AI Follow-Up

## Overview

**Goal:** Plant managers can ask follow-up questions about the smart summary directly in the AI chat, with morning report context pre-loaded — turning a static narrative into an interactive conversation.

**Dependencies:** Uses existing AI chat infrastructure (Epics 4-7)

**User Value:** "What was the root cause?" or "How does this compare to last week?" — answered without re-explaining context. The AI already knows what's in the morning report. Asset names in the summary become clickable links to asset detail pages.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I14 (Conversational Follow-Up on AI Summary) | Full |

## Stories

---

### Story 19.1: "Ask About This" Button on Smart Summary

**As a** Plant Manager reading the smart summary,
**I want** an "Ask about this" button that opens the AI chat pre-loaded with the morning report context,
**So that** I can ask follow-up questions without re-explaining what I'm looking at.

**Acceptance Criteria:**

**Given** the smart summary section is displayed on the morning report
**When** the user clicks "Ask about this"
**Then** the AI chat sidebar opens
**And** the chat is pre-loaded with context including:
  - The smart summary text
  - The current day's action items (categories, assets, metrics)
  - The date of the report being viewed
**And** a system message indicates: "I have the morning report context for {date}. Ask me anything about it."

**Given** the user types a question like "What was the root cause for Grinder 5?"
**When** the AI agent processes the query
**Then** the agent has access to the full `SummaryContext` (summary text, action items, evidence data)
**And** the response references specific data from the morning report
**And** citations link back to the relevant data sources

**Given** the user asks a question unrelated to the morning report
**When** the AI processes the query
**Then** the agent responds normally using its full tool suite
**And** the morning report context does not interfere with unrelated queries

**Technical Notes:**
- Pass `SummaryContext` object (summary text, action items, evidence) as conversation context when opening chat from the report
- The existing chat sidebar (`ChatSidebar.tsx`) accepts context — extend its props or use a context provider
- Modify the `/api/agent/query` request to include `report_context` when initiated from the morning report

**Files to Create/Modify:**
- `apps/web/src/components/action-list/MorningSummarySection.tsx` - Add "Ask about this" button
- `apps/web/src/components/chat/ChatSidebar.tsx` - Accept and pass report context
- `apps/web/src/app/morning-report/page.tsx` - Wire context from report data to chat
- `apps/api/app/api/agent.py` - Accept optional `report_context` in query request
- `apps/api/app/services/agent/executor.py` - Inject report context into agent system prompt

---

### Story 19.2: Clickable Asset Links in Smart Summary

**As a** Plant Manager reading the smart summary,
**I want** asset names mentioned in the summary to be clickable links,
**So that** I can quickly navigate to the asset's detail page or its action item.

**Acceptance Criteria:**

**Given** the smart summary text mentions an asset name (e.g., "Grinder 5")
**When** the summary is rendered
**Then** the asset name is displayed as a clickable link
**And** clicking it scrolls to or highlights that asset's action item on the current report

**Given** the smart summary mentions an asset that has an asset detail page
**When** the user clicks the asset name while holding Ctrl/Cmd
**Then** the asset detail page opens in a new tab

**Given** the summary text contains an asset name that doesn't match any known asset
**When** the summary renders
**Then** the text is rendered as plain text (no link)

**Technical Notes:**
- Post-process the summary markdown to identify and linkify known asset names
- Match against the list of asset names from the current report's action items
- Two click behaviors: default = scroll to action item on page, Ctrl+click = open asset detail
- Can use a regex replacement on the rendered markdown or a custom markdown renderer plugin

**Files to Create/Modify:**
- `apps/web/src/components/action-list/MorningSummarySection.tsx` - Add asset name linkification
- `apps/web/src/lib/linkifyAssets.ts` - Utility to find and linkify asset names in text

---

### Story 19.3: Context-Aware Follow-Up Suggestions

**As a** Plant Manager viewing the smart summary,
**I want** to see suggested follow-up questions relevant to today's report,
**So that** I know what to ask without thinking of questions from scratch.

**Acceptance Criteria:**

**Given** the smart summary is displayed
**When** the "Ask about this" button area renders
**Then** 2-3 contextual follow-up questions are shown as clickable chips below the button, e.g.:
  - "What were the top downtime reasons for Grinder 5?"
  - "How does today's OEE compare to last week?"
  - "What actions have been taken on recurring safety events?"

**Given** the user clicks a suggested question chip
**When** the chip is clicked
**Then** the AI chat sidebar opens with that question pre-filled and sent
**And** the report context is included (same as "Ask about this")

**Given** the smart summary content changes (different date or refreshed)
**When** the suggestions are generated
**Then** the suggestions update to reflect the new report content

**Technical Notes:**
- Generate suggestions from the SummaryContext: pick top action items and formulate questions
- Can be client-side logic (template-based) or server-side (LLM-generated)
- MVP: template-based using action item categories and asset names
- Use existing `FollowUpChips` component pattern from the chat

**Files to Create/Modify:**
- `apps/web/src/components/action-list/SuggestedQuestions.tsx` - Follow-up question chips
- `apps/web/src/components/action-list/MorningSummarySection.tsx` - Integrate suggestions below summary
- `apps/web/src/lib/generateSuggestions.ts` - Template-based question generation from report context
