# Conversational AI Follow-Up - User Acceptance Testing

**Epic**: 19
**Version**: 1.0
**Generated**: 2026-02-13
**Stories Covered**: 3

---

## Overview

### What Was Built

Plant managers can now interact with the AI-generated smart summary on the morning report instead of just reading it. An "Ask about this" button opens the AI chat pre-loaded with the report's context so follow-up questions get context-aware answers. Asset names in the summary are clickable links that jump to the matching action item on the page (or open the asset detail page in a new tab). Suggested follow-up questions appear as clickable chips so managers know what to ask without thinking of questions from scratch.

### Who Should Test

A Plant Manager, Shift Supervisor, or Operations Lead who regularly uses the morning report. No technical knowledge is needed — just familiarity with navigating the morning report page and the AI chat feature.

### Time Estimate

30–45 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: UAT / staging environment URL for the AI Hub application
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Use an existing Plant Manager account with access to the morning report
   - The account must have at least one day of action item data available

3. **Test Data Setup**
   - Ensure the morning report for at least one recent date has:
     - A generated AI smart summary (the "Powered by AI analysis" section)
     - At least 3 action items across different categories (e.g., one safety, one OEE/downtime, one financial)
     - At least 2 action items that reference recognizable asset names (e.g., "Grinder 5", "CAMA 2400")
   - Ideally have a second report date with different data available (for Scenario 8)

4. **Clean State**
   - Close the AI chat sidebar if it is open
   - Scroll to the top of the morning report page
   - Clear any prior chat conversation by refreshing the page

---

## Test Scenarios

### Scenario 1: "Ask About This" Button Appears on the Summary

**Purpose**: Verify the button is visible and correctly positioned when the smart summary is displayed.

**Starting Point**: Navigate to the morning report page for a date that has a generated AI smart summary.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the morning report page | The page loads and the AI smart summary section is visible at the top |
| 2 | Look below the AI summary text, near "Powered by AI analysis" | An "Ask about this" button with a chat/message icon is visible |
| 3 | Verify the button styling | The button has an outline style with a blue accent and looks consistent with the rest of the page design |

**Success Criteria**: The "Ask about this" button is clearly visible below the smart summary when the summary is loaded.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: "Ask About This" Opens Chat with Report Context

**Purpose**: Verify clicking the button opens the AI chat with morning report context pre-loaded.

**Starting Point**: Morning report page with smart summary visible and chat sidebar closed.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click the "Ask about this" button | The AI chat sidebar slides open from the right side of the screen |
| 2 | Read the first message in the chat | A system message says: "I have the morning report context for [date]. Ask me anything about it." (where [date] is the report date) |
| 3 | Type a follow-up question related to the report, e.g., "What was the root cause for [an asset name from the summary]?" and press Enter | The AI responds with information that references specific data from today's morning report — not a generic answer |
| 4 | Verify the AI references specific details | The response mentions asset names, metrics, or action items that appear in the current morning report |

**Success Criteria**: The AI chat opens with report context and can answer questions using specific data from today's morning report.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: Unrelated Questions Still Work Normally

**Purpose**: Verify that having report context loaded does not break the AI's ability to answer other questions.

**Starting Point**: Chat sidebar is open with morning report context loaded (from Scenario 2).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Type a question unrelated to the morning report, e.g., "What was our total production output last month?" | The AI responds with a relevant answer, using its normal data tools — not limited to only morning report context |
| 2 | Verify the response is useful | The answer addresses the question directly, not restricted by the morning report context |

**Success Criteria**: The AI can still answer general questions even when morning report context is loaded.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Clickable Asset Names in the Summary

**Purpose**: Verify that asset names mentioned in the smart summary are clickable and scroll to the corresponding action item.

**Starting Point**: Morning report page with smart summary visible. The summary should mention at least one asset that also appears in the action items list below.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at the AI summary text | Asset names that match action items on the page appear as blue clickable links |
| 2 | Click on a linked asset name (e.g., "Grinder 5") | The page smoothly scrolls down to the action item card for that asset |
| 3 | Observe the target action item card | The card briefly highlights (a blue ring/flash effect) to draw attention to it |
| 4 | Scroll back up to the summary | The asset link is still there and can be clicked again |

**Success Criteria**: Clicking an asset name in the summary scrolls to and highlights the matching action item card.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: Ctrl/Cmd+Click Opens Asset Detail Page

**Purpose**: Verify that holding Ctrl (Windows) or Cmd (Mac) while clicking an asset link opens the asset detail page in a new tab.

**Starting Point**: Morning report page with smart summary containing clickable asset links.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Hold down Ctrl (Windows) or Cmd (Mac) and click a linked asset name in the summary | A new browser tab opens |
| 2 | Check the new tab | It shows the action detail page for that specific asset |
| 3 | Return to the original tab | The morning report page is unchanged |

**Success Criteria**: Ctrl/Cmd+click on an asset link opens the asset detail page in a new browser tab.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Suggested Follow-Up Questions Appear

**Purpose**: Verify that 2–3 suggested follow-up questions are displayed as clickable chips below the summary.

**Starting Point**: Morning report page with smart summary and action items loaded.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look below the "Ask about this" button area | 2–3 suggested question chips are visible (e.g., "What were the top downtime reasons for Grinder 5?", "How does today's OEE compare to last week?") |
| 2 | Verify the questions are relevant to today's report | The questions reference specific asset names, categories, or metrics from today's action items — they are not generic |
| 3 | Verify the chips have arrow icons and consistent styling | Each chip is styled as a small outline button with an arrow icon, matching the application's design |

**Success Criteria**: 2–3 context-specific follow-up question chips are displayed below the summary section.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 7: Clicking a Suggested Question Opens Chat and Sends It

**Purpose**: Verify that clicking a suggested question chip opens the chat and automatically sends the question.

**Starting Point**: Morning report page with suggested question chips visible and chat sidebar closed.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click one of the suggested question chips | The AI chat sidebar opens from the right |
| 2 | Check the chat messages | The selected question appears as a sent message in the chat, and the morning report context is loaded |
| 3 | Wait for the AI response | The AI responds with an answer that references specific data from the morning report |
| 4 | Close the chat sidebar and click a different suggested question chip | The sidebar reopens with the new question sent, and the AI responds to the new question |

**Success Criteria**: Clicking a suggested question opens the chat, sends the question automatically, and receives a context-aware response.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Unrecognized Asset Names Render as Plain Text

**Purpose**: Verify that asset names in the summary that don't match any known action item are displayed as regular text (not clickable).

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Read the smart summary and look for any text that mentions equipment or asset names not listed in the action items below | Those names appear as normal text — not blue, not clickable |
| 2 | Confirm that only names matching actual action items are linked | Only known asset names from the action item list are rendered as clickable links |

**Result**: ☐ Pass  ☐ Fail

---

### Button and Suggestions Hidden When Summary Is Loading or Unavailable

**Purpose**: Verify the "Ask about this" button and suggested questions do not appear when there is no summary.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to a date that has no AI summary generated (or while the summary is loading) | The "Ask about this" button is not visible |
| 2 | Verify the suggested question chips are also absent | No question chips appear when there is no summary |
| 3 | Wait for the summary to finish loading (if applicable) | Once the summary appears, the button and suggestions become visible |

**Result**: ☐ Pass  ☐ Fail

---

### Suggestions Update When Viewing a Different Date

**Purpose**: Verify that suggested questions change when the report date or content changes.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note the current suggested questions on today's report | Record the text of the 2–3 suggested question chips |
| 2 | Navigate to a different report date that has different action items | The page loads with the new date's report |
| 3 | Check the suggested question chips | The questions have updated to reference data from the newly loaded report (different asset names, categories) |

**Result**: ☐ Pass  ☐ Fail

---

### Clearing Report Context in Chat

**Purpose**: Verify the user can clear the morning report context from the chat to start a fresh conversation.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the chat via "Ask about this" so report context is loaded | Chat opens with the morning report context message |
| 2 | Look for a "Clear context" button or option in the chat header | A "Clear context" button is visible |
| 3 | Click the "Clear context" button | The morning report context message is removed and the chat returns to its normal state |
| 4 | Ask a question | The AI responds using its standard tools, without referencing morning report context |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] See an "Ask about this" button on the smart summary section of the morning report
- [ ] Open the AI chat with morning report context pre-loaded by clicking the button
- [ ] Ask follow-up questions and receive answers that reference specific data from today's report
- [ ] Ask unrelated questions without the report context interfering
- [ ] Click asset names in the summary to scroll to the matching action item card
- [ ] Ctrl/Cmd+click asset names to open the asset detail page in a new tab
- [ ] See 2–3 relevant suggested follow-up questions as clickable chips
- [ ] Click a suggested question to open the chat and have it sent automatically
- [ ] Verify that unrecognized asset names appear as plain text (not clickable)
- [ ] Clear the report context from the chat when done

**Minimum passing**: All checkboxes marked

---

## Issues Log

| # | Scenario | Issue Description | Severity | Screenshot |
|---|----------|-------------------|----------|------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Severity Definitions

- **Critical**: Blocks core functionality, cannot proceed
- **Major**: Significant issue but workaround exists
- **Minor**: Cosmetic or minor inconvenience

---

## Sign-off

### Testing Summary

| Metric | Value |
|--------|-------|
| Scenarios Tested | \_\_ / 11 |
| Scenarios Passed | \_\_ / 11 |
| Critical Issues | |
| Major Issues | |
| Minor Issues | |

### Recommendation

☐ **Accept** - All criteria met, ready for production
☐ **Accept with conditions** - Minor issues noted, can proceed
☐ **Reject** - Critical/major issues must be resolved

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Product Owner | | | |
| Tech Lead | | | |

---

## Appendix

### Test Data Reference

- **Required action item categories**: At least one each of safety, OEE, and financial categories for full suggested question coverage
- **Required asset names**: At least 2 recognizable asset names that appear in both the summary text and the action items list (e.g., "Grinder 5", "CAMA 2400")
- **Report dates needed**: Two different dates with generated summaries (for the "suggestions update" edge case test)

### Environment Details

- **Application**: TFN AI Hub
- **Frontend**: Next.js 14 App Router, React 18
- **Backend**: FastAPI with LangChain agent
- **AI Chat**: Uses `/api/agent/chat` endpoint when report context is active, `/api/chat/query` for standard queries
- **Browser support**: Chrome (recommended), Firefox

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-19.md`
- Story 19.1: `_bmad-output/implementation-artifacts/stories/19-1-ask-about-this-button-on-smart-summary.md`
- Story 19.2: `_bmad-output/implementation-artifacts/stories/19-2-clickable-asset-links-in-smart-summary.md`
- Story 19.3: `_bmad-output/implementation-artifacts/stories/19-3-context-aware-followup-suggestions.md`

---

*Generated by BMAD epic-execute workflow*
