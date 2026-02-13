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
