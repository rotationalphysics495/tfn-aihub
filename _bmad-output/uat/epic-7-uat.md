# Epic 7: Proactive Agent Capabilities
## User Acceptance Testing (UAT) Document

**Version:** 1.0
**Epic:** 7 - Proactive Agent Capabilities
**Date Created:** January 9, 2026
**Last Updated:** January 9, 2026
**Document Status:** Ready for Testing

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Test Scenarios](#3-test-scenarios)
4. [Success Criteria](#4-success-criteria)
5. [Sign-off Section](#5-sign-off-section)

---

## 1. Overview

### What Was Built

Epic 7 introduces **Proactive Agent Capabilities** that transform the AI assistant from a reactive tool into a true plant management partner. These new features help plant managers work more efficiently by:

| Feature | What It Does |
|---------|--------------|
| **Memory Recall** | The agent remembers your past conversations about specific equipment or topics, so you don't have to repeat yourself |
| **Comparative Analysis** | Compare two or more machines side-by-side to see which is performing better and why |
| **Action List** | Ask "What should I focus on today?" and get a prioritized to-do list based on actual plant data |
| **Alert Check** | Quickly check if there are any active alerts or warnings that need attention |
| **Recommendation Engine** | Get proactive suggestions for improvements based on patterns the system detects in your data |

### User Value

- **Save Time**: No more repeating context from previous conversations
- **Better Decisions**: Compare assets objectively with real data
- **Stay Proactive**: Get improvement suggestions before problems occur
- **Morning Efficiency**: Start each day with a clear, data-driven priority list
- **Real-time Awareness**: Know immediately if something needs attention

---

## 2. Prerequisites

### Test Environment

| Requirement | Details |
|-------------|---------|
| **System Access** | Active account in the AI Hub production or staging environment |
| **Browser** | Chrome, Firefox, Safari, or Edge (latest version) |
| **Network** | Stable internet connection |
| **Device** | Desktop or laptop computer (mobile testing optional) |

### Test Accounts

You will need:
- [ ] A valid plant manager user account
- [ ] Access to at least one plant with historical data (30+ days recommended)
- [ ] Permission to access the AI Chat interface

### Test Data Requirements

For comprehensive testing, ensure:
- [ ] At least 2 similar assets exist (e.g., two grinders) for comparison testing
- [ ] Historical conversation data exists in the system (for memory recall testing)
- [ ] Recent operational data is available (last 7 days minimum)
- [ ] Some safety events or alerts exist (or can be simulated)

### Before You Begin

1. **Log in** to the AI Hub system
2. **Navigate** to the AI Chat interface
3. **Verify** you can see the chat input field and send messages
4. **Confirm** your user account is associated with the correct plant/facility

---

## 3. Test Scenarios

### Scenario 7.1: Memory Recall Tool

**Purpose:** Verify the agent can remember and recall past conversations about specific assets or topics.

---

#### Test 7.1.1: Recall Conversations About a Specific Asset

**Steps:**

1. Open the AI Chat interface
2. Type: **"What did we discuss about Grinder 5?"** (substitute an actual asset name from your plant)
3. Press Enter and wait for the response

**Expected Results:**

- [ ] Response appears within 3 seconds
- [ ] Response includes a summary of past conversations mentioning that asset
- [ ] Key decisions or conclusions are highlighted
- [ ] Dates of relevant conversations are shown
- [ ] Related topics are mentioned
- [ ] Results are organized (most relevant first)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.1.2: Recall Recent Topics

**Steps:**

1. Type: **"What issues have we talked about this week?"**
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response summarizes topics by category
- [ ] Unresolved items are highlighted
- [ ] Conversations are grouped logically (by asset or topic area)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.1.3: No Memory Found Handling

**Steps:**

1. Type: **"What did we discuss about [made-up asset name]?"** (use a name that doesn't exist)
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response clearly states no previous conversations were found
- [ ] Response offers to help with a fresh inquiry
- [ ] Agent does NOT make up fake memories or information

**Notes:**
```
Record any observations here:


```

---

#### Test 7.1.4: Stale Memory Warning

**Steps:**

1. Ask about a topic that was discussed more than 30 days ago
2. Type: **"What did we discuss about [old topic]?"**

**Expected Results:**

- [ ] Response includes a note indicating the discussion was more than 30 days ago
- [ ] Response suggests things may have changed since then

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.2: Comparative Analysis Tool

**Purpose:** Verify users can compare two or more assets side-by-side.

---

#### Test 7.2.1: Two-Asset Comparison

**Steps:**

1. Open the AI Chat interface
2. Type: **"Compare Grinder 5 vs Grinder 3"** (substitute actual asset names)
3. Press Enter and wait for the response

**Expected Results:**

- [ ] Response includes a side-by-side comparison table
- [ ] Metrics shown include: OEE, output, downtime, waste
- [ ] Better/worse indicators are clearly visible (e.g., +/- symbols)
- [ ] A summary of key differences is provided
- [ ] A recommendation is given if one asset is clearly better
- [ ] All metrics include data source citations

**Notes:**
```
Record any observations here:


```

---

#### Test 7.2.2: Multi-Asset Comparison

**Steps:**

1. Type: **"Compare all grinders this week"** (or another asset type in your plant)
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response compares all matching assets (up to 10)
- [ ] Assets are ranked by overall performance
- [ ] Best and worst performers are clearly identified
- [ ] Time period is clearly stated (should be "last 7 days" by default)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.2.3: Area-Level Comparison

**Steps:**

1. Type: **"Compare Grinding vs Packaging"** (substitute actual area names)
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response aggregates metrics at the area level
- [ ] Area totals and averages are shown
- [ ] Top/bottom performers within each area are identified

**Notes:**
```
Record any observations here:


```

---

#### Test 7.2.4: Incompatible Metrics Handling

**Steps:**

1. Compare two very different types of assets (e.g., a grinder vs a packaging machine)
2. Type: **"Compare [Asset A] vs [Asset B]"**

**Expected Results:**

- [ ] Response includes a note about comparability limitations
- [ ] Percentage-based comparisons are used where appropriate
- [ ] Agent explains any normalization applied

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.3: Action List Tool

**Purpose:** Verify users can get a prioritized daily action list.

---

#### Test 7.3.1: Daily Action List Generation

**Steps:**

1. Open the AI Chat interface
2. Type: **"What should I focus on today?"**
3. Press Enter and wait for the response

**Expected Results:**

- [ ] Response includes a prioritized list (maximum 5 items)
- [ ] Each action shows: priority rank, asset, issue, recommended action
- [ ] Supporting evidence is provided for each item
- [ ] Estimated impact (financial or operational) is shown
- [ ] Items are sorted: Safety first, then Financial Impact, then OEE gaps

**Notes:**
```
Record any observations here:


```

---

#### Test 7.3.2: Area-Filtered Actions

**Steps:**

1. Type: **"What should I focus on in Grinding?"** (substitute an actual area)
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response only shows actions for the specified area
- [ ] Priority logic remains the same (Safety > Financial > OEE)
- [ ] If no issues in that area, response is clear about it

**Notes:**
```
Record any observations here:


```

---

#### Test 7.3.3: No Issues Scenario

**Steps:**

1. If possible, test during a period when operations are running smoothly
2. Type: **"What should I focus on today?"**

**Expected Results:**

- [ ] Response clearly states "No critical issues identified - operations look healthy"
- [ ] Proactive improvement suggestions are offered (if patterns indicate opportunities)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.3.4: Alternative Query Phrasings

**Steps:**

Try each of these alternative questions:
1. **"Any priorities for this morning?"**
2. **"What needs attention?"**
3. **"Give me my daily action list"**

**Expected Results:**

- [ ] All variations trigger the Action List tool
- [ ] Responses are consistent in format and content

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.4: Alert Check Tool

**Purpose:** Verify users can quickly check for active alerts and warnings.

---

#### Test 7.4.1: Active Alerts Query

**Steps:**

1. Open the AI Chat interface
2. Type: **"Are there any alerts?"**
3. Press Enter and wait for the response

**Expected Results:**

- [ ] Response shows count of active alerts by severity
- [ ] For each alert: type, asset, description, recommended response
- [ ] Time since alert was triggered is shown
- [ ] Escalation status is indicated (if applicable)
- [ ] Alerts are sorted by severity (critical first)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.4.2: Severity Filtering

**Steps:**

1. Type: **"Any critical alerts?"**
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Only critical alerts are shown
- [ ] Response indicates the filter was applied
- [ ] Count of other severity alerts is mentioned (if any exist)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.4.3: No Alerts Scenario

**Steps:**

1. Test during a period when no alerts are active (or after clearing test alerts)
2. Type: **"Are there any alerts?"**

**Expected Results:**

- [ ] Response states "No active alerts - all systems normal"
- [ ] Time since last alert is shown (if any previous alerts exist)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.4.4: Stale Alert Flagging

**Steps:**

1. Ensure at least one alert has been active for more than 1 hour
2. Type: **"Are there any alerts?"**

**Expected Results:**

- [ ] Alerts older than 1 hour are flagged as "Requires Attention"
- [ ] Escalation is suggested for stale alerts

**Notes:**
```
Record any observations here:


```

---

#### Test 7.4.5: Alternative Query Phrasings

**Steps:**

Try each of these alternative questions:
1. **"Is anything wrong?"**
2. **"Any issues right now?"**
3. **"Check for warnings"**

**Expected Results:**

- [ ] All variations trigger the Alert Check tool
- [ ] Responses are consistent in format

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.5: Recommendation Engine

**Purpose:** Verify users receive proactive improvement suggestions based on patterns.

---

#### Test 7.5.1: Asset-Specific Recommendations

**Steps:**

1. Open the AI Chat interface
2. Type: **"How can we improve OEE for Grinder 5?"** (substitute an actual asset)
3. Press Enter and wait for the response

**Expected Results:**

- [ ] Response includes 2-3 specific recommendations
- [ ] Each recommendation includes:
  - [ ] What to do (specific action)
  - [ ] Expected impact (financial or operational)
  - [ ] Supporting evidence (data patterns)
- [ ] Similar past solutions are referenced (if available from memory)
- [ ] Recommendations are actionable and specific (not generic advice)

**Notes:**
```
Record any observations here:


```

---

#### Test 7.5.2: Plant-Wide Analysis

**Steps:**

1. Type: **"What should we focus on improving?"**
2. Press Enter and wait for the response

**Expected Results:**

- [ ] Response analyzes patterns across the entire plant
- [ ] Highest-impact improvement opportunities are identified
- [ ] Recommendations are ranked by potential ROI
- [ ] Supporting evidence spans multiple assets

**Notes:**
```
Record any observations here:


```

---

#### Test 7.5.3: Focus Area Recommendations

**Steps:**

1. Type: **"How do we reduce waste?"**
2. Press Enter and wait for the response

**Expected Results:**

- [ ] All recommendations relate specifically to waste reduction
- [ ] Relevant data is cited (waste metrics, patterns)
- [ ] Recommendations are practical and implementable

**Notes:**
```
Record any observations here:


```

---

#### Test 7.5.4: Insufficient Data Handling

**Steps:**

1. Ask about a newly added asset or one with limited history
2. Type: **"How can we improve [new asset name]?"**

**Expected Results:**

- [ ] Response clearly states more data is needed
- [ ] Specific data gaps are identified (what data would help)
- [ ] Agent does NOT make up recommendations without evidence

**Notes:**
```
Record any observations here:


```

---

#### Test 7.5.5: Confidence Levels

**Steps:**

1. Review recommendations from any of the above tests

**Expected Results:**

- [ ] Each recommendation shows a confidence level (High or Medium)
- [ ] Low-confidence recommendations are not shown
- [ ] Confidence level is clearly visible (e.g., [HIGH CONFIDENCE: 87%])

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.6: Cross-Tool Integration

**Purpose:** Verify tools work together seamlessly.

---

#### Test 7.6.1: Sequential Tool Usage

**Steps:**

1. Ask: **"What should I focus on today?"** (Action List)
2. Then ask: **"Compare those two assets"** (referencing assets from the action list)
3. Then ask: **"How can we improve the worse one?"** (Recommendation Engine)

**Expected Results:**

- [ ] Agent maintains context between questions
- [ ] Each tool provides relevant, connected information
- [ ] Conversation flows naturally

**Notes:**
```
Record any observations here:


```

---

#### Test 7.6.2: Memory + Recommendations

**Steps:**

1. Ask: **"What did we discuss about improving OEE last month?"** (Memory)
2. Then ask: **"What are your current recommendations?"** (Recommendation Engine)

**Expected Results:**

- [ ] Memory recall shows past discussions
- [ ] Recommendations may reference or build on past discussions
- [ ] Past solutions are incorporated where relevant

**Notes:**
```
Record any observations here:


```

---

### Scenario 7.7: Performance and Response Quality

**Purpose:** Verify overall system performance meets requirements.

---

#### Test 7.7.1: Response Time

**Steps:**

1. Run through 5 different queries from any of the scenarios above
2. Note the response time for each

**Expected Results:**

- [ ] All responses complete within 3 seconds
- [ ] Most responses complete within 2 seconds
- [ ] No timeouts or errors occur

**Response Times:**
| Query | Time (seconds) |
|-------|----------------|
| 1.    |                |
| 2.    |                |
| 3.    |                |
| 4.    |                |
| 5.    |                |

---

#### Test 7.7.2: Citation Quality

**Steps:**

1. Review any 3 responses that include data
2. Check that citations are present and readable

**Expected Results:**

- [ ] All data-backed statements include citations
- [ ] Citations reference specific sources (table, date, record)
- [ ] Citation format is consistent and readable

**Notes:**
```
Record any observations here:


```

---

#### Test 7.7.3: Error Handling

**Steps:**

1. Try asking questions with typos: **"Compair Grinder 5 and Grinder 3"**
2. Try asking about non-existent items: **"What's the OEE for XYZ123?"**
3. Try asking ambiguous questions: **"Compare everything"**

**Expected Results:**

- [ ] Agent handles typos gracefully (understands intent)
- [ ] Non-existent items get clear "not found" responses
- [ ] Ambiguous questions prompt clarification requests

**Notes:**
```
Record any observations here:


```

---

## 4. Success Criteria

### Mandatory Criteria (Must Pass)

All of the following must pass for UAT approval:

| # | Criterion | Pass/Fail |
|---|-----------|-----------|
| 1 | Memory Recall retrieves relevant past conversations via Mem0 | |
| 2 | Comparative Analysis shows side-by-side metrics for 2+ assets | |
| 3 | Action List tool surfaces prioritized daily actions with evidence | |
| 4 | Alert Check returns active warnings with recommended responses | |
| 5 | Recommendation Engine suggests improvements based on patterns | |
| 6 | All tools include citations where applicable | |
| 7 | Response time < 3 seconds (p95) for all tools | |
| 8 | Recommendations are actionable and data-backed | |
| 9 | Memory recall respects user context and relevance thresholds | |
| 10 | "No data" scenarios handled gracefully (no fabricated information) | |

### Quality Criteria (Should Pass)

| # | Criterion | Pass/Fail |
|---|-----------|-----------|
| 1 | Natural language variations are understood correctly | |
| 2 | Cross-tool context is maintained in conversation | |
| 3 | Error messages are helpful and non-technical | |
| 4 | Formatting is consistent and easy to read | |
| 5 | Priority logic is clear (Safety > Financial > OEE) | |

---

## 5. Sign-off Section

### Test Summary

| Category | Total Tests | Passed | Failed | Blocked |
|----------|-------------|--------|--------|---------|
| Memory Recall (7.1) | 4 | | | |
| Comparative Analysis (7.2) | 4 | | | |
| Action List (7.3) | 4 | | | |
| Alert Check (7.4) | 5 | | | |
| Recommendation Engine (7.5) | 5 | | | |
| Cross-Tool Integration (7.6) | 2 | | | |
| Performance & Quality (7.7) | 3 | | | |
| **TOTAL** | **27** | | | |

### Issues Discovered

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

*Severity: Critical / High / Medium / Low*
*Status: Open / In Progress / Resolved / Deferred*

### Overall Assessment

- [ ] **APPROVED** - All mandatory criteria passed, ready for production
- [ ] **CONDITIONALLY APPROVED** - Minor issues to be addressed post-deployment
- [ ] **NOT APPROVED** - Critical issues must be resolved before deployment

### Comments

```
Additional observations, concerns, or feedback:




```

---

### Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| UAT Tester | | | |
| Plant Manager (Business Owner) | | | |
| Product Owner | | | |
| QA Lead | | | |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 9, 2026 | QA Specialist | Initial UAT document creation |

---

*End of UAT Document - Epic 7: Proactive Agent Capabilities*
