TEST SPEC START
story_id: 19-1-ask-about-this-button-on-smart-summary
generated: 2026-02-12

test_specifications:

## AC1: "Ask about this" button visible on summary section — When the smart summary section is displayed on the morning report, an "Ask about this" button is rendered below the AI summary text (near the "Powered by AI analysis" label). The button uses the Industrial Clarity design system and is clearly associated with the summary content.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-001: "Ask about this" button renders when hasSummary is true
- Priority: P0
- Type: unit
- Given: The `useSmartSummary` hook returns `hasSummary=true`, `isSummaryLoading=false`, `isGenerating=false`, `summaryError=null`, and `smartSummary.summary_text` is a non-empty string
- When: The `MorningSummarySection` component renders
- Then: A button with text "Ask about this" is visible in the document, positioned below the AI summary text near the "Powered by AI analysis" label
- Data: Mock `useSmartSummary` returning `{ data: { summary_text: "3 safety events require attention. Grinder 5 OEE dropped to 62%.", is_fallback: false }, hasSummary: true, isLoading: false, isGenerating: false, error: null }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-002: Button has MessageSquare icon from lucide-react
- Priority: P1
- Type: unit
- Given: The smart summary is loaded and `hasSummary=true`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button contains an SVG icon element (the MessageSquare icon) adjacent to the button text
- Data: Same mock as UNIT-001

### 19-1-ask-about-this-button-on-smart-summary-UNIT-003: Button uses Industrial Clarity design system styling
- Priority: P1
- Type: unit
- Given: The smart summary is loaded and `hasSummary=true`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button renders with `variant="outline"` styling and info-blue accent (consistent with the Industrial Clarity design system), using compact size
- Data: Same mock as UNIT-001

## AC2: Chat sidebar opens with report context — Clicking the "Ask about this" button opens the existing ChatSidebar (the Radix Sheet overlay) and pre-loads the conversation with context including the smart summary text, current day's action items, the date of the report, and a system-level introductory message.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-004: ChatContextProvider exposes openChatWithContext function
- Priority: P0
- Type: unit
- Given: A component is wrapped in `ChatContextProvider`
- When: The component calls `useChatContext()`
- Then: The returned context object includes `openChatWithContext` as a function, `isOpen` as a boolean (initially `false`), and `reportContext` as `null`
- Data: Render a test consumer component inside `ChatContextProvider`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-005: openChatWithContext sets isOpen to true and stores report context
- Priority: P0
- Type: unit
- Given: A component has access to `useChatContext()` and `isOpen` is `false`
- When: `openChatWithContext({ summaryText: "Safety alert on Grinder 5", actionItems: [{ category: "safety", asset_name: "Grinder 5" }], reportDate: "2026-02-11" })` is called
- Then: `isOpen` becomes `true` and `reportContext` contains the passed `summaryText`, `actionItems`, and `reportDate`
- Data: ReportContext with summaryText, actionItems array, reportDate string

### 19-1-ask-about-this-button-on-smart-summary-UNIT-006: Clicking "Ask about this" calls openChatWithContext with correct data
- Priority: P0
- Type: unit
- Given: The `MorningSummarySection` renders with `hasSummary=true`, `smartSummary.summary_text="3 safety events detected. Grinder 5 OEE dropped to 62%."`, `useDailyActions` returns `data.actions` with 3 action items, and `data.report_date="2026-02-11"`
- When: The user clicks the "Ask about this" button
- Then: `openChatWithContext` is called once with an object containing `summaryText` (the cleaned summary text with citation tags removed), `actionItems` matching the action items from `useDailyActions`, and `reportDate="2026-02-11"`
- Data: Mock `useDailyActions` with actions: `[{ category: "safety", asset_name: "Grinder 5", primary_metric_value: 62 }, { category: "financial", asset_name: "Mixer-01", primary_metric_value: 15000 }, { category: "oee", asset_name: "Press-A", primary_metric_value: 78 }]`, report_date: "2026-02-11"

### 19-1-ask-about-this-button-on-smart-summary-INT-001: ChatSidebar opens when openChatWithContext is called
- Priority: P0
- Type: integration
- Given: The `ChatSidebar` component is mounted inside `ChatContextProvider` and the sidebar is closed (`isOpen=false`)
- When: `openChatWithContext` is called with valid report context
- Then: The ChatSidebar Sheet overlay becomes visible (the Radix Sheet opens with `open=true`)
- Data: ReportContext with summaryText, actionItems, reportDate

### 19-1-ask-about-this-button-on-smart-summary-INT-002: ChatSidebar displays system introductory message with report date
- Priority: P0
- Type: integration
- Given: The `ChatSidebar` is opened via `openChatWithContext` with `reportDate="2026-02-11"`
- When: The sidebar renders its message list
- Then: The first message displayed is a system/assistant message with content: "I have the morning report context for 2026-02-11. Ask me anything about it."
- Data: ReportContext with reportDate="2026-02-11"

### 19-1-ask-about-this-button-on-smart-summary-INT-003: ChatSidebar passes report_context in API requests to agent endpoint
- Priority: P0
- Type: integration
- Given: The `ChatSidebar` was opened via `openChatWithContext` with report context (summaryText, actionItems, reportDate), and a system intro message is displayed
- When: The user types "What was the root cause for Grinder 5?" and submits the message
- Then: The fetch call is made to `/api/agent/chat` (not `/api/chat/query`) with a JSON body containing `message: "What was the root cause for Grinder 5?"` and `report_context: { summary_text, action_items, report_date }` matching the original report context
- Data: Mock fetch, verify URL is `/api/agent/chat` and body contains `report_context` field

### 19-1-ask-about-this-button-on-smart-summary-INT-004: ChatSidebar without report context continues to use /api/chat/query
- Priority: P0
- Type: integration
- Given: The `ChatSidebar` was opened normally (via toggle/ChatTrigger) without any report context
- When: The user types "What is the OEE for Grinder 5?" and submits the message
- Then: The fetch call is made to `/api/chat/query` (not `/api/agent/chat`) with the normal request shape `{ question: "What is the OEE for Grinder 5?" }`
- Data: Mock fetch, verify URL is `/api/chat/query`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-007: Report context is cleared when user starts a new conversation
- Priority: P1
- Type: unit
- Given: The `ChatSidebar` is open with an active `reportContext` and the system intro message is displayed
- When: The user clicks a "Clear context" button or starts a new conversation
- Then: `reportContext` is set to `null`, the system intro message is removed, and subsequent API calls route to `/api/chat/query` instead of `/api/agent/chat`
- Data: Simulate clear context action, verify state reset

## AC3: Backend accepts optional report_context — The `/api/agent/chat` endpoint accepts an optional `report_context` field in the `AgentChatRequest` body. When present, the agent executor injects the report context into the system prompt.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-008: ReportContext Pydantic model validates correct input
- Priority: P0
- Type: unit
- Given: A valid `ReportContext` payload with `summary_text="3 safety events..."`, `action_items=[{"category": "safety", "asset_name": "Grinder 5"}]`, `report_date="2026-02-11"`
- When: The `ReportContext` model is instantiated
- Then: The model is created successfully with all fields matching the input values
- Data: `{ "summary_text": "3 safety events detected.", "action_items": [{"category": "safety", "asset_name": "Grinder 5", "primary_metric_value": 62}], "report_date": "2026-02-11" }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-009: AgentChatRequest accepts optional report_context field
- Priority: P0
- Type: unit
- Given: A valid `AgentChatRequest` payload with `message="What happened?"` and `report_context` containing valid ReportContext data
- When: The `AgentChatRequest` model is instantiated
- Then: The model is created successfully with `report_context` populated and all other fields at their defaults
- Data: `{ "message": "What happened?", "report_context": { "summary_text": "Summary text", "action_items": [], "report_date": "2026-02-11" } }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-010: AgentChatRequest works without report_context (backward compatible)
- Priority: P0
- Type: unit
- Given: A valid `AgentChatRequest` payload with only `message="What is OEE?"` and no `report_context` field
- When: The `AgentChatRequest` model is instantiated
- Then: The model is created successfully with `report_context=None`
- Data: `{ "message": "What is OEE?" }`

### 19-1-ask-about-this-button-on-smart-summary-INT-005: /api/agent/chat endpoint accepts request with report_context
- Priority: P0
- Type: integration
- Given: A valid JWT token and the agent is configured and initialized
- When: POST `/api/agent/chat` is called with body `{ "message": "Why did Grinder 5 fail?", "report_context": { "summary_text": "Grinder 5 OEE dropped to 62%", "action_items": [{"category": "oee", "asset_name": "Grinder 5"}], "report_date": "2026-02-11" } }`
- Then: The endpoint returns 200 OK with a valid `AgentResponse` body, and `agent.process_message()` was called with the `report_context` parameter
- Data: Mock agent returning a valid response, mock JWT verification

### 19-1-ask-about-this-button-on-smart-summary-INT-006: /api/agent/chat endpoint passes report_context to agent.process_message()
- Priority: P0
- Type: integration
- Given: A valid request with `report_context` is sent to `/api/agent/chat`
- When: The endpoint handler processes the request
- Then: `agent.process_message()` is called with keyword argument `report_context` matching the request's `report_context` value
- Data: Mock agent, inspect call args for `report_context` parameter

### 19-1-ask-about-this-button-on-smart-summary-INT-007: /api/agent/chat endpoint works without report_context (backward compatible)
- Priority: P0
- Type: integration
- Given: A valid JWT token and a request body with only `message="General question"` and no `report_context`
- When: POST `/api/agent/chat` is called
- Then: The endpoint returns 200 OK and `agent.process_message()` is called with `report_context=None`
- Data: Mock agent, verify process_message called without report_context

## AC4: Agent responds using report context — When the user types a question, the agent has access to the full SummaryContext and the response references specific data from the morning report. Citations link back to relevant data sources.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-011: process_message injects report context into agent input when provided
- Priority: P0
- Type: unit
- Given: `ManufacturingAgent` is initialized and `report_context` is provided with `summary_text="Grinder 5 OEE dropped to 62%. 2 safety events on Press-A."`, `action_items=[{"category": "oee", "asset_name": "Grinder 5", "primary_metric_value": 62}]`, `report_date="2026-02-11"`
- When: `process_message(message="Why did Grinder 5 fail?", user_id="user-1", report_context=report_context)` is called
- Then: The `_executor.ainvoke()` is called with an `input` value that contains the morning report context block including the summary text "Grinder 5 OEE dropped to 62%", the action items data, and the date "2026-02-11", prepended or appended to the user's question
- Data: Mock `_executor.ainvoke`, inspect the `input` key in the invocation args

### 19-1-ask-about-this-button-on-smart-summary-UNIT-012: Report context block includes formatted action items
- Priority: P1
- Type: unit
- Given: `report_context` with `action_items=[{"category": "safety", "asset_name": "Grinder 5", "primary_metric_value": 62, "recommendation_text": "Investigate bearing wear"}, {"category": "financial", "asset_name": "Mixer-01", "primary_metric_value": 15000}]`
- When: `process_message()` is called with this report context
- Then: The context block injected into the agent input contains formatted representations of both action items including their category, asset_name, primary_metric_value, and recommendation_text
- Data: Mock executor, inspect context block content

### 19-1-ask-about-this-button-on-smart-summary-UNIT-013: Report context block uses correct date in the header
- Priority: P1
- Type: unit
- Given: `report_context` with `report_date="2026-02-11"`
- When: `process_message()` is called with this report context
- Then: The injected context block contains the text "MORNING REPORT CONTEXT (for 2026-02-11)" or equivalent header with the correct date
- Data: Mock executor, inspect context block content for date string

### 19-1-ask-about-this-button-on-smart-summary-INT-008: Agent response references morning report data when context is provided
- Priority: P1
- Type: integration
- Given: The agent is initialized with a mock LLM, and a request is made with `report_context` containing specific asset data (Grinder 5 OEE 62%)
- When: `process_message(message="What was the root cause for Grinder 5?", report_context=report_context)` is called
- Then: The agent's input to the LLM includes the morning report context, enabling the LLM to reference "Grinder 5" and "62%" in its response
- Data: Mock LLM that echoes back its input, verify morning report data is present in the prompt

## AC5: Unrelated queries are unaffected — When the user asks a question unrelated to the morning report, the agent responds normally using its full tool suite. The morning report context does not interfere with unrelated queries.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-014: process_message does not inject context block when report_context is None
- Priority: P0
- Type: unit
- Given: `ManufacturingAgent` is initialized and `report_context` is `None` (not provided)
- When: `process_message(message="What is the current OEE for Plant A?", user_id="user-1", report_context=None)` is called
- Then: The `_executor.ainvoke()` is called with `input` equal to the user's message only — no "MORNING REPORT CONTEXT" block is prepended or appended
- Data: Mock `_executor.ainvoke`, inspect the `input` key to confirm no context block

### 19-1-ask-about-this-button-on-smart-summary-UNIT-015: Agent retains all tools when report context is present
- Priority: P0
- Type: unit
- Given: `ManufacturingAgent` is initialized with tools (e.g., asset_lookup, query_metrics) and `report_context` is provided
- When: `process_message()` is called with report context
- Then: The agent executor still has access to all registered tools — the tool list passed to the executor is unchanged from the no-context case
- Data: Compare tool list with and without report_context

### 19-1-ask-about-this-button-on-smart-summary-UNIT-016: Context block includes instruction to handle unrelated queries normally
- Priority: P1
- Type: unit
- Given: `report_context` is provided with valid data
- When: `process_message()` is called with this report context
- Then: The injected context block includes text instructing the agent to use standard tools for unrelated queries, e.g., "If the user's question is unrelated to the morning report, use your standard tools to answer."
- Data: Mock executor, inspect context block for unrelated-query instruction

### 19-1-ask-about-this-button-on-smart-summary-INT-009: Agent with report context can still answer unrelated questions
- Priority: P1
- Type: integration
- Given: The agent is initialized with report context about Grinder 5 OEE data
- When: `process_message(message="How many assets do we have in Plant B?", report_context=report_context)` is called
- Then: The agent does not error out, returns a valid `AgentResponse`, and the agent executor was invoked with access to its full tool suite
- Data: Mock LLM and tools, verify normal execution flow even with report_context present

## AC6: Button state handling — The button is disabled or hidden while the smart summary is loading, generating, or in an error state. It only appears when hasSummary is true.

### 19-1-ask-about-this-button-on-smart-summary-UNIT-017: Button is hidden when summary is loading
- Priority: P0
- Type: unit
- Given: `useSmartSummary` returns `isSummaryLoading=true`, `hasSummary=false`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button is NOT present in the document
- Data: Mock `useSmartSummary` with `{ isLoading: true, hasSummary: false, isGenerating: false, error: null }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-018: Button is hidden when summary is generating
- Priority: P0
- Type: unit
- Given: `useSmartSummary` returns `isGenerating=true`, `hasSummary=false`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button is NOT present in the document
- Data: Mock `useSmartSummary` with `{ isLoading: false, hasSummary: false, isGenerating: true, error: null }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-019: Button is hidden when summary has error
- Priority: P0
- Type: unit
- Given: `useSmartSummary` returns `summaryError=true`, `hasSummary=false`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button is NOT present in the document
- Data: Mock `useSmartSummary` with `{ isLoading: false, hasSummary: false, isGenerating: false, error: true }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-020: Button is hidden when hasSummary is false (no summary, no error)
- Priority: P0
- Type: unit
- Given: `useSmartSummary` returns `hasSummary=false`, `isSummaryLoading=false`, `isGenerating=false`, `summaryError=null`
- When: The `MorningSummarySection` component renders
- Then: The "Ask about this" button is NOT present in the document
- Data: Mock `useSmartSummary` with `{ isLoading: false, hasSummary: false, isGenerating: false, error: null, canGenerate: true }`

### 19-1-ask-about-this-button-on-smart-summary-UNIT-021: Button appears only when hasSummary transitions from false to true
- Priority: P1
- Type: unit
- Given: `useSmartSummary` initially returns `hasSummary=false, isLoading=true`, then updates to `hasSummary=true, isLoading=false` with valid summary data
- When: The `MorningSummarySection` component re-renders after the state transition
- Then: The "Ask about this" button becomes visible only after `hasSummary` is `true`
- Data: Mock `useSmartSummary` with sequential return values simulating loading to loaded transition

edge_cases:
  - Empty summary text: `smartSummary.summary_text` is an empty string but `hasSummary` is somehow `true` — button should still render but openChatWithContext passes empty summaryText
  - Very long summary text: summary_text exceeds 5000 characters — verify the report_context payload does not cause API request failures or system prompt overflow
  - Empty action items array: `useDailyActions` returns `data.actions=[]` — button still works and report_context.action_items is an empty list
  - Special characters in summary text: summary_text contains markdown, unicode, or special characters — verify they are passed through cleanly without corruption
  - Multiple rapid clicks: User clicks "Ask about this" multiple times quickly — only one sidebar open event should fire, no duplicate context injection
  - Stale context after date navigation: User opens chat with context for Feb 11, then navigates to Feb 10 report without closing chat — context remains for Feb 11 (documented known behavior)
  - Report context with citation tags: smartSummary.summary_text contains [Source: table, date] citation tags — verify cleanSummaryText strips them before passing to report context
  - ChatSidebar already open: If the sidebar is already open (from ChatTrigger) when user clicks "Ask about this" — should replace/update context and show new intro message

error_scenarios:
  - Network failure on agent chat: When report context is active and the API call to /api/agent/chat fails with a network error, the ChatSidebar should display an error message with retry capability
  - Agent not configured (503): When /api/agent/chat returns 503 because the agent is not configured, the ChatSidebar should display an appropriate error message
  - Rate limit exceeded (429): When /api/agent/chat returns 429, the ChatSidebar should display a rate limit message and retry-after information
  - Invalid report_context schema: Backend receives a report_context with missing required fields (e.g., no summary_text) — Pydantic validation returns 422
  - Agent timeout: The agent takes longer than the request timeout to respond — ChatSidebar handles the timeout gracefully with an error message
  - Supabase auth failure: When the ChatSidebar tries to get a Supabase session for the agent endpoint but fails — appropriate auth error displayed

test_file_mapping:
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-001 to UNIT-003: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-004 to UNIT-005: apps/web/src/components/chat/__tests__/ChatContextProvider.test.tsx
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-006 to UNIT-007: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
  - 19-1-ask-about-this-button-on-smart-summary-INT-001 to INT-004: apps/web/src/components/chat/__tests__/ChatSidebar.test.tsx
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-008 to UNIT-010: apps/api/tests/models/test_agent_models.py
  - 19-1-ask-about-this-button-on-smart-summary-INT-005 to INT-007: apps/api/tests/api/test_agent_api.py
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-011 to UNIT-013: apps/api/tests/services/agent/test_executor.py
  - 19-1-ask-about-this-button-on-smart-summary-INT-008 to INT-009: apps/api/tests/services/agent/test_executor.py
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-014 to UNIT-016: apps/api/tests/services/agent/test_executor.py
  - 19-1-ask-about-this-button-on-smart-summary-UNIT-017 to UNIT-021: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx

TEST SPEC END
