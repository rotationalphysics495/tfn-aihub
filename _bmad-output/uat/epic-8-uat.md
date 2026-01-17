# User Acceptance Testing Document
# Epic 8: Voice Briefing Foundation

**Version:** 1.1
**Date:** January 17, 2026
**Last Updated:** January 17, 2026
**Prepared For:** Plant Managers and Supervisors
**Test Environment:** TFN AI Hub - Voice Briefing System
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

Epic 8 introduces a **hands-free voice briefing system** for the TFN AI Hub. This feature transforms the traditional 45-minute morning dashboard review into a 3-minute spoken briefing. You can receive production updates through natural-sounding audio while walking to your office, pouring coffee, or preparing for the day.

| Feature | What It Does | User Benefit |
|---------|--------------|--------------|
| **Voice Briefings** | Receive spoken updates via ElevenLabs TTS technology | Hands-free operation, multitask while staying informed |
| **Morning Workflow** | Comprehensive overview of all 7 production areas | Quick plant-wide situational awareness |
| **Push-to-Talk** | Ask follow-up questions by voice during briefings | Natural interaction without touching your device |
| **Smart Number Formatting** | "About 2.1 million units" instead of "2,130,500 units" | Easier to understand spoken metrics |
| **Progress Tracking UI** | Visual display of current area, upcoming areas, and completion | Always know where you are in the briefing |
| **Supervisor Scoping** | Briefings limited to assigned assets only | Focused information relevant to your role |
| **User Preferences** | Customize area order, detail level, and voice on/off | Personalized experience tailored to your needs |
| **Onboarding Flow** | 2-minute setup for first-time users | Quick personalization from first interaction |
| **Mem0 AI Context** | Preferences sync to AI memory for smarter responses | AI understands your preferences and priorities |

### Who This Is For

- **Plant Managers**: Receive complete plant-wide briefings covering all 7 production areas:
  - Packing (CAMA, Pack Cells, Variety Pack, Bag Lines, Nuspark)
  - Rychigers (101-109, 1009)
  - Grinding (Grinders 1-5)
  - Powder (1002-1004 Fill & Pack, Manual Bulk)
  - Roasting (Roasters 1-4)
  - Green Bean (Manual, Silo Transfer)
  - Flavor Room (Coffee Flavor Room)

- **Supervisors**: Receive focused briefings on only your assigned assets

### What You Can Do

1. Trigger a morning briefing with one button press
2. Listen to production updates while walking to your station
3. Ask questions about any area using your voice
4. Pause, skip, or end the briefing at any time
5. Set your preferences during first-time onboarding (under 2 minutes)
6. Modify your preferences later through Settings > Preferences
7. Fall back to text-only mode when voice is unavailable

---

## 2. Prerequisites

### Test Environment Access

| Item | Requirement |
|------|-------------|
| Device | Tablet (iPad recommended) or Desktop computer |
| Browser | Chrome, Firefox, Safari 14.1+, or Edge (latest version) |
| Audio | Speakers or headphones required for voice playback |
| Microphone | Required for push-to-talk questions |
| Network | Stable internet connection |

### Test Accounts

Request test accounts from your IT administrator:

| Role | Account Type | What You'll See |
|------|--------------|-----------------|
| Plant Manager | `testpm@tfn.com` | All 7 production areas |
| Supervisor | `testsup@tfn.com` | Only assigned assets (3 assets in Grinding, Packing) |

### Before You Begin

1. **Clear your browser cache** to ensure you see the onboarding flow
2. **Allow microphone access** when prompted by your browser
3. **Ensure audio is unmuted** on your device
4. **Find a reasonably quiet location** for voice interactions

---

## 3. Test Scenarios

### Scenario 1: First-Time User Onboarding

**Purpose**: Verify that new users are guided through preference setup before using the system.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in with a test account that has never used the system | Onboarding overlay appears over the main screen |
| 2 | Read the Welcome screen | See message explaining the setup process and estimated time (under 2 minutes) |
| 3 | Click "Get Started" | Proceed to Role selection screen |
| 4 | Select "Plant Manager" | Role is highlighted, Continue button becomes active |
| 5 | Click "Continue" | Proceed to Area Order preference screen |
| 6 | Drag "Grinding" to the top of the list | Area list reorders to show Grinding first |
| 7 | Click "Continue" | Proceed to Detail Level screen |
| 8 | Select "Summary" | Summary option is highlighted |
| 9 | Click "Continue" | Proceed to Voice preference screen |
| 10 | Toggle Voice to "On" | Voice toggle shows as enabled |
| 11 | Click "Continue" | See Confirmation screen with your selections summarized |
| 12 | Click "Finish Setup" | Onboarding closes, you see the main dashboard |

**Pass/Fail Criteria**:
- [ ] Onboarding appeared on first login
- [ ] All 7 steps completed successfully
- [ ] Took less than 2 minutes to complete
- [ ] Preferences were saved (verify in Settings later)

---

### Scenario 2: Supervisor Onboarding (Different Flow)

**Purpose**: Verify that Supervisors see their assigned assets during onboarding.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in with the Supervisor test account | Onboarding overlay appears |
| 2 | Click through to Role selection | See Plant Manager and Supervisor options |
| 3 | Select "Supervisor" | Supervisor role is highlighted |
| 4 | Click "Continue" | See "Your Assigned Assets" screen |
| 5 | Review the asset list | See only your pre-assigned assets (read-only list) |
| 6 | Click "Continue" | Proceed to Area Order (only showing your areas) |
| 7 | Complete remaining steps | Finish onboarding successfully |

**Pass/Fail Criteria**:
- [ ] Supervisor saw the "Assigned Assets" step
- [ ] Asset list matched administrator-configured assignments
- [ ] Only relevant areas appeared in Area Order step

---

### Scenario 3: Starting a Morning Briefing (Plant Manager)

**Purpose**: Verify that Plant Managers can trigger and receive a full plant briefing.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Briefing page (click "Briefing" in navigation) | See the Briefing Launcher with "Start Morning Briefing" button |
| 2 | Click "Start Morning Briefing" | Loading indicator appears, briefing generates |
| 3 | Wait for briefing to load | Briefing starts within 30 seconds |
| 4 | Listen to the first area | Voice begins speaking the first area summary |
| 5 | Watch the progress stepper on the left | Current area is highlighted, others are dimmed or checked |
| 6 | Read along with the transcript | Text appears on screen matching spoken content |
| 7 | Wait for first area to complete | System asks "Any questions on [Area] before I continue?" |
| 8 | Wait 3-4 seconds without speaking | Countdown timer shows, then next area begins automatically |

**Pass/Fail Criteria**:
- [ ] Briefing generated within 30 seconds
- [ ] Voice playback started within 2 seconds
- [ ] All 7 areas were covered in your preferred order
- [ ] Progress stepper accurately showed completion
- [ ] Auto-continue worked after silence

---

### Scenario 4: Starting a Morning Briefing (Supervisor)

**Purpose**: Verify that Supervisors receive scoped briefings covering only their assigned assets.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in as Supervisor test account | Dashboard appears |
| 2 | Navigate to Briefing page | See the Briefing Launcher |
| 3 | Click "Start Morning Briefing" | Briefing generates |
| 4 | Listen to briefing content | Only your assigned assets are covered |
| 5 | Verify no plant-wide headline | Briefing starts directly with your first area |
| 6 | Count the areas covered | Only 2 areas (matching your 3 assigned assets across Grinding and Packing) |

**Pass/Fail Criteria**:
- [ ] Only assigned assets appeared in briefing
- [ ] No plant-wide overview was included
- [ ] Fewer areas than the full 7 were covered
- [ ] Content was relevant to Supervisor role

---

### Scenario 5: Asking Follow-Up Questions (Push-to-Talk)

**Purpose**: Verify that users can ask voice questions during briefing pauses.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a morning briefing | Briefing begins playing |
| 2 | Wait for a section to complete | System pauses and asks for questions |
| 3 | Press and hold the Push-to-Talk button | Microphone icon pulses, recording indicator appears |
| 4 | Speak: "What was the OEE for Grinding yesterday?" | Your words are captured |
| 5 | Release the button | Transcription appears in the transcript panel |
| 6 | Wait for response | Answer appears as text AND is spoken aloud |
| 7 | Verify citation | Response includes a source reference (e.g., "[Source: daily_summaries]") |
| 8 | Listen for follow-up prompt | System asks "Anything else on [Area]?" |

**Pass/Fail Criteria**:
- [ ] Push-to-talk recording worked (visual indicator appeared)
- [ ] Transcription completed within 2 seconds
- [ ] Answer was accurate and included citations
- [ ] Response was both spoken and displayed as text
- [ ] System allowed additional questions

---

### Scenario 6: Briefing Controls (Pause, Skip, End)

**Purpose**: Verify that playback controls function correctly.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a morning briefing | Briefing begins playing |
| 2 | Click the "Pause" button | Audio stops, button changes to "Resume" |
| 3 | Click "Resume" | Audio continues from where it stopped |
| 4 | Click "Skip to Next" | Current section ends immediately, next section begins |
| 5 | Click "End Briefing" | Confirmation dialog appears |
| 6 | Click "Confirm" in the dialog | Briefing stops, you return to Briefing launcher page |

**Pass/Fail Criteria**:
- [ ] Pause stopped playback immediately
- [ ] Resume continued from the correct position
- [ ] Skip moved to the next area
- [ ] End Briefing required confirmation
- [ ] Navigation returned to the launcher page

---

### Scenario 7: Voice Number Formatting

**Purpose**: Verify that numbers are spoken naturally in briefings.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a morning briefing | Briefing begins playing |
| 2 | Listen for a large production number | Hear "about 2.1 million units" (not "two million one hundred thirty thousand five hundred units") |
| 3 | Listen for a percentage | Hear "87 percent" (not "87.3 percent") |
| 4 | Listen for a time duration | Hear "about 3 days" or "about 72 hours" (not "4,320 minutes") |
| 5 | Listen for a small count | Hear exact number like "5 units" (small numbers stay precise) |

**Pass/Fail Criteria**:
- [ ] Large numbers were rounded and spoken naturally
- [ ] Percentages were rounded to whole numbers
- [ ] Durations were converted to sensible units
- [ ] Small numbers remained precise

---

### Scenario 8: Graceful Degradation (Text-Only Mode)

**Purpose**: Verify that the system works when voice is unavailable.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Preferences | Preferences page loads |
| 2 | Toggle Voice to "Off" | Voice setting is disabled |
| 3 | Save preferences | Confirmation message appears |
| 4 | Start a morning briefing | Briefing generates |
| 5 | Observe the briefing | Text appears but no audio plays |
| 6 | Verify controls work | Skip, Pause (N/A), and End still function |

**Pass/Fail Criteria**:
- [ ] Briefing displayed text without errors
- [ ] No audio playback occurred
- [ ] Navigation and controls still worked
- [ ] No error messages were shown

---

### Scenario 9: Modifying Preferences After Onboarding

**Purpose**: Verify that users can change their preferences at any time.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Preferences | Preferences page loads with current settings |
| 2 | Change area order (move Roasting to first) | Area list reorders |
| 3 | Change detail level to "Detailed" | Detailed option is selected |
| 4 | Toggle Voice setting | Setting changes state |
| 5 | Click "Save Changes" | Success message appears |
| 6 | Start a new morning briefing | Briefing uses your new preferences |

**Pass/Fail Criteria**:
- [ ] All current preferences were displayed on load
- [ ] All changes were applied successfully
- [ ] New briefing reflected the updated area order
- [ ] Detail level matched selection

---

### Scenario 10: Onboarding Abandonment and Re-trigger

**Purpose**: Verify that abandoning onboarding applies defaults and re-triggers later.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in with a fresh test account | Onboarding appears |
| 2 | Click the "X" or navigate away during onboarding | Onboarding closes |
| 3 | Attempt to use the system normally | System works with default settings |
| 4 | Log out and log back in | Onboarding appears again |

**Pass/Fail Criteria**:
- [ ] Abandonment did not cause errors
- [ ] Default preferences were applied (Plant Manager, Summary, Voice On)
- [ ] Onboarding triggered again on next login

---

### Scenario 11: No Speech Detection Handling

**Purpose**: Verify that the system handles accidental or empty recordings gracefully.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a briefing and wait for a pause | System waits for input |
| 2 | Press and release Push-to-Talk very quickly (< 0.5 seconds) | No transcription occurs (filtered) |
| 3 | Press Push-to-Talk, stay silent, then release | See "No speech detected" message |
| 4 | Press Push-to-Talk and speak normally | Normal transcription occurs |

**Pass/Fail Criteria**:
- [ ] Very short recordings were ignored (no error)
- [ ] Silent recordings showed appropriate message
- [ ] Normal speech was transcribed correctly
- [ ] User could retry immediately after either case

---

### Scenario 12: Supervisor with No Assigned Assets

**Purpose**: Verify appropriate handling when a Supervisor has no assets configured.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in as a Supervisor with no asset assignments | Dashboard appears |
| 2 | Navigate to Briefing page | Briefing Launcher appears |
| 3 | Click "Start Morning Briefing" | Message appears: "No assets assigned - contact your administrator" |
| 4 | Verify no briefing generates | No briefing content is displayed |

**Pass/Fail Criteria**:
- [ ] Clear error message was displayed
- [ ] System did not crash or show technical errors
- [ ] User understood they need administrator help

---

### Scenario 13: Performance Requirements Verification

**Purpose**: Verify that system meets all performance requirements (NFR7-NFR10).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a Morning Briefing and time it | Briefing generation completes within 30 seconds (NFR8) |
| 2 | Wait for voice to start after generation | Audio playback begins within 2 seconds (NFR9) |
| 3 | Use Push-to-Talk to ask a question | Transcription completes within 2 seconds (NFR10) |
| 4 | Wait for Q&A response | Response delivered within 2 seconds (NFR7) |
| 5 | Repeat the above 3 times | Consistent performance across attempts |

**Performance Tracking Table**:

| Metric | Target | Attempt 1 | Attempt 2 | Attempt 3 |
|--------|--------|-----------|-----------|-----------|
| Briefing generation | < 30 sec | | | |
| Voice playback start | < 2 sec | | | |
| STT transcription | < 2 sec | | | |
| Q&A response | < 2 sec | | | |

**Pass/Fail Criteria**:
- [ ] Briefing generation under 30 seconds (all attempts)
- [ ] Voice playback started within 2 seconds (all attempts)
- [ ] Transcription completed within 2 seconds (all attempts)
- [ ] Q&A responses delivered within 2 seconds (all attempts)

---

### Scenario 14: AI Preference Context (Mem0 Integration)

**Purpose**: Verify that user preferences are reflected in AI responses.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set area order to put "Grinding" first in Settings | Preferences saved successfully |
| 2 | Start a new Morning Briefing | Grinding area is presented first |
| 3 | During briefing, ask: "Why did you start with Grinding?" | AI acknowledges your preference |
| 4 | Ask: "What are my current preferences?" | AI can describe your settings |

**Pass/Fail Criteria**:
- [ ] Briefing reflected area order preference
- [ ] AI response acknowledged user preference
- [ ] AI demonstrated awareness of user settings

---

### Scenario 15: Briefing Content Quality (Synthesis Engine)

**Purpose**: Verify that briefings contain meaningful, synthesized insights rather than raw data.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start a Morning Briefing | Briefing generates and plays |
| 2 | Listen/read for a Headline Summary | Brief overview of overall plant status |
| 3 | Listen/read for "Top Wins" section | Areas performing above target are highlighted |
| 4 | Listen/read for "Top Concerns" section | Issues, gaps, and downtime are identified |
| 5 | Listen/read for Recommended Actions | Actionable items with supporting evidence |
| 6 | Check for citations | Data sources are referenced (e.g., "[Source: daily_summaries]") |

**Pass/Fail Criteria**:
- [ ] Briefing included a headline summary
- [ ] Top wins (>100% target) were identified
- [ ] Top concerns (gaps, issues) were called out
- [ ] Recommended actions were provided
- [ ] All metrics included citations to data sources
- [ ] Content was synthesized (narrative), not just raw numbers

---

## 4. Success Criteria

### Must Pass (Critical) - Epic Acceptance Criteria

All of the following must work for Epic 8 to be accepted. These map directly to the Epic's acceptance criteria:

| # | Criterion | NFR/FR | Verified |
|---|-----------|--------|----------|
| 1 | ElevenLabs TTS begins playback within 2 seconds | NFR9 | ☐ |
| 2 | Push-to-talk transcription completes within 2 seconds | NFR10 | ☐ |
| 3 | Briefing generation completes within 30 seconds | NFR8 | ☐ |
| 4 | Plant Managers see all 7 production areas | FR14-FR17 | ☐ |
| 5 | Supervisors see only their assigned assets | FR15 | ☐ |
| 6 | Numbers formatted for voice (e.g., "2.1 million" not "2,130,500") | FR19 | ☐ |
| 7 | Users can pause and ask follow-up questions with cited answers | FR20 | ☐ |
| 8 | Onboarding completes in under 2 minutes | FR43 | ☐ |
| 9 | Preferences persist across sessions via Supabase + Mem0 | FR40 | ☐ |
| 10 | Voice gracefully degrades to text-only if ElevenLabs unavailable | NFR22 | ☐ |
| 11 | Q&A interactions complete within 2 seconds | NFR7 | ☐ |

### Should Pass (Important)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Q&A responses include citations to data sources (FR20) | ☐ |
| 2 | Silence detection auto-continues after 3-4 seconds (FR12) | ☐ |
| 3 | Areas delivered in user's preferred order (FR36) | ☐ |
| 4 | Detail level matches user's preference (FR37) | ☐ |
| 5 | Progress stepper accurately reflects briefing status | ☐ |
| 6 | Keyboard shortcuts work (Space for pause, Arrow for skip) | ☐ |
| 7 | Preferences sync to Mem0 within 5 seconds for AI context | ☐ |
| 8 | Briefing content includes synthesized insights, not raw data | ☐ |

### Nice to Have (Enhancements)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Transcript auto-scrolls to current content | ☐ |
| 2 | Visual audio level indicator during recording | ☐ |
| 3 | Countdown timer visible during silence detection | ☐ |
| 4 | AI can describe user's current preferences when asked | ☐ |

---

## 5. Known Limitations

Please be aware of the following during testing:

1. **Network Dependency**: Voice features require internet connectivity. If connection is lost, text mode activates.

2. **Browser Microphone Permissions**: You must allow microphone access when prompted. If denied, push-to-talk will not work.

3. **Quiet Environment**: Background noise may affect voice recognition accuracy.

4. **Safari on iOS**: Some older iOS versions may have limited Web Audio API support.

5. **First Briefing Load**: The first briefing of the day may take slightly longer as data is retrieved.

---

## 6. Issue Reporting

If you encounter problems during testing:

1. **Note the exact steps** that led to the issue
2. **Capture a screenshot** if possible
3. **Note the browser and device** you're using
4. **Check the console** (if comfortable) for any error messages
5. **Report to**: [IT Support / Development Team Contact]

**Report Format**:
```
Scenario: [Which test scenario]
Step: [Which step number]
Expected: [What should have happened]
Actual: [What actually happened]
Device/Browser: [e.g., iPad Safari 16]
Screenshot: [Attached if available]
```

---

## 7. Sign-Off Section

### UAT Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Plant Manager Representative | _______________ | ___ / ___ / 2026 | _______________ |
| Supervisor Representative | _______________ | ___ / ___ / 2026 | _______________ |
| QA Lead | _______________ | ___ / ___ / 2026 | _______________ |
| Product Owner | _______________ | ___ / ___ / 2026 | _______________ |

### Approval Decision

☐ **APPROVED** - All critical criteria pass. Epic 8 is ready for production.

☐ **CONDITIONALLY APPROVED** - Minor issues exist but do not block deployment. Issues documented below.

☐ **NOT APPROVED** - Critical issues must be resolved before deployment. Issues documented below.

### Issues Requiring Resolution (if any)

| Issue # | Description | Severity | Resolution Required By |
|---------|-------------|----------|----------------------|
| | | | |
| | | | |
| | | | |

*Severity Levels: Critical / High / Medium / Low*
*Status: Open / In Progress / Resolved / Deferred*

### Test Summary

| Category | Total Tests | Passed | Failed | Blocked |
|----------|-------------|--------|--------|---------|
| Onboarding (Scenarios 1-2) | 2 | | | |
| Morning Briefing (Scenarios 3-4) | 2 | | | |
| Push-to-Talk & Q&A (Scenario 5) | 1 | | | |
| Briefing Controls (Scenario 6) | 1 | | | |
| Voice Number Formatting (Scenario 7) | 1 | | | |
| Graceful Degradation (Scenario 8) | 1 | | | |
| Preferences Management (Scenario 9) | 1 | | | |
| Edge Cases (Scenarios 10-12) | 3 | | | |
| Performance (Scenario 13) | 1 | | | |
| AI Context (Scenario 14) | 1 | | | |
| Content Quality (Scenario 15) | 1 | | | |
| **TOTAL** | **15** | | | |

### Additional Notes

_Space for any additional comments from testers or stakeholders._

```
Observations, concerns, or feedback:




```

---

### Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 17, 2026 | QA Specialist | Initial UAT document creation |
| 1.1 | January 17, 2026 | QA Specialist | Enhanced coverage, added test summary table |

---

**Document Prepared By**: QA Specialist
**Date**: January 17, 2026
**Epic Reference**: Epic 8 - Voice Briefing Foundation

---

*End of UAT Document - Epic 8: Voice Briefing Foundation*
