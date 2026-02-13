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
