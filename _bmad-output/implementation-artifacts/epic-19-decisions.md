# Epic 19 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 19
**Started:** 2026-02-12 11:25:09

---


## DESIGN: 19-1-ask-about-this-button-on-smart-summary
**Timestamp:** 2026-02-12 11:30:20

DESIGN START
story_id: 19-1-ask-about-this-button-on-smart-summary

files_to_modify:
  - path: apps/web/src/components/chat/ChatContextProvider.tsx
    action: create
    purpose: React Context provider to enable cross-component communication between MorningSummarySection and ChatSidebar. Exposes openChatWithContext(context) and reportContext state. Manages isOpen state that was previously local to ChatSidebar.

  - path: apps/web/src/components/chat/types.ts
    action: modify
    purpose: Add ReportContext interface (summaryText, actionItems, reportDate) and extend ChatState with openWithContext method

  - path: apps/web/src/components/chat/index.ts
    action: modify
    purpose: Export ChatContextProvider, useChatContext hook, and ReportContext type

  - path: apps/web/src/components/chat/ChatSidebar.tsx
    action: modify
    purpose: Consume useChatContext() for isOpen/reportContext state instead of local useState. When reportContext is present, inject system intro message and route API calls to /api/agent/chat with report_context payload instead of /api/chat/query. Add "Clear context" mechanism when starting new conversation.

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Add "Ask about this" button with MessageSquare icon below the "Powered by AI analysis" text. Button calls openChatWithContext() passing summary text, action items, and report date. Conditionally rendered only when hasSummary is true.

  - path: apps/web/src/app/layout.tsx
    action: modify
    purpose: Wrap ServiceWorkerProvider contents with ChatContextProvider so both {children} and ChatSidebar can access the chat context

  - path: apps/api/app/models/agent.py
    action: modify
    purpose: Add ReportContext Pydantic model (summary_text: str, action_items: List[Dict], report_date: str) and add optional report_context field to AgentChatRequest

  - path: apps/api/app/api/agent.py
    action: modify
    purpose: Pass request.report_context through to agent.process_message() call

  - path: apps/api/app/services/agent/executor.py
    action: modify
    purpose: Accept optional report_context parameter in process_message(). When present, prepend a morning report context block to the input message so the LLM has the summary, action items, and date available. The context is additive — the agent retains full tool access for unrelated queries.

patterns_to_use:
  - React Context Provider: Same pattern as ThemeProvider in layout.tsx — create a context with provider component and useChatContext() hook, mount at layout level
  - Existing ChatSidebar Sheet pattern: Extend the existing Sheet overlay, don't duplicate it. Lift isOpen state from local useState into the context provider
  - Dual API routing: When reportContext is active, ChatSidebar sends to /api/agent/chat (agent endpoint with full tool suite) instead of /api/chat/query (text-to-SQL). When no context, behavior remains unchanged on /api/chat/query
  - System prompt context injection: Append morning report data as a context block to the agent's input message (prepended to the user question), keeping it additive per AC#5
  - Industrial Clarity design system: Button uses variant="outline" with info-blue accent, MessageSquare icon, compact size

dependencies:
  - lucide-react: installed (already used for MessageSquare, Bot, Sparkles, etc.)
  - react: installed (Context API)
  - @radix-ui/react-dialog: installed (Sheet component)
  - pydantic: installed (backend models)
  - langchain: installed (agent executor)

acceptance_criteria_mapping:
  - AC1 ("Ask about this" button visible on summary section):
    - MorningSummarySection.tsx — Add Button with MessageSquare icon below the AI summary text, next to "Powered by AI analysis" (line ~285-287). Style with Industrial Clarity variant="outline" and info-blue accent.
  - AC2 (Chat sidebar opens with report context):
    - ChatContextProvider.tsx — openChatWithContext(context) sets reportContext state and opens sidebar
    - ChatSidebar.tsx — Reads reportContext from useChatContext(). When reportContext is set, injects system message: "I have the morning report context for {date}. Ask me anything about it." as the first message. Passes report_context in API requests to /api/agent/chat.
    - MorningSummarySection.tsx — onClick handler calls openChatWithContext({ summaryText: cleanSummaryText(smartSummary.summary_text), actionItems: data.actions, reportDate: data.report_date })
  - AC3 (Backend accepts optional report_context):
    - models/agent.py — New ReportContext model + optional report_context field on AgentChatRequest
    - api/agent.py — Passes report_context to agent.process_message()
  - AC4 (Agent responds using report context):
    - executor.py — process_message() accepts report_context parameter. When present, prepends a context block to the input: "MORNING REPORT CONTEXT ({date}): {summary}\nACTION ITEMS: {items}\nUse this context when answering." The LLM can reference specific data points from the summary and action items.
  - AC5 (Unrelated queries unaffected):
    - executor.py — Context is prepended as additional context to the input message, not replacing the system prompt. Agent retains all tools. The context block explicitly states "If the user's question is unrelated to the morning report, use your standard tools to answer."
  - AC6 (Button state handling):
    - MorningSummarySection.tsx — Button is conditionally rendered: only appears within the `hasSummary && !isSummaryLoading && !isGenerating && !summaryError` block (the existing "Real AI summary" section, line 278). This means it's hidden during loading, generating, and error states.

risks:
  - State lifting from ChatSidebar: Moving isOpen from local useState to context could break the ChatTrigger toggle behavior. Mitigation: ChatContextProvider exposes the same open/close/toggle interface. ChatTrigger's onClick calls context.open() instead of the local handler. Test thoroughly.
  - Dual API endpoint routing: ChatSidebar currently calls /api/chat/query; with report context it must call /api/agent/chat with a different request shape (message vs question, report_context field). Mitigation: Use a conditional in sendMessage() that checks if reportContext is active to decide endpoint and payload shape.
  - Agent response format mismatch: /api/agent/chat returns AgentResponse (content, citations, suggested_questions) while /api/chat/query returns ChatApiResponse (answer, citations, suggestions, meta). The ChatSidebar already maps ChatApiResponse fields; it will need a second mapping path for AgentResponse format. Mitigation: Add an AgentApiResponse interface and a branching path in the response handler.
  - Context stale state: If user navigates to a different date while chat is open with old context, the context becomes stale. Mitigation: Document this as known behavior; the context represents the report the user clicked from. User can clear context to start fresh.
  - System prompt size: Injecting full summary + all action items could be large. Mitigation: Truncate action items to key fields (asset_name, category, primary_metric_value, recommendation_text) and cap at a reasonable size.

estimated_test_files:
  - apps/web/src/components/chat/__tests__/ChatContextProvider.test.tsx: Test context provider — openChatWithContext sets state, isOpen toggles, reportContext cleared on new conversation
  - apps/web/src/components/chat/__tests__/ChatSidebar.test.tsx: Test ChatSidebar consumes context, displays system message when reportContext is active, routes to agent endpoint with report_context
  - apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx: Extend existing tests — "Ask about this" button renders only when hasSummary=true, button calls openChatWithContext with correct data, button hidden during loading/error states
  - apps/api/tests/test_agent_api.py: Extend existing tests — /api/agent/chat accepts report_context field, passes it to agent, returns normal response
  - apps/api/tests/services/agent/test_executor.py: Extend existing tests — process_message with report_context prepends context to input, without report_context behavior unchanged

implementation_order:
  1. Define ReportContext interface in apps/web/src/components/chat/types.ts
  2. Create ChatContextProvider.tsx with React Context, provider component, and useChatContext hook
  3. Update apps/web/src/components/chat/index.ts to export new provider, hook, and type
  4. Update apps/web/src/app/layout.tsx to wrap with ChatContextProvider
  5. Modify ChatSidebar.tsx to consume useChatContext() — lift isOpen state to context, add reportContext-aware system message injection, add conditional routing to /api/agent/chat when reportContext is active, add AgentApiResponse interface and response mapping
  6. Add "Ask about this" button to MorningSummarySection.tsx — import useChatContext, add button in the hasSummary section near "Powered by AI analysis", wire onClick to openChatWithContext
  7. Add ReportContext Pydantic model and report_context field to AgentChatRequest in apps/api/app/models/agent.py
  8. Pass report_context through in apps/api/app/api/agent.py chat endpoint
  9. Modify process_message() in executor.py to accept report_context and prepend context block to the input when present
  10. Write frontend tests (ChatContextProvider, ChatSidebar context integration, MorningSummarySection button)
  11. Write backend tests (API accepts report_context, executor injects context, normal flow unaffected)
DESIGN END

---

## DESIGN: 19-2-clickable-asset-links-in-smart-summary
**Timestamp:** 2026-02-13 07:29:14

DESIGN START
story_id: 19-2-clickable-asset-links-in-smart-summary

files_to_modify:
  - path: apps/web/src/lib/linkifyAssets.ts
    action: create
    purpose: New utility module containing linkifyAssetNames() and extractAssetNames() functions. linkifyAssetNames takes summary text and known asset names, returns text with [[ASSET:name]] marker tokens embedded. extractAssetNames extracts unique asset names from action item arrays. Sorting by name length descending prevents partial matches (e.g., "CAMA 2400" matched before "CAMA"). Case-insensitive matching preserves original case.

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Wire linkification into the existing ReactMarkdown rendering. Import linkifyAssetNames and extractAssetNames from lib/linkifyAssets. Build an assetName→actionId lookup map from data.actions. Pre-process cleanSummaryText output through linkifyAssetNames before passing to ReactMarkdown. Add a custom `components` prop to ReactMarkdown with a custom text renderer that splits text nodes on [[ASSET:name]] markers and renders them as clickable <button> elements. Default click scrolls to the matching InsightEvidenceCard via data-asset-name attribute. Ctrl/Cmd+click opens /morning-report/action/{actionId} in a new tab.

  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Add data-asset-name={item.asset.name} and id={`action-${item.id}`} attributes to the root <Card> element so that asset link clicks in the summary can scroll to and highlight the target card. Add a CSS animation keyframe class for a brief highlight flash when scrolled to.

  - path: apps/web/src/components/action-engine/ActionCardList.tsx
    action: modify
    purpose: Pass through the data-asset-name attribute on the wrapper <div role="listitem"> so that the InsightEvidenceCard's scroll target attributes are accessible from the card list context. Alternatively, the attribute on the Card element inside InsightEvidenceCard may suffice — verify during implementation that scrollIntoView targets correctly.

  - path: apps/web/src/__tests__/linkifyAssets.test.ts
    action: create
    purpose: Unit tests for the linkifyAssets utility — matching known assets, non-matching names rendered as plain text, partial match prevention (longer name matched first), case-insensitive matching with case preservation, empty inputs, special regex characters in asset names.

  - path: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
    action: modify
    purpose: Add tests for asset link rendering — verify matched asset names render as clickable elements, verify unmatched names render as plain text, verify click triggers scrollIntoView, verify Ctrl+click calls window.open.

patterns_to_use:
  - ReactMarkdown custom components prop: Follow the exact pattern from ChatMessage.tsx lines 167-233 where custom renderers are passed via the components prop. Add a custom `p` renderer that processes children to detect and replace [[ASSET:name]] marker tokens with interactive elements.
  - Marker token approach: Pre-process text to embed [[ASSET:name]] tokens, then let ReactMarkdown parse the markdown normally, then the custom text/p renderer splits on the token pattern and renders interactive elements. This avoids interfering with markdown syntax.
  - Link styling: Use text-info-blue hover:underline cursor-pointer matching ChatMessage.tsx line 208-209 for consistent link appearance.
  - Data attribute scroll targeting: Use data-asset-name attributes on card elements (similar to data-acknowledgment-tracking used in InsightEvidenceCardList.tsx line 90) for querySelector-based scroll targeting.
  - Utility in lib/ folder: Follow existing pattern of apps/web/src/lib/utils.ts for shared utilities.
  - Test pattern: Follow existing vitest + Testing Library pattern from MorningSummarySection.test.tsx with vi.mock for hooks.

dependencies:
  - react-markdown: installed (v9.0.1 — already used in MorningSummarySection.tsx)
  - remark-gfm: installed (v4.0.0 — already used in MorningSummarySection.tsx)
  - vitest: installed (existing test runner)
  - @testing-library/react: installed (existing test utils)

acceptance_criteria_mapping:
  - AC1 (Asset names are clickable links that scroll to the action item):
    - linkifyAssets.ts — linkifyAssetNames() matches known asset names and embeds [[ASSET:name]] markers
    - linkifyAssets.ts — extractAssetNames() extracts unique names from action items array
    - MorningSummarySection.tsx — Pre-process summary text: `linkifyAssetNames(cleanSummaryText(text), assetNames)`
    - MorningSummarySection.tsx — Custom ReactMarkdown `p` component renderer that detects [[ASSET:name]] tokens in children text nodes, splits them, and renders matched tokens as `<button>` elements with onClick handler
    - MorningSummarySection.tsx — onClick handler: `document.querySelector('[data-asset-name="AssetName"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' })` followed by a temporary highlight class toggle
    - InsightEvidenceCard.tsx — Add `data-asset-name={item.asset.name}` and `id={`action-${item.id}`}` to root Card element for scroll targeting
    - InsightEvidenceCard.tsx — Add CSS for brief ring/highlight flash animation on scroll target

  - AC2 (Ctrl/Cmd+click opens asset detail page in new tab):
    - MorningSummarySection.tsx — In the asset link button's onClick handler, check `event.metaKey || event.ctrlKey`. If true, call `window.open(`/morning-report/action/${actionId}`, '_blank')` using the assetName→actionId lookup map. If false, perform the scroll behavior from AC1.
    - MorningSummarySection.tsx — Build `Map<string, string>` (lowercased asset name → action item id) from data.actions for the Ctrl+click navigation lookup

  - AC3 (Unmatched asset names render as plain text):
    - linkifyAssets.ts — Only asset names present in the known list get [[ASSET:]] markers; unmatched text passes through as-is
    - MorningSummarySection.tsx — When no actions are loaded (data is null/empty), the summary text is rendered without any linkification (no markers = no links)
    - linkifyAssets.test.ts — Unit test verifies that unknown asset names are not wrapped with markers

risks:
  - Regex false positives in summary text: Asset names like "Line 1" or "Area A" could match common English text. Mitigation: Use word boundary assertions (\b) in the regex. Sort by name length descending so longer, more specific names are matched first. If a name is very short (< 3 chars), consider skipping it or requiring exact case match.
  - ReactMarkdown text node structure: ReactMarkdown may split text across multiple children or nest text within other elements (strong, em, li). The custom renderer must handle text nodes at multiple levels, not just within `p` elements. Mitigation: Override the `text` renderer if react-markdown v9 supports it, or override `p`, `li`, and `strong` to process their text children. Investigate react-markdown v9's component API during implementation to choose the cleanest approach.
  - Multiple action items with the same asset name: If two action items reference "Grinder 5", scrolling should target the first (highest priority) one. Mitigation: When building the assetName→actionId map, use the first occurrence (items are already sorted by priority in the rendered list).
  - Marker token collision with user text: The [[ASSET:name]] format is unlikely to appear in LLM-generated summary text, but it could theoretically occur. Mitigation: Use a sufficiently unique marker format. The double-bracket-plus-prefix format is very unlikely in natural language or markdown.
  - Highlight flash on scroll: The target card may already be visible, requiring the highlight to still trigger. Mitigation: Always apply the highlight class on click regardless of scroll distance. Use a short setTimeout to remove the highlight class after ~1.5s.
  - Both MorningSummarySection and InsightEvidenceCardList call useDailyActions independently: The summary section already has access to data.actions (line 84), so no additional data fetching is needed. The lookup map is built from the summary section's own hook data.

estimated_test_files:
  - apps/web/src/__tests__/linkifyAssets.test.ts: Unit tests for linkifyAssetNames (known asset matching, partial match prevention with length sorting, case-insensitive matching, empty inputs, special characters in names, no markers for unknown names) and extractAssetNames (deduplication, empty array handling)
  - apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx: Extend existing tests — verify asset names render as buttons/links when they match action items, verify unmatched names render as plain text, verify click handler calls scrollIntoView, verify Ctrl+click calls window.open with correct URL

implementation_order:
  1. Create apps/web/src/lib/linkifyAssets.ts with linkifyAssetNames() and extractAssetNames() functions. linkifyAssetNames sorts names by length desc, builds a regex with word boundaries, replaces matches with [[ASSET:name]] markers. extractAssetNames extracts unique names from an array of objects with asset_name field.
  2. Create apps/web/src/__tests__/linkifyAssets.test.ts with comprehensive unit tests for the utility functions — run tests to verify correctness before wiring into components.
  3. Modify apps/web/src/components/action-engine/InsightEvidenceCard.tsx — add data-asset-name={item.asset.name} and id={`action-${item.id}`} to the root Card element. Add a CSS utility class or inline Tailwind for the scroll-to highlight flash animation (e.g., `[&.highlight-flash]:ring-2 [&.highlight-flash]:ring-info-blue` with a transition).
  4. Modify apps/web/src/components/action-list/MorningSummarySection.tsx:
     a. Import linkifyAssetNames, extractAssetNames from @/lib/linkifyAssets
     b. Build assetNames list from data?.actions using extractAssetNames
     c. Build assetNameToId Map<string, string> (lowercased name → action id) from data?.actions, keeping first occurrence per name
     d. Pre-process summary: linkifyAssetNames(cleanSummaryText(text), assetNames)
     e. Add components prop to ReactMarkdown with a custom text/paragraph renderer that:
        - Splits text children on /\[\[ASSET:(.*?)\]\]/ pattern
        - Renders matched segments as <button> with text-info-blue hover:underline cursor-pointer styling
        - onClick: if metaKey/ctrlKey, window.open to action detail page; else scrollIntoView + highlight flash
        - Renders non-matched segments as plain text spans
     f. Define a scrollToAsset(assetName) helper that queries [data-asset-name="name"], scrolls it into view, and adds/removes a highlight class
  5. Extend apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx — add tests for asset link rendering and click behaviors.
  6. Run full test suite (cd apps/web && npm run test:run) to verify no regressions.
DESIGN END

---

## TEST_SPEC: 19-2-clickable-asset-links-in-smart-summary
**Timestamp:** 2026-02-13 07:32:37

TEST SPEC START
story_id: 19-2-clickable-asset-links-in-smart-summary
generated: 2026-02-13

test_specifications:

## AC1: Given the smart summary text mentions an asset name (e.g., "Grinder 5"), When the summary is rendered, Then the asset name is displayed as a clickable link, And clicking it scrolls to or highlights that asset's action item on the current report.

### 19-2-clickable-asset-links-in-smart-summary-UNIT-001: linkifyAssetNames wraps a known asset name with a marker token
- Priority: P0
- Type: unit
- Given: A summary text "Grinder 5 needs attention today" and known asset names ["Grinder 5"]
- When: linkifyAssetNames() is called with the text and asset names
- Then: The returned string contains "[[ASSET:Grinder 5]]" in place of the plain "Grinder 5" text
- Data: { text: "Grinder 5 needs attention today", assetNames: ["Grinder 5"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-002: linkifyAssetNames wraps multiple distinct asset names in a single summary
- Priority: P0
- Type: unit
- Given: A summary text mentioning "Grinder 5" and "CAMA 2400" and known asset names ["Grinder 5", "CAMA 2400"]
- When: linkifyAssetNames() is called
- Then: Both asset names are replaced with their respective [[ASSET:...]] markers
- Data: { text: "Grinder 5 is degrading. CAMA 2400 has downtime.", assetNames: ["Grinder 5", "CAMA 2400"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-003: linkifyAssetNames performs case-insensitive matching while preserving original case
- Priority: P0
- Type: unit
- Given: Summary text contains "grinder 5" (lowercase) and known asset names include "Grinder 5" (title case)
- When: linkifyAssetNames() is called
- Then: The text is matched and the marker preserves the original case from the summary text: "[[ASSET:grinder 5]]"
- Data: { text: "grinder 5 is running hot", assetNames: ["Grinder 5"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-004: linkifyAssetNames sorts names by length descending to prevent partial matches
- Priority: P0
- Type: unit
- Given: Known asset names include both "CAMA" and "CAMA 2400", and summary text mentions "CAMA 2400"
- When: linkifyAssetNames() is called
- Then: "CAMA 2400" is matched as a whole (not partially as "CAMA"), producing "[[ASSET:CAMA 2400]]" rather than "[[ASSET:CAMA]] 2400"
- Data: { text: "CAMA 2400 is offline", assetNames: ["CAMA", "CAMA 2400"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-005: linkifyAssetNames handles asset names appearing multiple times in summary
- Priority: P1
- Type: unit
- Given: Summary text mentions "Grinder 5" twice and known asset names include "Grinder 5"
- When: linkifyAssetNames() is called
- Then: Both occurrences are replaced with [[ASSET:Grinder 5]] markers
- Data: { text: "Grinder 5 is critical. Check Grinder 5 immediately.", assetNames: ["Grinder 5"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-006: extractAssetNames returns unique asset names from action items array
- Priority: P0
- Type: unit
- Given: An array of action items where two items share the same asset_name "Grinder 5"
- When: extractAssetNames() is called with the array
- Then: The result contains "Grinder 5" only once (deduplicated)
- Data: { actions: [{ asset_name: "Grinder 5" }, { asset_name: "Grinder 5" }, { asset_name: "CAMA 2400" }] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-007: extractAssetNames returns empty array for empty input
- Priority: P1
- Type: unit
- Given: An empty array of action items
- When: extractAssetNames() is called with the empty array
- Then: An empty array is returned
- Data: { actions: [] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-008: linkifyAssetNames handles asset names containing regex special characters
- Priority: P1
- Type: unit
- Given: Known asset names include "Line (A+B)" which contains regex metacharacters
- When: linkifyAssetNames() is called with text containing "Line (A+B)"
- Then: The name is correctly matched and wrapped with [[ASSET:Line (A+B)]] without regex errors
- Data: { text: "Line (A+B) needs review", assetNames: ["Line (A+B)"] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-009: linkifyAssetNames returns original text when assetNames array is empty
- Priority: P1
- Type: unit
- Given: Summary text "Grinder 5 is critical" and an empty asset names array
- When: linkifyAssetNames() is called
- Then: The original text is returned unchanged (no markers inserted)
- Data: { text: "Grinder 5 is critical", assetNames: [] }

### 19-2-clickable-asset-links-in-smart-summary-UNIT-010: linkifyAssetNames returns empty string for empty text input
- Priority: P2
- Type: unit
- Given: An empty string as text and known asset names ["Grinder 5"]
- When: linkifyAssetNames() is called
- Then: An empty string is returned
- Data: { text: "", assetNames: ["Grinder 5"] }

### 19-2-clickable-asset-links-in-smart-summary-INT-001: MorningSummarySection renders asset names as clickable elements when they match action items
- Priority: P0
- Type: integration
- Given: useDailyActions returns actions with asset_name "Grinder 5", and useSmartSummary returns a summary containing "Grinder 5"
- When: The MorningSummarySection component is rendered
- Then: The text "Grinder 5" is rendered as a clickable button/link element (not plain text), styled with text-info-blue hover:underline cursor-pointer
- Data: Mock useDailyActions with actions: [{ id: "act-1", asset_name: "Grinder 5", ... }], mock useSmartSummary with summary_text: "Grinder 5 needs immediate attention"

### 19-2-clickable-asset-links-in-smart-summary-INT-002: Clicking an asset link scrolls to the corresponding action item card
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5", and a DOM element with data-asset-name="Grinder 5" exists in the document
- When: The user clicks the "Grinder 5" asset link
- Then: scrollIntoView({ behavior: 'smooth', block: 'center' }) is called on the target element
- Data: Mock scrollIntoView on target element, mock useDailyActions and useSmartSummary as above

### 19-2-clickable-asset-links-in-smart-summary-INT-003: Clicking an asset link applies a highlight flash animation to the target card
- Priority: P1
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5", and the InsightEvidenceCard for that asset exists in the DOM
- When: The user clicks the "Grinder 5" asset link
- Then: A highlight CSS class is temporarily added to the target card element, and removed after approximately 1.5 seconds
- Data: Same mock setup as INT-002, verify classList changes via spy/timer

### 19-2-clickable-asset-links-in-smart-summary-INT-004: InsightEvidenceCard renders with data-asset-name attribute for scroll targeting
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard component is rendered with an item where asset.name is "Grinder 5"
- When: The component is rendered
- Then: The root Card element has a data-asset-name attribute with value "Grinder 5"
- Data: Mock ActionItem with asset: { id: "asset-1", name: "Grinder 5", area: "Area A" }

### 19-2-clickable-asset-links-in-smart-summary-INT-005: InsightEvidenceCard renders with id attribute for action-based targeting
- Priority: P1
- Type: integration
- Given: An InsightEvidenceCard component is rendered with an item where id is "act-123"
- When: The component is rendered
- Then: The root Card element has an id attribute with value "action-act-123"
- Data: Mock ActionItem with id: "act-123"

### 19-2-clickable-asset-links-in-smart-summary-UNIT-011: linkifyAssetNames uses word boundaries to avoid matching inside other words
- Priority: P1
- Type: unit
- Given: Known asset name "Line 1" and text "Pipeline 1 is running. Line 1 is offline."
- When: linkifyAssetNames() is called
- Then: Only "Line 1" (standalone occurrence) is matched, not "Line 1" inside "Pipeline 1"
- Data: { text: "Pipeline 1 is running. Line 1 is offline.", assetNames: ["Line 1"] }

### 19-2-clickable-asset-links-in-smart-summary-INT-006: Multiple action items with same asset name — scroll targets first occurrence
- Priority: P1
- Type: integration
- Given: Two action items both have asset_name "Grinder 5" (ids "act-1" and "act-2"), and summary mentions "Grinder 5"
- When: The user clicks the "Grinder 5" asset link
- Then: The scroll targets the first action item's card (act-1), as it has higher priority in the rendered list
- Data: Mock useDailyActions with two items for "Grinder 5"; verify querySelector returns first match


## AC2: Given the smart summary mentions an asset that has an asset detail page, When the user clicks the asset name while holding Ctrl/Cmd, Then the asset detail page opens in a new tab.

### 19-2-clickable-asset-links-in-smart-summary-INT-007: Ctrl+click on asset link opens asset detail page in new tab
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5" (action id "act-1")
- When: The user Ctrl+clicks the "Grinder 5" asset link (event.ctrlKey = true)
- Then: window.open is called with "/morning-report/action/act-1" and "_blank" target
- Data: Mock window.open, mock useDailyActions with actions: [{ id: "act-1", asset_name: "Grinder 5" }], simulate click with ctrlKey: true

### 19-2-clickable-asset-links-in-smart-summary-INT-008: Cmd+click on asset link opens asset detail page in new tab (macOS)
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5" (action id "act-1")
- When: The user Cmd+clicks the "Grinder 5" asset link (event.metaKey = true)
- Then: window.open is called with "/morning-report/action/act-1" and "_blank" target
- Data: Same as INT-007 but simulate click with metaKey: true instead of ctrlKey

### 19-2-clickable-asset-links-in-smart-summary-INT-009: Ctrl+click does NOT trigger scroll behavior
- Priority: P1
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5" and a corresponding action card in the DOM
- When: The user Ctrl+clicks the "Grinder 5" asset link
- Then: scrollIntoView is NOT called on any element (only window.open is called)
- Data: Mock both window.open and scrollIntoView, verify only window.open is called

### 19-2-clickable-asset-links-in-smart-summary-INT-010: Normal click (without modifier keys) does NOT open new tab
- Priority: P1
- Type: integration
- Given: MorningSummarySection is rendered with an asset link for "Grinder 5"
- When: The user clicks the "Grinder 5" asset link without any modifier keys
- Then: window.open is NOT called, and scrollIntoView IS called on the target element
- Data: Mock window.open and scrollIntoView, simulate normal click, verify window.open not called

### 19-2-clickable-asset-links-in-smart-summary-INT-011: Ctrl+click uses correct action ID from lookup map when multiple assets exist
- Priority: P1
- Type: integration
- Given: Actions include [{ id: "act-1", asset_name: "Grinder 5" }, { id: "act-2", asset_name: "CAMA 2400" }], summary mentions both
- When: The user Ctrl+clicks the "CAMA 2400" asset link
- Then: window.open is called with "/morning-report/action/act-2" (the correct action ID for CAMA 2400)
- Data: Mock useDailyActions with two actions, mock window.open, verify correct URL


## AC3: Given the summary text contains an asset name that doesn't match any known asset, When the summary renders, Then the text is rendered as plain text (no link).

### 19-2-clickable-asset-links-in-smart-summary-UNIT-012: linkifyAssetNames does not wrap unknown asset names with markers
- Priority: P0
- Type: unit
- Given: Summary text "Unknown Machine X is failing" and known asset names ["Grinder 5", "CAMA 2400"]
- When: linkifyAssetNames() is called
- Then: The text is returned unchanged — "Unknown Machine X" remains as plain text, no [[ASSET:]] markers are inserted
- Data: { text: "Unknown Machine X is failing", assetNames: ["Grinder 5", "CAMA 2400"] }

### 19-2-clickable-asset-links-in-smart-summary-INT-012: Summary renders unmatched asset-like text as plain text (no clickable elements)
- Priority: P0
- Type: integration
- Given: useSmartSummary returns summary mentioning "Unknown Machine X", and useDailyActions returns actions with asset_name "Grinder 5" only
- When: MorningSummarySection is rendered
- Then: "Unknown Machine X" appears as plain text in the DOM (not wrapped in a button or anchor element)
- Data: Mock useSmartSummary with "Unknown Machine X is failing", mock useDailyActions with only "Grinder 5" action

### 19-2-clickable-asset-links-in-smart-summary-INT-013: Summary renders as plain text when no actions are loaded (data is null)
- Priority: P0
- Type: integration
- Given: useSmartSummary returns a summary mentioning "Grinder 5", and useDailyActions returns null/undefined data (still loading)
- When: MorningSummarySection is rendered
- Then: All text including "Grinder 5" renders as plain text with no clickable asset links
- Data: Mock useDailyActions with data: null or data.actions: undefined, mock useSmartSummary with text containing "Grinder 5"

### 19-2-clickable-asset-links-in-smart-summary-INT-014: Summary renders as plain text when actions array is empty
- Priority: P1
- Type: integration
- Given: useSmartSummary returns summary mentioning "Grinder 5", and useDailyActions returns an empty actions array
- When: MorningSummarySection is rendered
- Then: "Grinder 5" renders as plain text with no clickable link
- Data: Mock useDailyActions with data.actions: [], mock useSmartSummary with "Grinder 5 needs review"

### 19-2-clickable-asset-links-in-smart-summary-UNIT-013: linkifyAssetNames only wraps names present in the known list
- Priority: P1
- Type: unit
- Given: Summary text mentions both "Grinder 5" and "Line 3", but known asset names only includes "Grinder 5"
- When: linkifyAssetNames() is called
- Then: Only "Grinder 5" is wrapped with [[ASSET:Grinder 5]] marker; "Line 3" remains as plain text
- Data: { text: "Grinder 5 and Line 3 need review", assetNames: ["Grinder 5"] }


edge_cases:
  - Asset name is a single character or very short string (e.g., "A") — could match common words; verify behavior with short names
  - Asset name contains markdown-special characters (e.g., asterisks, underscores: "Grinder_5") — verify no markdown rendering interference
  - Summary text is entirely composed of asset names with no surrounding text
  - Asset name appears inside a markdown bold/italic/list context (e.g., "**Grinder 5** is critical") — verify marker token insertion works correctly inside markdown formatting
  - Summary text contains the marker token format [[ASSET:...]] as literal text from the LLM — verify no false positive rendering
  - Asset name appears at the very start or very end of the summary text
  - Two asset names are adjacent in the text with no separator (e.g., "Grinder 5CAMA 2400") — verify no false match
  - Summary text is null or undefined — verify graceful handling

error_scenarios:
  - scrollIntoView target element not found in DOM (action card not rendered yet) — click should not throw
  - window.open blocked by popup blocker during Ctrl+click — should fail gracefully
  - useDailyActions returns error state — summary should still render as plain text without crashing
  - useSmartSummary returns null/empty summary_text — component should handle gracefully (no linkification attempted)
  - Action item has null or empty asset_name — extractAssetNames should skip/filter it out
  - Very long asset name that could cause regex performance issues (ReDoS) — verify no performance degradation

test_file_mapping:
  - 19-2-clickable-asset-links-in-smart-summary-UNIT-*: apps/web/src/__tests__/linkifyAssets.test.ts
  - 19-2-clickable-asset-links-in-smart-summary-INT-001 to INT-003: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
  - 19-2-clickable-asset-links-in-smart-summary-INT-004 to INT-005: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.test.tsx
  - 19-2-clickable-asset-links-in-smart-summary-INT-006 to INT-014: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx

TEST SPEC END

---

## DESIGN: 19-2-clickable-asset-links-in-smart-summary
**Timestamp:** 2026-02-13 10:32:56

DESIGN START
story_id: 19-2-clickable-asset-links-in-smart-summary

files_to_modify:
  - path: apps/web/src/lib/linkifyAssets.ts
    action: create
    purpose: New utility module with two functions. linkifyAssetNames() takes summary text and known asset names, sorts names by length descending, builds a case-insensitive regex with escaped special characters and word boundaries, and replaces matches with [[ASSET:originalCaseText]] marker tokens. extractAssetNames() extracts and deduplicates asset names from an array of action items (filtering out empty/null names).

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Wire linkification into the existing ReactMarkdown rendering pipeline. Import linkifyAssetNames and extractAssetNames from @/lib/linkifyAssets. Build assetNames list from data?.actions using extractAssetNames. Build a Map<string, string> (lowercased asset name → action item id, keeping first occurrence per name) for Ctrl+click navigation. Pre-process summary text through linkifyAssetNames() after cleanSummaryText(). Add a custom `components` prop to the ReactMarkdown instance at line 283, with overrides for `p`, `li`, `strong` (and any other element that can contain text children) that detect [[ASSET:name]] tokens in text node children and render them as clickable <button> elements. The button's onClick handler checks event.metaKey || event.ctrlKey: if true, calls window.open('/morning-report/action/{id}', '_blank'); if false, queries document for [data-asset-name="name"], calls scrollIntoView({ behavior: 'smooth', block: 'center' }), and adds a temporary highlight class. Style buttons with text-info-blue hover:underline cursor-pointer inline font-inherit to match surrounding text.

  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Add data-asset-name={item.asset.name} and id={`action-${item.id}`} attributes to the root <Card> element (line 62) for scroll targeting from asset links. Add a Tailwind transition class for the highlight flash animation — when a 'highlight-flash' class is added, show a brief ring-2 ring-info-blue effect via CSS transition, then remove it after ~1.5s via the clicking component's setTimeout.

  - path: apps/web/src/__tests__/linkifyAssets.test.ts
    action: create
    purpose: Unit tests for linkifyAssetNames (known asset matching, multiple assets, case-insensitive with case preservation, length-descending sorting to prevent partial matches, multiple occurrences, regex special characters in names, empty inputs, word boundary behavior) and extractAssetNames (deduplication, empty array, null/empty asset_name filtering). Follows vitest + describe/it/expect pattern.

  - path: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
    action: modify
    purpose: Add new test describe block for Story 19.2 with integration tests: asset names render as clickable buttons when matching action items, unmatched names render as plain text, click triggers scrollIntoView on target element, Ctrl+click calls window.open with correct URL, Cmd+click (metaKey) calls window.open, plain text when no actions loaded. Follows existing mock setup patterns already in the file.

patterns_to_use:
  - ReactMarkdown custom components prop: Follow ChatMessage.tsx lines 167-233 pattern. Add components={{ p: ..., li: ..., strong: ... }} to the ReactMarkdown instance in MorningSummarySection. Each override processes its children to find text strings containing [[ASSET:name]] tokens and splits them into interleaved plain text spans and clickable button elements.
  - Marker token approach: Pre-process text with [[ASSET:name]] tokens before passing to ReactMarkdown. ReactMarkdown parses markdown first, then custom renderers detect tokens in text nodes. This avoids interfering with markdown syntax (bold, lists, headings).
  - Link styling: text-info-blue hover:underline cursor-pointer matching ChatMessage.tsx line 208-209.
  - Data attribute scroll targeting: data-asset-name attribute on Card element, queried via document.querySelector('[data-asset-name="name"]'). Similar to data-acknowledgment-tracking pattern in InsightEvidenceCardList.tsx line 90.
  - Utility in lib/ folder: Follow apps/web/src/lib/utils.ts pattern for shared utilities.
  - Test mocking pattern: Mocks declared before imports with vi.mock(), factory functions with spread overrides, cleanup in beforeEach/afterEach. Follow existing MorningSummarySection.test.tsx patterns exactly.

dependencies:
  - react-markdown: installed (v9.0.1 — already used in MorningSummarySection.tsx)
  - remark-gfm: installed (v4.0.0 — already used in MorningSummarySection.tsx)
  - vitest: installed (existing test runner)
  - @testing-library/react: installed (existing test utils)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (Asset names are clickable links that scroll to the action item):
    - linkifyAssets.ts — linkifyAssetNames() matches known asset names from action items and wraps them with [[ASSET:name]] markers in the summary text
    - linkifyAssets.ts — extractAssetNames() extracts unique, non-empty names from action items array
    - MorningSummarySection.tsx — Pre-process: linkifyAssetNames(cleanSummaryText(text), assetNames) before passing to ReactMarkdown
    - MorningSummarySection.tsx — Custom component renderers on ReactMarkdown detect [[ASSET:name]] tokens in text children, render as <button> elements styled as links
    - MorningSummarySection.tsx — onClick handler (no modifier keys): document.querySelector('[data-asset-name="name"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), then add/remove highlight-flash class with setTimeout
    - InsightEvidenceCard.tsx — Add data-asset-name={item.asset.name} and id={`action-${item.id}`} to root <Card> element (line 62)
    - InsightEvidenceCard.tsx — CSS transition support for highlight-flash class (ring-2 ring-info-blue, removed after ~1.5s)

  - AC2 (Ctrl/Cmd+click opens asset detail page in new tab):
    - MorningSummarySection.tsx — In asset link button onClick, check event.metaKey || event.ctrlKey. If true, use assetNameToId lookup Map to find action ID, then window.open('/morning-report/action/{actionId}', '_blank'). Does NOT trigger scroll behavior.
    - MorningSummarySection.tsx — Build Map<string, string> (lowercased asset name → first matching action item id) from data?.actions for navigation lookup

  - AC3 (Unmatched asset names render as plain text):
    - linkifyAssets.ts — Only names present in the known asset names list get [[ASSET:]] markers; all other text passes through unchanged
    - MorningSummarySection.tsx — When data?.actions is null/empty, assetNames is empty, so linkifyAssetNames returns original text unchanged = no clickable links
    - MorningSummarySection.tsx — Custom renderers only convert [[ASSET:...]] tokens to buttons; all other text is plain spans

risks:
  - ReactMarkdown v9 text node structure: Text within markdown elements (bold, italic, list items) may be split across multiple React children or nested in wrapper elements. The custom component overrides need to handle text children at multiple levels (p, li, strong, em). Mitigation: Create a shared processChildren() helper function that recursively processes children arrays, handling both string children (splitting on marker tokens) and React element children (passing through unchanged). Apply this helper in overrides for p, li, strong, and em components.
  - Regex false positives with short asset names: Names like "A" or "Line 1" could match common English text. Mitigation: Use \b word boundary assertions. Sort by length descending so longer names match first. Already-matched regions won't be re-matched since the marker tokens replace them.
  - Regex special characters in asset names: Names containing parentheses, plus signs, etc. (e.g., "Line (A+B)") would break the regex. Mitigation: Escape all regex special characters in asset names before building the regex pattern using a standard escapeRegExp utility.
  - Multiple action items with same asset name: Two action items could reference "Grinder 5". Mitigation: When building the assetNameToId map, use the first occurrence per name (items are already sorted by priority in the API response). For scroll targeting, querySelector('[data-asset-name="Grinder 5"]') naturally returns the first DOM match.
  - Marker token collision: The [[ASSET:name]] format could theoretically appear in LLM-generated summary text. Mitigation: Extremely unlikely given the double-bracket + ASSET prefix format. No additional mitigation needed.
  - Preserving existing markdown CSS classes: The ReactMarkdown wrapper div (line 282) has Tailwind classes for lists, headings, etc. Adding custom component overrides must not conflict. Mitigation: Only override elements where text processing is needed (p, li, strong, em). For other elements, don't override — they inherit the existing CSS from the wrapper div's descendant selectors.
  - scrollIntoView target not found: If the InsightEvidenceCard hasn't rendered yet or the asset name doesn't match the data-asset-name exactly. Mitigation: Use optional chaining (?.scrollIntoView) so the click is a no-op if the target isn't found. The data-asset-name value comes from item.asset.name which is the same source as the action item's asset_name used for linkification, so they should match.

estimated_test_files:
  - apps/web/src/__tests__/linkifyAssets.test.ts: Unit tests for linkifyAssetNames (single asset match, multiple assets, case-insensitive matching, length-descending sorting for partial match prevention, multiple occurrences, regex special characters, empty text, empty asset names, word boundary behavior, unmatched names unchanged) and extractAssetNames (deduplication, empty array, null/empty name filtering)
  - apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx: Integration tests for Story 19.2 — asset names render as clickable buttons when matching action items, unmatched names render as plain text, click triggers scrollIntoView, Ctrl+click calls window.open with correct action URL, metaKey click works same as ctrlKey, no links when actions data is null/empty, no links when actions array is empty, correct action ID used for Ctrl+click with multiple assets

implementation_order:
  1. Create apps/web/src/lib/linkifyAssets.ts — implement extractAssetNames() and linkifyAssetNames(). extractAssetNames filters out empty/null values and deduplicates. linkifyAssetNames sorts names by length descending, escapes regex special chars, builds a single regex with alternation and \b word boundaries, and does a global case-insensitive replace wrapping matches with [[ASSET:matchedText]] preserving the original case from the source text.
  2. Create apps/web/src/__tests__/linkifyAssets.test.ts — comprehensive unit tests covering all test spec UNIT cases (001-013). Run tests to verify utility correctness before wiring into components.
  3. Modify apps/web/src/components/action-engine/InsightEvidenceCard.tsx — add data-asset-name={item.asset.name} and id={`action-${item.id}`} to the root <Card> element at line 62. Add transition-all to existing className for smooth highlight animation support.
  4. Modify apps/web/src/components/action-list/MorningSummarySection.tsx:
     a. Import linkifyAssetNames, extractAssetNames from @/lib/linkifyAssets
     b. Derive assetNames using useMemo: extractAssetNames(data?.actions ?? []) where actions are mapped to { asset_name } objects
     c. Derive assetNameToId Map<string, string> using useMemo: iterate data?.actions, for each action, lowercase asset_name as key, action id as value, only set if key not already in map (first-wins)
     d. Create a processTextChildren() helper function that takes React children and the assetNameToId map, recursively processes string children by splitting on /\[\[ASSET:(.*?)\]\]/g pattern, renders matched segments as <button> with onClick handler and link styling, renders non-matched segments as <span>
     e. Create a scrollToAsset(assetName: string) function that queries [data-asset-name="assetName"], calls scrollIntoView, adds 'highlight-flash' class with ring-2 ring-info-blue, removes it after 1500ms via setTimeout
     f. Create the onClick handler for asset buttons: check event.metaKey || event.ctrlKey → window.open(); else → scrollToAsset()
     g. Define the custom components object for ReactMarkdown with overrides for p, li, strong, em that call processTextChildren() on their children
     h. Update the ReactMarkdown instance at line 283 to: (1) pass linkified text as children, (2) add the components prop
     i. Ensure the components object is stable (defined outside render or wrapped in useMemo) to avoid unnecessary re-renders
  5. Extend apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx — add Story 19.2 describe block with integration tests per test spec (INT-001 through INT-014). Mock window.open, verify scrollIntoView calls (already mocked in setup.ts), create DOM elements with data-asset-name for scroll target verification.
  6. Run full test suite: cd apps/web && npm run test:run — verify all new and existing tests pass with no regressions.
DESIGN END

---

## TEST_SPEC: 19-2-clickable-asset-links-in-smart-summary
**Timestamp:** 2026-02-13 10:36:05

TEST SPEC START
story_id: 19-2-clickable-asset-links-in-smart-summary
generated: 2026-02-13

test_specifications:

## AC1: Given the smart summary text mentions an asset name (e.g., "Grinder 5"), When the summary is rendered, Then the asset name is displayed as a clickable link, And clicking it scrolls to or highlights that asset's action item on the current report.

### 19-2-clickable-asset-links-in-smart-summary-UNIT-001: linkifyAssetNames wraps a single known asset name with marker token
- Priority: P0
- Type: unit
- Given: Summary text "Grinder 5 needs immediate attention" and known asset names ["Grinder 5"]
- When: linkifyAssetNames() is called with the text and asset names
- Then: The returned string contains "[[ASSET:Grinder 5]] needs immediate attention"
- Data: text = "Grinder 5 needs immediate attention", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-002: linkifyAssetNames wraps multiple known asset names with marker tokens
- Priority: P0
- Type: unit
- Given: Summary text mentioning "Grinder 5" and "CAMA 2400" and known asset names ["Grinder 5", "CAMA 2400"]
- When: linkifyAssetNames() is called
- Then: Both asset names are wrapped with [[ASSET:...]] markers, and surrounding text is unchanged
- Data: text = "Grinder 5 and CAMA 2400 require maintenance", assetNames = ["Grinder 5", "CAMA 2400"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-003: linkifyAssetNames performs case-insensitive matching with original case preservation
- Priority: P0
- Type: unit
- Given: Summary text contains "grinder 5" (lowercase) and known asset names include "Grinder 5" (mixed case)
- When: linkifyAssetNames() is called
- Then: The matched text preserves the original case from the source text: "[[ASSET:grinder 5]]"
- Data: text = "grinder 5 needs work", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-004: linkifyAssetNames sorts names by length descending to prevent partial matches
- Priority: P0
- Type: unit
- Given: Summary text contains "CAMA 2400" and known asset names include both "CAMA" and "CAMA 2400"
- When: linkifyAssetNames() is called
- Then: "CAMA 2400" is matched as a whole (not "CAMA" alone), returning "[[ASSET:CAMA 2400]]" not "[[ASSET:CAMA]] 2400"
- Data: text = "CAMA 2400 is down", assetNames = ["CAMA", "CAMA 2400"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-005: linkifyAssetNames handles multiple occurrences of the same asset name
- Priority: P1
- Type: unit
- Given: Summary text mentions "Grinder 5" twice and known asset names include "Grinder 5"
- When: linkifyAssetNames() is called
- Then: Both occurrences are wrapped with [[ASSET:Grinder 5]] markers
- Data: text = "Grinder 5 failed. Check Grinder 5 immediately.", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-006: linkifyAssetNames escapes regex special characters in asset names
- Priority: P1
- Type: unit
- Given: Summary text contains "Line (A+B)" and known asset names include "Line (A+B)"
- When: linkifyAssetNames() is called
- Then: The name is correctly matched and wrapped as "[[ASSET:Line (A+B)]]" without regex errors
- Data: text = "Line (A+B) is running", assetNames = ["Line (A+B)"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-007: linkifyAssetNames returns original text unchanged when asset names list is empty
- Priority: P1
- Type: unit
- Given: Summary text "Grinder 5 needs attention" and an empty asset names array
- When: linkifyAssetNames() is called with empty assetNames
- Then: The original text is returned unmodified with no markers
- Data: text = "Grinder 5 needs attention", assetNames = []

### 19-2-clickable-asset-links-in-smart-summary-UNIT-008: linkifyAssetNames returns empty string when input text is empty
- Priority: P2
- Type: unit
- Given: Empty summary text and a non-empty asset names array
- When: linkifyAssetNames() is called
- Then: An empty string is returned
- Data: text = "", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-009: linkifyAssetNames respects word boundaries
- Priority: P1
- Type: unit
- Given: Summary text "Grinder 50 is running" and known asset names include "Grinder 5"
- When: linkifyAssetNames() is called
- Then: "Grinder 50" is NOT matched (word boundary prevents partial number match), text is returned unchanged
- Data: text = "Grinder 50 is running", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-010: extractAssetNames extracts unique asset names from action items
- Priority: P0
- Type: unit
- Given: An array of action items with asset_name fields, some duplicated
- When: extractAssetNames() is called
- Then: A deduplicated array of asset name strings is returned
- Data: actions = [{ asset_name: "Grinder 5" }, { asset_name: "CAMA 2400" }, { asset_name: "Grinder 5" }] → ["Grinder 5", "CAMA 2400"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-011: extractAssetNames filters out empty and null asset names
- Priority: P1
- Type: unit
- Given: An array of action items where some have empty string or null asset_name
- When: extractAssetNames() is called
- Then: Only non-empty, non-null asset names are returned
- Data: actions = [{ asset_name: "Grinder 5" }, { asset_name: "" }, { asset_name: null }] → ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-UNIT-012: extractAssetNames returns empty array for empty input
- Priority: P2
- Type: unit
- Given: An empty array of action items
- When: extractAssetNames() is called
- Then: An empty array is returned
- Data: actions = [] → []

### 19-2-clickable-asset-links-in-smart-summary-UNIT-013: linkifyAssetNames does not match asset name embedded in the middle of a word
- Priority: P1
- Type: unit
- Given: Summary text "TheGrinder 5 model" and known asset names include "Grinder 5"
- When: linkifyAssetNames() is called
- Then: "TheGrinder 5" is NOT matched due to word boundary, text returned unchanged
- Data: text = "TheGrinder 5 model", assetNames = ["Grinder 5"]

### 19-2-clickable-asset-links-in-smart-summary-INT-001: Asset names in summary render as clickable buttons when matching action items
- Priority: P0
- Type: integration
- Given: The smart summary contains "Grinder 5 needs immediate attention" and action items include an item with asset_name "Grinder 5"
- When: MorningSummarySection renders the summary
- Then: "Grinder 5" is rendered as a clickable button element (not plain text) with class "text-info-blue" and "cursor-pointer"
- Data: Mock useDailyActions to return actions with asset_name "Grinder 5"; mock useSmartSummary to return summary_text containing "Grinder 5"

### 19-2-clickable-asset-links-in-smart-summary-INT-002: Clicking asset link scrolls to the matching action item card
- Priority: P0
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link and a DOM element exists with data-asset-name="Grinder 5"
- When: The user clicks the "Grinder 5" link (no modifier keys)
- Then: scrollIntoView({ behavior: 'smooth', block: 'center' }) is called on the target element
- Data: Create a mock DOM element with data-asset-name="Grinder 5" and spy on scrollIntoView

### 19-2-clickable-asset-links-in-smart-summary-INT-003: Clicking asset link adds highlight flash animation to target card
- Priority: P1
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link and a target card exists in the DOM
- When: The user clicks the "Grinder 5" link (no modifier keys)
- Then: A highlight class (e.g., "highlight-flash") is temporarily added to the target card element, and removed after approximately 1500ms
- Data: Create a mock DOM element with data-asset-name="Grinder 5"; use vi.useFakeTimers() to verify class removal

### 19-2-clickable-asset-links-in-smart-summary-INT-004: Multiple asset names in summary all render as clickable links
- Priority: P1
- Type: integration
- Given: The smart summary mentions "Grinder 5" and "CAMA 2400" and action items include both asset names
- When: MorningSummarySection renders the summary
- Then: Both "Grinder 5" and "CAMA 2400" are rendered as clickable button elements
- Data: Mock actions with both asset names; summary_text = "Grinder 5 is critical. CAMA 2400 needs review."

### 19-2-clickable-asset-links-in-smart-summary-INT-005: Asset links render correctly within markdown bold text
- Priority: P1
- Type: integration
- Given: The smart summary contains "**Grinder 5** needs attention" (asset name inside markdown bold) and action items include "Grinder 5"
- When: MorningSummarySection renders the summary
- Then: "Grinder 5" is rendered as a clickable button element inside a bold wrapper, maintaining both bold styling and link functionality
- Data: summary_text = "**Grinder 5** needs attention", actions with asset_name "Grinder 5"

### 19-2-clickable-asset-links-in-smart-summary-INT-006: Asset links render correctly within markdown list items
- Priority: P1
- Type: integration
- Given: The smart summary contains a markdown list with asset names (e.g., "- Grinder 5 is critical") and action items include "Grinder 5"
- When: MorningSummarySection renders the summary
- Then: "Grinder 5" within the list item is rendered as a clickable button element
- Data: summary_text = "- Grinder 5 is critical\n- CAMA 2400 needs review", actions with matching asset_names

### 19-2-clickable-asset-links-in-smart-summary-INT-007: No links when actions data is null (loading state)
- Priority: P1
- Type: integration
- Given: The smart summary contains asset names but useDailyActions returns null/undefined data
- When: MorningSummarySection renders the summary
- Then: All asset names render as plain text with no clickable buttons
- Data: Mock useDailyActions with data: null; summary_text = "Grinder 5 needs attention"

### 19-2-clickable-asset-links-in-smart-summary-INT-008: No links when actions array is empty
- Priority: P1
- Type: integration
- Given: The smart summary contains asset names but useDailyActions returns an empty actions array
- When: MorningSummarySection renders the summary
- Then: All asset names render as plain text with no clickable buttons
- Data: Mock useDailyActions with data.actions = []; summary_text = "Grinder 5 needs attention"

### 19-2-clickable-asset-links-in-smart-summary-INT-009: Scroll target not found is handled gracefully (no-op)
- Priority: P1
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link but no element with data-asset-name="Grinder 5" exists in the DOM
- When: The user clicks the "Grinder 5" link
- Then: No error is thrown, click is a no-op (optional chaining prevents failure)
- Data: No DOM element with matching data-asset-name; verify no console errors or thrown exceptions

## AC2: Given the smart summary mentions an asset that has an asset detail page, When the user clicks the asset name while holding Ctrl/Cmd, Then the asset detail page opens in a new tab.

### 19-2-clickable-asset-links-in-smart-summary-INT-010: Ctrl+click on asset link opens action detail page in new tab
- Priority: P0
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link and the action item has id "action-123"
- When: The user Ctrl+clicks the "Grinder 5" link (event.ctrlKey = true)
- Then: window.open is called with ('/morning-report/action/action-123', '_blank')
- Data: Mock window.open; action item with id "action-123" and asset_name "Grinder 5"

### 19-2-clickable-asset-links-in-smart-summary-INT-011: Cmd+click (metaKey) on asset link opens action detail page in new tab
- Priority: P0
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link and the action item has id "action-123"
- When: The user Cmd+clicks the "Grinder 5" link (event.metaKey = true)
- Then: window.open is called with ('/morning-report/action/action-123', '_blank')
- Data: Mock window.open; action item with id "action-123" and asset_name "Grinder 5"

### 19-2-clickable-asset-links-in-smart-summary-INT-012: Ctrl/Cmd+click does NOT trigger scroll behavior
- Priority: P1
- Type: integration
- Given: The smart summary renders "Grinder 5" as a clickable link and a scroll target exists in the DOM
- When: The user Ctrl+clicks the "Grinder 5" link
- Then: window.open is called, but scrollIntoView is NOT called on the target element
- Data: Spy on both window.open and scrollIntoView; verify only window.open is called

### 19-2-clickable-asset-links-in-smart-summary-INT-013: Ctrl+click uses correct action ID when multiple assets exist
- Priority: P1
- Type: integration
- Given: Summary mentions "Grinder 5" and "CAMA 2400", action items map Grinder 5 → id "action-123" and CAMA 2400 → id "action-456"
- When: The user Ctrl+clicks the "CAMA 2400" link
- Then: window.open is called with ('/morning-report/action/action-456', '_blank'), not the Grinder 5 action ID
- Data: Two action items with different IDs and asset names

### 19-2-clickable-asset-links-in-smart-summary-INT-014: Duplicate asset names use first action item ID for Ctrl+click navigation
- Priority: P2
- Type: integration
- Given: Two action items have asset_name "Grinder 5" with ids "action-123" (first/higher priority) and "action-789" (second)
- When: The user Ctrl+clicks the "Grinder 5" link
- Then: window.open is called with the first action item's ID ('/morning-report/action/action-123', '_blank')
- Data: Two action items with same asset_name but different IDs

## AC3: Given the summary text contains an asset name that doesn't match any known asset, When the summary renders, Then the text is rendered as plain text (no link).

### 19-2-clickable-asset-links-in-smart-summary-UNIT-014: linkifyAssetNames does not wrap unmatched names with markers
- Priority: P0
- Type: unit
- Given: Summary text "Unknown Machine X needs repair" and known asset names ["Grinder 5", "CAMA 2400"]
- When: linkifyAssetNames() is called
- Then: The text is returned unchanged with no [[ASSET:...]] markers
- Data: text = "Unknown Machine X needs repair", assetNames = ["Grinder 5", "CAMA 2400"]

### 19-2-clickable-asset-links-in-smart-summary-INT-015: Unmatched asset-like text renders as plain text in the component
- Priority: P0
- Type: integration
- Given: Summary text contains "Unknown Asset" which does not match any action item asset_name
- When: MorningSummarySection renders the summary
- Then: "Unknown Asset" is rendered as plain text, not as a clickable button or link element
- Data: summary_text = "Unknown Asset has issues. Grinder 5 is critical.", actions with only asset_name "Grinder 5"; verify "Unknown Asset" is NOT a button

### 19-2-clickable-asset-links-in-smart-summary-UNIT-015: linkifyAssetNames only wraps matched names, leaving all other text intact
- Priority: P1
- Type: unit
- Given: Summary text with a mix of matched and unmatched names
- When: linkifyAssetNames() is called
- Then: Only known asset names get [[ASSET:...]] markers; all other text including unmatched asset-like names remains as plain text
- Data: text = "Grinder 5 and Unknown Machine need work", assetNames = ["Grinder 5"] → "[[ASSET:Grinder 5]] and Unknown Machine need work"

edge_cases:
  - Asset name is a substring of another word in the summary (e.g., "Grinder 5" should not match "Grinder 50" or "TheGrinder 5")
  - Asset name contains regex special characters like parentheses, plus signs, or dots (e.g., "Line (A+B)", "Motor 3.5")
  - Same asset name appears in both bold and plain markdown contexts within a single summary
  - Summary text is very long with many asset references (performance consideration)
  - Asset name is a single character or very short string (potential for false positives)
  - LLM-generated summary text contains markdown formatting around asset names (e.g., "**Grinder 5**" with bold markers)
  - Action items data loads after the summary has already rendered (race condition / re-render)

error_scenarios:
  - Scroll target element not found in the DOM when asset link is clicked (should be a no-op, no error thrown)
  - Action items data is null or undefined when summary renders (should degrade to plain text, no errors)
  - Asset name in action item is empty string or null (should be filtered out by extractAssetNames)
  - window.open is blocked by popup blocker on Ctrl/Cmd+click (browser-level, no app crash)
  - Malformed summary text with broken markdown syntax (ReactMarkdown should still handle gracefully)

test_file_mapping:
  - 19-2-clickable-asset-links-in-smart-summary-UNIT-*: apps/web/src/__tests__/linkifyAssets.test.ts
  - 19-2-clickable-asset-links-in-smart-summary-INT-*: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx

TEST SPEC END

---

## DESIGN: 19-3-context-aware-followup-suggestions
**Timestamp:** 2026-02-13 11:03:05

DESIGN START
story_id: 19-3-context-aware-followup-suggestions

files_to_modify:
  - path: apps/web/src/lib/generateSuggestions.ts
    action: create
    purpose: Pure utility function for template-based question generation. Accepts action items array, summary text, and report date. Returns 2-3 contextual follow-up question strings prioritized by category (safety > OEE > financial > trend). No LLM call — purely client-side template logic. Uses ActionItem type from useDailyActions.

  - path: apps/web/src/components/action-list/SuggestedQuestions.tsx
    action: create
    purpose: Client-side component that renders 2-3 suggested follow-up question chips below the AI summary. Replicates FollowUpChips visual pattern (Button variant="outline" size="sm", ChevronRight icon, Industrial Clarity colors, fade-in animation). Accepts actionItems, summaryText, reportDate, and onQuestionSelect callback. Uses useMemo to memoize generated suggestions. Returns null when no suggestions can be generated.

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Import and render SuggestedQuestions component below the "Powered by AI analysis" / "Ask about this" button row, inside the hasSummary conditional block (after line 395). Wire onQuestionSelect to call openChatWithQuestion() from the extended ChatContext, passing both the question text and the full report context (summaryText, actionItems, reportDate). This ensures the sidebar opens with context AND auto-sends the question.

  - path: apps/web/src/components/chat/ChatContextProvider.tsx
    action: modify
    purpose: Add openChatWithQuestion(context: ReportContext, question: string) method to the context value. This method stores the pending question alongside the report context so ChatSidebar can detect it and auto-send the question after opening. Add pendingQuestion state (string | null) and clearPendingQuestion callback.

  - path: apps/web/src/components/chat/ChatSidebar.tsx
    action: modify
    purpose: Add a useEffect that detects when pendingQuestion changes (via context). When a pending question is present and the sidebar is open, auto-call handleFollowUpSelect(question) to send it, then clear the pending question via context. This enables SuggestedQuestions to open chat AND submit a question in one action.

  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: Add SuggestedQuestions to the barrel export file.

  - path: apps/web/src/__tests__/generateSuggestions.test.ts
    action: create
    purpose: Unit tests for generateSuggestions utility — covers safety/OEE/financial/trend question generation, priority ordering, 2-3 question limit, empty input handling, asset name interpolation, and reactivity to changing inputs.

  - path: apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
    action: create
    purpose: Component tests for SuggestedQuestions — renders chips when action data exists, calls onQuestionSelect on click, returns null when no suggestions, proper ARIA attributes, animation classes, max 2-3 chips.

patterns_to_use:
  - FollowUpChips visual pattern: Replicate exact Button variant="outline" size="sm" styling, ChevronRight icon, border-industrial-300, bg-industrial-50, hover:bg-info-blue/10, animate-in fade-in slide-in-from-bottom-2, role="group" aria-label, min-h-[44px] touch targets. Replicate structure from FollowUpChips.tsx but with different semantics (opens chat with context + question vs. just sending a message).
  - ChatContext Provider pattern: Extend the existing ChatContextProvider (Story 19.1) with openChatWithQuestion(context, question) and pendingQuestion state. Same pattern as openChatWithContext but additionally stores the question to auto-send.
  - useMemo for derived data: Use useMemo in SuggestedQuestions to memoize generateSuggestions() output based on actionItems, summaryText, reportDate. Ensures suggestions recalculate reactively when props change (AC #3).
  - Pure utility function in lib/: Follow the same pattern as lib/linkifyAssets.ts — export pure functions with clear input/output types, no side effects, easily testable.
  - Vitest + Testing Library test pattern: Follow FollowUpChips.test.tsx pattern exactly — describe blocks, vi.fn() for mocks, render/screen/fireEvent from @testing-library/react, toBeInTheDocument/toHaveAttribute assertions.

dependencies:
  - react: installed (useState, useMemo, useCallback, useEffect)
  - lucide-react: installed (ChevronRight)
  - @/components/ui/button: installed (Shadcn Button)
  - @/lib/utils: installed (cn)
  - vitest: installed (testing)
  - @testing-library/react: installed (component testing)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (2-3 contextual follow-up questions shown as clickable chips below the button):
    - generateSuggestions.ts — Template-based logic generates 2-3 questions from action items by category. Safety actions → "What actions have been taken on recurring safety events?" OEE actions → "What were the top downtime reasons for {assetName}?" Financial actions → "What is driving the ${amount} production loss on {assetName}?" Trend → "How does today's OEE compare to last week?" Priority: safety > OEE > financial > trend. Cap at 3.
    - SuggestedQuestions.tsx — Renders the generated questions as clickable chips using Button variant="outline" size="sm" with ChevronRight icon. Container has role="group" aria-label="Suggested follow-up questions about the morning report". Returns null when no suggestions.
    - MorningSummarySection.tsx — Renders SuggestedQuestions inside the hasSummary block, after the "Ask about this" button row (after line 394). Passes data.actions, cleaned summary text, and report date.
    - action-list/index.ts — Exports SuggestedQuestions from barrel.

  - AC2 (Clicking a chip opens AI chat sidebar with question pre-filled and sent, with report context):
    - ChatContextProvider.tsx — New method openChatWithQuestion(context: ReportContext, question: string) that sets reportContext, sets pendingQuestion, and opens the sidebar.
    - ChatSidebar.tsx — New useEffect watches pendingQuestion from context. When pendingQuestion is set and sidebar is open, calls handleFollowUpSelect(pendingQuestion) to auto-send it, then calls clearPendingQuestion(). This creates the exact user experience: sidebar opens → report context intro message appears → question is auto-sent → AI responds with context-aware answer.
    - MorningSummarySection.tsx — Wire onQuestionSelect callback: calls openChatWithQuestion({ summaryText, actionItems, reportDate }, question) so both context and question are delivered together.

  - AC3 (Suggestions update when smart summary content changes):
    - SuggestedQuestions.tsx — Uses useMemo with [actionItems, summaryText, reportDate] as dependencies. When any of these change (different date selected, data refreshed), useMemo recalculates and re-renders with new suggestions.
    - MorningSummarySection.tsx — Passes live data from useDailyActions() and useSmartSummary() hooks as props. These hooks re-fetch when reportDate changes, causing the SuggestedQuestions to receive new data and regenerate.

risks:
  - Pending question race condition: If openChatWithQuestion is called before ChatSidebar has finished processing a previous reportContext change (intro message), the handleFollowUpSelect could fire before the intro message is set. Mitigation: In the ChatSidebar useEffect for pendingQuestion, add a small delay (setTimeout ~150ms) or check that messages have been reset with the intro message before sending the pending question. Alternatively, chain the pending question processing after the reportContext useEffect by using a flag or dependency ordering.
  - Context re-trigger on same report: If user clicks the same suggested question twice, openChatWithQuestion will set the same reportContext. The ChatSidebar useEffect checks `reportContext !== activeReportContextRef.current` so it won't reset messages on subsequent clicks with identical context. Need to ensure the pendingQuestion still fires even when the context hasn't changed. Mitigation: Make pendingQuestion a separate state that always triggers regardless of context changes. Use a counter or unique ID to ensure the useEffect fires even for the same question text.
  - Empty suggestions state: If there are no action items and no summary, generateSuggestions returns empty array, and SuggestedQuestions returns null. This is the correct behavior — no visual change. But need to test this doesn't leave extra whitespace/margin in the summary card. Mitigation: SuggestedQuestions returns null outright, not an empty div.
  - ChatContext interface extension: Adding openChatWithQuestion and pendingQuestion to ChatContextProvider changes the context interface. The existing openChatWithContext and all consumers must continue to work. Mitigation: openChatWithQuestion is additive — it doesn't change the existing openChatWithContext signature. Default pendingQuestion to null in the default context value.
  - Asset name availability: generateSuggestions needs asset names from action items. If action items haven't loaded yet (data is null), no suggestions are generated. This is correct but means suggestions appear after a data-fetch delay. The useMemo will recalculate once data arrives. No user-facing issue.

estimated_test_files:
  - apps/web/src/__tests__/generateSuggestions.test.ts: Unit tests for generateSuggestions utility — returns 2-3 questions when action items exist; returns safety question when safety actions present; returns OEE question with specific asset name when OEE actions present; returns financial question when financial actions present; returns trend question as filler; respects priority ordering (safety > OEE > financial > trend); returns empty array when no action items and no summary; caps output at 3 questions max; returns at least 2 when data is sufficient; updates output when input data changes; handles mixed categories correctly; uses the worst-performing asset name in OEE questions; includes financial impact amount in financial questions.
  - apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx: Component tests — renders suggestion chips when action data is provided; calls onQuestionSelect when a chip is clicked with correct question text; returns null when no suggestions can be generated (empty actions, no summary); has proper ARIA attributes (role="group", aria-label); applies animation classes (animate-in, fade-in); limits display to 2-3 chips maximum; each chip has ChevronRight icon; chips have proper aria-label attributes; applies custom className.

implementation_order:
  1. Create apps/web/src/lib/generateSuggestions.ts — Define SuggestionContext interface (actions: ActionItem[], summaryText: string, reportDate: string). Implement generateSuggestions() with template-based logic: filter actions by category, extract asset names and metric values, build question templates per category, prioritize safety > OEE > financial > trend, return top 2-3. Export function and interface.
  2. Create apps/web/src/__tests__/generateSuggestions.test.ts — Write comprehensive unit tests following the linkifyAssets.test.ts pattern. Cover all category combinations, priority ordering, empty inputs, asset name interpolation, and output limits. Run tests to verify utility correctness before building the component.
  3. Create apps/web/src/components/action-list/SuggestedQuestions.tsx — 'use client' component. Props: actionItems (ActionItem[]), summaryText (string), reportDate (string), onQuestionSelect ((question: string) => void), className (optional). Internally calls generateSuggestions() via useMemo. Renders chips replicating FollowUpChips visual pattern. Returns null when suggestions array is empty.
  4. Create apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx — Component tests following FollowUpChips.test.tsx pattern. Test rendering, click callbacks, null return, ARIA attributes, animation classes, chip limits.
  5. Modify apps/web/src/components/chat/ChatContextProvider.tsx — Add pendingQuestion state (string | null). Add openChatWithQuestion(context: ReportContext, question: string) method that sets reportContext, sets pendingQuestion, and opens sidebar. Add clearPendingQuestion() method. Export both on the context value. Update the default context with no-op values.
  6. Modify apps/web/src/components/chat/ChatSidebar.tsx — Add useEffect that watches pendingQuestion from useChatContext(). When pendingQuestion is non-null and isOpen is true, wait a brief delay (to let the intro message render), then call handleFollowUpSelect(pendingQuestion), then call clearPendingQuestion(). This auto-sends the suggested question.
  7. Modify apps/web/src/components/action-list/MorningSummarySection.tsx — Import SuggestedQuestions from './SuggestedQuestions'. Import openChatWithQuestion from useChatContext (already imported). Add SuggestedQuestions component inside the hasSummary block, after the "Ask about this" button row (after line 394, before the closing </div>). Pass actionItems={data?.actions ?? []}, summaryText={cleanSummaryText(smartSummary?.summary_text ?? '')}, reportDate={data?.report_date ?? ''}, onQuestionSelect handler that calls openChatWithQuestion with report context and question.
  8. Modify apps/web/src/components/action-list/index.ts — Add export { SuggestedQuestions } from './SuggestedQuestions' to barrel file.
  9. Run full test suite (cd apps/web && npx vitest run) to verify all new and existing tests pass with no regressions.
DESIGN END

---

## DESIGN: 19-3-context-aware-followup-suggestions
**Timestamp:** 2026-02-13 11:03:22

DESIGN START
story_id: 19-3-context-aware-followup-suggestions

files_to_modify:
  - path: apps/web/src/lib/generateSuggestions.ts
    action: create
    purpose: Pure utility function for template-based question generation. Accepts ActionItem array, summary text, and report date. Returns 2-3 contextual follow-up question strings prioritized by category (safety > OEE > financial > trend). No LLM calls — all logic is client-side template matching against action item categories and asset names.

  - path: apps/web/src/components/action-list/SuggestedQuestions.tsx
    action: create
    purpose: Client component that renders 2-3 contextual follow-up questions as clickable chips below the AI summary. Replicates the exact FollowUpChips visual pattern (Button variant="outline" size="sm", ChevronRight icon, Industrial Clarity styling, fade-in animation). Accepts actionItems, summaryText, and onQuestionSelect props. Uses useMemo to memoize generateSuggestions output. Returns null when no suggestions can be generated.

  - path: apps/web/src/components/chat/ChatContextProvider.tsx
    action: modify
    purpose: Extend ChatContextValue interface and provider to support openChatWithQuestion(context, question). This new method sets reportContext, opens the sidebar, AND sets a pendingQuestion string. ChatSidebar will consume the pendingQuestion to auto-send it on open. This is the cleanest approach since the context provider already manages cross-component communication between MorningSummarySection and ChatSidebar.

  - path: apps/web/src/components/chat/types.ts
    action: modify
    purpose: No changes needed — ReportContext interface from Story 19.1 already has the fields needed (summaryText, actionItems, reportDate).

  - path: apps/web/src/components/chat/ChatSidebar.tsx
    action: modify
    purpose: Add a useEffect that watches for pendingQuestion from useChatContext(). When a pendingQuestion is set and the sidebar is open, auto-send it via handleFollowUpSelect (which adds user message + calls sendMessage). Clear pendingQuestion after consuming it. This enables suggested question chips to open the sidebar AND immediately send the question with report context.

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Import and render SuggestedQuestions component below the "Ask about this" button row (after line 394). Pass data.actions, smartSummary.summary_text, and data.report_date as props. Wire onQuestionSelect to call openChatWithQuestion from useChatContext, passing the report context and selected question.

  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: Add SuggestedQuestions to barrel export.

  - path: apps/web/src/lib/__tests__/generateSuggestions.test.ts
    action: create
    purpose: Comprehensive unit tests for generateSuggestions utility covering: returns 2-3 questions, safety-related questions when safety actions present, OEE-related questions with asset name, financial-related questions, empty array when no data, priority ordering (safety > OEE > financial > trend), output updates when input changes.

  - path: apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
    action: create
    purpose: Component tests for SuggestedQuestions covering: renders chips when action data provided, calls onQuestionSelect on click, returns null when no suggestions, proper ARIA attributes, animation classes, limits display to 2-3 chips.

patterns_to_use:
  - FollowUpChips visual pattern: Replicate exact styling — Button variant="outline" size="sm", border-industrial-300, bg-industrial-50, hover:bg-info-blue/10, min-h-[44px] touch target, ChevronRight icon, animate-in fade-in slide-in-from-bottom-2 duration-300, role="group" aria-label, aria-label="Ask: {question}" on each button
  - ChatContextProvider cross-component communication: Extend existing openChatWithContext pattern with a new openChatWithQuestion(context, question) method that also sets a pendingQuestion state. ChatSidebar consumes and auto-sends it. This follows the established provider pattern from Story 19.1.
  - useMemo for derived data: Memoize generateSuggestions output in SuggestedQuestions component based on actionItems and summaryText props, ensuring suggestions recalculate reactively when data changes (AC#3).
  - Pure utility in lib/ folder: Follow linkifyAssets.ts pattern — export pure functions with TypeScript interfaces, no React dependencies, easily testable.
  - Vitest + Testing Library test pattern: Follow FollowUpChips.test.tsx structure exactly — describe/it/expect, render + screen + fireEvent, vi.mock for hooks, null checks, ARIA assertions.

dependencies:
  - react: installed (useState, useMemo, useCallback, useEffect)
  - lucide-react: installed (ChevronRight icon)
  - @/components/ui/button: installed (Shadcn Button)
  - @/lib/utils: installed (cn() class merger)
  - vitest: installed (test runner)
  - @testing-library/react: installed (component testing)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (2-3 contextual follow-up questions shown as clickable chips below the button):
    - generateSuggestions.ts — SuggestionContext interface accepting ActionItem[], summaryText, reportDate. Template-based generation logic: checks action item categories (safety, oee, financial) and extracts asset names to build contextual questions. Priority: safety > OEE > financial > trend. Returns top 2-3 strings.
    - SuggestedQuestions.tsx — Receives actionItems and summaryText props, calls generateSuggestions via useMemo, renders results as Button chips with FollowUpChips visual pattern. Returns null when generateSuggestions returns empty array. ARIA: role="group" aria-label="Suggested follow-up questions about the morning report".
    - MorningSummarySection.tsx — Renders <SuggestedQuestions> below the "Ask about this" button row (after line 394), inside the existing hasSummary block. Passes data.actions, smartSummary.summary_text.
    - action-list/index.ts — Exports SuggestedQuestions.

  - AC2 (Clicking a chip opens AI chat sidebar with question pre-filled and sent, including report context):
    - ChatContextProvider.tsx — Add openChatWithQuestion(context: ReportContext, question: string) method. Sets reportContext, sets pendingQuestion state, and opens sidebar.
    - ChatSidebar.tsx — Add useEffect watching pendingQuestion from useChatContext(). When pendingQuestion is set and sidebar is open, call handleFollowUpSelect(pendingQuestion) to send the question as a user message with report context (since reportContext is also set, sendMessage routes to /api/agent/chat with report_context payload). Clear pendingQuestion after consumption via clearPendingQuestion().
    - MorningSummarySection.tsx — Wire SuggestedQuestions onQuestionSelect to call openChatWithQuestion with report context (summaryText, actionItems, reportDate) and the selected question string.

  - AC3 (Suggestions update when smart summary content changes):
    - SuggestedQuestions.tsx — useMemo dependency array includes actionItems and summaryText. When either changes (different date selected, data refreshed), generateSuggestions re-runs and the component re-renders with new suggestions.
    - MorningSummarySection.tsx — Passes data.actions and smartSummary.summary_text as props, which are reactive to hook state changes (useDailyActions and useSmartSummary both re-fetch when report date changes).

risks:
  - Race condition between reportContext set and pendingQuestion send: When openChatWithQuestion sets both reportContext and pendingQuestion simultaneously, ChatSidebar's useEffect for reportContext (line 152) resets messages, while the pendingQuestion useEffect needs to fire after that reset. Mitigation: Use a small delay (setTimeout ~50ms) in the pendingQuestion useEffect or use useRef to track whether the context intro message has been set before sending the pending question. The simplest approach: have the pendingQuestion useEffect check that messages include the report context intro message before sending.
  - handleFollowUpSelect is defined inside ChatSidebar and not exposed via context: The pendingQuestion mechanism avoids this by letting ChatSidebar consume the pending question internally and call its own handleFollowUpSelect. No need to expose handleFollowUpSelect externally.
  - Suggestion staleness when action items are still loading: If useDailyActions hasn't loaded yet (data is null), generateSuggestions receives empty input and returns []. SuggestedQuestions returns null. When data loads, useMemo recalculates and suggestions appear. No stale state.
  - Template questions may feel repetitive across days: The questions reference specific asset names and categories from the day's data, so they naturally vary. For MVP, template-based is acceptable. Can be enhanced with LLM-generated suggestions in a future story.
  - ChatSidebar test disruption: Adding pendingQuestion consumption to ChatSidebar could break existing tests. Mitigation: The new useEffect only fires when pendingQuestion is non-null. The default context has pendingQuestion as null. Existing tests that mock useChatContext with the default values won't trigger the new behavior.

estimated_test_files:
  - apps/web/src/lib/__tests__/generateSuggestions.test.ts: Unit tests for generateSuggestions — returns 2-3 questions when action items exist, returns safety question when safety actions present (with asset name interpolation), returns OEE question with worst-performing asset name, returns financial question when financial actions present, returns empty array when no action items and no summary, respects priority ordering (safety > OEE > financial > trend), updates output when input data changes, handles mixed categories, always generates at most 3 questions
  - apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx: Component tests — renders suggestion chips when action data provided, calls onQuestionSelect with question string when chip clicked, returns null when no suggestions generated (empty actions), has proper ARIA attributes (role="group", aria-label), applies animation classes (animate-in, fade-in), limits display to 2-3 chips maximum, renders ChevronRight icon on each chip
  - apps/web/src/components/chat/__tests__/ChatContextProvider.test.tsx: Extend existing tests — openChatWithQuestion sets reportContext, pendingQuestion, and opens sidebar; clearPendingQuestion resets pendingQuestion to null

implementation_order:
  1. Create apps/web/src/lib/generateSuggestions.ts — Define SuggestionContext interface (actions: ActionItem[], summaryText: string, reportDate: string). Implement generateSuggestions() function: filter actions by category, extract asset names for each category, build template questions referencing specific assets (e.g., "What were the top downtime reasons for {assetName}?"), prioritize safety > OEE > financial > trend, return top 2-3 questions. Import ActionItem and ActionCategory types from @/hooks/useDailyActions.
  2. Create apps/web/src/lib/__tests__/generateSuggestions.test.ts — Write comprehensive unit tests covering all priority scenarios, empty inputs, asset name interpolation, category-specific questions, and output limit. Run tests to verify utility correctness.
  3. Modify apps/web/src/components/chat/ChatContextProvider.tsx — Add pendingQuestion state (string | null, default null). Add openChatWithQuestion(context: ReportContext, question: string) method that calls setReportContext, setPendingQuestion, and setIsOpen(true). Add clearPendingQuestion() method. Export both in ChatContextValue interface.
  4. Modify apps/web/src/components/chat/ChatSidebar.tsx — Destructure pendingQuestion and clearPendingQuestion from useChatContext(). Add a useEffect that watches [pendingQuestion, isOpen, messages]: when pendingQuestion is truthy and isOpen is true and messages length > 0 (context intro has been set), call handleFollowUpSelect(pendingQuestion) and then clearPendingQuestion(). The message length check ensures the report context intro message from the existing useEffect (line 152) has been set before the question is sent.
  5. Create apps/web/src/components/action-list/SuggestedQuestions.tsx — 'use client' component. Props: actionItems (ActionItem[]), summaryText (string), reportDate (string), onQuestionSelect ((question: string) => void). Use useMemo to call generateSuggestions. Return null if no suggestions. Render with FollowUpChips visual pattern (flex wrap, animation, outline buttons, ChevronRight icon, ARIA attributes).
  6. Create apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx — Component tests following FollowUpChips.test.tsx pattern. Mock generateSuggestions module. Test rendering, click callbacks, null return, ARIA, animation classes.
  7. Modify apps/web/src/components/action-list/MorningSummarySection.tsx — Import SuggestedQuestions and openChatWithQuestion (via useChatContext which is already imported). After the "Ask about this" button div (line 394), add <SuggestedQuestions> passing data?.actions, smartSummary?.summary_text, data?.report_date. Wire onQuestionSelect to call openChatWithQuestion with the same report context object used by the "Ask about this" button, plus the selected question string. Place inside the same hasSummary conditional block.
  8. Modify apps/web/src/components/action-list/index.ts — Add `export { SuggestedQuestions } from './SuggestedQuestions'` to barrel exports.
  9. Extend apps/web/src/components/chat/__tests__/ChatContextProvider.test.tsx — Add tests for openChatWithQuestion and clearPendingQuestion.
  10. Run full test suite (cd apps/web && npx vitest run) to verify all new and existing tests pass with no regressions.
DESIGN END

---

## TEST_SPEC: 19-3-context-aware-followup-suggestions
**Timestamp:** 2026-02-13 11:06:14

TEST SPEC START
story_id: 19-3-context-aware-followup-suggestions
generated: 2026-02-13

test_specifications:

## AC1: Given the smart summary is displayed, When the "Ask about this" button area renders, Then 2-3 contextual follow-up questions are shown as clickable chips below the button

### 19-3-context-aware-followup-suggestions-UNIT-001: generateSuggestions returns safety question when safety actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with actionItems containing a safety-category item with asset_name "Press Line 2"
- When: generateSuggestions is called with the context
- Then: The returned array includes a question string referencing safety and "Press Line 2" (e.g., "What actions have been taken on Press Line 2 safety events?")
- Data: `{ actions: [{ id: '1', asset_name: 'Press Line 2', category: 'safety', priority_level: 'critical', ... }], summaryText: 'Safety event on Press Line 2', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-002: generateSuggestions returns OEE question with asset name when OEE actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with actionItems containing an oee-category item with asset_name "Grinder 5"
- When: generateSuggestions is called with the context
- Then: The returned array includes a question string referencing downtime/OEE and "Grinder 5" (e.g., "What were the top downtime reasons for Grinder 5?")
- Data: `{ actions: [{ id: '2', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high', ... }], summaryText: 'OEE drop on Grinder 5', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-003: generateSuggestions returns financial question when financial actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with actionItems containing a financial-category item with asset_name "Kiln 3" and financial_impact_usd of 12500
- When: generateSuggestions is called with the context
- Then: The returned array includes a question string referencing financial impact and "Kiln 3"
- Data: `{ actions: [{ id: '3', asset_name: 'Kiln 3', category: 'financial', financial_impact_usd: 12500, ... }], summaryText: 'Financial loss on Kiln 3', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-004: generateSuggestions returns 2-3 questions when multiple categories present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with actionItems spanning all three categories (safety, oee, financial)
- When: generateSuggestions is called with the context
- Then: The returned array has length between 2 and 3 inclusive
- Data: `{ actions: [safetyItem, oeeItem, financialItem], summaryText: 'Full report summary', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-005: generateSuggestions returns empty array when no action items and no summary
- Priority: P0
- Type: unit
- Given: A SuggestionContext with empty actions array and empty summaryText
- When: generateSuggestions is called with the context
- Then: The returned array is empty (`[]`)
- Data: `{ actions: [], summaryText: '', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-006: generateSuggestions respects priority ordering safety > OEE > financial > trend
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items across all categories (safety, oee, financial) and a non-empty summaryText (enabling trend question)
- When: generateSuggestions is called with the context
- Then: The first question in the returned array is safety-related, the second is OEE-related, and if a third exists it is financial-related (trend question comes last in priority)
- Data: `{ actions: [safetyItem, oeeItem, financialItem], summaryText: 'Full report with trends', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-007: generateSuggestions includes trend question when fewer than 3 category questions are generated
- Priority: P1
- Type: unit
- Given: A SuggestionContext with only one category of action items (e.g., one safety item) and a non-empty summaryText
- When: generateSuggestions is called with the context
- Then: The returned array includes a trend comparison question (e.g., "How does today's OEE compare to last week?") as one of the 2-3 suggestions
- Data: `{ actions: [safetyItem], summaryText: 'Safety event summary', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-008: generateSuggestions never returns more than 3 questions
- Priority: P1
- Type: unit
- Given: A SuggestionContext with many action items across all categories (e.g., 3 safety, 3 OEE, 3 financial items)
- When: generateSuggestions is called with the context
- Then: The returned array has at most 3 elements
- Data: `{ actions: [safetyItem1, safetyItem2, safetyItem3, oeeItem1, oeeItem2, oeeItem3, financialItem1, financialItem2, financialItem3], summaryText: 'Busy day', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-009: generateSuggestions handles mixed categories with correct asset name interpolation
- Priority: P1
- Type: unit
- Given: A SuggestionContext with a safety item for "Press Line 2" and an OEE item for "Grinder 5"
- When: generateSuggestions is called with the context
- Then: Each generated question references the correct asset name for its category (safety question mentions "Press Line 2", OEE question mentions "Grinder 5")
- Data: `{ actions: [{ asset_name: 'Press Line 2', category: 'safety', ... }, { asset_name: 'Grinder 5', category: 'oee', ... }], summaryText: 'Mixed report', reportDate: '2026-02-10' }`

### 19-3-context-aware-followup-suggestions-UNIT-010: SuggestedQuestions renders suggestion chips when action data is provided
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component receives actionItems with safety and oee categories and a non-empty summaryText
- When: The component renders
- Then: 2-3 Button elements are rendered, each displaying the text of a generated suggestion with a ChevronRight icon
- Data: Mock actionItems with safety and oee categories, summaryText "Production summary"

### 19-3-context-aware-followup-suggestions-UNIT-011: SuggestedQuestions calls onQuestionSelect when a chip is clicked
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component renders with valid action data and an onQuestionSelect mock callback
- When: The user clicks on one of the suggestion chips
- Then: onQuestionSelect is called once with the question string from that chip
- Data: Mock actionItems, `onQuestionSelect = vi.fn()`

### 19-3-context-aware-followup-suggestions-UNIT-012: SuggestedQuestions returns null when no suggestions can be generated
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component receives empty actionItems array and empty summaryText
- When: The component renders
- Then: container.firstChild is null (nothing rendered)
- Data: `actionItems: [], summaryText: '', reportDate: '2026-02-10'`

### 19-3-context-aware-followup-suggestions-UNIT-013: SuggestedQuestions has proper ARIA attributes
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component renders with valid action data
- When: The component renders
- Then: The container element has `role="group"` and `aria-label="Suggested follow-up questions about the morning report"`, and each chip button has `aria-label="Ask: {question text}"`
- Data: Mock actionItems with at least one category

### 19-3-context-aware-followup-suggestions-UNIT-014: SuggestedQuestions applies animation classes
- Priority: P1
- Type: unit
- Given: SuggestedQuestions component renders with valid action data
- When: The component renders
- Then: The group container has CSS classes `animate-in` and `fade-in`
- Data: Mock actionItems with at least one category

### 19-3-context-aware-followup-suggestions-UNIT-015: SuggestedQuestions limits display to maximum 3 chips
- Priority: P1
- Type: unit
- Given: generateSuggestions returns exactly 3 questions
- When: The component renders
- Then: Exactly 3 chip buttons are rendered, no more
- Data: Mock actionItems spanning all categories to produce 3 suggestions

### 19-3-context-aware-followup-suggestions-INT-001: SuggestedQuestions renders inside MorningSummarySection below AI summary
- Priority: P0
- Type: integration
- Given: MorningSummarySection has loaded smart summary data and action items with at least one category
- When: The morning summary section renders with hasSummary=true
- Then: The SuggestedQuestions component is rendered within the smart summary card, below the "Ask about this" button row, displaying 2-3 contextual question chips
- Data: Mock useDailyActions returning data.actions with safety/oee items, mock useSmartSummary returning summary_text

### 19-3-context-aware-followup-suggestions-INT-002: MorningSummarySection does not render SuggestedQuestions when no summary
- Priority: P1
- Type: integration
- Given: MorningSummarySection has no smart summary (useSmartSummary returns null or loading state)
- When: The morning summary section renders
- Then: No SuggestedQuestions chips are visible
- Data: Mock useSmartSummary returning null

## AC2: Given the user clicks a suggested question chip, When the chip is clicked, Then the AI chat sidebar opens with that question pre-filled and sent, And the report context is included

### 19-3-context-aware-followup-suggestions-INT-003: Clicking suggestion chip calls openChatWithQuestion with report context and question
- Priority: P0
- Type: integration
- Given: MorningSummarySection renders SuggestedQuestions with valid action data, and useChatContext provides openChatWithQuestion
- When: The user clicks on a suggestion chip (e.g., "What were the top downtime reasons for Grinder 5?")
- Then: openChatWithQuestion is called with: (1) a ReportContext object containing summaryText, actionItems, and reportDate from the current report data, and (2) the question string from the clicked chip
- Data: Mock useChatContext with openChatWithQuestion = vi.fn(), mock action data with oee category

### 19-3-context-aware-followup-suggestions-UNIT-016: ChatContextProvider.openChatWithQuestion sets reportContext, pendingQuestion, and opens sidebar
- Priority: P0
- Type: unit
- Given: ChatContextProvider is rendered with a TestConsumer that calls openChatWithQuestion
- When: openChatWithQuestion is called with a ReportContext and a question string
- Then: isOpen becomes true, reportContext is set to the provided context, and pendingQuestion is set to the provided question string
- Data: `{ summaryText: 'Test summary', actionItems: [{ asset_name: 'Grinder 5' }], reportDate: '2026-02-10' }`, question: "What were the top downtime reasons for Grinder 5?"

### 19-3-context-aware-followup-suggestions-UNIT-017: ChatContextProvider.clearPendingQuestion resets pendingQuestion to null
- Priority: P1
- Type: unit
- Given: ChatContextProvider has a pendingQuestion set via openChatWithQuestion
- When: clearPendingQuestion is called
- Then: pendingQuestion is reset to null
- Data: Previously set pendingQuestion: "What were the top downtime reasons for Grinder 5?"

### 19-3-context-aware-followup-suggestions-INT-004: ChatSidebar consumes pendingQuestion and auto-sends it
- Priority: P0
- Type: integration
- Given: ChatSidebar is open with a reportContext set and a pendingQuestion of "What were the top downtime reasons for Grinder 5?"
- When: The sidebar processes the pendingQuestion (useEffect fires after messages include context intro)
- Then: A user message with the pendingQuestion text appears in the message list, sendMessage is called with the question, and clearPendingQuestion is invoked to reset the pending state
- Data: Mock useChatContext returning pendingQuestion, isOpen=true, and report context

### 19-3-context-aware-followup-suggestions-E2E-001: Full flow - click suggestion chip opens chat with question sent
- Priority: P0
- Type: e2e
- Given: The morning report page is loaded with smart summary and action items containing safety and OEE items
- When: The user clicks one of the suggestion chips below the smart summary
- Then: The chat sidebar slides open, a report context intro message appears, and the clicked question is displayed as a user message with an AI response loading
- Data: Full page render with mocked API responses for useDailyActions and useSmartSummary

## AC3: Given the smart summary content changes (different date or refreshed), When the suggestions are generated, Then the suggestions update to reflect the new report content

### 19-3-context-aware-followup-suggestions-UNIT-018: generateSuggestions output changes when input data changes
- Priority: P0
- Type: unit
- Given: generateSuggestions was called with actions containing oee item for "Grinder 5"
- When: generateSuggestions is called again with different actions containing oee item for "Kiln 3"
- Then: The returned questions now reference "Kiln 3" instead of "Grinder 5"
- Data: First call: `{ actions: [oeeItemGrinder5], ... }`, second call: `{ actions: [oeeItemKiln3], ... }`

### 19-3-context-aware-followup-suggestions-UNIT-019: SuggestedQuestions re-renders with new suggestions when props change
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component was rendered with actionItems containing oee item for "Grinder 5"
- When: The component is re-rendered with new actionItems containing oee item for "Kiln 3"
- Then: The displayed chips update to reflect the new data (questions reference "Kiln 3", previous "Grinder 5" questions are gone)
- Data: Initial props: `{ actionItems: [oeeGrinder5], ... }`, updated props: `{ actionItems: [oeeKiln3], ... }`

### 19-3-context-aware-followup-suggestions-INT-005: Suggestions update when report date changes in MorningSummarySection
- Priority: P1
- Type: integration
- Given: MorningSummarySection is displaying suggestions based on Monday's data (safety item for "Press Line 2")
- When: The report date changes (e.g., user navigates to Tuesday's report) and new data loads with different action items (oee item for "Grinder 5")
- Then: The suggestion chips update to reflect Tuesday's data (no longer shows "Press Line 2" safety question, now shows "Grinder 5" OEE question)
- Data: Two sets of mock data for different report dates

### 19-3-context-aware-followup-suggestions-INT-006: Suggestions update when smart summary is refreshed/regenerated
- Priority: P1
- Type: integration
- Given: MorningSummarySection displays suggestions based on initial smart summary and action items
- When: The user clicks regenerate on the smart summary and new data is returned
- Then: The suggestion chips re-render with suggestions derived from the updated data
- Data: Initial and refreshed mock data with different action items

edge_cases:
  - generateSuggestions with action items that have empty/missing asset_name — should handle gracefully without interpolation errors
  - generateSuggestions with duplicate categories (e.g., 5 OEE items) — should pick the most relevant (e.g., highest priority) asset for the question template
  - SuggestedQuestions receives undefined actionItems — should return null without throwing
  - SuggestedQuestions receives undefined summaryText — should still generate category-based questions from action items alone
  - All action items are of the same category (e.g., all safety) — should still produce 2-3 diverse questions including trend
  - Action items with very long asset names — chip text should truncate gracefully (line-clamp-2)
  - ChatSidebar receives pendingQuestion while sidebar is closed — should not attempt to send until sidebar is open
  - ChatSidebar pendingQuestion fires before report context intro message is set — must wait for context intro before sending
  - Rapid clicks on multiple suggestion chips — only the first click should trigger (debounce or ignore while loading)

error_scenarios:
  - generateSuggestions throws or returns unexpected type — SuggestedQuestions should catch and return null
  - openChatWithQuestion called when ChatContextProvider is not mounted — should no-op via default context
  - ChatSidebar sendMessage fails after pendingQuestion is consumed — error message should appear in chat, pendingQuestion should not re-send
  - Network failure during chat response after suggestion chip click — user sees error state in chat sidebar, not in suggestions component

test_file_mapping:
  - 19-3-context-aware-followup-suggestions-UNIT-001 to UNIT-009: apps/web/src/lib/__tests__/generateSuggestions.test.ts
  - 19-3-context-aware-followup-suggestions-UNIT-010 to UNIT-015: apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
  - 19-3-context-aware-followup-suggestions-UNIT-016 to UNIT-017: apps/web/src/components/chat/__tests__/ChatContextProvider.test.tsx
  - 19-3-context-aware-followup-suggestions-UNIT-018 to UNIT-019: apps/web/src/lib/__tests__/generateSuggestions.test.ts and apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
  - 19-3-context-aware-followup-suggestions-INT-001 to INT-006: apps/web/src/components/action-list/__tests__/MorningSummarySection.suggestions.test.tsx and apps/web/src/components/chat/__tests__/ChatSidebar.pendingQuestion.test.tsx
  - 19-3-context-aware-followup-suggestions-E2E-001: apps/web/src/components/action-list/__tests__/SuggestedQuestions.e2e.test.tsx (or Playwright if available)

TEST SPEC END

---

## TEST_SPEC: 19-3-context-aware-followup-suggestions
**Timestamp:** 2026-02-13 11:06:38

TEST SPEC START
story_id: 19-3-context-aware-followup-suggestions
generated: 2026-02-13

test_specifications:

## AC1: Given the smart summary is displayed, When the "Ask about this" button area renders, Then 2-3 contextual follow-up questions are shown as clickable chips below the button

### 19-3-context-aware-followup-suggestions-UNIT-001: generateSuggestions returns safety question when safety actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items that include at least one item with category "safety" and asset_name "Grinder 5"
- When: generateSuggestions() is called with this context
- Then: The returned array contains a question referencing safety events (e.g., containing "safety" and "Grinder 5")
- Data: ActionItem fixture with category: 'safety', asset_name: 'Grinder 5', priority_level: 'critical'

### 19-3-context-aware-followup-suggestions-UNIT-002: generateSuggestions returns OEE question with specific asset name when OEE actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items that include at least one item with category "oee" and asset_name "Grinder 5"
- When: generateSuggestions() is called with this context
- Then: The returned array contains a question referencing OEE/downtime for "Grinder 5" (e.g., "What were the top downtime reasons for Grinder 5?")
- Data: ActionItem fixture with category: 'oee', asset_name: 'Grinder 5', primary_metric_value: '72%'

### 19-3-context-aware-followup-suggestions-UNIT-003: generateSuggestions returns financial question when financial actions present
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items that include at least one item with category "financial", asset_name "Line 2", and financial_impact_usd: 12500
- When: generateSuggestions() is called with this context
- Then: The returned array contains a question referencing financial impact and "Line 2" (e.g., containing "$12,500" or "production loss" and "Line 2")
- Data: ActionItem fixture with category: 'financial', asset_name: 'Line 2', financial_impact_usd: 12500

### 19-3-context-aware-followup-suggestions-UNIT-004: generateSuggestions returns trend/comparison question as filler
- Priority: P1
- Type: unit
- Given: A SuggestionContext with fewer than 3 category-specific actions (e.g., only 1 safety action) and a valid summary text
- When: generateSuggestions() is called with this context
- Then: The returned array includes a trend/comparison question (e.g., "How does today's OEE compare to last week?") to fill up to 2-3 suggestions
- Data: Single safety ActionItem fixture, summaryText: "OEE was 78% across all lines."

### 19-3-context-aware-followup-suggestions-UNIT-005: generateSuggestions respects priority ordering safety > OEE > financial > trend
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items spanning all three categories (safety, oee, financial) — more than 3 possible questions
- When: generateSuggestions() is called with this context
- Then: The returned array is ordered with safety question first, then OEE, then financial (trend excluded since safety + OEE + financial = 3)
- Data: Fixtures with one safety, one oee, one financial ActionItem each

### 19-3-context-aware-followup-suggestions-UNIT-006: generateSuggestions returns exactly 2-3 questions (not fewer, not more)
- Priority: P0
- Type: unit
- Given: A SuggestionContext with action items spanning all categories (safety, oee, financial) and a valid summary text
- When: generateSuggestions() is called with this context
- Then: The returned array length is between 2 and 3 inclusive
- Data: Multiple ActionItem fixtures across all categories

### 19-3-context-aware-followup-suggestions-UNIT-007: generateSuggestions caps output at 3 questions maximum
- Priority: P0
- Type: unit
- Given: A SuggestionContext with many action items across all categories (e.g., 3 safety, 3 oee, 3 financial items)
- When: generateSuggestions() is called with this context
- Then: The returned array has at most 3 elements
- Data: 9 ActionItem fixtures (3 per category)

### 19-3-context-aware-followup-suggestions-UNIT-008: generateSuggestions returns empty array when no action items and no summary
- Priority: P0
- Type: unit
- Given: A SuggestionContext with an empty actions array and empty/blank summaryText
- When: generateSuggestions() is called with this context
- Then: The returned array is empty ([])
- Data: { actions: [], summaryText: '', reportDate: '2026-02-13' }

### 19-3-context-aware-followup-suggestions-UNIT-009: generateSuggestions uses worst-performing asset name for OEE questions
- Priority: P1
- Type: unit
- Given: A SuggestionContext with multiple OEE action items for different assets, where "Grinder 5" has the highest priority_rank (worst performer)
- When: generateSuggestions() is called with this context
- Then: The OEE question references "Grinder 5" (the worst performer), not other assets
- Data: OEE ActionItem fixtures for "Grinder 5" (priority_rank: 1) and "Line 3" (priority_rank: 3)

### 19-3-context-aware-followup-suggestions-UNIT-010: generateSuggestions includes financial impact amount in financial questions
- Priority: P1
- Type: unit
- Given: A SuggestionContext with a financial action item having financial_impact_usd: 15000
- When: generateSuggestions() is called with this context
- Then: The financial question includes a formatted dollar amount (e.g., "$15,000")
- Data: ActionItem fixture with category: 'financial', financial_impact_usd: 15000

### 19-3-context-aware-followup-suggestions-UNIT-011: generateSuggestions handles mixed categories correctly
- Priority: P1
- Type: unit
- Given: A SuggestionContext with 1 safety and 2 OEE action items (no financial)
- When: generateSuggestions() is called with this context
- Then: The returned array contains a safety question first, then an OEE question, then a trend question (since no financial actions exist)
- Data: 1 safety + 2 oee ActionItem fixtures

### 19-3-context-aware-followup-suggestions-UNIT-012: generateSuggestions returns at least 2 questions when sufficient data exists
- Priority: P1
- Type: unit
- Given: A SuggestionContext with only 1 OEE action item and a valid summary text
- When: generateSuggestions() is called with this context
- Then: The returned array has at least 2 elements (OEE question + trend question)
- Data: Single OEE ActionItem, summaryText with OEE content

### 19-3-context-aware-followup-suggestions-UNIT-013: SuggestedQuestions renders suggestion chips when action data is provided
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component is rendered with actionItems containing safety and OEE items, a valid summaryText, and a reportDate
- When: The component mounts
- Then: 2-3 Button elements with variant="outline" and size="sm" are visible, each containing question text and a ChevronRight icon
- Data: ActionItem fixtures with safety and OEE categories

### 19-3-context-aware-followup-suggestions-UNIT-014: SuggestedQuestions calls onQuestionSelect with correct question text when chip is clicked
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component is rendered with valid actionItems and an onQuestionSelect callback (vi.fn())
- When: The user clicks on one of the suggestion chips
- Then: The onQuestionSelect callback is called exactly once with the question text string displayed on the chip
- Data: ActionItem fixtures, mock onQuestionSelect function

### 19-3-context-aware-followup-suggestions-UNIT-015: SuggestedQuestions returns null when no suggestions can be generated
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component is rendered with empty actionItems array and empty summaryText
- When: The component attempts to render
- Then: The component renders nothing (returns null), no container or chips are present in the DOM
- Data: { actionItems: [], summaryText: '', reportDate: '2026-02-13' }

### 19-3-context-aware-followup-suggestions-UNIT-016: SuggestedQuestions has proper ARIA attributes
- Priority: P0
- Type: unit
- Given: SuggestedQuestions component is rendered with valid action data
- When: The component mounts
- Then: The container element has role="group" and aria-label="Suggested follow-up questions about the morning report", and each chip button has an aria-label starting with "Ask: " followed by the question text
- Data: ActionItem fixtures

### 19-3-context-aware-followup-suggestions-UNIT-017: SuggestedQuestions applies animation classes
- Priority: P1
- Type: unit
- Given: SuggestedQuestions component is rendered with valid action data
- When: The component mounts
- Then: Each suggestion chip has animation classes: "animate-in", "fade-in", "slide-in-from-bottom-2", "duration-300"
- Data: ActionItem fixtures

### 19-3-context-aware-followup-suggestions-UNIT-018: SuggestedQuestions limits display to maximum 3 chips
- Priority: P1
- Type: unit
- Given: SuggestedQuestions component is rendered with action items that could generate more than 3 suggestions (many items across all categories)
- When: The component mounts
- Then: At most 3 chip buttons are rendered in the DOM
- Data: Many ActionItem fixtures across all categories

### 19-3-context-aware-followup-suggestions-UNIT-019: SuggestedQuestions applies custom className
- Priority: P2
- Type: unit
- Given: SuggestedQuestions component is rendered with a className prop "mt-4 custom-class"
- When: The component mounts
- Then: The container element includes "mt-4" and "custom-class" in its class list
- Data: ActionItem fixtures, className="mt-4 custom-class"

## AC2: Given the user clicks a suggested question chip, When the chip is clicked, Then the AI chat sidebar opens with that question pre-filled and sent, And the report context is included

### 19-3-context-aware-followup-suggestions-INT-001: Clicking a suggestion chip opens ChatSidebar with question pre-filled and report context
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with a smart summary and action items, and the ChatContextProvider is available, and the chat sidebar is closed
- When: The user clicks a suggested question chip (e.g., "What were the top downtime reasons for Grinder 5?")
- Then: openChatWithQuestion is called with the ReportContext (summaryText, actionItems, reportDate) and the selected question string, AND the chat sidebar opens (isOpen becomes true)
- Data: Mock useDailyActions returning actions with OEE items, mock useSmartSummary returning summary data, mock useChatContext with openChatWithQuestion spy

### 19-3-context-aware-followup-suggestions-INT-002: ChatSidebar auto-sends the pending question after opening with context
- Priority: P0
- Type: integration
- Given: ChatSidebar is rendered with a ChatContextProvider, and openChatWithQuestion has been called with a question "What were the top downtime reasons for Grinder 5?" and a valid ReportContext
- When: The sidebar opens and the pending question is detected
- Then: handleFollowUpSelect (or equivalent send mechanism) is called with the question text, the question appears as a sent user message, and clearPendingQuestion is called to reset the pending state
- Data: pendingQuestion: "What were the top downtime reasons for Grinder 5?", ReportContext fixture

### 19-3-context-aware-followup-suggestions-INT-003: Report context is included when question is sent from suggestion chip
- Priority: P0
- Type: integration
- Given: The MorningSummarySection has rendered with smart summary containing "OEE across all lines was 82%..." and actions for assets "Grinder 5" and "Line 2"
- When: The user clicks a suggested question chip
- Then: The ReportContext passed to openChatWithQuestion includes summaryText matching the cleaned summary, actionItems matching the current action data, and reportDate matching the current report date
- Data: Mock smart summary and action items data matching MorningSummarySection props

### 19-3-context-aware-followup-suggestions-INT-004: Clicking a second suggestion chip re-sends with updated question
- Priority: P1
- Type: integration
- Given: The user has already clicked one suggestion chip and the chat sidebar is open with a previous question sent
- When: The user clicks a different suggestion chip
- Then: openChatWithQuestion is called again with the new question text, and the new question is sent as a message in the sidebar
- Data: Two different suggestion chips visible, mock openChatWithQuestion

### 19-3-context-aware-followup-suggestions-INT-005: Clicking the same suggestion chip twice triggers the question again
- Priority: P1
- Type: integration
- Given: The user has already clicked a suggestion chip once, and the chat sidebar is open
- When: The user clicks the same suggestion chip again
- Then: The pendingQuestion state triggers the useEffect again (via counter/unique ID mechanism), and the question is re-sent
- Data: Same suggestion chip clicked twice, mock pendingQuestion mechanism

### 19-3-context-aware-followup-suggestions-E2E-001: End-to-end flow from suggestion chip click to AI response
- Priority: P0
- Type: e2e
- Given: The morning report page is loaded with a smart summary and action items, and suggested question chips are visible below the "Ask about this" button
- When: The user clicks the first suggestion chip
- Then: The chat sidebar opens, the report context intro message is shown, the question appears as a user message, and an AI response begins streaming
- Data: Full morning report data with smart summary and action items for at least 2 categories

## AC3: Given the smart summary content changes (different date or refreshed), When the suggestions are generated, Then the suggestions update to reflect the new report content

### 19-3-context-aware-followup-suggestions-UNIT-020: Suggestions recalculate when actionItems prop changes
- Priority: P0
- Type: unit
- Given: SuggestedQuestions is rendered with safety action items generating a safety-related suggestion
- When: The actionItems prop updates to only contain OEE action items (e.g., simulating a date change)
- Then: The rendered suggestion chips update to show OEE-related questions instead of safety questions
- Data: Initial: [safety ActionItem], Updated: [oee ActionItem]

### 19-3-context-aware-followup-suggestions-UNIT-021: Suggestions recalculate when summaryText prop changes
- Priority: P0
- Type: unit
- Given: SuggestedQuestions is rendered with summaryText "OEE was 78% across all lines" and matching action items
- When: The summaryText prop updates to "Safety incident reported on Grinder 5" with updated action items
- Then: The rendered suggestion chips reflect the new content
- Data: Initial summary + actions, updated summary + actions

### 19-3-context-aware-followup-suggestions-UNIT-022: Suggestions recalculate when reportDate prop changes
- Priority: P1
- Type: unit
- Given: SuggestedQuestions is rendered with reportDate "2026-02-12" and associated action items
- When: The reportDate prop changes to "2026-02-13" (with different action items)
- Then: The rendered suggestion chips update to reflect the new date's data
- Data: Two sets of action items for different dates

### 19-3-context-aware-followup-suggestions-INT-006: Suggestions update when MorningSummarySection receives new smart summary data
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with initial smart summary and action data, and suggestion chips are visible
- When: The useSmartSummary and useDailyActions hooks return new data (e.g., after a refresh or date change)
- Then: The suggestion chips re-render with new questions reflecting the updated report content
- Data: Initial mock data → updated mock data with different categories/assets

### 19-3-context-aware-followup-suggestions-UNIT-023: generateSuggestions produces different output for different inputs
- Priority: P1
- Type: unit
- Given: Two different SuggestionContext objects: one with safety actions for "Grinder 5", another with OEE actions for "Line 2"
- When: generateSuggestions() is called with each context
- Then: The returned arrays contain different question strings reflecting the different inputs
- Data: Two distinct SuggestionContext fixtures

### 19-3-context-aware-followup-suggestions-UNIT-024: useMemo prevents unnecessary recalculation with same inputs
- Priority: P2
- Type: unit
- Given: SuggestedQuestions is rendered with specific actionItems and summaryText
- When: The parent component re-renders but passes the same actionItems and summaryText references
- Then: The generateSuggestions function is not called again (memoized result is reused)
- Data: Stable ActionItem array reference, stable summaryText string

edge_cases:
  - Action items array is null or undefined (component should handle gracefully, return null)
  - summaryText is undefined or null (should not throw, treat as empty)
  - Action items with missing asset_name field (should skip or use fallback text)
  - Action items with financial_impact_usd of 0 (should not generate misleading "$0" question)
  - Extremely long asset names (should not break chip layout)
  - Only trend question can be generated (1 item, should still return at least the trend question)
  - All action items are the same category (e.g., 5 OEE items — should generate 1 OEE question + trend, not 5 OEE questions)
  - reportDate is empty string or invalid format
  - ChatSidebar receives pendingQuestion while still processing previous context change (race condition)

error_scenarios:
  - generateSuggestions receives malformed ActionItem objects (missing required fields)
  - onQuestionSelect callback throws an error (component should not crash)
  - ChatContextProvider is not available in the component tree (useChatContext throws)
  - openChatWithQuestion is called but sidebar fails to open (network or state issue)
  - Multiple rapid clicks on suggestion chips (debounce/guard needed)

test_file_mapping:
  - 19-3-context-aware-followup-suggestions-UNIT-001 to UNIT-012: apps/web/src/lib/__tests__/generateSuggestions.test.ts
  - 19-3-context-aware-followup-suggestions-UNIT-013 to UNIT-019: apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
  - 19-3-context-aware-followup-suggestions-UNIT-020 to UNIT-024: apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx
  - 19-3-context-aware-followup-suggestions-INT-001 to INT-003: apps/web/src/components/action-list/__tests__/MorningSummarySection.suggestions.test.tsx
  - 19-3-context-aware-followup-suggestions-INT-004 to INT-006: apps/web/src/components/action-list/__tests__/MorningSummarySection.suggestions.test.tsx
  - 19-3-context-aware-followup-suggestions-E2E-001: apps/web/e2e/morning-report-suggestions.spec.ts (or Cypress/Playwright equivalent)

TEST SPEC END

---
