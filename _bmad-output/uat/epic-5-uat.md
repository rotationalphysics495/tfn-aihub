# User Acceptance Testing (UAT) Document

## Epic 5: Agent Foundation & Core Tools

**Version:** 1.0
**Date:** January 9, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 5 delivers a smarter AI assistant with specialized tools for answering your most common questions about manufacturing operations. Instead of a general-purpose AI, you now have purpose-built tools that understand OEE, downtime, assets, and production status - and always show you exactly where the data comes from.

**In plain terms, we built:**

1. **Asset Lookup Tool** - Ask about any machine by name (like "Tell me about Grinder 5") and get a complete snapshot: current status, today's output vs target, 7-day OEE average, and top downtime reasons. No more navigating through multiple reports.

2. **OEE Query Tool** - Ask "What's the OEE for the Grinding area?" and get a breakdown of Availability, Performance, and Quality. The AI tells you which component is your biggest opportunity for improvement.

3. **Downtime Analysis Tool** - Ask "Why was Grinder 5 down yesterday?" and get a ranked list of reasons (Pareto analysis). The AI identifies the "vital few" causes responsible for 80% of your downtime.

4. **Production Status Tool** - Ask "How are we doing today?" and see all assets ranked by how they're tracking against targets. Assets behind schedule appear first so you know where to focus.

5. **Smarter Chat Integration** - The chat sidebar now shows clickable follow-up questions based on what you asked. Responses include source citations you can click to see the actual data.

6. **Faster Responses** - Common questions are cached so repeated queries return instantly instead of hitting the database each time.

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

- At least 5-8 assets configured (e.g., Grinder 1, Grinder 5, Line 3, Press 2, CAMA 800-1)
- At least one area with multiple assets (e.g., "Grinding" area with Grinder 1, 2, 3, 5)
- Production data from the past 7 days (daily summaries with OEE values)
- Downtime records with multiple reason codes
- Live snapshots with current shift output data
- Shift targets configured for key assets

### Before You Begin

1. Ensure you have a stable internet connection
2. Log in to the application (you should see the Command Center)
3. Have this document available for reference
4. Note: AI responses typically take 1-3 seconds; complex queries may take up to 5 seconds

---

## 3. Test Scenarios

### Scenario 1: Opening the AI Chat and Basic Interaction

**Objective:** Verify the chat sidebar works and routes to the new AI agent.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Log in and navigate to the Command Center dashboard | Dashboard displays |
| 1.2 | Look for the chat button in the bottom-right corner | A circular button with a message icon is visible |
| 1.3 | Click the chat button | A sidebar slides in from the right side |
| 1.4 | Observe the chat sidebar | Shows "AI Assistant" header, welcome message, and input field |
| 1.5 | Type "Hello" and press Enter | Your message appears on the right side |
| 1.6 | Wait for the AI response | Loading indicator appears, then AI greeting displays |
| 1.7 | Click the X button to close the sidebar | Sidebar slides closed |

**Pass Criteria:** Chat opens/closes smoothly. Messages send and receive correctly.

---

### Scenario 2: Asset Lookup - Basic Query

**Objective:** Verify the AI can look up information about a specific asset.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Open the AI chat sidebar | Chat displays |
| 2.2 | Type: "Tell me about Grinder 5" | Text appears in input field |
| 2.3 | Press Enter to send | Message sends, loading indicator appears |
| 2.4 | Wait for the response (1-3 seconds) | AI responds with asset information |
| 2.5 | Check the response content | Response includes: (a) Asset name and area, (b) Current status (running/down/idle), (c) Current output vs shift target, (d) 7-day OEE average, (e) Top downtime reason |
| 2.6 | Look for citations in the response | Response shows source citations (e.g., "[1]", "[2]") |
| 2.7 | Look for follow-up question chips below the response | Clickable buttons appear with questions like "Show me Grinder 5's OEE trend" |

**Pass Criteria:** AI provides comprehensive asset snapshot with all data points cited. Follow-up suggestions appear.

---

### Scenario 3: Asset Lookup - Unknown Asset

**Objective:** Verify the AI handles requests for non-existent assets gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Open the AI chat | Chat displays |
| 3.2 | Type: "Tell me about Machine XYZ999" | Text appears in input |
| 3.3 | Press Enter to send | Message sends |
| 3.4 | Wait for the response | AI responds |
| 3.5 | Check the response content | Response should: (a) State "I don't have data for Machine XYZ999", (b) Suggest similar assets (e.g., "Did you mean...?"), (c) NOT make up any performance data |

**Pass Criteria:** AI honestly indicates asset not found and provides helpful suggestions.

---

### Scenario 4: Asset Lookup - Fuzzy Name Matching

**Objective:** Verify the AI can find assets even with imprecise names.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Open the AI chat | Chat displays |
| 4.2 | Type: "How is grinder5 doing?" (no space) | Text appears |
| 4.3 | Press Enter to send | Message sends |
| 4.4 | Check the response | AI finds "Grinder 5" despite the typo |
| 4.5 | Try another variation: "grinder #5" | Ask with hash symbol |
| 4.6 | Check the response | AI still finds "Grinder 5" |

**Pass Criteria:** AI recognizes asset names with common variations (no spaces, symbols, different capitalization).

---

### Scenario 5: OEE Query - Single Asset

**Objective:** Verify the AI can provide OEE breakdown for a specific asset.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Open the AI chat | Chat displays |
| 5.2 | Type: "What's the OEE for Grinder 5?" | Text appears |
| 5.3 | Press Enter to send | Message sends |
| 5.4 | Wait for the response | AI responds with OEE data |
| 5.5 | Check the response content | Response includes: (a) Overall OEE percentage, (b) Availability percentage, (c) Performance percentage, (d) Quality percentage, (e) Target comparison (if available) |
| 5.6 | Look for analysis insight | AI should indicate which component (A, P, or Q) is the biggest opportunity |
| 5.7 | Verify citations | All data points have source citations |

**Pass Criteria:** AI provides complete OEE breakdown with actionable insight on biggest opportunity.

---

### Scenario 6: OEE Query - Area Level

**Objective:** Verify the AI can aggregate OEE for an entire area.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Open the AI chat | Chat displays |
| 6.2 | Type: "What's the OEE for the Grinding area?" | Text appears |
| 6.3 | Press Enter to send | Message sends |
| 6.4 | Wait for the response | AI responds with area-wide OEE |
| 6.5 | Check the response content | Response includes: (a) Aggregated OEE for the area, (b) Individual asset OEE values, (c) Assets ranked by performance, (d) Indication of which assets are pulling down the average |
| 6.6 | Look for follow-up questions | Chips suggest investigating underperformers |

**Pass Criteria:** AI aggregates OEE across area and identifies underperforming assets.

---

### Scenario 7: OEE Query - Time Range

**Objective:** Verify the AI understands time range specifications.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Ask: "What was Grinder 5's OEE last week?" | Message sends |
| 7.2 | Check the response | Response covers 7-day period with date range shown |
| 7.3 | Ask: "How about yesterday?" | Follow-up message |
| 7.4 | Check the response | Response shows single-day OEE for yesterday |
| 7.5 | Ask: "What about this month?" | Another variation |
| 7.6 | Check the response | Response covers appropriate date range |

**Pass Criteria:** AI correctly interprets "yesterday", "last week", "this month" and cites the actual date range queried.

---

### Scenario 8: Downtime Analysis - Basic Query

**Objective:** Verify the AI can analyze downtime reasons.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Open the AI chat | Chat displays |
| 8.2 | Type: "Why was Grinder 5 down yesterday?" | Text appears |
| 8.3 | Press Enter to send | Message sends |
| 8.4 | Wait for the response | AI responds with downtime analysis |
| 8.5 | Check the response content | Response includes: (a) Total downtime minutes, (b) Reasons ranked by duration (Pareto), (c) Percentage of total for each reason, (d) Which reasons are the "vital few" (causing 80% of downtime) |
| 8.6 | Look for safety-related items | Any safety-related downtime should be highlighted separately |

**Pass Criteria:** AI provides Pareto-style ranking of downtime reasons with percentages.

---

### Scenario 9: Downtime Analysis - No Downtime

**Objective:** Verify the AI handles assets with no downtime appropriately.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Ask about an asset that had good uptime (or use a test asset known to have 100% uptime) | Message sends |
| 9.2 | Example: "Was Grinder 2 down yesterday?" | Ask about well-performing asset |
| 9.3 | Check the response | Response should: (a) State "[Asset] had no recorded downtime in [period]", (b) Show uptime percentage (100%), (c) Include positive acknowledgment (not just empty response) |

**Pass Criteria:** AI provides positive feedback when no downtime occurred rather than an error message.

---

### Scenario 10: Downtime Analysis - Area Level

**Objective:** Verify the AI can analyze downtime across an area.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Type: "What are the top downtime reasons for the Grinding area this week?" | Message sends |
| 10.2 | Wait for the response | AI responds with area-wide analysis |
| 10.3 | Check the response content | Response includes: (a) Aggregated downtime across all assets, (b) Reasons ranked by total duration, (c) Which assets contributed to each reason |

**Pass Criteria:** AI aggregates downtime across area and shows which assets contributed to each reason.

---

### Scenario 11: Production Status - Plant Wide

**Objective:** Verify the AI can show real-time production status.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | Open the AI chat | Chat displays |
| 11.2 | Type: "How are we doing today?" | Text appears |
| 11.3 | Press Enter to send | Message sends |
| 11.4 | Wait for the response | AI responds with production status |
| 11.5 | Check the response content | Response includes: (a) Multiple assets listed, (b) Current output vs target for each, (c) Variance (units and percentage), (d) Status indicator (ahead/on-track/behind), (e) Assets sorted by variance (worst first) |
| 11.6 | Look for summary statistics | Total assets, count ahead/on-track/behind, assets needing attention |

**Pass Criteria:** AI provides plant-wide production snapshot with assets prioritized by need for attention.

---

### Scenario 12: Production Status - Area Filtered

**Objective:** Verify the AI can filter production status by area.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 12.1 | Type: "How is the Grinding area doing?" | Message sends |
| 12.2 | Wait for the response | AI responds with area-specific status |
| 12.3 | Check the response | Response shows: (a) Only assets in the Grinding area, (b) Area-level totals (total output, total target), (c) Area-wide variance percentage |

**Pass Criteria:** AI correctly filters to requested area and provides area totals.

---

### Scenario 13: Production Status - Data Freshness Warning

**Objective:** Verify the AI warns when data may be stale.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 13.1 | Ask: "What's the current production status?" | Message sends |
| 13.2 | If test data is more than 30 minutes old | Response should include a warning |
| 13.3 | Look for warning message | Warning like "Data is from [timestamp], may not reflect current status" |
| 13.4 | If data is fresh (within 30 minutes) | No warning should appear |

**Pass Criteria:** AI warns users when live data is stale so they know to check the floor.

---

### Scenario 14: Status Thresholds Verification

**Objective:** Verify status indicators use correct thresholds.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 14.1 | Ask: "How are we doing today?" | Get production status |
| 14.2 | Find an asset marked "ahead" | Should be >=5% above target |
| 14.3 | Find an asset marked "on-track" | Should be within +/-5% of target |
| 14.4 | Find an asset marked "behind" | Should be >5% below target |
| 14.5 | Verify the color coding | Ahead = green, On-track = yellow, Behind = red |

**Pass Criteria:** Status indicators match expected thresholds and colors.

---

### Scenario 15: Citation Interaction

**Objective:** Verify citations are clickable and show source details.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 15.1 | Ask any data question (e.g., "What's the OEE for Grinder 5?") | Get response with citations |
| 15.2 | Look for citation markers | Small numbered badges like [1], [2] in the response |
| 15.3 | Click on a citation badge | A popover or panel opens |
| 15.4 | Review the citation details | Shows: (a) Source (e.g., "supabase.daily_summaries"), (b) Table name, (c) Timestamp when data was retrieved |
| 15.5 | Close the citation popover | Click X or outside the popover |

**Pass Criteria:** Citations are clickable and show actual data source information.

---

### Scenario 16: Follow-Up Question Chips

**Objective:** Verify follow-up question chips work correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 16.1 | Ask: "Tell me about Grinder 5" | Get asset response |
| 16.2 | Look below the response | Clickable chip buttons appear (e.g., "Show me Grinder 5's OEE trend", "What caused downtime?") |
| 16.3 | Click one of the follow-up chips | The question is automatically sent as your next message |
| 16.4 | Wait for response | AI responds to the follow-up question |
| 16.5 | Verify the flow | New response also has follow-up suggestions |

**Pass Criteria:** Clicking a follow-up chip sends that question automatically. Chips match chat UI styling.

---

### Scenario 17: Unknown Query Handling

**Objective:** Verify the AI handles questions it can't answer.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 17.1 | Ask something outside the tool scope: "What's the weather like?" | Message sends |
| 17.2 | Wait for response | AI responds honestly |
| 17.3 | Check the response | Response should: (a) Indicate it cannot help with that request, (b) Suggest what types of questions it CAN answer, (c) NOT make up an answer |
| 17.4 | Ask: "What will production be next month?" | Prediction question |
| 17.5 | Check response | AI clarifies it cannot predict future data |

**Pass Criteria:** AI honestly states limitations and suggests valid question types.

---

### Scenario 18: Response Caching - Speed Test

**Objective:** Verify repeated queries return faster due to caching.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 18.1 | Ask: "What's the OEE for Grinder 5?" | First query |
| 18.2 | Note the response time | May take 2-3 seconds |
| 18.3 | Wait 10 seconds | Brief pause |
| 18.4 | Ask the exact same question again | Same query |
| 18.5 | Note the response time | Should be noticeably faster (under 1 second) |
| 18.6 | Check response metadata | May include "cached_at" timestamp |

**Pass Criteria:** Second query is faster than the first. Cache improves response time.

---

### Scenario 19: Loading State

**Objective:** Verify loading indicators appear during processing.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 19.1 | Ask a question that requires data lookup | Message sends |
| 19.2 | Immediately observe the chat area | Loading indicator (dots or spinner) appears |
| 19.3 | Observe the send button | Should be disabled while processing |
| 19.4 | Wait for the response | Loading indicator disappears when response arrives |
| 19.5 | Send button re-enables | Can send new messages |

**Pass Criteria:** Loading indicator visible during all processing. Send button disabled to prevent duplicate sends.

---

### Scenario 20: Error Recovery

**Objective:** Verify the chat handles errors gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 20.1 | Attempt to send an empty message (press Enter with no text) | Message should NOT send (button disabled or ignored) |
| 20.2 | If network error occurs | User-friendly error message displays |
| 20.3 | Try sending another message after error | Chat recovers and allows new messages |
| 20.4 | Check that the chat doesn't freeze | Interface remains responsive |

**Pass Criteria:** Errors show friendly messages. Chat remains functional after errors.

---

### Scenario 21: Mobile Responsiveness

**Objective:** Verify the chat works on smaller screens.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 21.1 | Open the app on a tablet or resize browser to tablet width (~768px) | Chat sidebar adjusts |
| 21.2 | Send a message | Message sends correctly |
| 21.3 | Check citations | Citations are tappable/clickable |
| 21.4 | Check follow-up chips | Chips are tappable with adequate touch target size |
| 21.5 | Check tables in responses | Tables scroll horizontally if needed |
| 21.6 | On mobile width (~375px) | Chat takes full width, still functional |

**Pass Criteria:** All chat features work on tablet and mobile. Touch targets are adequate size.

---

### Scenario 22: Response Formatting

**Objective:** Verify responses are formatted clearly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 22.1 | Ask: "How are we doing today?" | Get multi-asset response |
| 22.2 | Check if tables display correctly | Data aligned in columns, readable |
| 22.3 | Check status colors | "Behind" appears in red, "ahead" in green |
| 22.4 | Check for markdown rendering | Bold text, lists, etc. render properly |
| 22.5 | Verify text is not truncated | All content readable |

**Pass Criteria:** Responses are well-formatted with appropriate colors and structure.

---

## 4. Success Criteria Checklist

### Agent Framework

- [ ] Chat routes to new agent endpoint
- [ ] Loading indicator shows during processing
- [ ] Send button disabled while processing
- [ ] Responses include citations
- [ ] Follow-up question chips appear

### Asset Lookup Tool

- [ ] Can look up assets by name
- [ ] Shows current status (running/down/idle)
- [ ] Shows current output vs target
- [ ] Shows 7-day OEE average
- [ ] Shows top downtime reason
- [ ] Unknown assets handled gracefully with suggestions
- [ ] Fuzzy name matching works (grinder5, Grinder #5, etc.)

### OEE Query Tool

- [ ] Can query single asset OEE
- [ ] Can query area-level OEE
- [ ] Shows A/P/Q component breakdown
- [ ] Identifies biggest improvement opportunity
- [ ] Supports time ranges (yesterday, last week, etc.)
- [ ] Shows target comparison when available
- [ ] No data scenarios handled gracefully

### Downtime Analysis Tool

- [ ] Shows Pareto ranking of downtime reasons
- [ ] Shows percentage of total for each reason
- [ ] Identifies "vital few" causes (80% threshold)
- [ ] Highlights safety-related downtime
- [ ] No downtime shows positive message
- [ ] Area-level aggregation works

### Production Status Tool

- [ ] Shows current output vs target for all assets
- [ ] Shows variance (units and percentage)
- [ ] Assets sorted by variance (worst first)
- [ ] Status indicators correct (ahead/on-track/behind)
- [ ] Status colors correct (green/yellow/red)
- [ ] Warns when data is stale (>30 min old)
- [ ] Area filtering works

### Citations & Transparency

- [ ] All factual responses include citations
- [ ] Citations are clickable
- [ ] Citation popover shows source details
- [ ] Timestamps included in citations

### Follow-Up Questions

- [ ] Follow-up chips appear after responses
- [ ] Clicking chip sends that question
- [ ] Questions are contextually relevant
- [ ] Maximum 3 chips displayed

### Error Handling & Honesty

- [ ] Unknown assets not fabricated
- [ ] Missing data clearly indicated
- [ ] Unsupported questions declined honestly
- [ ] Network errors show friendly messages
- [ ] Empty messages prevented

### Performance & Caching

- [ ] Repeated queries faster (cached)
- [ ] Response time < 2 seconds for cached data
- [ ] Response time < 5 seconds for fresh queries

### Accessibility & Usability

- [ ] Keyboard navigation works
- [ ] Responsive on tablet and mobile
- [ ] Tables readable and scrollable
- [ ] Touch targets adequate on mobile

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **Response Time for First Query** - The first time you ask a question, it may take 2-5 seconds as data is fetched from the database. Subsequent identical queries will be faster due to caching.

2. **Cache Duration by Data Type** - Different data has different cache durations:
   - Live production data: 60 seconds (changes frequently)
   - Daily OEE/Downtime data: 15 minutes (updated periodically)
   - Asset metadata: 1 hour (rarely changes)

3. **Plant-Wide Queries Take Longer** - Questions about "all assets" or "the entire plant" require more data and may take slightly longer than single-asset queries.

4. **Natural Language Variations** - While the AI handles common variations ("grinder 5", "Grinder5", "grinder #5"), very unusual phrasings may not be recognized. Rephrase if the AI doesn't understand.

5. **Data Freshness Depends on Pipeline** - Live snapshots are only as fresh as the polling pipeline. If you see stale data warnings frequently, notify IT to check the data pipeline.

6. **Memory from Previous Epics** - The AI still has memory from Epic 4, but the new tools focus on current operational data. For historical asset resolutions, you may need to ask specifically.

7. **Follow-Up Questions Are Suggestions** - The follow-up chips are AI-generated suggestions. You can always type your own questions instead.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 5, Step 5.5)
2. **Question Asked** (exact text you typed)
3. **Expected Behavior** (what should have happened)
4. **Actual Behavior** (what actually happened)
5. **Screenshots** (especially for citation issues, formatting problems)
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
| Chat Basics (Scenario 1) | [ ] | [ ] | [ ] | |
| Asset Lookup (Scenarios 2-4) | [ ] | [ ] | [ ] | |
| OEE Queries (Scenarios 5-7) | [ ] | [ ] | [ ] | |
| Downtime Analysis (Scenarios 8-10) | [ ] | [ ] | [ ] | |
| Production Status (Scenarios 11-14) | [ ] | [ ] | [ ] | |
| Citations (Scenario 15) | [ ] | [ ] | [ ] | |
| Follow-Up Chips (Scenario 16) | [ ] | [ ] | [ ] | |
| Error Handling (Scenarios 17, 20) | [ ] | [ ] | [ ] | |
| Caching & Performance (Scenarios 18-19) | [ ] | [ ] | [ ] | |
| Responsive Design (Scenario 21) | [ ] | [ ] | [ ] | |
| Formatting (Scenario 22) | [ ] | [ ] | [ ] | |

### Epic 5 Acceptance Criteria Verification

- [ ] **VERIFIED** - Agent framework operational with tool selection
- [ ] **VERIFIED** - All 4 core tools (Asset, OEE, Downtime, Production) work correctly
- [ ] **VERIFIED** - Agent correctly selects tools based on user intent
- [ ] **VERIFIED** - All responses include citations with source and timestamp
- [ ] **VERIFIED** - Response time < 2 seconds for typical queries
- [ ] **VERIFIED** - Agent gracefully handles unknown queries
- [ ] **VERIFIED** - Tool response caching improves repeated query speed
- [ ] **VERIFIED** - Chat UI connected to new agent with follow-up chips
- [ ] **NOT VERIFIED** - Issues found (document in comments)

### NFR Compliance Verification

- [ ] **NFR4 (Agent Honesty)** - Agent never fabricates data; unknown items handled gracefully
- [ ] **NFR5 (Tool Extensibility)** - Tools auto-register without code changes (dev verification)
- [ ] **NFR6 (Response Structure)** - All responses follow consistent citation format
- [ ] **NFR7 (Tool Response Caching)** - Cached queries noticeably faster

### Overall Assessment

- [ ] **APPROVED** - All critical scenarios pass. Epic 5 is ready for production deployment.
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
| 1.0 | January 9, 2026 | QA Specialist | Initial UAT document for Epic 5 |

---

*End of UAT Document*
