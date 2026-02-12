# Email Notifications & Response Tracking - User Acceptance Testing

**Epic**: 15
**Version**: 1.0
**Generated**: 2026-02-11
**Stories Covered**: 4

---

## Overview

### What Was Built

When a manager assigns a follow-up action to a team member, the system now sends an email notification to the assignee with all the relevant details and a link to respond. The assignee can click the link, read the context, and submit their response without needing to log in. The manager can then view the full conversation thread — what was sent, what was replied, and when — directly inside the app. Unread responses are highlighted so nothing falls through the cracks.

### Who Should Test

A **Plant Manager** or **Operations Lead** who regularly assigns follow-up actions to team members, and a **team member** (e.g., maintenance technician, operator) who would receive those assignments via email. Both roles are needed to test the full round-trip workflow.

### Time Estimate

45–60 minutes (both roles testing together)

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: `{test_environment_url}` (confirm with your admin)
   - Browser: Chrome (recommended) or Firefox

2. **Test Accounts**
   - **Manager account**: A user with the Plant Manager role who can assign follow-ups
   - **Team member account**: A user who is listed as a team member and has a valid email address configured in the system
   - Both accounts must be able to log in to the TFN AI Hub application

3. **Test Data Setup**
   - At least one **action item** must exist (from a completed AI briefing report) so that the manager can assign a follow-up from it
   - The team member's email address must be deliverable (use a real inbox or a test inbox you can check, such as a shared mailbox or email alias)
   - SMTP credentials must be configured in the environment (ask your admin to verify `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM` are set)

4. **Clean State**
   - Ensure the action item you plan to use does not already have a follow-up assigned to the same team member (or create a fresh action item)
   - Check the team member's email inbox and clear or note any prior test notification emails

---

## Test Scenarios

### Scenario 1: Assign a Follow-Up and Receive Email Notification

**Purpose**: Verify that assigning a follow-up sends an email notification to the assignee with all the correct details.

**Starting Point**: Logged in as the Manager. Navigate to the Action Engine and locate an action item.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on an action item to open its details | The action item detail view opens showing recommendation, evidence, and financial impact |
| 2 | Click the "Assign Follow-Up" button | The Assign Follow-Up dialog opens |
| 3 | Select a team member from the assignee dropdown | The team member's name appears as the selected assignee |
| 4 | Type an optional note (e.g., "Please inspect the bearing on Unit 3 and report findings") | The note text appears in the note field |
| 5 | Click "Assign" to save the follow-up | The dialog closes. A success message confirms the follow-up was created |
| 6 | Check the team member's email inbox (within 60 seconds) | An email arrives with the subject line: `[Action Required] {category} — {asset_name}: {action_summary}` |
| 7 | Open the email and review its contents | The email body contains: the action item recommendation, evidence summary, financial impact (if any), who assigned it, the manager's note, and a "Respond" button or link |

**Success Criteria**: The assignee receives an email within 60 seconds of the follow-up being assigned, and the email contains all the action item details plus the manager's note.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: Respond to a Follow-Up via the Email Link

**Purpose**: Verify that the assignee can click the link in the email, see the action item context, and submit a response without logging in.

**Starting Point**: The team member has received the notification email from Scenario 1.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the notification email and click the "Respond" button/link | A new browser tab opens showing the TFN AI Hub response page |
| 2 | Review the context displayed on the page | The page shows: the action item summary, asset name, category, who assigned it, the manager's note, and the report date. No login is required |
| 3 | Type a response in the text field (e.g., "Inspected the bearing. Found early wear on the inner race. Recommending replacement during next planned shutdown.") | The text appears in the response field |
| 4 | Click "Submit Response" | A success confirmation appears: "Your response has been recorded" with a green checkmark |
| 5 | Try clicking "Submit Response" again | The submit button is disabled — double submission is prevented |

**Success Criteria**: The assignee can submit a response through the email link without logging in, and sees a clear success confirmation.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: View the Conversation Thread as a Manager

**Purpose**: Verify that the manager can see the full message thread (sent notification + received response) inside the app.

**Starting Point**: Logged in as the Manager. The team member has already submitted a response (Scenario 2 completed).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the My Assignments panel or the action card where the follow-up was assigned | The follow-up entry is visible in the list |
| 2 | Look for an unread indicator on the follow-up entry | A blue dot or badge appears on the follow-up, indicating a new unread response |
| 3 | Click on the follow-up entry to view its details | A message thread opens showing the conversation |
| 4 | Review the outbound message | The thread shows "Sent to {assignee} at {time}" with the original assignment notification content |
| 5 | Review the inbound response | The thread shows "{assignee} replied at {time}" with the full response text submitted by the team member |
| 6 | Close and reopen the follow-up detail | The unread indicator (blue dot) is no longer visible — the response has been marked as read |

**Success Criteria**: The manager can see the full conversation thread in chronological order, and the unread indicator clears after viewing.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Follow-Up Status Updates After Response

**Purpose**: Verify that the follow-up status changes appropriately when a response is received.

**Starting Point**: Logged in as the Manager. The follow-up was originally in "Assigned" status.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Before the team member responds, check the follow-up status | The status shows "Assigned" |
| 2 | After the team member submits their response via the email link (Scenario 2) | The follow-up status automatically updates to "In Progress" |
| 3 | Verify the status is visible in the My Assignments panel | The status badge shows "In Progress" |

**Success Criteria**: The follow-up status transitions from "Assigned" to "In Progress" automatically when the first response is submitted.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: Follow-Up with No Response Yet

**Purpose**: Verify that when no response has been received, the thread shows the appropriate waiting state.

**Starting Point**: Logged in as the Manager. A new follow-up has just been assigned (but the team member has not yet responded).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the follow-up entry and open the thread view | The message thread opens |
| 2 | Review what is displayed | Only the outbound notification message is shown ("Sent to {assignee} at {time}") |
| 3 | Check for a waiting indicator | A note appears: "Awaiting response from {assignee_name}" |
| 4 | Verify there is no unread indicator on this follow-up | No blue dot or badge is visible (there is nothing new to read) |

**Success Criteria**: The thread shows only the sent notification and clearly indicates the system is awaiting a response.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Expired Response Link

**Purpose**: Verify that an expired or already-used response link shows an appropriate message and does not allow submission.

**Starting Point**: A response link that has already been used (from Scenario 2) or a link that is more than 72 hours old.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click the "Respond" link from the notification email again (after already submitting a response in Scenario 2) | The response page opens |
| 2 | Review what is displayed | A message appears: "This link has expired. Please log in to the app to respond." No response form is shown |
| 3 | Verify no text field or submit button is visible | The page shows only the expiry message — no way to submit another response |

**Success Criteria**: Used or expired links display a clear expiry message and do not allow further submissions.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 7: Invalid Response Link

**Purpose**: Verify that a tampered or invalid response link shows an error without exposing system details.

**Starting Point**: No prior setup needed.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | In the browser address bar, navigate to a response URL with a made-up token (e.g., `{app_url}/followups/00000000-0000-0000-0000-000000000000/respond?token=fake-token-123`) | The page loads |
| 2 | Review what is displayed | An "Invalid link" or "Page not found" message is shown. No action item details or response form are displayed |

**Success Criteria**: Invalid links return a generic error message without revealing any system information.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Email Service Unavailable

**Purpose**: Verify that follow-up assignments still work even when the email system is down or not configured.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Ask your admin to temporarily disable or misconfigure SMTP settings | SMTP is non-functional |
| 2 | Assign a new follow-up to a team member | The follow-up is created successfully. The dialog closes with a success message |
| 3 | Verify the follow-up appears in the My Assignments panel | The follow-up is listed with "Assigned" status |
| 4 | Note that no email arrives (expected) | The assignment is saved; email delivery failed silently without blocking the assignment |

**Result**: ☐ Pass  ☐ Fail

---

### Access Control — Unauthorized Thread Viewing

**Purpose**: Verify that users who are neither the assigner nor the assignee cannot view the conversation thread.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in as a third user who is not the assigner or assignee of any existing follow-up | The user is logged in |
| 2 | Attempt to access the message thread for a follow-up belonging to other users | The thread either returns no messages or shows an access-denied response. No conversation content is visible |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] Assign a follow-up and the assignee receives an email notification within 60 seconds
- [ ] The notification email contains all the action item details, assigner info, and a response link
- [ ] The assignee can submit a response via the email link without logging in
- [ ] The manager can view the full conversation thread (sent + received messages) inside the app
- [ ] Unread responses are indicated with a visual badge that clears after viewing
- [ ] Follow-up status updates from "Assigned" to "In Progress" when a response is received
- [ ] Expired or used response links show an appropriate message and block further submissions
- [ ] Invalid response links show a generic error without revealing system details
- [ ] Follow-up assignments succeed even when the email service is unavailable

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
| Scenarios Tested | \_\_ / 7 |
| Scenarios Passed | \_\_ / 7 |
| Edge Cases Tested | \_\_ / 2 |
| Edge Cases Passed | \_\_ / 2 |
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

- **Action Item**: Any action item from a completed AI briefing report with a recommendation, evidence summary, and optionally a financial impact value
- **Team Member**: A user listed in the team members directory with a valid, deliverable email address
- **Manager**: A user with Plant Manager role who can assign follow-ups
- **SMTP Configuration**: Environment variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` must be set for email scenarios

### Environment Details

- **Application URL**: Confirm with admin (e.g., `https://staging.tfn-aihub.example.com`)
- **API URL**: Confirm with admin (e.g., `https://staging-api.tfn-aihub.example.com`)
- **Browser**: Chrome 120+ or Firefox 120+ recommended
- **Email Client**: Any email client that supports HTML rendering (Outlook, Gmail, Apple Mail)

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-15.md`
- Stories: `_bmad-output/implementation-artifacts/stories/15-*.md`

---

*Generated by BMAD epic-execute workflow*
