# User Acceptance Testing (UAT) Document

## Epic 2: Data Pipelines & Production Intelligence

**Version:** 1.0
**Date:** January 6, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 2 brings your Command Center to life with real production data, financial insights, and safety monitoring. This is the heart of the Manufacturing Performance Assistant - where you'll spend most of your time monitoring factory floor operations.

**In plain terms, we built:**

1. **Morning Report Pipeline** - Every day at 6:00 AM, the system automatically pulls yesterday's complete production data. When you arrive for your shift, all the numbers are ready and waiting.

2. **Live Pulse Updates** - Every 15 minutes, the system refreshes with the latest production numbers from the floor. You're never more than 15 minutes behind what's actually happening.

3. **Throughput Dashboard** - See at a glance which machines are hitting their targets and which are behind. Green means on track, amber means attention needed.

4. **OEE Metrics View** - The classic Availability × Performance × Quality calculation, broken down by machine and shift, so you know exactly where efficiency is being lost.

5. **Downtime Pareto Analysis** - A chart showing the biggest causes of downtime, ranked from worst to least. Focus on the top few issues to get the biggest improvements.

6. **Safety Alert System** - When any machine reports a "Safety Issue" code, the system immediately shows a red alert. Safety always comes first.

7. **Financial Impact Calculator** - Every minute of downtime and every scrapped unit is translated into dollars. You can see exactly what problems are costing the plant.

8. **Cost of Loss Widget** - A summary widget showing today's total financial losses from downtime and waste, visible right on your dashboard.

9. **Live Pulse Ticker** - A real-time status display showing current shift production, OEE, active machines, and any safety concerns - all updating every 15 minutes.

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
- Sample production data from the previous day (for Morning Report tests)
- At least one safety event in the system (for Safety Alert tests)
- Cost center data configured (for financial calculations)

If test data is not available, some scenarios will show empty states - this is expected behavior.

### Before You Begin

1. Ensure you have a stable internet connection
2. Have the test account credentials ready
3. Have this document available for reference (printed or on a second screen)
4. If using a tablet, ensure it's charged and connected to your facility's network

---

## 3. Test Scenarios

### Scenario 1: Command Center Dashboard - Live View

**Objective:** Verify the Command Center now displays live production data instead of placeholders.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Log in and navigate to the Command Center dashboard | Dashboard loads with multiple data sections visible |
| 1.2 | Locate the "Live Pulse" section | Section shows actual production metrics OR a "No data available" message (not a "Coming Soon" placeholder) |
| 1.3 | Look for the "Last Updated" timestamp | A timestamp shows when data was last refreshed (should be within the last 15 minutes if pipeline is running) |
| 1.4 | Observe the Live Pulse Ticker at the top | Shows current shift throughput, OEE percentage, and machine counts |
| 1.5 | Wait approximately 15 minutes (or click refresh if available) | Data updates with new timestamp |

**Pass Criteria:** Live production data displays (or appropriate empty state). Timestamps are current.

---

### Scenario 2: Throughput Dashboard

**Objective:** Verify the Actual vs Target production view works correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Navigate to the Throughput Dashboard (from Live Pulse section or navigation menu) | Page loads showing asset cards in a grid layout |
| 2.2 | Identify an asset card | Card shows: Asset name, Actual output number, Target number, Percentage of target, and a status color |
| 2.3 | Verify status colors are correct | Green = 100% or above target, Amber = 90-99% of target, Darker amber = below 90% of target |
| 2.4 | **IMPORTANT:** Check for red color usage | Red should NOT appear for production status (red is reserved for safety only) |
| 2.5 | Look for the "Last Updated" indicator | Shows when data was last refreshed |
| 2.6 | If filters are available, try filtering by area | Cards filter to show only selected area |
| 2.7 | If filters are available, try filtering by status (e.g., "Behind Target") | Cards filter to show only assets with that status |
| 2.8 | View on tablet and step back 3 feet | Numbers remain readable from 3 feet away |

**Pass Criteria:** All asset cards display correctly. Status colors match thresholds. No red used for production status. Readable from 3 feet.

---

### Scenario 3: OEE Metrics View

**Objective:** Verify OEE (Overall Equipment Effectiveness) calculations display correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Navigate to the OEE Metrics page (from navigation or link) | Page loads with OEE display |
| 3.2 | Locate the Plant-wide OEE indicator | Large percentage display (e.g., "78.5%") prominently shown |
| 3.3 | Find the three OEE components | Displays show: Availability %, Performance %, Quality % |
| 3.4 | Verify the math makes sense | OEE ≈ Availability × Performance × Quality (as percentages) |
| 3.5 | Check OEE status colors | Green = 85%+, Yellow = 70-84%, Red = below 70% (this is acceptable use of red for OEE, not safety) |
| 3.6 | Find the asset breakdown | List or table showing OEE for each individual machine |
| 3.7 | Look for Yesterday/Live toggle | Toggle should switch between T-1 (yesterday) and Live (current shift) data |
| 3.8 | Toggle between Yesterday and Live | Data changes; visual styling may differ (cooler colors for Yesterday, vibrant for Live) |
| 3.9 | Verify target comparison | If configured, target OEE is shown alongside actual |

**Pass Criteria:** OEE displays correctly with all three components. Toggle works. Asset breakdown available.

---

### Scenario 4: Downtime Pareto Analysis

**Objective:** Verify the downtime breakdown and Pareto chart display correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Navigate to the Downtime Pareto Analysis page | Page loads with a chart and data table |
| 4.2 | Identify the Pareto chart | Bar chart showing downtime by reason code, sorted from highest to lowest |
| 4.3 | Look for the cumulative percentage line | An overlay line showing cumulative % reaching toward 100% |
| 4.4 | Look for the 80% threshold indicator | Line or marker at 80% showing the "Pareto principle" point |
| 4.5 | Review the Cost of Loss widget | Financial summary showing total downtime cost in dollars |
| 4.6 | Review the breakdown table | Table with columns: Asset, Reason Code, Duration, Start Time, End Time, Financial Impact ($) |
| 4.7 | Try sorting the table | Click column headers to sort; verify sorting works |
| 4.8 | If safety-related downtime exists, verify highlighting | "Safety Issue" reason codes should appear in red/highlighted |
| 4.9 | Look for Yesterday/Live toggle | Toggle should switch data source |
| 4.10 | If pagination exists, navigate through pages | Pagination controls work correctly |

**Pass Criteria:** Pareto chart displays correctly. Table is sortable. Safety issues are highlighted. Financial impact shown.

---

### Scenario 5: Safety Alert System

**Objective:** Verify safety alerts display prominently and correctly.

**Note:** This test requires at least one safety event in the system. If none exist, verify the empty state behavior.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Navigate to Command Center dashboard | Dashboard loads |
| 5.2 | Look at the header area | If active safety alerts exist, a red safety indicator badge should be visible with count |
| 5.3 | Look for Safety Alert Banner | If active alerts, a prominent red banner appears at the top of the page |
| 5.4 | **VERIFY EXCLUSIVE RED:** Check that Safety Red color is used ONLY for safety incidents | No other element on the page should use the same shade of bright red |
| 5.5 | Verify alert is readable from distance | Safety banner text should be large enough to read from 3+ feet |
| 5.6 | If banner has a link, click it | Should navigate to asset detail or safety event detail |
| 5.7 | Find and click the Acknowledge button (if available) | Alert should be dismissed (may require appropriate permissions) |
| 5.8 | If no safety events exist, verify empty state | No red indicators should appear anywhere on dashboard |

**Pass Criteria:** Safety alerts are highly visible. Safety Red is used ONLY for actual safety incidents. Alerts can be acknowledged.

---

### Scenario 6: Financial Impact Display

**Objective:** Verify financial costs are displayed throughout the system.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Navigate to Command Center dashboard | Dashboard loads |
| 6.2 | Locate the Financial Intelligence / Cost of Loss widget | Widget displays total financial loss in dollars (e.g., "$12,500.00") |
| 6.3 | Verify currency formatting | Dollar sign present, proper comma separation for thousands, two decimal places |
| 6.4 | Look for breakdown categories | Should show: Downtime Cost, Waste/Scrap Cost, possibly OEE Loss Cost |
| 6.5 | Navigate to Throughput Dashboard | Cost of Loss widget should also appear here |
| 6.6 | Navigate to Downtime Pareto Analysis | Cost of Loss widget should also appear here |
| 6.7 | Verify financial values in the downtime table | Each row should show a Financial Impact ($) column |
| 6.8 | Check for loading states | When refreshing, widget should show loading indicator |

**Pass Criteria:** Financial data displays consistently across all views. Currency is properly formatted.

---

### Scenario 7: Live Pulse Ticker

**Objective:** Verify the real-time status ticker displays correctly and updates.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Navigate to Command Center dashboard | Dashboard loads with Live Pulse Ticker visible |
| 7.2 | Identify production metrics | Shows: Current Output, Target Output, Throughput Percentage |
| 7.3 | Identify OEE metric | Shows current shift OEE percentage |
| 7.4 | Identify machine status counts | Shows counts for: Running, Idle, Down machines |
| 7.5 | Identify financial impact | Shows current shift Cost of Loss in dollars |
| 7.6 | Look for active downtime | If machines are down, shows reason codes |
| 7.7 | Look for safety indicator | If safety events active, safety section shows red alert |
| 7.8 | Check "Last Updated" timestamp | Should be within last 15-20 minutes |
| 7.9 | Check for "Live" indicator | Pulsing or animated indicator showing data is live |
| 7.10 | Wait 15+ minutes or trigger refresh | Data updates with new timestamp |
| 7.11 | If data is older than 20 minutes | "Data Stale" warning should appear |

**Pass Criteria:** All ticker sections display correctly. Live indicator is visible. Data refreshes periodically.

---

### Scenario 8: Data Freshness and Staleness

**Objective:** Verify the system properly indicates when data is fresh or stale.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Check any dashboard showing live data | "Last Updated" timestamp visible |
| 8.2 | Verify timestamp format | Should show time in readable format (e.g., "2 minutes ago" or "10:45 AM") |
| 8.3 | If data is within 15 minutes | No warning should appear |
| 8.4 | If data is between 15-20 minutes old | May show subtle freshness indicator |
| 8.5 | If data is over 20 minutes old | Clear "Data Stale" warning should appear |
| 8.6 | Look for manual refresh option | Refresh button should be available |
| 8.7 | Click refresh button | Data should reload and timestamp updates |

**Pass Criteria:** Users can always tell how fresh the data is. Stale data triggers a warning.

---

### Scenario 9: Industrial Clarity - Factory Floor Visibility

**Objective:** Verify all screens meet visibility requirements for factory floor use.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Open Live Pulse Ticker on a tablet | Display loads |
| 9.2 | Step back 3 feet from the screen | Primary metrics (OEE %, Output numbers) are clearly readable |
| 9.3 | Observe color contrast | All text stands out clearly against backgrounds |
| 9.4 | Check Safety Alerts (if present) | Red safety alerts are immediately noticeable |
| 9.5 | Check status indicators | Green/Amber/Red indicators are distinguishable |
| 9.6 | Open Throughput Dashboard on tablet | Cards display clearly |
| 9.7 | Step back 3 feet | Asset names and percentages are readable |
| 9.8 | Open OEE Metrics on tablet | Large OEE gauge/number displays |
| 9.9 | Step back 3 feet | OEE percentage is clearly visible |

**Pass Criteria:** All primary metrics are readable from 3 feet away. High contrast maintained.

---

### Scenario 10: Morning Report Data (T-1)

**Objective:** Verify yesterday's data is available and correctly labeled.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Navigate to OEE Metrics page | Page loads |
| 10.2 | Select "Yesterday" view (if toggle available) | Data switches to T-1 (yesterday's data) |
| 10.3 | Verify visual styling change | "Yesterday" view should have cooler/more muted colors than "Live" view |
| 10.4 | Navigate to Downtime Pareto Analysis | Page loads |
| 10.5 | Select "Yesterday" view | Data switches to T-1 |
| 10.6 | Verify data shows yesterday's date | Date indicators should show previous day |
| 10.7 | Compare numbers between Yesterday and Live | Values should differ (unless production is identical) |

**Pass Criteria:** Yesterday's data is accessible and visually distinguished from live data.

---

### Scenario 11: Empty States and Error Handling

**Objective:** Verify the system handles missing data gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | If an asset has no data, view its card | Should show "No data available" message, not an error |
| 11.2 | If no downtime events exist, view Pareto page | Should show "No downtime events" message, chart area empty but not broken |
| 11.3 | If no safety events exist | Safety indicators should be hidden or show "0", not "Error" |
| 11.4 | If financial data missing, view Cost of Loss | Should show "$0.00" or "N/A", not an error |
| 11.5 | Navigate to a non-existent page (e.g., `/dashboard/invalid`) | Friendly 404 error page, not a crash |
| 11.6 | If API is slow, observe loading states | Skeleton loaders or spinners should appear, not blank screens |

**Pass Criteria:** All empty/error states show user-friendly messages. No technical errors exposed.

---

## 4. Success Criteria Checklist

### Data Pipelines

- [ ] Morning Report data (yesterday) is available
- [ ] Live Pulse data updates every 15 minutes
- [ ] Data freshness timestamps are accurate
- [ ] Stale data warnings appear when appropriate

### Throughput Dashboard

- [ ] All assets display with actual/target values
- [ ] Status colors are correct (green/amber, NO red for production)
- [ ] Filters work correctly (area, status)
- [ ] Data refreshes automatically
- [ ] Readable from 3 feet on tablet

### OEE Metrics

- [ ] Plant-wide OEE displays prominently
- [ ] Three components (A×P×Q) show correctly
- [ ] Per-asset breakdown is available
- [ ] Yesterday/Live toggle works
- [ ] Color coding matches thresholds

### Downtime Pareto

- [ ] Pareto chart displays correctly
- [ ] Cumulative percentage line visible
- [ ] 80% threshold marked
- [ ] Table is sortable
- [ ] Safety issues are highlighted in red
- [ ] Financial impact shown per event

### Safety Alerts

- [ ] Active safety alerts show red indicator
- [ ] Safety banner is prominent and readable
- [ ] Safety Red is used ONLY for safety incidents
- [ ] Alerts link to details
- [ ] Acknowledgment works

### Financial Context

- [ ] Cost of Loss widget displays on Command Center
- [ ] Cost of Loss widget displays on Throughput Dashboard
- [ ] Cost of Loss widget displays on Downtime Pareto
- [ ] Currency formatting is correct ($X,XXX.XX)
- [ ] Breakdown shows Downtime and Waste costs

### Live Pulse Ticker

- [ ] Production metrics display
- [ ] OEE metric displays
- [ ] Machine status counts display
- [ ] Financial impact displays
- [ ] Safety indicator works
- [ ] "Live" pulsing indicator visible
- [ ] Auto-refresh works

### Industrial Clarity

- [ ] All primary metrics readable from 3 feet
- [ ] High contrast maintained
- [ ] Safety Red used exclusively for safety
- [ ] Visual distinction between Live and Yesterday views

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **15-Minute Data Delay:** Live data is at most 15 minutes old. This is by design - the system polls every 15 minutes to balance freshness with system load.

2. **Morning Report Timing:** Yesterday's complete data is available after 6:00 AM. If testing before 6 AM, T-1 data may be incomplete.

3. **Financial Estimates:** If cost center data is not configured for an asset, financial calculations use default rates. These may be flagged as "Estimated" in the display.

4. **Safety Event Simulation:** If no real safety events exist in the test environment, safety alert functionality cannot be fully tested.

5. **Action List Placeholder:** The Daily Action List section remains a placeholder - this will be implemented in Epic 3.

6. **AI Features Not Yet Active:** The AI chat and synthesis features are not yet available - these will be implemented in Epic 3 and 4.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 4, Step 4.3)
2. **Expected Behavior** (what should have happened)
3. **Actual Behavior** (what actually happened)
4. **Screenshots** (if possible)
5. **Browser and Device** used
6. **Date and Time** of the issue

Report defects to: [Contact your IT administrator or QA lead]

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
| Live View Dashboard (Scenario 1) | [ ] | [ ] | [ ] | |
| Throughput Dashboard (Scenario 2) | [ ] | [ ] | [ ] | |
| OEE Metrics View (Scenario 3) | [ ] | [ ] | [ ] | |
| Downtime Pareto (Scenario 4) | [ ] | [ ] | [ ] | |
| Safety Alert System (Scenario 5) | [ ] | [ ] | [ ] | |
| Financial Impact Display (Scenario 6) | [ ] | [ ] | [ ] | |
| Live Pulse Ticker (Scenario 7) | [ ] | [ ] | [ ] | |
| Data Freshness (Scenario 8) | [ ] | [ ] | [ ] | |
| Factory Floor Visibility (Scenario 9) | [ ] | [ ] | [ ] | |
| Morning Report Data (Scenario 10) | [ ] | [ ] | [ ] | |
| Empty States/Errors (Scenario 11) | [ ] | [ ] | [ ] | |

### Overall Assessment

- [ ] **APPROVED** - All critical scenarios pass. Epic 2 is ready for production deployment.
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
| 1.0 | January 6, 2026 | QA Specialist | Initial UAT document for Epic 2 |

---

*End of UAT Document*
