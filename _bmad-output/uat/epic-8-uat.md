# User Acceptance Testing Document
# Epic 8: Voice Briefing Foundation

**Version:** 1.0
**Date:** January 17, 2026
**Prepared For:** Plant Managers and Supervisors
**Test Environment:** TFN AI Hub - Voice Briefing System

---

## 1. Overview

### What Was Built

Epic 8 introduces a **hands-free voice briefing system** for the TFN AI Hub. This feature allows you to receive your morning production updates through spoken audio instead of reading dashboards. Key capabilities include:

- **Morning Voice Briefings**: Start your day with a spoken summary of overnight production across all plant areas
- **Push-to-Talk Questions**: Ask follow-up questions using your voice during briefings
- **Personalized Content**: Supervisors see only their assigned assets; Plant Managers see the full plant
- **Customizable Preferences**: Choose your preferred area order, detail level, and voice settings
- **Natural Number Reading**: Numbers are spoken naturally (e.g., "about 2 million units" instead of "2,130,500 units")

### Who This Is For

- **Plant Managers**: Receive complete plant-wide briefings covering all 7 production areas
- **Supervisors**: Receive focused briefings on only your assigned assets

### What You Can Do

1. Trigger a morning briefing with one button press
2. Listen to production updates while walking to your station
3. Ask questions about any area using your voice
4. Pause, skip, or end the briefing at any time
5. Set your preferences during first-time onboarding
6. Modify your preferences later through Settings

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

## 4. Success Criteria

### Must Pass (Critical)

All of the following must work for Epic 8 to be accepted:

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Plant Managers can start and receive full plant briefings | ☐ |
| 2 | Supervisors receive briefings with only their assigned assets | ☐ |
| 3 | Voice playback begins within 2 seconds of briefing generation | ☐ |
| 4 | Briefing generation completes within 30 seconds | ☐ |
| 5 | Push-to-talk transcription completes within 2 seconds | ☐ |
| 6 | Numbers are formatted naturally for voice (millions, percentages) | ☐ |
| 7 | Users can pause, skip, and end briefings | ☐ |
| 8 | First-time onboarding appears and can be completed | ☐ |
| 9 | Preferences persist after logout/login | ☐ |
| 10 | System falls back to text-only if voice is disabled/unavailable | ☐ |

### Should Pass (Important)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Q&A responses include citations to data sources | ☐ |
| 2 | Silence detection auto-continues after 3-4 seconds | ☐ |
| 3 | Onboarding completes in under 2 minutes | ☐ |
| 4 | Progress stepper accurately reflects briefing status | ☐ |
| 5 | Keyboard shortcuts work (Space for pause, Arrow for skip) | ☐ |

### Nice to Have (Enhancements)

| # | Criterion | Verified |
|---|-----------|----------|
| 1 | Transcript auto-scrolls to current content | ☐ |
| 2 | Visual audio level indicator during recording | ☐ |
| 3 | Countdown timer visible during silence detection | ☐ |

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

### Additional Notes

_Space for any additional comments from testers or stakeholders._

---

**Document Prepared By**: QA Specialist
**Date**: January 17, 2026
**Epic Reference**: Epic 8 - Voice Briefing Foundation
