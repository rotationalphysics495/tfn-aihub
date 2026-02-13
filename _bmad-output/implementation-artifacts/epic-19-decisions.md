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
