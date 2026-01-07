# User Acceptance Testing (UAT) Document

## Epic 3: Action Engine & AI Synthesis

**Version:** 1.0
**Date:** January 6, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 3 transforms your Command Center into a smart decision-making tool. Instead of manually reviewing multiple dashboards each morning, the system now tells you exactly what needs attention and why. This is where AI meets manufacturing operations.

**In plain terms, we built:**

1. **Action Engine** - A smart prioritization system that automatically identifies the most critical issues requiring your attention. It analyzes safety events, production performance, and financial losses to create a ranked list of what matters most.

2. **Daily Action List** - Your new morning landing page. When you log in, you immediately see a prioritized list of issues to address, ranked by importance: Safety issues always come first, then performance problems, then financial concerns.

3. **Morning Report View** - A redesigned landing page specifically for your morning meetings. See yesterday's performance summary at a glance with clear action items you can discuss with your team.

4. **Insight + Evidence Cards** - Each action recommendation is now shown as a card with two parts: the recommendation on the left ("What to do") and the supporting data on the right ("Why it matters"). You can trust the recommendations because you can see exactly what data supports them.

5. **AI-Powered Smart Summary** - An intelligent summary written in plain English that explains what happened yesterday and what you should focus on today. The AI analyzes all your data and writes a morning briefing for you.

---

## 2. Prerequisites

### Test Environment

| Item | Details |
|------|---------|
| **Application URL** | Contact your IT administrator for the test environment URL |
| **Supported Browsers** | Chrome (recommended), Firefox, Safari, Edge |
| **Supported Devices** | Tablet (iPad/Android recommended), Desktop computer |
| **Recommended Screen** | Tablet or larger for best factory floor visibility |

### Test Accounts

You will need a test account to perform these tests. Contact your IT administrator to obtain:

- Test email address
- Test password

**Note:** Do NOT use production credentials for testing.

### Test Data Requirements

For meaningful testing, ensure the test environment has:

- At least 3-5 assets (machines) configured
- Sample production data from the previous day (yesterday's data)
- At least one unresolved safety event (for Safety priority testing)
- Assets with OEE below 85% target (for OEE priority testing)
- Assets with financial losses above $1,000 (for Financial priority testing)
- Cost center data configured for financial calculations

If test data is not available, some scenarios will show empty states - this is expected behavior.

### Before You Begin

1. Ensure you have a stable internet connection
2. Have the test account credentials ready
3. Have this document available for reference (printed or on a second screen)
4. If using a tablet, ensure it's charged and connected to your facility's network
5. Note: Testing is best performed after 6:30 AM when the morning report pipeline has completed

---

## 3. Test Scenarios

### Scenario 1: Morning Report as Default Landing Page

**Objective:** Verify that after login, you land directly on the Morning Report / Daily Action List page.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Log out if currently logged in | You are on the login page |
| 1.2 | Enter your valid test email and password, then click "Sign In" | You are redirected to the Morning Report page (not the old Command Center) |
| 1.3 | Verify the page header | Page shows "Morning Report" or "Daily Action List" as the title |
| 1.4 | Look for yesterday's date | The page shows which date's data you're viewing (should be yesterday) |
| 1.5 | Verify page loads quickly | Page should display content within 2 seconds of login |

**Pass Criteria:** Login redirects to Morning Report page. Date context is clear.

---

### Scenario 2: Daily Action List Display

**Objective:** Verify the prioritized action list appears correctly on the Morning Report page.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | On the Morning Report page, locate the Action List section | A list of action items is visible (or empty state message if no issues exist) |
| 2.2 | If items exist, verify they are numbered | Each item shows a rank number (#1, #2, #3, etc.) |
| 2.3 | Look at the first few items | Items should be sorted with most critical at the top |
| 2.4 | Identify the category indicators | Each item should show its category: SAFETY, FINANCIAL, or OEE |
| 2.5 | Check for loading state | While data loads, a loading skeleton or spinner appears (not a blank screen) |
| 2.6 | If no action items exist | Message displays: "All systems performing within targets" or similar positive message |

**Pass Criteria:** Action list displays with clear numbering and categories. Empty state is user-friendly.

---

### Scenario 3: Safety Priority - Always First

**Objective:** Verify that Safety issues always appear at the top of the action list.

**Note:** This test requires at least one unresolved safety event in the system.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | On the Morning Report, look at the action list | Safety items (if any exist) appear at the TOP of the list |
| 3.2 | Identify safety items by their category badge | Badge shows "SAFETY" with a red color |
| 3.3 | Verify Safety Red color usage | Safety items use bright red (#DC2626) for their border or accent |
| 3.4 | **CRITICAL CHECK:** Look at non-safety items | Non-safety items should NOT use the same bright red color |
| 3.5 | If multiple safety items exist | They should all appear before any OEE or Financial items |
| 3.6 | Check priority level indicator | Safety items should show "CRITICAL" priority |

**Pass Criteria:** All safety items appear first. Safety Red is exclusive to safety issues.

---

### Scenario 4: OEE Priority Items

**Objective:** Verify that OEE (performance) issues appear after safety items with correct priority indicators.

**Note:** This test requires assets with OEE below the 85% target.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | On the action list, find OEE-related items | Items with "OEE" category badge are visible (after any safety items) |
| 4.2 | Verify the OEE badge color | Badge uses yellow/amber color (NOT red) |
| 4.3 | Check the OEE value displayed | Shows actual OEE percentage vs target (e.g., "OEE: 72.5% vs 85% target") |
| 4.4 | Verify priority level | Items should show HIGH, MEDIUM, or LOW based on how far below target |
| 4.5 | Check ordering within OEE category | Worst performers (biggest gap from target) should appear first |
| 4.6 | Identify the asset name | Each OEE item clearly shows which machine/asset it refers to |

**Pass Criteria:** OEE items appear after safety, sorted by gap severity. Yellow/amber coloring used.

---

### Scenario 5: Financial Impact Priority Items

**Objective:** Verify that Financial loss items appear correctly with dollar amounts.

**Note:** This test requires assets with financial losses above $1,000 threshold.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | On the action list, find Financial-related items | Items with "FINANCIAL" category badge are visible |
| 5.2 | Verify financial items appear after OEE items | Priority order is: Safety > OEE > Financial |
| 5.3 | Check the Financial badge color | Badge uses amber/orange color (NOT red) |
| 5.4 | Look for dollar amounts | Financial impact is displayed in dollars (e.g., "$3,240 loss") |
| 5.5 | Verify currency formatting | Proper dollar sign, comma separators, decimal places (e.g., "$1,234.56") |
| 5.6 | Check ordering within Financial category | Highest losses should appear first |

**Pass Criteria:** Financial items show clear dollar amounts. Sorted by loss amount descending.

---

### Scenario 6: Morning Summary Section

**Objective:** Verify the summary header provides a quick overview of yesterday's performance.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | On the Morning Report page, locate the summary section | Summary appears at the top, above the action list |
| 6.2 | Check for date context | Shows "Yesterday's Performance" with the actual date |
| 6.3 | Look for key metric counts | Shows: Total Action Items, Safety Events count, Financial Items count |
| 6.4 | Verify the numbers match the list | Counts should match actual items in the action list below |
| 6.5 | Look for AI Summary placeholder | A section labeled "AI Summary" or similar exists (may be populated or placeholder) |
| 6.6 | Verify styling | Uses cooler/muted colors (Retrospective mode) indicating historical data |

**Pass Criteria:** Summary shows correct counts matching the action list. Date is clear.

---

### Scenario 7: Insight + Evidence Card Design

**Objective:** Verify action items are displayed as cards with recommendation and evidence.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Click on any action item card OR find the detailed card view | Card expands or navigates to show full Insight + Evidence layout |
| 7.2 | Identify the two-column layout | Left side shows the recommendation; Right side shows supporting data |
| 7.3 | On the LEFT (Insight) side, verify these elements are present: | |
| 7.3a | - Recommendation text | Clear action statement (e.g., "Address Grinder 5 downtime") |
| 7.3b | - Priority badge | SAFETY, FINANCIAL, or OEE badge with appropriate color |
| 7.3c | - Financial impact (if applicable) | Dollar amount prominently displayed |
| 7.3d | - Asset name | Which machine this refers to |
| 7.3e | - Timestamp | When this insight was generated |
| 7.4 | On the RIGHT (Evidence) side, verify these elements: | |
| 7.4a | - Supporting data | Actual metrics or event details that support the recommendation |
| 7.4b | - Data source reference | Shows where the data came from (e.g., "Source: daily_summaries") |
| 7.5 | Try expanding/collapsing the evidence section | Evidence section should expand to show more detail when clicked |
| 7.6 | Look for a "View Details" link | Link should navigate to more detailed information |

**Pass Criteria:** Cards clearly show both the recommendation AND the evidence supporting it.

---

### Scenario 8: Evidence Section - Safety Events

**Objective:** Verify evidence cards for Safety items show correct safety event details.

**Note:** This test requires at least one safety event in the system.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Find a Safety action item and view its evidence | Evidence section is visible |
| 8.2 | Check for safety event time | Shows when the safety event occurred |
| 8.3 | Check for reason code | Shows the safety reason code (e.g., "Safety Interlock") |
| 8.4 | Check for severity level | Shows severity (e.g., Critical, High, Medium) |
| 8.5 | Check for asset reference | Shows which machine had the safety event |
| 8.6 | Verify data source citation | Shows reference like "Source: safety_events, [date]" |

**Pass Criteria:** Safety evidence shows complete event details with verifiable source.

---

### Scenario 9: Evidence Section - OEE Deviation

**Objective:** Verify evidence cards for OEE items show the performance gap clearly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Find an OEE action item and view its evidence | Evidence section is visible |
| 9.2 | Look for actual vs target comparison | Shows both actual OEE and target OEE (e.g., "72.5% vs 85% target") |
| 9.3 | Check for gap visualization | Visual indicator or number showing the gap (e.g., "-12.5% deviation") |
| 9.4 | Check for timeframe | Shows what time period the OEE covers |
| 9.5 | Verify data source citation | Shows reference like "Source: daily_summaries, [date]" |
| 9.6 | If a mini-chart is present | Chart should clearly show actual vs target |

**Pass Criteria:** OEE evidence clearly shows the performance gap with target comparison.

---

### Scenario 10: Evidence Section - Financial Loss

**Objective:** Verify evidence cards for Financial items show cost breakdown.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Find a Financial action item and view its evidence | Evidence section is visible |
| 10.2 | Look for total loss amount | Shows total financial loss in dollars |
| 10.3 | Check for cost breakdown | Shows breakdown by category (e.g., Downtime Cost, Waste Cost) |
| 10.4 | Verify currency formatting | All amounts show proper dollar formatting |
| 10.5 | Check for asset reference | Shows which machine caused the loss |
| 10.6 | Verify data source citation | Shows reference like "Source: daily_summaries, [date]" |

**Pass Criteria:** Financial evidence shows itemized cost breakdown with verifiable source.

---

### Scenario 11: Smart Summary - AI-Generated Text

**Objective:** Verify the AI-powered smart summary is displayed and readable.

**Note:** Smart Summary requires the LLM service to be configured. If not available, a fallback template should display.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | On the Morning Report page, locate the Smart Summary section | Summary section is visible (in header or dedicated area) |
| 11.2 | If AI Summary is available: | |
| 11.2a | - Check for Executive Summary | 2-3 sentence overview of yesterday's performance |
| 11.2b | - Check for Priority Issues | Numbered list of top issues with explanations |
| 11.2c | - Check for data citations | Specific references like "[Asset: Grinder 5, OEE: 72%]" in the text |
| 11.2d | - Check for recommendations | Each issue includes "What to do" action item |
| 11.3 | If AI Summary is NOT available (fallback): | |
| 11.3a | - Check for fallback message | Message like "AI summary unavailable - showing key metrics" |
| 11.3b | - Check for basic metrics | Still shows Safety events count, OEE gaps, Financial losses |
| 11.4 | Verify summary is in plain English | No technical jargon; readable by non-technical managers |
| 11.5 | Check for timestamp | Shows when the summary was generated |

**Pass Criteria:** Either AI summary with citations displays, OR clear fallback with basic metrics.

---

### Scenario 12: Data Citations and Traceability

**Objective:** Verify all AI recommendations cite specific data points (NFR1 Compliance).

| Step | Action | Expected Result |
|------|--------|-----------------|
| 12.1 | Review any Insight + Evidence card | Evidence section is visible |
| 12.2 | Look for "Source:" references | Each evidence piece cites the source table (e.g., "daily_summaries", "safety_events") |
| 12.3 | Look for date references | Citations include the date of the data |
| 12.4 | Look for specific values | Numbers match what's displayed (e.g., if card shows "72% OEE", citation shows same) |
| 12.5 | In the Smart Summary, look for bracketed citations | Format like "[Asset: Grinder 5, OEE: 72%]" |
| 12.6 | **CRITICAL:** No vague claims | Every recommendation should link to specific data, not general statements |

**Pass Criteria:** All recommendations have verifiable data citations. No "trust me" statements.

---

### Scenario 13: View Mode Navigation

**Objective:** Verify users can switch between Morning Report and Live Pulse views.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 13.1 | On the Morning Report page, look for view toggle | Toggle or buttons showing "Morning Report" and "Live Pulse" options |
| 13.2 | Verify current view is highlighted | "Morning Report" should be selected/highlighted |
| 13.3 | Click on "Live Pulse" option | Page navigates to the Live Pulse / Command Center dashboard |
| 13.4 | On Live Pulse page, click "Morning Report" | Returns to the Morning Report page |
| 13.5 | Look for breadcrumb navigation | Shows current location (e.g., "Home > Morning Report") |
| 13.6 | Verify visual styling difference | Morning Report uses cooler colors; Live Pulse uses more vibrant colors |

**Pass Criteria:** Toggle between views works correctly. Visual distinction between views is clear.

---

### Scenario 14: Action Card Drill-Down Navigation

**Objective:** Verify clicking on action cards navigates to detailed information.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 14.1 | On the action list, click on any action item card | Card expands OR navigates to detail page |
| 14.2 | If evidence section expands in-place | More detail is revealed with smooth animation |
| 14.3 | Look for asset name click | Clicking on asset name should navigate to Asset Detail view |
| 14.4 | Look for "View Details" link | Link navigates to full evidence/detail page |
| 14.5 | Use browser back button | Returns to the Morning Report action list |
| 14.6 | Verify keyboard navigation | Tab through cards; Enter key activates the focused card |

**Pass Criteria:** Users can drill down into action items. Navigation works correctly.

---

### Scenario 15: Industrial Clarity - Factory Floor Visibility

**Objective:** Verify all Epic 3 screens meet visibility requirements for factory floor use.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 15.1 | Open Morning Report on a tablet | Page loads completely |
| 15.2 | Step back 3 feet from the screen | Action item titles and priority badges are clearly readable |
| 15.3 | Check the priority ranking numbers | #1, #2, #3 numbers are large and visible from 3 feet |
| 15.4 | Check category badges (SAFETY, OEE, FINANCIAL) | Badges are readable; colors are distinguishable |
| 15.5 | **CRITICAL:** Check Safety Red usage | Only SAFETY items use bright red. OEE uses yellow. Financial uses amber. |
| 15.6 | Check financial amounts | Dollar amounts are readable from 3 feet |
| 15.7 | Check contrast in Summary section | Text stands out clearly against background |
| 15.8 | Open an Insight + Evidence card | Both recommendation and evidence text are readable from 3 feet |

**Pass Criteria:** All primary content readable from 3 feet. Safety Red exclusive to safety items.

---

### Scenario 16: Responsive Design - Tablet and Desktop

**Objective:** Verify Epic 3 screens work well on both tablet and desktop.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 16.1 | View Morning Report on tablet (or resize browser to 768px) | Layout adapts; action cards stack or adjust |
| 16.2 | Insight + Evidence cards on tablet | Two-column layout may stack (evidence below insight) |
| 16.3 | View Morning Report on desktop (full width) | Layout uses available space; cards may show in grid |
| 16.4 | Insight + Evidence cards on desktop | Two-column layout shows side-by-side |
| 16.5 | Rotate tablet between portrait and landscape | Layout adapts to both orientations |
| 16.6 | Check all text is readable | No text is cut off or overlapping in any view |

**Pass Criteria:** All screens work on tablet and desktop. Text never truncated.

---

### Scenario 17: Loading States and Performance

**Objective:** Verify the system handles loading states gracefully and performs well.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 17.1 | Refresh the Morning Report page | Loading skeleton appears immediately (within 500ms) |
| 17.2 | Observe full page load | Complete content displays within 2 seconds |
| 17.3 | If network is slow, observe behavior | Skeleton loaders show, not blank screens |
| 17.4 | Click on an action card to expand | Expansion animates smoothly, no jank |
| 17.5 | Navigate between Morning Report and Live Pulse | Transitions are quick and smooth |

**Pass Criteria:** Loading states always visible. No blank screens. Responsive interactions.

---

### Scenario 18: Empty State Handling

**Objective:** Verify the system handles situations when no action items exist.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 18.1 | If no action items match filters (all systems OK): | |
| 18.1a | - Check action list area | Shows positive message like "All systems performing within targets" |
| 18.1b | - Check for visual indicator | May show a checkmark or positive icon |
| 18.2 | Summary section with no issues | Shows zero counts for all categories (Safety: 0, OEE: 0, Financial: 0) |
| 18.3 | Smart Summary with no issues | Either shows "No issues to report" or positive summary |
| 18.4 | Verify no error messages | Empty state is NOT shown as an error |

**Pass Criteria:** Empty states are positive and user-friendly. No errors shown.

---

### Scenario 19: Error Handling

**Objective:** Verify the system handles errors gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 19.1 | If API fails (simulate by disconnecting network): | |
| 19.1a | - Check for error message | User-friendly message like "Unable to load action list. Please try again." |
| 19.1b | - Check for retry button | Button to retry loading is available |
| 19.2 | If Smart Summary AI fails: | |
| 19.2a | - Check for fallback | Template-based summary shows instead of AI summary |
| 19.2b | - Check for indicator | Message indicates AI summary is unavailable |
| 19.3 | Navigate to non-existent action detail | Friendly 404 or redirect, not crash |
| 19.4 | Verify no technical errors exposed | No stack traces, JSON errors, or database messages shown to users |

**Pass Criteria:** All errors show user-friendly messages with retry options where applicable.

---

### Scenario 20: Authentication Protection

**Objective:** Verify Morning Report and action endpoints require login.

**Automated Verification Command:**
```bash
cd apps/api && source venv/bin/activate && python -m pytest tests/test_actions_api.py::TestVersionedDailyActionListEndpoint::test_v1_daily_endpoint_requires_auth tests/test_auth.py::TestProtectedActionEndpoints -v
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 20.1 | Log out of the application | Redirected to login page |
| 20.2 | Try to navigate directly to Morning Report URL | Redirected to login page (cannot access) |
| 20.3 | Try to access API directly (e.g., /api/v1/actions/daily in browser) | Returns 401 Unauthorized (no data shown) |
| 20.4 | Log back in | Successfully access Morning Report |

**Pass Criteria:** All Epic 3 pages and APIs require authentication.

---

## 4. Success Criteria Checklist

### Action Engine Prioritization

- [ ] Safety items always appear FIRST in the action list
- [ ] Safety items are marked as "CRITICAL" priority
- [ ] OEE items appear AFTER all safety items
- [ ] OEE items sorted by gap severity (worst first)
- [ ] Financial items appear AFTER OEE items
- [ ] Financial items sorted by dollar amount (highest first)
- [ ] No duplicate assets in the list (consolidated)

### Morning Report Landing Page

- [ ] Login redirects to Morning Report (not old dashboard)
- [ ] Page loads within 2 seconds
- [ ] Date context (yesterday) is prominently displayed
- [ ] Summary section shows correct counts
- [ ] Action list displays with priority numbering
- [ ] View mode toggle works (Morning Report / Live Pulse)

### Insight + Evidence Cards

- [ ] Cards show two-column layout (insight left, evidence right)
- [ ] Recommendation text is clear and actionable
- [ ] Priority badge displays with correct color
- [ ] Financial impact shown in dollars where applicable
- [ ] Evidence section shows supporting data
- [ ] Data source citations are present
- [ ] Evidence section can expand/collapse
- [ ] Clicking asset name navigates to details

### Smart Summary (AI)

- [ ] AI summary displays (if configured) with executive overview
- [ ] Priority issues are listed with explanations
- [ ] Data citations in brackets (e.g., [Asset: X, OEE: Y%])
- [ ] Recommendations are specific and actionable
- [ ] Fallback shows key metrics if AI unavailable
- [ ] Summary is in plain English (no jargon)

### Visual Compliance (Industrial Clarity)

- [ ] Safety Red (#DC2626) used ONLY for safety items
- [ ] OEE items use yellow/amber color
- [ ] Financial items use amber/orange color
- [ ] Priority badges readable from 3 feet
- [ ] Dollar amounts readable from 3 feet
- [ ] Action item titles readable from 3 feet
- [ ] High contrast maintained throughout
- [ ] Retrospective mode (cool colors) for historical data

### Data Citations (NFR1 Compliance)

- [ ] Every action item has evidence source reference
- [ ] Citations show table name and date
- [ ] Specific values are cited (not vague claims)
- [ ] Smart Summary includes bracketed citations
- [ ] Users can trace any claim to raw data

### Performance & Accessibility

- [ ] Loading skeletons appear immediately
- [ ] Full page loads within 2 seconds
- [ ] Responsive on tablet and desktop
- [ ] Keyboard navigation works
- [ ] Error states are user-friendly
- [ ] Empty states are positive (not errors)

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **Morning Report Timing:** The AI Smart Summary and action items are based on yesterday's data (T-1). If testing very early in the morning (before 6:30 AM), the morning report pipeline may not have completed yet.

2. **AI Summary Availability:** The Smart Summary requires an LLM service (OpenAI or Anthropic) to be configured. If not configured, a template-based fallback displays - this is expected behavior, not a bug.

3. **Configurable Thresholds:** The default thresholds are:
   - OEE Target: 85% (assets below this appear in action list)
   - Financial Loss: $1,000 (losses above this appear in action list)
   - Your environment may have different thresholds configured.

4. **Safety Event Requirement:** Safety-related testing requires actual safety events in the database. If none exist, safety priority cannot be fully tested.

5. **Asset Deduplication:** If an asset has both safety AND OEE issues, it appears only once in the list (under Safety, the higher priority), with all evidence consolidated.

6. **Live Pulse vs Morning Report:** The Morning Report shows yesterday's data. The Live Pulse shows current shift data (up to 15 minutes old). These are different views with different data.

7. **AI Chat Not Yet Available:** The AI conversational chat feature is planned for Epic 4 and is not part of this testing.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 7, Step 7.3)
2. **Expected Behavior** (what should have happened)
3. **Actual Behavior** (what actually happened)
4. **Screenshots** (if possible)
5. **Browser and Device** used
6. **Date and Time** of the issue
7. **Test Data Used** (which assets, what type of issue)

Report defects to: [Contact your IT administrator or QA lead]

### Severity Guide

| Severity | Description | Example |
|----------|-------------|---------|
| **Critical** | System unusable, data loss, security issue | Cannot login, action list crashes, safety alerts not showing |
| **High** | Major feature broken, workaround difficult | Evidence cards not displaying, wrong priority order |
| **Medium** | Feature partially working, workaround exists | Styling incorrect, minor calculation errors |
| **Low** | Cosmetic issue, enhancement suggestion | Text alignment, color shade preferences |

---

## 7. Sign-Off Section

### Tester Information

| Field | Entry |
|-------|-------|
| **Tester Name** | _________________________________ |
| **Role/Title** | _________________________________ |
| **Test Date** | _________________________________ |
| **Test Environment** | _________________________________ |
| **Browser/Device Used** | _________________________________ |

### Test Results Summary

| Category | Pass | Fail | Not Tested | Notes |
|----------|------|------|------------|-------|
| Morning Report Landing (Scenarios 1-2) | [ ] | [ ] | [ ] | |
| Safety Priority (Scenario 3) | [ ] | [ ] | [ ] | |
| OEE Priority (Scenario 4) | [ ] | [ ] | [ ] | |
| Financial Priority (Scenario 5) | [ ] | [ ] | [ ] | |
| Morning Summary Section (Scenario 6) | [ ] | [ ] | [ ] | |
| Insight + Evidence Cards (Scenarios 7-10) | [ ] | [ ] | [ ] | |
| Smart Summary AI (Scenario 11) | [ ] | [ ] | [ ] | |
| Data Citations (Scenario 12) | [ ] | [ ] | [ ] | |
| View Navigation (Scenarios 13-14) | [ ] | [ ] | [ ] | |
| Industrial Clarity (Scenario 15) | [ ] | [ ] | [ ] | |
| Responsive Design (Scenario 16) | [ ] | [ ] | [ ] | |
| Performance (Scenario 17) | [ ] | [ ] | [ ] | |
| Empty/Error States (Scenarios 18-19) | [ ] | [ ] | [ ] | |
| Authentication (Scenario 20) | [ ] | [ ] | [ ] | |

### Overall Assessment

- [ ] **APPROVED** - All critical scenarios pass. Epic 3 is ready for production deployment.
- [ ] **APPROVED WITH CONDITIONS** - Minor issues noted but do not block deployment.
- [ ] **NOT APPROVED** - Critical issues found. Requires fixes before deployment.

### Comments/Notes

_________________________________________________________________________

_________________________________________________________________________

_________________________________________________________________________

### Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Tester** | | | |
| **QA Lead** | | | |
| **Product Owner** | | | |
| **Technical Lead** | | | |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 6, 2026 | QA Specialist | Initial UAT document for Epic 3 |

---

*End of UAT Document*
