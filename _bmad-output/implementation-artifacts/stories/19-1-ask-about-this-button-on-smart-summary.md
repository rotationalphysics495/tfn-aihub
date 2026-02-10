# Story 19.1: "Ask About This" Button on Smart Summary

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager reading the smart summary,
I want an "Ask about this" button that opens the AI chat pre-loaded with the morning report context,
so that I can ask follow-up questions without re-explaining what I'm looking at.

## Acceptance Criteria

1. **"Ask about this" button visible on summary section** -- When the smart summary section is displayed on the morning report, an "Ask about this" button is rendered below the AI summary text (near the "Powered by AI analysis" label). The button uses the Industrial Clarity design system and is clearly associated with the summary content.

2. **Chat sidebar opens with report context** -- Clicking the "Ask about this" button opens the existing `ChatSidebar` (the Radix Sheet overlay) and pre-loads the conversation with context including:
   - The smart summary text (cleaned, from `smartSummary.summary_text`)
   - The current day's action items (categories, asset names, metric values from `useDailyActions`)
   - The date of the report being viewed (the T-1 date string)
   - A system-level introductory message: "I have the morning report context for {date}. Ask me anything about it."

3. **Backend accepts optional report_context** -- The `/api/agent/chat` endpoint accepts an optional `report_context` field in the `AgentChatRequest` body. When present, the agent executor injects the report context into the system prompt so the LLM can reference specific morning report data when answering follow-up questions.

4. **Agent responds using report context** -- When the user types a question like "What was the root cause for Grinder 5?", the agent has access to the full `SummaryContext` (summary text, action items, evidence data) and the response references specific data from the morning report. Citations link back to the relevant data sources.

5. **Unrelated queries are unaffected** -- When the user asks a question unrelated to the morning report, the agent responds normally using its full tool suite. The morning report context does not interfere with unrelated queries (i.e., it is additive context, not a restrictive filter).

6. **Button state handling** -- The button is disabled or hidden while the smart summary is loading, generating, or in an error state. It only appears when `hasSummary` is `true`.

## Tasks / Subtasks

- [ ] Task 1: Create ChatContext provider for cross-component communication (AC: #2)
  - [ ] 1.1 Create `apps/web/src/components/chat/ChatContextProvider.tsx` with React Context that exposes `openChatWithContext(context: ReportContext)` and `isOpen` state
  - [ ] 1.2 Define `ReportContext` interface: `{ summaryText: string; actionItems: ActionItem[]; reportDate: string; }`
  - [ ] 1.3 Wrap `ChatSidebar` state management to use the context provider
  - [ ] 1.4 Mount `ChatContextProvider` in `apps/web/src/app/layout.tsx` wrapping both `{children}` and `<ChatSidebar />`
  - [ ] 1.5 Export context hook `useChatContext()` from `apps/web/src/components/chat/index.ts`

- [ ] Task 2: Add "Ask about this" button to MorningSummarySection (AC: #1, #6)
  - [ ] 2.1 Import `useChatContext` in `apps/web/src/components/action-list/MorningSummarySection.tsx`
  - [ ] 2.2 Add a `MessageSquare` (lucide) + "Ask about this" button below the AI summary text, next to "Powered by AI analysis"
  - [ ] 2.3 Style with Industrial Clarity: `variant="outline"` using info-blue accent, compact size
  - [ ] 2.4 On click, call `openChatWithContext()` passing the summary text, action items from `useDailyActions`, and the report date
  - [ ] 2.5 Conditionally render: only when `hasSummary` is `true` and not loading/generating/error

- [ ] Task 3: Modify ChatSidebar to accept and use report context (AC: #2)
  - [ ] 3.1 Update `ChatSidebar` to consume `useChatContext()` instead of local `isOpen` state
  - [ ] 3.2 When `reportContext` is provided, inject a system message as the first message: "I have the morning report context for {date}. Ask me anything about it."
  - [ ] 3.3 Pass `report_context` in the API request body when sending messages while report context is active
  - [ ] 3.4 Clear report context when the user explicitly starts a new conversation (optional: add a "Clear context" chip or button)

- [ ] Task 4: Extend AgentChatRequest model with report_context (AC: #3)
  - [ ] 4.1 Add `report_context` optional field to `AgentChatRequest` in `apps/api/app/models/agent.py` with Pydantic schema: `Optional[ReportContext]` containing `summary_text: str`, `action_items: List[Dict]`, `report_date: str`
  - [ ] 4.2 Create `ReportContext` Pydantic model in `apps/api/app/models/agent.py`

- [ ] Task 5: Inject report context into agent system prompt (AC: #4, #5)
  - [ ] 5.1 Modify `apps/api/app/api/agent.py` chat endpoint to pass `report_context` through to `agent.process_message()`
  - [ ] 5.2 Update `ManufacturingAgent.process_message()` in `apps/api/app/services/agent/executor.py` to accept optional `report_context` parameter
  - [ ] 5.3 When `report_context` is present, append a context block to the system prompt: "MORNING REPORT CONTEXT ({date}): {summary_text}\n\nACTION ITEMS: {formatted_items}\n\nUse this context to answer follow-up questions about today's morning report."
  - [ ] 5.4 Ensure the context is additive -- the agent still has access to all its tools and can handle unrelated queries

- [ ] Task 6: Write tests (AC: #1-6)
  - [ ] 6.1 Frontend: test "Ask about this" button renders only when summary is available
  - [ ] 6.2 Frontend: test clicking button opens chat with context message
  - [ ] 6.3 Backend: test `/api/agent/chat` accepts and passes `report_context`
  - [ ] 6.4 Backend: test agent system prompt includes report context when provided
  - [ ] 6.5 Backend: test agent handles queries normally when no report context is provided

## Dev Notes

### Architecture Pattern: Cross-Component Communication

The key challenge is that `MorningSummarySection` (in `action-list/`) needs to open and configure `ChatSidebar` (in `chat/`), which is mounted at the root layout level. These components have no parent-child relationship.

**Solution: React Context Provider**

The `ChatSidebar` is currently mounted in `apps/web/src/app/layout.tsx` as a global component with entirely local state (`useState` for `isOpen`, `messages`, etc.). To allow `MorningSummarySection` to open the sidebar with pre-loaded context, introduce a `ChatContextProvider` that:
1. Holds the `isOpen` state and `reportContext` state
2. Exposes `openChatWithContext(context)` to any descendant
3. Is consumed by `ChatSidebar` to react to external open requests

This pattern is already established in the codebase with `ThemeProvider` wrapping the app. The `ChatContextProvider` follows the same pattern.

**CRITICAL: Do NOT create a separate chat endpoint or duplicate the sidebar.** The existing `ChatSidebar` and `/api/agent/chat` endpoint must be extended, not replaced.

### Frontend File Changes

| File | Change |
|------|--------|
| `apps/web/src/components/chat/ChatContextProvider.tsx` | **NEW** - React Context for chat state + report context |
| `apps/web/src/components/chat/ChatSidebar.tsx` | **MODIFY** - Consume context provider, handle report context in messages and API calls |
| `apps/web/src/components/chat/types.ts` | **MODIFY** - Add `ReportContext` interface |
| `apps/web/src/components/chat/index.ts` | **MODIFY** - Export new provider and hook |
| `apps/web/src/components/action-list/MorningSummarySection.tsx` | **MODIFY** - Add "Ask about this" button |
| `apps/web/src/app/layout.tsx` | **MODIFY** - Wrap with `ChatContextProvider` |

### Backend File Changes

| File | Change |
|------|--------|
| `apps/api/app/models/agent.py` | **MODIFY** - Add `ReportContext` model and `report_context` field to `AgentChatRequest` |
| `apps/api/app/api/agent.py` | **MODIFY** - Pass `report_context` to agent |
| `apps/api/app/services/agent/executor.py` | **MODIFY** - Accept `report_context`, inject into system prompt |

### Existing Component Details

**`ChatSidebar` current state (from `apps/web/src/components/chat/ChatSidebar.tsx`):**
- Uses Radix `Sheet` component with `side="right"`, 400px width
- State: `isOpen`, `messages`, `inputValue`, `isLoading`, `lastFailedMessage` -- all local `useState`
- Sends to `POST ${apiBaseUrl}/api/chat/query` with `{ question: messageContent }`
- Welcome message from `WELCOME_MESSAGE` constant
- No external open mechanism currently exists

**`MorningSummarySection` current state (from `apps/web/src/components/action-list/MorningSummarySection.tsx`):**
- Uses `useDailyActions()` for action data and summary counts
- Uses `useSmartSummary()` for AI summary text
- `hasSummary` boolean available for conditional rendering
- `smartSummary.summary_text` contains the raw AI narrative
- `cleanSummaryText()` function strips citation tags for display
- Summary footer currently shows "Powered by AI analysis" text -- the button should go near here

**`AgentChatRequest` current state (from `apps/api/app/models/agent.py`):**
- Fields: `message` (str), `context` (Optional[QueryContext]), `chat_history` (Optional[List[ChatMessage]]), `force_refresh` (bool)
- `QueryContext` already exists with fields like `asset_focus`, `time_range`, `metric_focus` -- but it's designed for tool hints, not full report context
- The new `report_context` should be a separate field, not shoehorned into `QueryContext`

**`ManufacturingAgent.process_message()` current state (from `apps/api/app/services/agent/executor.py`):**
- Accepts: `message`, `user_id`, `chat_history`, `force_refresh`
- System prompt is defined as `AGENT_SYSTEM_PROMPT` module constant with `{tool_descriptions}` placeholder
- Prompt is constructed in `_create_agent()` via `ChatPromptTemplate.from_messages()`
- To inject report context, the simplest approach is to append it to the `input` field as a prefix or modify the system prompt dynamically

**IMPORTANT: The `ChatSidebar` currently calls `POST /api/chat/query` (the text-to-SQL endpoint), NOT `POST /api/agent/chat`.** The chat endpoint handler is in `apps/web/src/components/chat/ChatSidebar.tsx` line 170. When report context is active, the request should route to `/api/agent/chat` instead, since the agent endpoint has the full tool suite. Alternatively, the `report_context` can be appended to the `/api/chat/query` request. The recommended approach is to use the agent endpoint when report context is present.

### System Prompt Injection Pattern

When `report_context` is provided, append this block to the system prompt:

```
---
MORNING REPORT CONTEXT (for {report_date}):

SUMMARY:
{summary_text}

ACTION ITEMS:
{formatted_action_items}

Use the above morning report context when answering follow-up questions. Reference specific data points, asset names, and metrics from this context. If the user's question is unrelated to the morning report, use your standard tools to answer.
---
```

This approach keeps the context additive and non-restrictive per AC #5.

### Project Structure Notes

- All new frontend files go under `apps/web/src/components/chat/` except the button which is added to the existing `MorningSummarySection.tsx`
- Backend changes are limited to the existing `apps/api/app/` structure
- No new API routes needed -- the existing `/api/agent/chat` endpoint is extended
- No database changes required
- No new dependencies required -- `lucide-react` (for `MessageSquare` icon) and React Context are already available

### Testing Standards

- **Frontend:** Vitest + Testing Library. Test files go in `__tests__/` subdirectory of the component folder. See existing patterns in `apps/web/src/components/chat/__tests__/`.
- **Backend:** Pytest. Test files go in `apps/api/tests/`. See `apps/api/tests/services/` for service tests.
- Test the context provider in isolation, then test integration with ChatSidebar.

### References

- [Source: docs/architecture-web.md#AI-Chat-System] -- ChatSidebar architecture, Sheet overlay pattern, FollowUpChips component
- [Source: docs/architecture-web.md#Component-Architecture] -- action-list component category, chat component category
- [Source: docs/architecture-web.md#Root-Layout] -- Global ChatSidebar mounting in layout.tsx
- [Source: docs/architecture-api.md#Agent-Executor] -- LangChain AgentExecutor, system prompt, tool orchestration
- [Source: docs/architecture-api.md#AI-Routes] -- `/api/agent` router prefix for agent queries
- [Source: _bmad-output/planning-artifacts/epic-19.md#Story-19.1] -- Full acceptance criteria and technical notes
- [Source: docs/improvements.md#Conversational-follow-up-on-AI-summary] -- Product requirements and context injection approach

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
