# Meeting Mode & Teams Integration - User Acceptance Testing

**Epic**: 18
**Version**: 1.0
**Generated**: 2026-02-12
**Stories Covered**: 5

---

## Overview

### What Was Built

Plant managers can now run their morning standup directly from the app using a new "Meeting Mode" that shows a condensed, scannable view of the top action items. The app also integrates with Microsoft Teams to automatically post a morning summary card each day, notify team members when they're assigned follow-ups, and send escalation nudges when safety events or follow-ups go unaddressed.

### Who Should Test

A **Plant Manager** or **Operations Lead** who regularly runs morning standups and uses Microsoft Teams. The tester should have access to the TFN AI Hub web application and a Teams channel where webhook messages can be received.

### Time Estimate

45–60 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: Your staging/test environment URL (e.g., `https://staging.tfn-aihub.example.com`)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Log in with a Plant Manager account that has access to morning reports
   - Ensure at least one additional team member account exists for follow-up assignment testing

3. **Test Data Setup**
   - A morning report should already exist for today's date (or a recent date) with at least 3–5 action items, including at least one **safety** item
   - At least one follow-up assignment should exist in "assigned" status
   - The `TEAMS_WEBHOOK_URL` environment variable should be configured with a valid Teams Incoming Webhook URL pointing to a test channel

4. **Clean State**
   - Open the morning report page in normal (non-meeting) mode before beginning
   - Have the target Teams channel visible so you can observe incoming messages

---

## Test Scenarios

### Scenario 1: Activate Meeting Mode from the Morning Report

**Purpose**: Verify that a plant manager can switch to a condensed "meeting mode" view that shows only the key talking points for a standup meeting.

**Starting Point**: Logged in, viewing the morning report page in normal mode.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at the top of the morning report page, near the title | You see a "Meeting Mode" toggle button |
| 2 | Click the "Meeting Mode" toggle | The page switches to a condensed layout showing large cards with only the headline, asset name, priority, and who's assigned |
| 3 | Check the section headers | You see three clear sections: "Safety", "Yesterday's Performance", and "Today's Priorities" |
| 4 | Count the visible action items | No more than 5 items are shown, with the highest-priority items first |
| 5 | Look at the browser address bar | The URL now includes `?mode=meeting` |

**Success Criteria**: The meeting mode view shows a condensed, scannable layout with section headers and no more than 5 prioritized items.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: Use Meeting Mode During a Standup

**Purpose**: Verify that the meeting mode view supports the standup workflow — managers can see assignments and quickly assign follow-ups.

**Starting Point**: Meeting mode is active (from Scenario 1).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at any action item card in meeting mode | You see a prominent "Assign Follow-Up" button directly on the card (not hidden in a menu) |
| 2 | Check if any items already have someone assigned | Assigned items show a visible badge with the assignee's name |
| 3 | Click the "Assign Follow-Up" button on one of the items | A dialog opens allowing you to select a team member and add a note |
| 4 | Assign the follow-up to a team member and save | The dialog closes, and the assignment badge appears on the card |

**Success Criteria**: Follow-up assignments are easy to make directly from meeting mode cards, and assignment badges are clearly visible.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: Switch Back to Normal Mode

**Purpose**: Verify that toggling off meeting mode restores the full report with all details.

**Starting Point**: Meeting mode is active.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click the "Meeting Mode" toggle button again | The page switches back to the full report view |
| 2 | Look at the action items | All evidence details, metrics, and drill-down options are visible again |
| 3 | Check the browser address bar | The `?mode=meeting` parameter is removed from the URL |

**Success Criteria**: The full report view is completely restored with all detail sections visible.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Open Meeting Mode via Direct Link

**Purpose**: Verify that sharing a meeting mode URL opens the report directly in meeting mode.

**Starting Point**: Logged in, on any page in the app.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | In the browser address bar, navigate to the morning report URL with `?mode=meeting` appended (e.g., `/morning-report?date=2026-02-12&mode=meeting`) | The morning report loads directly in meeting mode — condensed layout with large cards and section headers |
| 2 | Verify the toggle button shows meeting mode as active | The toggle button appears in its "on" or "pressed" state |

**Success Criteria**: A direct URL with `?mode=meeting` opens the report in meeting mode automatically.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: Morning Summary Card Arrives in Teams

**Purpose**: Verify that a summary of the morning report is automatically posted to the Teams channel.

**Starting Point**: The Teams test channel is open and the morning pipeline has run (or has been manually triggered).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the configured Teams channel | You see a new card titled "Morning Report — {today's date}" |
| 2 | Read the summary line on the card | It shows the total number of action items broken down by category (e.g., "5 action items: 1 safety, 2 OEE misses, 2 financial") |
| 3 | Look at the bullet points on the card | The top 3 action items are listed with asset name and headline |
| 4 | Click the "Open Report" button on the card | Your browser opens the morning report page for that date |

**Success Criteria**: The Teams card displays an accurate summary of the morning report and links back to the app.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Follow-Up Assignment Notification in Teams

**Purpose**: Verify that when a manager assigns a follow-up, a notification appears in the Teams channel.

**Starting Point**: Logged in to the app, Teams channel visible.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the morning report and assign a follow-up to a team member (via the "Assign Follow-Up" button on any action item) | The follow-up is created successfully in the app |
| 2 | Switch to the Teams channel | A new notification card appears with the message: "{your name} assigned you a follow-up: {action summary} on {asset name}" |
| 3 | Check the card details | The card shows the action summary, asset name, category, who assigned it, and any note you added |
| 4 | Click the "View in App" button on the card | Your browser opens the morning report page |

**Success Criteria**: A Teams notification is posted immediately when a follow-up is assigned, with all relevant details and a working link back to the app.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 7: Escalation Nudge for Unacknowledged Safety Event

**Purpose**: Verify that the system sends a reminder when a safety event goes unaddressed for more than 2 hours.

**Starting Point**: A safety action item exists that has not been resolved, and at least 2 hours have passed since it was created. The escalation background task has run (runs hourly).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check the Teams channel after the escalation check has run | You see a nudge message: "Safety alert on {asset name} has been unacknowledged for {X} hours. Please review." |
| 2 | Check that the message includes a link | An "Open Report" button is present on the card |
| 3 | Click the "Open Report" button | Your browser opens the morning report page |

**Success Criteria**: An escalation nudge is automatically posted for unacknowledged safety events after 2 hours.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 8: Escalation Nudge for Stale Follow-Up

**Purpose**: Verify that the system sends a reminder when a follow-up assignment sits without an update for more than 24 hours.

**Starting Point**: A follow-up exists in "assigned" status that was last updated more than 24 hours ago. The escalation background task has run.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check the Teams channel after the escalation check has run | You see a nudge message: "Follow-up for {asset name} assigned to {assignee} has had no update for 24 hours" |
| 2 | Now update the follow-up status in the app (e.g., change to "in progress") | The follow-up is updated |
| 3 | Wait for the next escalation check to run | No new nudge is sent for this follow-up (since it was recently updated) |

**Success Criteria**: Stale follow-ups trigger a nudge after 24 hours, and updating the follow-up stops future nudges.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Edge Case 1: Morning Report with No Action Items

**Purpose**: Verify the system handles a day with no action items gracefully in both meeting mode and the Teams card.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the morning report on a date with no action items and enable meeting mode | Meeting mode shows section headers but displays "No items" under each section |
| 2 | Check the Teams channel for the morning summary card for that date | The card reads: "Morning Report — {date}: All clear. No action items today." with an "Open Report" button |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 2: Teams Webhook Not Configured

**Purpose**: Verify the system works normally when no Teams webhook URL is set.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Remove or leave blank the `TEAMS_WEBHOOK_URL` environment variable and restart the app | The app starts without errors |
| 2 | Run the morning pipeline | The morning report is generated successfully; no Teams card is sent (and no errors appear in the app) |
| 3 | Assign a follow-up to a team member | The follow-up is created successfully; no Teams notification is sent (and no errors appear) |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 3: Teams Webhook Test Button

**Purpose**: Verify an admin can test the Teams connection.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Send a test request to the Teams webhook test endpoint (`POST /api/v1/notifications/teams/test`) via the API or admin tools | A test card appears in the Teams channel with the message "TFN AI Hub - Connection Test" |
| 2 | If no webhook URL is configured, send the same test request | The API returns an error message indicating Teams is not configured (no crash or unexpected error) |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 4: Escalation Rate Limiting

**Purpose**: Verify the system does not spam the Teams channel with repeated nudges for the same item.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note a safety escalation nudge that was sent to Teams | The nudge message appears in the channel |
| 2 | Wait for the next escalation check to run (within 4 hours of the first nudge) | No duplicate nudge is sent for the same item |
| 3 | Wait until more than 4 hours have passed since the first nudge, then let the escalation check run again | A new nudge is sent (since the cooldown period has elapsed) |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] Switch to meeting mode and see a condensed, scannable view of the top 3–5 action items grouped by category
- [ ] Assign follow-ups directly from meeting mode cards with a prominent button
- [ ] Toggle back to normal mode and see the full report restored
- [ ] Share a meeting mode URL that opens directly in meeting mode
- [ ] Receive a morning summary card in Teams each day with action item counts and a link to the report
- [ ] Receive a Teams notification when assigned a follow-up with all relevant details
- [ ] See escalation nudges in Teams for unacknowledged safety events (2+ hours) and stale follow-ups (24+ hours)
- [ ] Confirm that the system works normally when Teams is not configured (no errors, no crashes)
- [ ] Confirm that escalation nudges are rate-limited (no duplicate nudges within 4 hours)

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
| Scenarios Tested | \_\_ / 12 |
| Scenarios Passed | \_\_ / 12 |
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

| Data | Description |
|------|-------------|
| Morning report | A report with 3–5 action items including at least 1 safety item, 1 OEE item, and 1 financial item |
| Team members | At least 2 user accounts — one Plant Manager (tester) and one team member (assignee) |
| Safety event | A safety event created 2+ hours ago with status not "resolved" |
| Stale follow-up | A follow-up in "assigned" status with `updated_at` older than 24 hours |
| Teams webhook | A valid Microsoft Teams Incoming Webhook URL for a test channel |

### Environment Details

| Setting | Value |
|---------|-------|
| `TEAMS_WEBHOOK_URL` | Teams Incoming Webhook URL for the test channel |
| `WEBAPP_BASE_URL` | Base URL of the web app (for "Open Report" links in Teams cards) |
| `ESCALATION_CHECK_INTERVAL_MINUTES` | Default: 60 (how often escalation checks run) |
| `ESCALATION_SAFETY_THRESHOLD_HOURS` | Default: 2 (hours before safety nudge) |
| `ESCALATION_FOLLOWUP_THRESHOLD_HOURS` | Default: 24 (hours before follow-up nudge) |
| `ESCALATION_COOLDOWN_HOURS` | Default: 4 (minimum hours between nudges for same item) |

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-18.md`
- Stories: `_bmad-output/implementation-artifacts/stories/18-*.md`

---

*Generated by BMAD epic-execute workflow*
