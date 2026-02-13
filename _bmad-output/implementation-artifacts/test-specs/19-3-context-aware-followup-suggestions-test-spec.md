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
