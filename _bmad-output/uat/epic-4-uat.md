# User Acceptance Testing (UAT) Document

## Epic 4: AI Chat & Memory

**Version:** 1.0
**Date:** January 7, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 4 delivers your new AI-powered assistant for querying factory data using natural language. Think of it as having a knowledgeable colleague available 24/7 who can instantly look up production data, remember your past conversations, and always show you exactly where the information came from.

**In plain terms, we built:**

1. **AI Chat Sidebar** - A chat interface that slides in from the right side of your screen. You can ask questions in plain English like "What was Grinder 5's OEE yesterday?" and get immediate answers.

2. **Natural Language Query** - You no longer need to navigate complex reports or write queries. Just type your question and the AI translates it into a database query for you.

3. **Memory System** - The AI remembers your past questions and conversations. If you asked about Grinder 5 last week, the AI can recall that context when you ask follow-up questions.

4. **Asset History Tracking** - The system stores past resolutions, maintenance notes, and incidents linked to specific equipment. When you ask "Why does Grinder 5 keep failing?", the AI can pull up relevant history.

5. **Cited Responses** - Every answer from the AI includes citations showing exactly where the data came from. No guessing - you can click on any citation to see the actual source data.

---

## 2. Prerequisites

### Test Environment

| Item | Details |
|------|---------|
| **Application URL** | Contact your IT administrator for the test environment URL |
| **Supported Browsers** | Chrome (recommended), Firefox, Safari, Edge |
| **Supported Devices** | Desktop computer, tablet (iPad/Android) |
| **Recommended Screen** | Tablet or larger for best chat experience |

### Test Accounts

You will need a test account to perform these tests. Contact your IT administrator to obtain:

- Test email address
- Test password

**Note:** Do NOT use production credentials for testing.

### Test Data Requirements

For meaningful testing, ensure the test environment has:

- At least 3-5 assets configured (e.g., Grinder 5, Line 3, Press 2)
- Production data from the past 7 days (daily summaries)
- At least 2-3 historical asset events (downtime, maintenance records)

### Before You Begin

1. Ensure you have a stable internet connection
2. Log in to the application (you should see the Command Center)
3. Have this document available for reference
4. Note: AI responses may take 2-5 seconds to generate

---

## 3. Test Scenarios

### Scenario 1: Opening the AI Chat

**Objective:** Verify the AI chat sidebar opens and closes correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Log in and navigate to the Command Center dashboard | Dashboard displays |
| 1.2 | Look for a floating chat button in the bottom-right corner of the screen | A blue circular button with a message icon is visible |
| 1.3 | Click the chat button | A sidebar slides in from the right side of the screen |
| 1.4 | Observe the chat sidebar | The sidebar shows "AI Assistant" in the header, a welcome message, and an input field at the bottom |
| 1.5 | Click the X button in the top-right of the sidebar OR press the Escape key | The sidebar closes and slides out of view |
| 1.6 | Click the chat button again | The sidebar reopens |

**Pass Criteria:** Chat opens/closes smoothly. Interface is clear and professional.

---

### Scenario 2: Sending a Basic Question

**Objective:** Verify users can send questions and receive AI responses.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Open the AI chat sidebar | Chat sidebar displays |
| 2.2 | Click in the text input field at the bottom | Cursor appears in the input field |
| 2.3 | Type: "Hello" | Text appears in the input field |
| 2.4 | Press Enter OR click the Send button | Your message appears in the chat as a user message (right-aligned, blue background) |
| 2.5 | Wait for the response | A loading indicator (animated dots) appears briefly |
| 2.6 | Observe the AI response | An AI response appears (left-aligned, gray background) with a greeting or acknowledgment |

**Pass Criteria:** Messages send and responses appear. Clear visual distinction between your messages and AI responses.

---

### Scenario 3: Asking a Production Data Question

**Objective:** Verify the AI can answer questions about production data.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Open the AI chat sidebar | Chat sidebar displays |
| 3.2 | Type: "What was the OEE for Grinder 5 yesterday?" | Text appears in input |
| 3.3 | Press Enter to send | Message sends and loading indicator appears |
| 3.4 | Wait for the response (may take 2-5 seconds) | AI responds with OEE information |
| 3.5 | Check the response content | Response should include: (a) A specific OEE percentage number, (b) Reference to "Grinder 5", (c) Reference to yesterday's date |
| 3.6 | Look for citations in the response | Response should include bracketed citations like [Source: daily_summaries/...] |

**Pass Criteria:** AI provides a specific, data-backed answer with citations. If no data exists, the AI should say so clearly (not make up numbers).

---

### Scenario 4: Verifying Citations

**Objective:** Verify that AI responses include clickable citations that show source data.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Ask a question that will return data (e.g., "Show me downtime for Line 3 this week") | AI responds with information and citations |
| 4.2 | Look at the citations in the response | Citations appear as colored text: blue for database sources, purple for memory/history sources |
| 4.3 | Hover over a citation link | A tooltip appears showing citation summary |
| 4.4 | Click on a citation link | A side panel opens showing the source data details |
| 4.5 | Review the source data panel | Panel shows: source type, actual data values, and timestamp |
| 4.6 | Close the citation panel (click X or outside the panel) | Panel closes, returning to the chat |

**Pass Criteria:** Citations are clickable and show actual source data. No citations link to non-existent data.

---

### Scenario 5: Checking Grounding Score

**Objective:** Verify that AI responses show confidence indicators.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Ask a factual question (e.g., "What was the financial loss from downtime yesterday?") | AI responds with information |
| 5.2 | Look for a confidence/grounding badge near the response | A badge showing "High Confidence", "Medium", or similar indicator should appear |
| 5.3 | If the grounding score is shown as a number, note it | Score should be between 0.6 and 1.0 for validated responses |
| 5.4 | Ask a vague or unanswerable question (e.g., "What will happen next month?") | AI should indicate uncertainty or insufficient evidence |

**Pass Criteria:** Responses include confidence indicators. Low-confidence responses are clearly marked or include disclaimers.

---

### Scenario 6: Testing Memory - Follow-up Questions

**Objective:** Verify the AI remembers context from previous questions in the conversation.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Open a new chat (or refresh the page and reopen chat) | Fresh chat window |
| 6.2 | Ask: "Tell me about Grinder 5's performance yesterday" | AI responds with Grinder 5 information |
| 6.3 | Follow up with: "What about the day before that?" | AI should understand "that" refers to Grinder 5 and provide data from 2 days ago |
| 6.4 | Ask: "How does this compare to the average?" | AI should understand context and compare Grinder 5's performance to averages |
| 6.5 | Ask: "Which asset had the worst OEE this week?" | AI responds with different asset information |
| 6.6 | Ask: "Why did it have low OEE?" | AI should understand "it" refers to the asset from the previous answer |

**Pass Criteria:** AI maintains conversation context. Follow-up questions work without repeating asset names.

---

### Scenario 7: Asset History Memory

**Objective:** Verify the AI can recall past resolutions and historical context for assets.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Open the AI chat sidebar | Chat displays |
| 7.2 | Ask: "Why does Grinder 5 keep failing?" OR "What's the history of issues with Grinder 5?" | AI searches asset history |
| 7.3 | Review the response | Response should include: (a) References to past incidents or maintenance, (b) Historical context about recurring issues, (c) Citations with purple "Memory" tags |
| 7.4 | If history exists, check for dates | Historical references should include when events occurred |
| 7.5 | Click on a memory citation (purple link) | Side panel shows the historical record details |

**Pass Criteria:** AI provides historical context when available. Memory citations link to actual history records.

---

### Scenario 8: Asking Financial Questions

**Objective:** Verify the AI can answer questions about financial impact.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Open the AI chat | Chat displays |
| 8.2 | Ask: "What was the total financial loss from downtime last week?" | AI processes the question |
| 8.3 | Review the response | Response should include: (a) A dollar amount, (b) Time period referenced, (c) Citation showing calculation source |
| 8.4 | Ask: "Which asset caused the most financial loss?" | AI responds with asset identification and dollar amount |
| 8.5 | Ask: "Break down the costs by day" | AI provides daily breakdown if data available |

**Pass Criteria:** Financial questions return specific dollar amounts with citations. No made-up numbers.

---

### Scenario 9: Multi-Asset Questions

**Objective:** Verify the AI can handle questions about multiple assets or areas.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Ask: "Compare OEE between all grinders this week" | AI processes the comparison |
| 9.2 | Review the response | Response includes: (a) Multiple assets listed, (b) OEE values for each, (c) Which performed best/worst |
| 9.3 | Ask: "Show me all safety events in the Grinding area" | AI retrieves area-wide data |
| 9.4 | Ask: "What's the overall plant performance today?" | AI provides plant-wide summary |

**Pass Criteria:** AI can aggregate and compare data across multiple assets.

---

### Scenario 10: Handling Unknown Data

**Objective:** Verify the AI handles questions about non-existent data gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Ask about a non-existent asset: "What's the OEE for Machine XYZ123?" | AI should NOT make up data |
| 10.2 | Review the response | Response should indicate: (a) Asset not found, OR (b) No data available for that asset |
| 10.3 | Ask about future data: "What will the production be next month?" | AI should clarify it cannot predict future data |
| 10.4 | Ask about very old data: "What was OEE five years ago?" | AI should indicate data is not available if it doesn't exist |

**Pass Criteria:** AI clearly states when data is unavailable rather than fabricating answers.

---

### Scenario 11: Keyboard Navigation

**Objective:** Verify the chat is fully keyboard accessible.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | Open the chat sidebar | Chat opens |
| 11.2 | Press Tab repeatedly | Focus moves through interactive elements (input, send button, close button) |
| 11.3 | Type a question in the input field | Text enters |
| 11.4 | Press Enter | Message sends (same as clicking Send) |
| 11.5 | Press Shift+Enter | A new line is added to the input (does not send) |
| 11.6 | Press Escape | Chat sidebar closes |

**Pass Criteria:** All chat functions accessible via keyboard. Tab order is logical.

---

### Scenario 12: Responsive Design

**Objective:** Verify the chat works on different screen sizes.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 12.1 | Open the chat on a desktop browser (full screen) | Chat sidebar takes up partial width (~400px) |
| 12.2 | Resize browser to tablet width (~768px) | Chat remains functional, may take more screen width |
| 12.3 | On mobile width (~375px) | Chat takes full width |
| 12.4 | Send a message at each size | Messages display correctly |
| 12.5 | Check that text is not cut off | All content readable, no horizontal scrolling needed |

**Pass Criteria:** Chat adapts to screen size while remaining functional.

---

### Scenario 13: Response Performance

**Objective:** Verify AI responses are generated within acceptable time.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 13.1 | Open the chat and ask a simple question: "What is OEE?" | Response appears within 3 seconds |
| 13.2 | Ask a data query: "Show OEE for all assets yesterday" | Response appears within 7 seconds |
| 13.3 | Ask a complex query: "Compare this week's performance to last week for all assets in the Grinding area" | Response appears within 10 seconds |
| 13.4 | During wait time, observe the loading indicator | Animated dots or spinner shows system is working |

**Pass Criteria:** Simple queries < 5 seconds. Complex queries < 10 seconds. Loading indicator always visible during processing.

---

### Scenario 14: Error Handling

**Objective:** Verify the chat handles errors gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 14.1 | Attempt to send an empty message (press Enter with no text) | Send button should be disabled OR message should not send |
| 14.2 | Send an extremely long message (1000+ characters if possible) | System handles gracefully - either accepts, truncates, or shows a length warning |
| 14.3 | If possible, disconnect internet and send a message | Error message appears indicating connection issue |
| 14.4 | Reconnect and try again | System recovers and allows new messages |

**Pass Criteria:** Errors show user-friendly messages. No crashes or frozen states.

---

## 4. Success Criteria Checklist

### Chat Interface

- [ ] Chat button visible on Command Center dashboard
- [ ] Chat sidebar opens and closes smoothly
- [ ] Input field accepts text and cursor is visible
- [ ] Messages send when pressing Enter or clicking Send
- [ ] User messages appear on right (blue background)
- [ ] AI messages appear on left (gray background)
- [ ] Loading indicator shows while AI is processing

### Natural Language Queries

- [ ] AI understands questions about OEE
- [ ] AI understands questions about downtime
- [ ] AI understands questions about financial loss
- [ ] AI can answer questions about specific assets
- [ ] AI can compare multiple assets
- [ ] AI can filter by date ranges (yesterday, last week, this month)

### Citations (NFR1 Compliance)

- [ ] All factual responses include citations
- [ ] Data citations appear in blue
- [ ] Memory citations appear in purple
- [ ] Clicking citations opens source data panel
- [ ] Source data panel shows actual database values
- [ ] No citations link to non-existent data
- [ ] Grounding score/confidence indicator visible

### Memory System

- [ ] AI remembers context within a conversation
- [ ] Follow-up questions work without repeating context
- [ ] Asset history is retrievable
- [ ] Past resolutions can be recalled

### Error Handling

- [ ] Unknown assets handled gracefully (no made-up data)
- [ ] Missing data clearly indicated
- [ ] Network errors show friendly messages
- [ ] Empty messages prevented

### Accessibility & Usability

- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Shift+Enter creates new line
- [ ] Responsive on tablet and desktop
- [ ] Text readable from standard viewing distance

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **Response Time Variability** - Complex queries may take 5-10 seconds. This is normal for AI processing with database queries.

2. **Data Recency** - The AI can only access data that has been loaded into the system. Very recent data (within the last few minutes) may not be available yet.

3. **Predictive Questions** - The AI cannot predict future performance. Questions about "next week" or "next month" will be declined.

4. **Natural Language Limits** - Very complex or ambiguous questions may require rephrasing. The AI will ask for clarification when needed.

5. **Citation Panel Design** - The citation detail panel shows raw data values. Visual formatting improvements may come in future releases.

6. **Session Memory** - Memory within a single chat session is maintained. Long-term memory across sessions is stored but may require specific questions to recall.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 4, Step 4.3)
2. **Question Asked** (exact text you typed)
3. **Expected Behavior** (what should have happened)
4. **Actual Behavior** (what actually happened)
5. **Screenshots** (if possible, especially of incorrect citations)
6. **Browser and Device** used
7. **Date and Time** of the issue

Report defects to: [Contact your IT administrator or QA lead]

---

## 7. Sign-Off Section

### Tester Information

| Field | Entry |
|-------|-------|
| **Tester Name** | Dmitri Spiropoulos |
| **Role/Title** | QA |
| **Test Date** | January 30, 2026 |
| **Test Environment** | UAT |
| **Browser/Device Used** | _________________________________ |

### Test Results Summary

| Category | Pass | Fail | Not Tested | Notes |
|----------|------|------|------------|-------|
| Chat Interface (Scenarios 1-2) | [x] | [ ] | [ ] | All scenarios pass |
| Production Queries (Scenario 3) | [x] | [ ] | [ ] | All scenarios pass |
| Citations (Scenarios 4-5) | [ ] | [x] | [ ] | 5.3: Confidence percentage always shows 80% regardless of actual grounding score |
| Memory - Context (Scenario 6) | [ ] | [x] | [ ] | 6.2-6.3: Date logic off by 1 day; 6.4: "Unable to execute query" error, retry failed |
| Asset History (Scenario 7) | [ ] | [x] | [ ] | 7.5: No purple memory link displayed |
| Financial Questions (Scenario 8) | [ ] | [x] | [ ] | 8.2, 8.5: "Unable to provide reliable answer" even at 0.2 threshold; 8.3: Blocked by 8.2 failure |
| Multi-Asset Queries (Scenario 9) | [ ] | [x] | [ ] | 9.4: "Unable to provide reliable answer" even at 0.2 threshold |
| Error Handling (Scenarios 10, 14) | [x] | [ ] | [ ] | All scenarios pass |
| Accessibility (Scenarios 11-12) | [x] | [ ] | [ ] | All scenarios pass |
| Performance (Scenario 13) | [x] | [ ] | [ ] | All scenarios pass |

### NFR1 Compliance Verification

- [ ] **VERIFIED** - All AI responses include citations to data sources
- [ ] **VERIFIED** - Citations link to actual data (no hallucinated references)
- [ ] **VERIFIED** - Confidence indicators present on responses
- [x] **NOT VERIFIED** - Issues found (document in comments)

### Overall Assessment

- [ ] **APPROVED** - All critical scenarios pass. Epic 4 is ready for production deployment.
- [ ] **APPROVED WITH CONDITIONS** - Minor issues noted but do not block deployment.
- [x] **NOT APPROVED** - Critical issues found. Requires fixes before deployment.

### Comments/Notes

**Grounding Threshold Issues:**
- Chat would not respond with answers to any questions until grounding confidence level was lowered to 0.2
- After lowering threshold, responses returned grounding confidence consistently between 0.25-0.30 with no deviation
- Several tests continued to have "Unable to provide reliable answer" errors even with the lowered threshold

**Response Formatting Issues:**
- Chatbot returns raw database query results instead of human-readable format
- Example: `datetime.datetime(2026, 1, 29, 2, 15, 59, 455000, tzinfo=datetime.timezone.utc)` instead of "January 29, 2026"

**Input Handling Issues:**
- "Hello" receives AI response, but shorter greetings like "Hi" returns a processing error
- General questions/statements (e.g., "Hello", "What will performance be next week?") have responses prefixed with "Col 0:" and extra periods at end of sentences

**Specific Scenario Failures:**
- Scenario 5.3: Confidence percentage always displays 80% regardless of actual grounding score
- Scenario 6.2-6.3: Date logic off by 1 day (yesterday returns today, day before returns yesterday)
- Scenario 6.4: "Unable to execute query" error, retry button non-functional
- Scenario 7.5: Purple memory link not displayed
- Scenario 8.2, 8.5, 9.4: "Unable to provide reliable answer" errors persist at 0.2 threshold

### Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Tester** | Dmitri Spiropoulos | | January 30, 2026 |
| **QA Lead** | | | |
| **Product Owner** | | | |
| **Technical Lead** | | | |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 7, 2026 | QA Specialist | Initial UAT document for Epic 4 |
| 1.1 | January 30, 2026 | Dmitri Spiropoulos | UAT testing completed - NOT APPROVED with critical issues documented |

---

*End of UAT Document*
