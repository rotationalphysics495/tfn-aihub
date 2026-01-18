# User Acceptance Testing Document
# Epic 9: Shift Handoff & EOD Summary

**Version:** 1.0
**Date:** January 18, 2026
**Last Updated:** January 18, 2026
**Prepared For:** Plant Managers, Supervisors, and Administrators
**Test Environment:** TFN AI Hub - Shift Handoff & EOD System
**Document Status:** Ready for Testing

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Test Scenarios](#3-test-scenarios)
4. [Success Criteria](#4-success-criteria)
5. [Known Limitations](#5-known-limitations)
6. [Issue Reporting](#6-issue-reporting)
7. [Sign-Off Section](#7-sign-off-section)

---

## 1. Overview

### What Was Built

Epic 9 introduces **Shift Handoff** and **End of Day Summary** features to ensure knowledge doesn't walk out the door when shifts change. This creates accountability loops and continuous improvement through prediction tracking.

| Feature | What It Does | User Benefit |
|---------|--------------|--------------|
| **Shift Handoff Creation** | Outgoing supervisors create handoff records for incoming shifts | Knowledge transfer between shifts |
| **Auto-Generated Summaries** | System synthesizes shift data into narrative summaries | No manual data compilation needed |
| **Voice Notes** | Record voice notes up to 60 seconds each (max 5 per handoff) | Quick context that's hard to type |
| **Handoff Review** | Incoming supervisors see pending handoffs with notifications | Never miss critical shift information |
| **Q&A Follow-Up** | Ask questions about handoff content with AI-powered answers | Clarify anything before taking over |
| **Acknowledgment Flow** | Formally acknowledge receipt of handoffs | Clear audit trail of knowledge transfer |
| **Offline Support** | View handoffs without internet, queue acknowledgments | Access critical info anywhere on the floor |
| **EOD Summary** | Plant Managers review actual outcomes vs morning predictions | Close the feedback loop on predictions |
| **Morning vs Actual Comparison** | Compare morning briefing concerns to what actually happened | Assess prediction accuracy over time |
| **EOD Reminders** | Optional push notifications to remind you to review EOD | Don't forget to close out the day |
| **Admin Asset Assignment** | Assign supervisors to specific assets/areas | Control who sees what in briefings and handoffs |
| **Admin Role Management** | Assign roles (Supervisor, Plant Manager, Admin) | Manage access levels for all users |
| **Audit Logging** | All admin changes logged with before/after values | Full accountability and troubleshooting |

### Who This Is For

- **Outgoing Supervisors**: Create comprehensive shift handoffs with summaries and voice notes
- **Incoming Supervisors**: Review handoffs, ask questions, and acknowledge receipt
- **Plant Managers**: Review End of Day summaries comparing morning predictions to actual outcomes
- **Administrators**: Assign supervisors to assets and manage user roles with full audit trails

### What You Can Do

**Supervisors:**
1. Create a shift handoff at the end of your shift
2. Review auto-generated shift summaries
3. Add voice notes (up to 5, max 60 seconds each)
4. View pending handoffs when starting your shift
5. Ask follow-up questions about handoff content
6. Acknowledge handoffs to create an audit trail
7. Access handoffs offline on the plant floor

**Plant Managers:**
1. Trigger End of Day summaries
2. Compare morning briefing predictions to actual outcomes
3. Track prediction accuracy over time
4. Receive optional EOD reminder notifications

**Administrators:**
1. Assign supervisors to specific assets and areas
2. Preview assignment impact before saving
3. Set temporary assignments with expiration dates
4. Assign roles (Supervisor, Plant Manager, Admin)
5. View complete audit logs of all changes

---

## 2. Prerequisites

### Test Environment Access

| Item | Requirement |
|------|-------------|
| Device | Tablet (iPad recommended), Desktop, or Mobile |
| Browser | Chrome, Firefox, Safari 14.1+, or Edge (latest version) |
| Audio | Speakers/headphones for voice note playback |
| Microphone | Required for recording voice notes |
| Network | Internet connection (offline features available for viewing) |

### Test Accounts

Request test accounts from your IT administrator:

| Role | Account Type | What You'll See |
|------|--------------|-----------------|
| Admin | `testadmin@tfn.com` | Asset assignment grid, user management, audit logs |
| Plant Manager | `testpm@tfn.com` | All areas, EOD summary with comparison |
| Supervisor (Outgoing) | `testsup1@tfn.com` | Assigned assets (Grinding, Packing) - creates handoffs |
| Supervisor (Incoming) | `testsup2@tfn.com` | Assigned assets (Grinding, Packing) - reviews handoffs |

### Before You Begin

1. **Allow microphone access** when prompted for voice notes
2. **Allow notification access** if testing EOD reminders
3. **Test with multiple accounts** to simulate outgoing/incoming supervisor scenarios
4. **Use incognito/private windows** to log in as different users simultaneously

---

## 3. Test Scenarios

### SECTION A: Shift Handoff Creation (Outgoing Supervisor)

---

### Scenario 1: Creating a Shift Handoff

**Purpose**: Verify that outgoing supervisors can create handoffs with auto-generated summaries.

**Prerequisites**: Log in as `testsup1@tfn.com` (Outgoing Supervisor)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Handoff page (click "Handoff" in navigation) | See Handoff list page |
| 2 | Click "Create Shift Handoff" button | Handoff creation wizard opens |
| 3 | Review Step 1: Shift Confirmation | See your assigned assets pre-populated, shift type auto-detected (Day/Swing/Night based on current time) |
| 4 | Verify shift time range | Shows last 8 hours (e.g., "2:00 PM - 10:00 PM") |
| 5 | Click "Next" | Proceed to Step 2: Shift Summary |
| 6 | Wait for summary generation | Auto-generated summary appears within 15 seconds |
| 7 | Review summary content | See: production status, downtime reasons, any safety incidents, active alerts |
| 8 | Optionally add text notes | Notes field accepts your input |
| 9 | Click "Next" | Proceed to Step 3: Voice Notes |
| 10 | Click "Next" (skip voice for now) | Proceed to Step 4: Confirmation |
| 11 | Review all information | See summary of handoff details |
| 12 | Click "Submit Handoff" | Success message appears, redirected to handoff list |

**Pass/Fail Criteria**:
- [ ] Assigned assets were pre-populated
- [ ] Shift type was correctly auto-detected
- [ ] Summary generated within 15 seconds
- [ ] Summary included production, downtime, and alerts
- [ ] Handoff was successfully created

---

### Scenario 2: Adding Voice Notes to Handoff

**Purpose**: Verify that supervisors can record and attach voice notes.

**Prerequisites**: Log in as `testsup1@tfn.com`, microphone access granted

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start creating a new handoff | Wizard opens |
| 2 | Navigate to Step 3: Voice Notes | See "Add Voice Note" button |
| 3 | Click "Add Voice Note" | Recording interface appears |
| 4 | Press and hold the record button | Pulsing indicator shows recording active |
| 5 | Speak for 10-15 seconds about an issue | Audio level indicator shows your voice being captured |
| 6 | Release the record button | Recording stops, transcription begins |
| 7 | Wait for transcription | Transcript appears below the audio within 3 seconds |
| 8 | Review the voice note | See duration (e.g., "0:12"), play button, transcript |
| 9 | Click play button | Audio plays back correctly |
| 10 | Record a second voice note | "2/5 voice notes" indicator updates |
| 11 | Continue to confirmation and submit | Voice notes are saved with handoff |

**Pass/Fail Criteria**:
- [ ] Recording indicator appeared during recording
- [ ] 60-second countdown timer visible during recording
- [ ] Transcription completed within 3 seconds
- [ ] Audio playback worked correctly
- [ ] Voice note count updated (X/5)
- [ ] Voice notes were attached to final handoff

---

### Scenario 3: Voice Note Limit Enforcement

**Purpose**: Verify that the 5 voice note limit and 60-second duration are enforced.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add 5 voice notes to a handoff | Counter shows "5/5 voice notes" |
| 2 | Try to add a 6th voice note | "Add Voice Note" button is disabled |
| 3 | Delete one voice note (click X) | Counter updates to "4/5", button re-enabled |
| 4 | Start recording and hold for 60+ seconds | Recording auto-stops at 60 seconds |
| 5 | Review the auto-stopped note | Shows exactly "1:00" duration |

**Pass/Fail Criteria**:
- [ ] Maximum 5 voice notes enforced
- [ ] Delete button works to remove notes
- [ ] 60-second auto-stop works
- [ ] No error messages shown

---

### Scenario 4: No Assets Assigned Error

**Purpose**: Verify appropriate error when supervisor has no asset assignments.

**Prerequisites**: Use a test account with no assigned assets

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Handoff page | Handoff list appears |
| 2 | Click "Create Shift Handoff" | Error message appears |
| 3 | Read the error message | "No assets assigned - contact your administrator" |
| 4 | Verify no handoff wizard opens | Creation is blocked |

**Pass/Fail Criteria**:
- [ ] Clear error message displayed
- [ ] Handoff creation blocked
- [ ] User understands they need admin help

---

### Scenario 5: Duplicate Handoff Prevention

**Purpose**: Verify that duplicate handoffs for the same shift are prevented.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create and submit a shift handoff | Handoff created successfully |
| 2 | Click "Create Shift Handoff" again | Prompt appears asking to edit existing or add supplemental note |
| 3 | Select "Edit existing" | Navigate to existing handoff for editing |
| 4 | Select "Add supplemental note" | Opens form to add additional notes to existing handoff |

**Pass/Fail Criteria**:
- [ ] System detected existing handoff
- [ ] User given choice to edit or supplement
- [ ] No duplicate handoffs created

---

### SECTION B: Handoff Review (Incoming Supervisor)

---

### Scenario 6: Viewing Pending Handoffs

**Purpose**: Verify that incoming supervisors are notified of pending handoffs.

**Prerequisites**:
- Handoff created by `testsup1@tfn.com` for shared assets
- Log in as `testsup2@tfn.com` (Incoming Supervisor)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Handoff page | Handoff list appears |
| 2 | Look for notification banner | Banner shows "Handoff available from [Name]" |
| 3 | View the Pending Handoffs section | See handoff cards with status "Pending" |
| 4 | Review handoff card info | Shows: outgoing supervisor name, timestamp, summary preview |
| 5 | Click on a handoff card | Navigate to handoff detail page |

**Pass/Fail Criteria**:
- [ ] Notification banner appeared for pending handoff
- [ ] Handoff card showed correct information
- [ ] Navigation to detail page worked

---

### Scenario 7: Reviewing Handoff Details

**Purpose**: Verify that incoming supervisors can view all handoff content.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open a pending handoff | Detail page loads |
| 2 | Review Shift Summary section | Auto-generated summary with citations displayed |
| 3 | Review Text Notes section | Any notes from outgoing supervisor visible |
| 4 | Review Voice Notes section | Voice notes listed with play buttons |
| 5 | Click play on a voice note | Audio plays, transcript displayed below |
| 6 | Use playback controls | Play/pause, seek bar work correctly |
| 7 | See Acknowledge button | Button visible at bottom of page |

**Pass/Fail Criteria**:
- [ ] All sections displayed correctly
- [ ] Voice notes played back
- [ ] Transcripts showed below audio
- [ ] Citations appeared in summary
- [ ] Acknowledge button visible

---

### Scenario 8: Asking Follow-Up Questions (Q&A)

**Purpose**: Verify that incoming supervisors can ask questions about handoff content.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open a handoff detail page | Q&A section visible |
| 2 | Type a question: "What caused the downtime on Line 3?" | Question appears in input field |
| 3 | Click "Send" or press Enter | Question submitted, loading indicator appears |
| 4 | Wait for AI response | Response appears within 15 seconds |
| 5 | Review the response | Answer references handoff content, includes citations |
| 6 | Ask another question | Q&A thread grows, all questions/answers preserved |
| 7 | Verify AI vs Human indicator | AI responses show AI badge |

**Pass/Fail Criteria**:
- [ ] Question submitted successfully
- [ ] AI response received within 15 seconds
- [ ] Response included relevant citations
- [ ] Q&A thread preserved all entries
- [ ] AI responses clearly marked

---

### Scenario 9: Acknowledging a Handoff

**Purpose**: Verify that acknowledgment creates an audit trail.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open a pending handoff | Detail page with Acknowledge button |
| 2 | Click "Acknowledge Handoff" | Confirmation dialog appears |
| 3 | Optionally add acknowledgment notes | Notes text area available |
| 4 | Type: "Understood. Will monitor Line 3 closely." | Notes accepted |
| 5 | Click "Confirm" | Acknowledgment processed |
| 6 | View success message | "Handoff acknowledged" confirmation |
| 7 | Return to handoff list | Handoff now shows "Acknowledged" status |
| 8 | Re-open the handoff | See acknowledgment details (user, timestamp, notes) |

**Pass/Fail Criteria**:
- [ ] Confirmation dialog appeared
- [ ] Optional notes accepted
- [ ] Acknowledgment recorded successfully
- [ ] Status changed to "Acknowledged"
- [ ] Acknowledgment details visible (user, time, notes)

---

### Scenario 10: Acknowledgment Notification (Outgoing Supervisor)

**Purpose**: Verify that outgoing supervisors are notified when their handoff is acknowledged.

**Prerequisites**:
- Handoff created by `testsup1@tfn.com`
- Have `testsup1@tfn.com` logged in (can use separate browser/tab)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | As `testsup2@tfn.com`: Acknowledge a handoff | Acknowledgment successful |
| 2 | As `testsup1@tfn.com`: Check for notification | In-app notification appears |
| 3 | Review notification content | Shows: acknowledging user, timestamp, any notes |
| 4 | Click the notification | Navigate to handoff detail page |

**Pass/Fail Criteria**:
- [ ] Notification appeared for outgoing supervisor
- [ ] Notification contained correct information
- [ ] Click navigated to handoff detail

---

### SECTION C: Offline Capabilities

---

### Scenario 11: Viewing Handoffs Offline

**Purpose**: Verify that handoffs can be viewed without internet connection.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View a handoff while online | Handoff loads and displays |
| 2 | Disconnect from internet (airplane mode or disable WiFi) | Connection lost |
| 3 | Navigate to the same handoff | Handoff displays from cache |
| 4 | Look for offline indicator | Banner shows "Viewing offline - some features limited" |
| 5 | Play a cached voice note | Audio plays from local cache |
| 6 | Try to ask a Q&A question | Feature shows as unavailable offline |

**Pass/Fail Criteria**:
- [ ] Handoff displayed from cache
- [ ] Offline banner appeared
- [ ] Voice notes played from cache
- [ ] Q&A appropriately disabled offline

---

### Scenario 12: Offline Acknowledgment Queuing

**Purpose**: Verify that acknowledgments queue offline and sync when reconnected.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View a pending handoff while online | Handoff displays |
| 2 | Disconnect from internet | Connection lost |
| 3 | Click "Acknowledge Handoff" | Acknowledgment queued |
| 4 | See pending sync indicator | "Acknowledgment pending sync" message |
| 5 | Reconnect to internet | Connection restored |
| 6 | Wait for sync | Acknowledgment syncs automatically |
| 7 | Verify handoff status | Status changes to "Acknowledged" |

**Pass/Fail Criteria**:
- [ ] Acknowledgment queued while offline
- [ ] Pending sync indicator shown
- [ ] Auto-sync occurred on reconnect
- [ ] Acknowledgment recorded correctly

---

### Scenario 13: Stale Cache Warning

**Purpose**: Verify that old cached data shows a warning.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View a handoff and note the time | Handoff cached |
| 2 | Wait 48+ hours (or have IT simulate old cache) | Cache becomes stale |
| 3 | Go offline and view the handoff | Handoff displays |
| 4 | Look for stale warning | Warning: "Data may be outdated (cached 48+ hours ago)" |
| 5 | Reconnect to internet | Warning cleared, fresh data loaded |

**Pass/Fail Criteria**:
- [ ] Stale cache warning appeared
- [ ] Warning cleared on reconnect
- [ ] Fresh data loaded after reconnect

---

### SECTION D: End of Day Summary (Plant Manager)

---

### Scenario 14: Triggering EOD Summary

**Purpose**: Verify that Plant Managers can generate End of Day summaries.

**Prerequisites**: Log in as `testpm@tfn.com` (Plant Manager)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Briefing > End of Day | EOD Summary page loads |
| 2 | Click "Generate EOD Summary" | Summary generation begins |
| 3 | Wait for generation | Summary appears within 30 seconds |
| 4 | Review summary sections | See: Performance vs Target, Wins, Concerns, Outlook |
| 5 | Check for citations | All data points include source references |

**Pass/Fail Criteria**:
- [ ] EOD page accessible to Plant Manager
- [ ] Summary generated within 30 seconds
- [ ] All required sections present
- [ ] Citations included throughout

---

### Scenario 15: Morning vs Actual Comparison

**Purpose**: Verify that EOD compares morning predictions to actual outcomes.

**Prerequisites**: Morning briefing generated earlier today

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate EOD Summary | Summary with comparison section |
| 2 | Find "Morning Comparison" section | Section shows morning concerns vs outcomes |
| 3 | Review concern outcomes | Each concern labeled: Materialized, Averted, Escalated, or Unexpected |
| 4 | Check accuracy metrics | See: prediction accuracy %, false positives, misses |
| 5 | Identify unexpected issues | New issues not predicted in morning highlighted |

**Pass/Fail Criteria**:
- [ ] Comparison section present
- [ ] Morning concerns matched to outcomes
- [ ] Outcomes correctly classified
- [ ] Accuracy metrics calculated

---

### Scenario 16: EOD Without Morning Briefing

**Purpose**: Verify graceful handling when no morning briefing exists.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Ensure no morning briefing today (or use test day) | No morning briefing record |
| 2 | Generate EOD Summary | Summary generates |
| 3 | Look for comparison section | See message: "No morning briefing to compare" |
| 4 | Verify other sections present | Performance, Wins, Concerns, Outlook still shown |

**Pass/Fail Criteria**:
- [ ] No error when morning briefing missing
- [ ] Clear message about no comparison
- [ ] Other sections displayed normally

---

### Scenario 17: EOD Push Notification Reminder

**Purpose**: Verify that EOD reminder notifications work.

**Prerequisites**: Enable EOD reminders in Settings

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Preferences | Preferences page loads |
| 2 | Enable "EOD Reminder" toggle | Toggle turns on |
| 3 | Set reminder time (e.g., 5:00 PM) | Time picker accepts input |
| 4 | Save preferences | Settings saved |
| 5 | Wait for reminder time | Push notification received |
| 6 | Review notification | "Ready to review your End of Day summary?" |
| 7 | Tap/click notification | Navigates directly to EOD page |

**Pass/Fail Criteria**:
- [ ] Reminder toggle and time picker work
- [ ] Push notification received at configured time
- [ ] Notification text correct
- [ ] Click navigates to EOD page

---

### Scenario 18: EOD Reminder - Already Viewed Skip

**Purpose**: Verify that reminder is skipped if EOD already viewed.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate and view EOD summary | Summary viewed |
| 2 | Wait for reminder time | Reminder time arrives |
| 3 | Check for notification | No notification received |
| 4 | Verify in system | System notes "Already reviewed" |

**Pass/Fail Criteria**:
- [ ] No duplicate reminder after viewing
- [ ] System correctly detected prior view

---

### SECTION E: Admin - Asset Assignment

---

### Scenario 19: Viewing Asset Assignment Grid

**Purpose**: Verify that Admins can view and manage supervisor assignments.

**Prerequisites**: Log in as `testadmin@tfn.com` (Admin)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Admin > Assignments | Assignment grid page loads |
| 2 | Review grid layout | Columns: Areas/Assets, Rows: Supervisors |
| 3 | See checkbox cells | Each user-asset combination has checkbox |
| 4 | Find existing assignments | Checkboxes are checked for current assignments |
| 5 | Verify all supervisors listed | All supervisor accounts appear as rows |

**Pass/Fail Criteria**:
- [ ] Grid loaded successfully
- [ ] Supervisors displayed as rows
- [ ] Assets grouped by area as columns
- [ ] Current assignments shown as checked

---

### Scenario 20: Making Assignment Changes with Preview

**Purpose**: Verify that assignment changes show impact preview.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check a new asset checkbox for a supervisor | Checkbox becomes checked |
| 2 | Look for preview panel | Preview shows: "User will see X assets across Y areas" |
| 3 | Uncheck an existing assignment | Preview updates |
| 4 | Verify changes not saved yet | "Unsaved changes" indicator visible |
| 5 | Click "Save Changes" | Confirmation dialog appears |
| 6 | Click "Confirm" | Changes saved, success message |
| 7 | Refresh page | Changes persist |

**Pass/Fail Criteria**:
- [ ] Preview showed impact immediately
- [ ] Changes not saved until confirmed
- [ ] Confirmation dialog appeared
- [ ] Changes persisted after save

---

### Scenario 21: Setting Temporary Assignments

**Purpose**: Verify that temporary assignments with expiration work.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check a new asset for a supervisor | Assignment selected |
| 2 | Find "Set Expiration" option | Expiration date picker available |
| 3 | Set expiration to 7 days from now | Date accepted |
| 4 | Save the assignment | Assignment saved with expiration |
| 5 | View the grid | Assignment shows expiration indicator (clock icon or badge) |
| 6 | Hover over the indicator | Tooltip shows expiration date |

**Pass/Fail Criteria**:
- [ ] Expiration date picker worked
- [ ] Assignment saved with expiration
- [ ] Visual indicator for temporary assignments
- [ ] Expiration date visible on hover

---

### SECTION F: Admin - Role Management

---

### Scenario 22: Viewing User Roles

**Purpose**: Verify that Admins can view all users and their roles.

**Prerequisites**: Log in as `testadmin@tfn.com` (Admin)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Admin > Users | User management page loads |
| 2 | Review user list | See table with users and current roles |
| 3 | Verify role badges | Roles shown: Plant Manager, Supervisor, Admin |
| 4 | Find role statistics | Summary counts of each role type |

**Pass/Fail Criteria**:
- [ ] User list loaded successfully
- [ ] All roles displayed correctly
- [ ] Role badges visually distinguishable

---

### Scenario 23: Changing a User's Role

**Purpose**: Verify that role changes are saved with audit trail.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find a Supervisor user in the list | User row visible |
| 2 | Click role dropdown/edit button | Role selection appears |
| 3 | Select "Plant Manager" | New role selected |
| 4 | Confirmation dialog appears | Dialog asks to confirm change |
| 5 | Click "Confirm" | Role change saved |
| 6 | Verify role updated in list | User now shows "Plant Manager" badge |
| 7 | Navigate to Admin > Audit Logs | Find the role change entry |

**Pass/Fail Criteria**:
- [ ] Role selection worked
- [ ] Confirmation required before change
- [ ] New role displayed immediately
- [ ] Audit log entry created

---

### Scenario 24: Last Admin Protection

**Purpose**: Verify that the last Admin cannot be removed.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Identify the only Admin account | Only one admin exists |
| 2 | Try to change that Admin to Supervisor | Attempt the change |
| 3 | Read error message | "Cannot remove last admin" |
| 4 | Verify role unchanged | Admin role still assigned |

**Pass/Fail Criteria**:
- [ ] System prevented removing last admin
- [ ] Clear error message displayed
- [ ] Role remained as Admin

---

### Scenario 25: New User Default Role

**Purpose**: Verify that new users get Supervisor role by default.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Have IT create a new user account | New user created |
| 2 | Check user list in Admin > Users | New user appears |
| 3 | Verify default role | Role shows as "Supervisor" |
| 4 | Admin promotes to Plant Manager if needed | Role change requires explicit action |

**Pass/Fail Criteria**:
- [ ] New user automatically got Supervisor role
- [ ] Promotion required explicit admin action

---

### SECTION G: Admin - Audit Logging

---

### Scenario 26: Viewing Audit Logs

**Purpose**: Verify that Admins can view all configuration changes.

**Prerequisites**: Log in as `testadmin@tfn.com` (Admin)

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Admin > Audit Logs | Audit log page loads |
| 2 | Review log entries | Entries in reverse chronological order |
| 3 | See entry columns | Timestamp, Admin, Action Type, Target, Summary |
| 4 | Expand an entry | See before/after values for changes |
| 5 | Note batch indicators | Bulk operations show linked batch ID |

**Pass/Fail Criteria**:
- [ ] Audit log page loaded
- [ ] Entries sorted newest first
- [ ] All columns displayed
- [ ] Before/after values visible on expand

---

### Scenario 27: Filtering Audit Logs

**Purpose**: Verify that audit log filters work correctly.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set date range filter (last 7 days) | Results filtered to date range |
| 2 | Filter by action type "role_change" | Only role changes shown |
| 3 | Filter by target user | Only changes for that user shown |
| 4 | Click "Clear Filters" | All filters removed, full list shown |
| 5 | Verify filter state in URL | URL parameters reflect filters |

**Pass/Fail Criteria**:
- [ ] Date range filter worked
- [ ] Action type filter worked
- [ ] Target user filter worked
- [ ] Clear filters worked
- [ ] Filters shareable via URL

---

### Scenario 28: Audit Log Integrity

**Purpose**: Verify that audit logs are tamper-evident.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note the entry count for today | Count recorded |
| 2 | Make a role change | Audit entry created |
| 3 | Verify entry count increased | One new entry |
| 4 | Attempt to edit an audit entry (via any means) | Editing not possible |
| 5 | Attempt to delete an audit entry | Deletion not possible |
| 6 | Check entries from 30+ days ago | Entries still available (within 90 day retention) |

**Pass/Fail Criteria**:
- [ ] Entries are append-only
- [ ] No edit capability exists
- [ ] No delete capability exists
- [ ] 90-day retention maintained

---

## 4. Success Criteria

### Must Pass (Critical) - Epic Acceptance Criteria

All of the following must work for Epic 9 to be accepted:

| # | Criterion | Requirement Ref | Verified |
|---|-----------|-----------------|----------|
| 1 | Outgoing supervisors can trigger handoff and add voice notes | FR21, FR23 | ☐ |
| 2 | Handoff records persist and are viewable by incoming supervisor | FR24, FR25 | ☐ |
| 3 | Incoming supervisors can ask follow-up questions with cited answers | FR26, FR52 | ☐ |
| 4 | Acknowledgment creates audit trail; outgoing supervisor notified | FR27, FR28, FR55 | ☐ |
| 5 | Handoffs cached locally for offline review | NFR20 | ☐ |
| 6 | Acknowledgment syncs automatically when connectivity restored | NFR21 | ☐ |
| 7 | EOD summary compares morning briefing to actual outcomes | FR32, FR33 | ☐ |
| 8 | Push notification reminders delivered within 60 seconds | FR34 | ☐ |
| 9 | Admins can assign supervisors to assets with preview | FR46, FR48 | ☐ |
| 10 | All admin changes logged with audit trail | FR56 | ☐ |
| 11 | 99.9% uptime during shift change windows (5-7 AM, 5-7 PM) | NFR19 | ☐ |
| 12 | Audit logs retained for 90 days minimum | NFR25 | ☐ |

### Should Pass (Important)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Voice note transcription completes within 3 seconds | ☐ |
| 2 | Handoff summary generates within 15 seconds | ☐ |
| 3 | Voice note limit enforced (5 max, 60 seconds each) | ☐ |
| 4 | Temporary assignments show expiration indicator | ☐ |
| 5 | Last admin protection prevents role removal | ☐ |
| 6 | New users default to Supervisor role | ☐ |
| 7 | Audit log filters work correctly | ☐ |
| 8 | Before/after values captured for all changes | ☐ |

### Nice to Have (Enhancements)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Q&A real-time updates when both supervisors online | ☐ |
| 2 | Stale cache warning after 48 hours | ☐ |
| 3 | Prediction accuracy trends over time | ☐ |
| 4 | Batch operations linked by batch ID in audit | ☐ |

---

## 5. Known Limitations

Please be aware of the following during testing:

1. **Voice Notes**: Recording requires microphone permissions. If denied, text notes are the fallback.

2. **Offline Mode**: Q&A and new handoff creation require internet. Only viewing and acknowledgment work offline.

3. **Push Notifications**: Requires browser notification permissions. Safari may have limitations on iOS.

4. **EOD Comparison**: Requires a morning briefing from the same day. Without one, comparison section is skipped.

5. **Real-time Notifications**: Outgoing supervisor must have app open to receive instant in-app notifications.

6. **Audit Log Filters**: URL-based filters may not work in incognito mode due to session handling.

7. **First Load**: Initial page loads may be slower as Service Worker caches resources.

---

## 6. Issue Reporting

If you encounter problems during testing:

1. **Note the exact steps** that led to the issue
2. **Capture a screenshot** if possible
3. **Note the browser and device** you're using
4. **Note online/offline status** when the issue occurred
5. **Report to**: [IT Support / Development Team Contact]

**Report Format**:
```
Scenario: [Which test scenario]
Step: [Which step number]
Expected: [What should have happened]
Actual: [What actually happened]
Device/Browser: [e.g., iPad Safari 16]
Online/Offline: [Online / Offline]
Screenshot: [Attached if available]
```

---

## 7. Sign-Off Section

### UAT Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Plant Manager Representative | _______________ | ___ / ___ / 2026 | _______________ |
| Supervisor Representative (Outgoing) | _______________ | ___ / ___ / 2026 | _______________ |
| Supervisor Representative (Incoming) | _______________ | ___ / ___ / 2026 | _______________ |
| Administrator Representative | _______________ | ___ / ___ / 2026 | _______________ |
| QA Lead | _______________ | ___ / ___ / 2026 | _______________ |
| Product Owner | _______________ | ___ / ___ / 2026 | _______________ |

### Approval Decision

☐ **APPROVED** - All critical criteria pass. Epic 9 is ready for production.

☐ **CONDITIONALLY APPROVED** - Minor issues exist but do not block deployment. Issues documented below.

☐ **NOT APPROVED** - Critical issues must be resolved before deployment. Issues documented below.

### Issues Requiring Resolution (if any)

| Issue # | Description | Severity | Status | Resolution Required By |
|---------|-------------|----------|--------|----------------------|
| | | | | |
| | | | | |
| | | | | |

*Severity Levels: Critical / High / Medium / Low*
*Status: Open / In Progress / Resolved / Deferred*

### Test Summary

| Category | Total Tests | Passed | Failed | Blocked |
|----------|-------------|--------|--------|---------|
| **Section A: Handoff Creation** (Scenarios 1-5) | 5 | | | |
| **Section B: Handoff Review** (Scenarios 6-10) | 5 | | | |
| **Section C: Offline Capabilities** (Scenarios 11-13) | 3 | | | |
| **Section D: EOD Summary** (Scenarios 14-18) | 5 | | | |
| **Section E: Admin Asset Assignment** (Scenarios 19-21) | 3 | | | |
| **Section F: Admin Role Management** (Scenarios 22-25) | 4 | | | |
| **Section G: Admin Audit Logging** (Scenarios 26-28) | 3 | | | |
| **TOTAL** | **28** | | | |

### Additional Notes

_Space for any additional comments from testers or stakeholders._

```
Observations, concerns, or feedback:




```

---

### Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 18, 2026 | QA Specialist | Initial UAT document creation |

---

**Document Prepared By**: QA Specialist
**Date**: January 18, 2026
**Epic Reference**: Epic 9 - Shift Handoff & EOD Summary

---

*End of UAT Document - Epic 9: Shift Handoff & EOD Summary*
