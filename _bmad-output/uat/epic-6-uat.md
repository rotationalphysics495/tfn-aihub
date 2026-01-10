# User Acceptance Testing (UAT) Document

## Epic 6: Safety & Financial Intelligence Tools

**Version:** 1.0
**Date:** January 9, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 6 adds safety and financial intelligence tools to your AI assistant. You can now ask about safety incidents, understand the financial impact of downtime and waste, identify your biggest cost drivers, and analyze performance trends over time.

**In plain terms, we built:**

1. **Safety Events Tool** - Ask "Any safety incidents today?" and get a complete list of safety events with severity levels, affected assets, and resolution status. Critical incidents appear first so you can prioritize action.

2. **Financial Impact Tool** - Ask "What's the cost of downtime for Grinder 5 yesterday?" and see dollar amounts with transparent calculations. The AI shows you exactly how it calculated the cost (downtime minutes x hourly rate).

3. **Cost of Loss Tool** - Ask "What are we losing money on?" and get a ranked list of your biggest cost drivers. See what's costing you the most, grouped by category (downtime, waste, quality), with root causes identified where available.

4. **Trend Analysis Tool** - Ask "How has Grinder 5 performed over the last 30 days?" and see if performance is improving, declining, or stable. The AI highlights anomalies (unusual days) and compares current performance to baseline.

---

## 2. Prerequisites

### Test Environment

| Item | Details |
|------|---------|
| **Application URL** | Contact your IT administrator for the test environment URL |
| **Supported Browsers** | Chrome (recommended), Firefox, Safari, Edge |
| **Supported Devices** | Desktop computer, tablet (iPad/Android) |
| **Recommended Screen** | Tablet or larger for best experience |

### Test Accounts

You will need a test account to perform these tests. Contact your IT administrator to obtain:

- Test email address
- Test password

**Note:** Do NOT use production credentials for testing.

### Test Data Requirements

For meaningful testing, ensure the test environment has:

- At least 5-8 assets configured across multiple areas (e.g., Grinding, Packaging)
- Safety events with various severity levels (critical, high, medium, low)
- Safety events with different resolution statuses (open, under investigation, resolved)
- Cost center data configured for assets (hourly rates, cost per unit)
- Daily summaries with downtime minutes, waste counts, and OEE values
- Downtime reasons recorded for root cause analysis
- At least 7-30 days of historical data for trend analysis

### Before You Begin

1. Ensure you have a stable internet connection
2. Log in to the application (you should see the Command Center)
3. Have this document available for reference
4. Note: AI responses typically take 1-3 seconds; complex queries may take up to 5 seconds

---

## 3. Test Scenarios

### Scenario 1: Safety Events - Basic Query

**Objective:** Verify the AI can retrieve safety incidents for a given time period.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Open the AI chat sidebar | Chat displays |
| 1.2 | Type: "Any safety incidents today?" | Text appears in input field |
| 1.3 | Press Enter to send | Message sends, loading indicator appears |
| 1.4 | Wait for the response (1-3 seconds) | AI responds with safety information |
| 1.5 | Check the response content | Response includes: (a) Count of safety events, (b) For each event: timestamp, asset name, severity, description, (c) Resolution status (open/under investigation/resolved), (d) Affected area |
| 1.6 | Verify sorting order | Events sorted by severity (critical first), then by recency |
| 1.7 | Look for citations in the response | Response shows source citations (e.g., "[Source: safety_events]") |

**Pass Criteria:** AI provides complete safety event list with all data points. Critical events appear first.

---

### Scenario 2: Safety Events - Area Filter

**Objective:** Verify the AI can filter safety incidents by area.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Open the AI chat | Chat displays |
| 2.2 | Type: "Show me safety incidents for the Packaging area this week" | Text appears |
| 2.3 | Press Enter to send | Message sends |
| 2.4 | Wait for the response | AI responds with filtered safety data |
| 2.5 | Check the response content | Response shows: (a) Only events from Packaging area, (b) Summary statistics (total events, resolved vs open) |
| 2.6 | Verify all events are from Packaging | No events from other areas appear |

**Pass Criteria:** AI correctly filters to requested area and shows summary statistics.

---

### Scenario 3: Safety Events - Severity Filter

**Objective:** Verify the AI can filter safety incidents by severity level.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Type: "Show me critical safety incidents" | Message sends |
| 3.2 | Wait for the response | AI responds with filtered data |
| 3.3 | Check the response content | Only "critical" severity events appear |
| 3.4 | Try: "What about high severity safety incidents?" | Another severity filter |
| 3.5 | Check the response | Only "high" severity events appear |

**Pass Criteria:** AI correctly filters by severity level.

---

### Scenario 4: Safety Events - No Incidents

**Objective:** Verify the AI responds appropriately when no safety incidents exist.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Ask about a time/area combination with no incidents | Message sends |
| 4.2 | Example: "Any safety incidents in Assembly yesterday?" (if Assembly had none) | Query sends |
| 4.3 | Check the response | Response states "No safety incidents recorded for [scope] in [time range]" |
| 4.4 | Verify tone | Message is presented as positive news (not an error) |

**Pass Criteria:** AI provides positive acknowledgment when no incidents found.

---

### Scenario 5: Financial Impact - Single Asset

**Objective:** Verify the AI can calculate financial impact for a specific asset.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Open the AI chat | Chat displays |
| 5.2 | Type: "What's the cost of downtime for Grinder 5 yesterday?" | Text appears |
| 5.3 | Press Enter to send | Message sends |
| 5.4 | Wait for the response | AI responds with financial data |
| 5.5 | Check the response content | Response includes: (a) Total financial loss in dollars, (b) Breakdown by category (downtime cost, waste cost), (c) Hourly rate used for calculation, (d) Comparison to average loss for this asset |
| 5.6 | Verify calculation transparency | Response shows formulas (e.g., "47 min x $2,393.62/hr / 60 = $1,875.00") |
| 5.7 | Look for citations | Citations reference daily_summaries and cost_centers |

**Pass Criteria:** AI provides complete financial breakdown with transparent calculations.

---

### Scenario 6: Financial Impact - Area Level

**Objective:** Verify the AI can aggregate financial impact across an area.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Type: "What's the financial impact for the Grinding area this week?" | Message sends |
| 6.2 | Wait for the response | AI responds with aggregated data |
| 6.3 | Check the response content | Response includes: (a) Total loss across all assets in area, (b) Per-asset breakdown, (c) Highest-cost asset identified |
| 6.4 | Verify the highest-cost asset | Should be clearly highlighted as the top contributor |

**Pass Criteria:** AI aggregates correctly and identifies the highest-cost asset.

---

### Scenario 7: Financial Impact - Missing Cost Data

**Objective:** Verify the AI handles missing cost center data gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Ask about an asset without cost center data configured (if available in test data) | Message sends |
| 7.2 | Wait for the response | AI responds honestly |
| 7.3 | Check the response | Response indicates "Unable to calculate financial impact for [asset] - no cost center data" |
| 7.4 | Look for alternative metrics | Response provides non-financial metrics (downtime minutes, waste count) |

**Pass Criteria:** AI honestly indicates when cost data is unavailable and provides alternative information.

---

### Scenario 8: Cost of Loss - Basic Query

**Objective:** Verify the AI can rank financial losses across the plant.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Open the AI chat | Chat displays |
| 8.2 | Type: "What are we losing money on?" | Text appears |
| 8.3 | Press Enter to send | Message sends |
| 8.4 | Wait for the response | AI responds with ranked losses |
| 8.5 | Check the response content | Response includes: (a) Ranked list of losses (highest first), (b) For each loss: asset, category, amount, root cause, (c) Total loss across all items, (d) Percentage of total for each item |
| 8.6 | Verify grouping | Losses grouped by category (downtime, waste, quality) |
| 8.7 | Look for root causes | Root causes shown where available (e.g., "Material Jam", "Blade Change") |

**Pass Criteria:** AI provides comprehensive ranked loss analysis with root causes.

---

### Scenario 9: Cost of Loss - Top N Query

**Objective:** Verify the AI can limit results and show trends.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Type: "What are the top 3 cost drivers this week?" | Message sends |
| 9.2 | Wait for the response | AI responds |
| 9.3 | Check the response content | Response shows: (a) Only top 3 items, (b) Trend vs previous week (up/down/stable) |
| 9.4 | Verify trend indicators | Each item shows if it's getting better or worse |

**Pass Criteria:** AI limits to requested number and includes trend comparison.

---

### Scenario 10: Cost of Loss - Area Filter with Comparison

**Objective:** Verify the AI can filter by area and compare to plant average.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Type: "What's the cost of loss for the Grinding area?" | Message sends |
| 10.2 | Wait for the response | AI responds with area-specific data |
| 10.3 | Check the response content | Response shows: (a) Losses filtered to Grinding area only, (b) Comparison to plant-wide average |
| 10.4 | Verify comparison | Shows if area is above/below plant average (with percentage) |

**Pass Criteria:** AI filters to area and provides plant-wide comparison.

---

### Scenario 11: Trend Analysis - Basic Query

**Objective:** Verify the AI can analyze performance trends over time.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | Open the AI chat | Chat displays |
| 11.2 | Type: "How has Grinder 5 performed over the last 30 days?" | Text appears |
| 11.3 | Press Enter to send | Message sends |
| 11.4 | Wait for the response | AI responds with trend analysis |
| 11.5 | Check the response content | Response includes: (a) Trend direction (improving/declining/stable), (b) Average metric value over the period, (c) Min and max values with dates, (d) Notable anomalies (unusual values), (e) Comparison to baseline (first week of period) |
| 11.6 | Verify the conclusion | AI provides text explaining the trend supported by data |

**Pass Criteria:** AI provides complete trend analysis with supporting evidence.

---

### Scenario 12: Trend Analysis - Metric Specific

**Objective:** Verify the AI can focus on specific metrics.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 12.1 | Type: "What's the OEE trend for Grinder 5 this month?" | Message sends |
| 12.2 | Wait for the response | AI responds with OEE-specific trend |
| 12.3 | Check the response | Focus is on OEE metric specifically |
| 12.4 | Try: "How about the downtime trend?" | Different metric |
| 12.5 | Check the response | Focus shifts to downtime metric |

**Pass Criteria:** AI correctly focuses on requested metric type.

---

### Scenario 13: Trend Analysis - Custom Time Range

**Objective:** Verify the AI supports various time ranges and adjusts granularity.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 13.1 | Type: "How has Grinder 5 performed over the last 90 days?" | Message sends |
| 13.2 | Wait for the response | AI responds with extended trend |
| 13.3 | Check the granularity | For 90 days, data should be weekly (not daily) for clarity |
| 13.4 | Ask: "What about the last 14 days?" | Shorter period |
| 13.5 | Check the granularity | Should use daily granularity |

**Pass Criteria:** AI adjusts granularity appropriately based on time range.

---

### Scenario 14: Trend Analysis - Insufficient Data

**Objective:** Verify the AI handles cases with not enough data for trend analysis.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 14.1 | Ask about a trend for a new asset with less than 7 days of data | Message sends |
| 14.2 | Wait for the response | AI responds honestly |
| 14.3 | Check the response | States "Not enough data for trend analysis - need at least 7 days" |
| 14.4 | Look for alternative | Shows available point-in-time data instead |
| 14.5 | Look for suggestion | Suggests trying a longer time range |

**Pass Criteria:** AI honestly indicates insufficient data and provides helpful alternatives.

---

### Scenario 15: Trend Analysis - Anomaly Detection

**Objective:** Verify the AI detects and highlights unusual performance days.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 15.1 | Type: "How has Grinder 5 performed over the last 30 days?" | Message sends |
| 15.2 | Wait for the response | AI responds with trend |
| 15.3 | Look for anomalies section | If anomalies exist, they are highlighted |
| 15.4 | Check anomaly details | Each anomaly shows: (a) Date, (b) Value observed, (c) How far from average (e.g., "2.5 standard deviations below mean"), (d) Possible cause (if available from downtime reasons) |

**Pass Criteria:** Anomalies (>2 standard deviations from mean) are detected and explained.

---

### Scenario 16: Cross-Tool Query Flow

**Objective:** Verify follow-up questions work across the new tools.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 16.1 | Ask: "Any safety incidents today?" | Get safety response |
| 16.2 | Look for follow-up chips | Suggestions like "What's the financial impact?" may appear |
| 16.3 | Click a relevant follow-up chip | Question sends automatically |
| 16.4 | Verify response | Appropriate tool responds |
| 16.5 | Ask: "What are the top cost drivers?" | Cost of loss query |
| 16.6 | Look for follow-up chips | May suggest drilling into specific assets |

**Pass Criteria:** Follow-up questions guide users naturally between related tools.

---

### Scenario 17: Citation Verification - Financial Tools

**Objective:** Verify financial calculations are properly cited and transparent.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 17.1 | Ask: "What's the financial impact for Grinder 5 yesterday?" | Message sends |
| 17.2 | Look for calculation citations | Formulas shown inline (e.g., "47 min x $2,393.62/hr / 60 = $1,875.00") |
| 17.3 | Look for data source citations | References to daily_summaries, cost_centers tables |
| 17.4 | Click a citation (if clickable) | Shows source details (table, timestamp) |
| 17.5 | Verify all financial figures are cited | No figures appear without supporting evidence |

**Pass Criteria:** All financial calculations show their formulas and data sources.

---

### Scenario 18: Time Range Interpretation

**Objective:** Verify the AI correctly interprets various time expressions.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 18.1 | Ask: "Any safety incidents yesterday?" | Covers yesterday only |
| 18.2 | Ask: "What were the costs this week?" | Covers current week |
| 18.3 | Ask: "Show me the trend for the last 14 days" | Covers exactly 14 days |
| 18.4 | Ask: "What happened today?" | Covers today only |
| 18.5 | Check date ranges in responses | Each response should cite the actual date range queried |

**Pass Criteria:** AI correctly interprets time expressions and shows date ranges in responses.

---

### Scenario 19: Response Caching - Performance Test

**Objective:** Verify repeated queries return faster due to caching.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 19.1 | Ask: "Any safety incidents today?" | First query |
| 19.2 | Note the response time | May take 1-3 seconds |
| 19.3 | Wait 30 seconds | Brief pause (safety data has 60s cache) |
| 19.4 | Ask the exact same question | Same query |
| 19.5 | Note the response time | Should be faster (under 1 second) |
| 19.6 | Ask: "What's the financial impact for Grinder 5?" | Financial query |
| 19.7 | Repeat after 5 minutes | Within 15-minute cache |
| 19.8 | Note response time | Should still be fast |

**Pass Criteria:** Cached queries are noticeably faster. Safety data caches for 60 seconds, financial data for 15 minutes.

---

### Scenario 20: Error Handling

**Objective:** Verify the tools handle errors gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 20.1 | Ask about a non-existent asset: "What's the cost for Machine XYZ999?" | Message sends |
| 20.2 | Check response | Indicates asset not found, may suggest similar assets |
| 20.3 | Ask an unsupported question: "Predict next week's safety incidents" | Prediction request |
| 20.4 | Check response | AI indicates it cannot predict future events |
| 20.5 | Send an empty message | Press Enter with no text |
| 20.6 | Verify behavior | Message should not send (button disabled or ignored) |

**Pass Criteria:** Errors show friendly messages. AI never fabricates data.

---

### Scenario 21: Mobile Responsiveness

**Objective:** Verify the new tools work on smaller screens.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 21.1 | Open the app on a tablet or resize browser to tablet width | Chat adjusts |
| 21.2 | Ask: "What are we losing money on?" | Cost of loss query |
| 21.3 | Check if ranked list is readable | List displays clearly |
| 21.4 | Check if percentages and amounts are visible | Numbers not cut off |
| 21.5 | Check follow-up chips | Chips are tappable with adequate touch target |
| 21.6 | On mobile width (~375px) | Chat takes full width, data still readable |

**Pass Criteria:** Financial tables and lists are readable on smaller screens.

---

### Scenario 22: Data Freshness Indicators

**Objective:** Verify responses indicate when data was last updated.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 22.1 | Ask any question from the new tools | Get response |
| 22.2 | Look for data freshness indicator | Response includes timestamp or "as of" time |
| 22.3 | Check safety events query | Should show data freshness (60-second cache means very recent) |
| 22.4 | Check financial query | Should show data freshness |

**Pass Criteria:** All responses include data freshness information.

---

## 4. Success Criteria Checklist

### Safety Events Tool

- [ ] Can query safety incidents for today
- [ ] Can query safety incidents for custom time ranges (yesterday, this week)
- [ ] Shows count of events
- [ ] Shows timestamp, asset, severity, description for each event
- [ ] Shows resolution status (open/under investigation/resolved)
- [ ] Shows affected area
- [ ] Events sorted by severity (critical first), then recency
- [ ] Can filter by area
- [ ] Can filter by severity level
- [ ] "No incidents" scenario shows positive message
- [ ] Citations included with source and timestamp
- [ ] Cache TTL of 60 seconds (safety data stays fresh)

### Financial Impact Tool

- [ ] Can query financial impact for single asset
- [ ] Can query financial impact for entire area
- [ ] Shows total financial loss in dollars
- [ ] Shows breakdown by category (downtime cost, waste cost)
- [ ] Shows hourly rate used for calculation
- [ ] Shows comparison to average loss
- [ ] Calculations are transparent (formulas shown)
- [ ] Missing cost center data handled gracefully
- [ ] Returns non-financial metrics when cost data unavailable
- [ ] Per-asset breakdown shown for area queries
- [ ] Highest-cost asset identified for area queries
- [ ] Citations reference daily_summaries and cost_centers
- [ ] Cache TTL of 15 minutes

### Cost of Loss Tool

- [ ] Can query "What are we losing money on?"
- [ ] Shows ranked list of losses (highest first)
- [ ] Shows asset, category, amount, root cause for each item
- [ ] Shows total loss across all items
- [ ] Shows percentage of total for each item
- [ ] Losses grouped by category (downtime, waste, quality)
- [ ] Can limit to top N items (e.g., "top 3 cost drivers")
- [ ] Shows trend vs previous period (up/down/stable)
- [ ] Can filter by area
- [ ] Shows comparison to plant-wide average
- [ ] Root causes extracted from downtime_reasons
- [ ] Citations included
- [ ] Cache TTL of 15 minutes

### Trend Analysis Tool

- [ ] Can query performance trends over time
- [ ] Shows trend direction (improving/declining/stable)
- [ ] Shows average metric value over period
- [ ] Shows min and max values with dates
- [ ] Shows notable anomalies (>2 std dev from mean)
- [ ] Shows comparison to baseline (first week)
- [ ] Supports multiple metrics (OEE, output, downtime, waste)
- [ ] Supports time ranges: 7, 14, 30, 60, 90 days
- [ ] Adjusts granularity (daily for <=30 days, weekly for >30 days)
- [ ] Handles insufficient data (<7 days) gracefully
- [ ] Shows available point-in-time data when trend not possible
- [ ] Anomalies include possible causes where available
- [ ] Citations with date range included
- [ ] Cache TTL of 15 minutes

### Citations & Transparency

- [ ] Safety events include citations with source table and timestamp
- [ ] Financial calculations show formulas explicitly
- [ ] Cost of loss citations reference data sources
- [ ] Trend analysis citations include date range
- [ ] All responses include data freshness indicator

### Follow-Up Questions

- [ ] Follow-up chips appear after responses
- [ ] Clicking chip sends that question
- [ ] Questions are contextually relevant to the tool used
- [ ] Cross-tool suggestions work (e.g., safety -> financial impact)

### Error Handling & Honesty

- [ ] Unknown assets handled gracefully
- [ ] Missing cost center data reported honestly
- [ ] Insufficient trend data reported honestly
- [ ] Unsupported questions declined politely
- [ ] Network errors show friendly messages
- [ ] AI never fabricates safety or financial data

### Performance & Caching

- [ ] Safety data cache: 60 seconds (fresh data)
- [ ] Financial data cache: 15 minutes
- [ ] Response time < 2 seconds for cached data
- [ ] Response time < 5 seconds for fresh queries

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **Safety Data Freshness** - Safety events have a 60-second cache to ensure data is fresh. This means the first query after 60 seconds may be slightly slower.

2. **Financial Data Requires Cost Centers** - Financial impact calculations require cost center data (hourly rates, cost per unit) to be configured in the system. If this data is missing for an asset, the tool will indicate this honestly and provide non-financial metrics instead.

3. **Trend Analysis Needs History** - Trend analysis requires at least 7 days of historical data to identify patterns. New assets or recently added assets may not have enough data for trend analysis.

4. **Anomaly Detection Sensitivity** - Anomalies are defined as values more than 2 standard deviations from the mean. In highly variable processes, this may result in many anomalies; in stable processes, few or none.

5. **Weekly Granularity for Long Ranges** - For time ranges over 30 days, the trend tool automatically switches to weekly granularity to improve readability. You cannot force daily granularity for 90-day queries.

6. **Root Causes from Downtime Reasons** - Root causes shown in cost of loss analysis come from the downtime_reasons field in daily summaries. If downtime reasons were not recorded, root cause will not be available.

7. **Financial Formulas Are Simplified** - The formulas shown (downtime_minutes x hourly_rate / 60) are simplified for clarity. Actual costs may vary based on overtime, shift differentials, etc.

8. **Cache Timing** - If you query immediately after data changes, you may see cached (older) data. Wait for the cache to expire (60s for safety, 15min for financial) or the data will refresh naturally.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 5, Step 5.5)
2. **Question Asked** (exact text you typed)
3. **Expected Behavior** (what should have happened)
4. **Actual Behavior** (what actually happened)
5. **Screenshots** (especially for calculation issues, missing data)
6. **Browser and Device** used
7. **Date and Time** of the issue

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
| Safety Events - Basic (Scenarios 1-4) | [ ] | [ ] | [ ] | |
| Financial Impact (Scenarios 5-7) | [ ] | [ ] | [ ] | |
| Cost of Loss (Scenarios 8-10) | [ ] | [ ] | [ ] | |
| Trend Analysis (Scenarios 11-15) | [ ] | [ ] | [ ] | |
| Cross-Tool Flow (Scenario 16) | [ ] | [ ] | [ ] | |
| Citations (Scenario 17) | [ ] | [ ] | [ ] | |
| Time Range Interpretation (Scenario 18) | [ ] | [ ] | [ ] | |
| Caching & Performance (Scenario 19) | [ ] | [ ] | [ ] | |
| Error Handling (Scenario 20) | [ ] | [ ] | [ ] | |
| Mobile Responsiveness (Scenario 21) | [ ] | [ ] | [ ] | |
| Data Freshness (Scenario 22) | [ ] | [ ] | [ ] | |

### Epic 6 Acceptance Criteria Verification

- [ ] **VERIFIED** - Safety Events tool returns incidents with severity, status, affected assets
- [ ] **VERIFIED** - Financial Impact tool calculates dollar losses using cost_centers data
- [ ] **VERIFIED** - Cost of Loss tool ranks issues by financial impact
- [ ] **VERIFIED** - Trend Analysis tool shows performance over 7-90 day windows
- [ ] **VERIFIED** - All tools include citations with source and timestamp
- [ ] **VERIFIED** - Response time < 2 seconds (p95)
- [ ] **VERIFIED** - Safety data is always fresh (60s cache max)
- [ ] **VERIFIED** - Financial calculations are transparent (show formulas)
- [ ] **NOT VERIFIED** - Issues found (document in comments)

### NFR Compliance Verification

- [ ] **NFR4 (Agent Honesty)** - Agent never fabricates data; missing data clearly indicated
- [ ] **NFR6 (Response Structure)** - All responses follow consistent citation format
- [ ] **NFR7 (Tool Response Caching)** - Cached queries noticeably faster; appropriate TTLs observed

### Overall Assessment

- [ ] **APPROVED** - All critical scenarios pass. Epic 6 is ready for production deployment.
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
| 1.0 | January 9, 2026 | QA Specialist | Initial UAT document for Epic 6 |

---

*End of UAT Document*
