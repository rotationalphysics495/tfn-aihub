# User Acceptance Testing (UAT) Document

## Epic 1: Project Foundation & Infrastructure

**Version:** 1.0
**Date:** January 6, 2026
**Prepared For:** Plant Managers, Line Supervisors, QA Team
**Status:** Ready for Testing

---

## 1. Overview

### What Was Built

Epic 1 establishes the foundation for the Manufacturing Performance Assistant - your new "Command Center" for monitoring factory floor operations. This phase focused on setting up the core infrastructure that all future features will build upon.

**In plain terms, we built:**

1. **A Secure Login System** - You can now log in with your email and password. Your session stays active as you work and logs you out securely when you're done.

2. **The Command Center Dashboard** - A home base screen with three main areas:
   - **Daily Action List** (placeholder - coming in Epic 3)
   - **Live Pulse** for real-time monitoring (placeholder - coming in Epic 2)
   - **Financial Intelligence** widgets (placeholder - coming in Epic 2)

3. **A High-Visibility Design System** - All screens use large text and high-contrast colors so you can read them from 3 feet away on factory floor tablets.

4. **Database Infrastructure** - Behind the scenes, we created the data storage systems needed to track assets, cost centers, shift targets, and analytical data.

5. **Manufacturing Database Connection** - A secure, read-only connection to your existing manufacturing data system.

---

## 2. Prerequisites

### Test Environment

| Item | Details |
|------|---------|
| **Application URL** | Contact your IT administrator for the test environment URL |
| **Supported Browsers** | Chrome (recommended), Firefox, Safari, Edge |
| **Supported Devices** | Desktop computer, tablet (iPad/Android), mobile phone |
| **Recommended Screen** | Tablet or larger for best experience |

### Test Accounts

You will need a test account to perform these tests. Contact your IT administrator to obtain:

- Test email address
- Test password

**Note:** Do NOT use production credentials for testing.

### Before You Begin

1. Ensure you have a stable internet connection
2. Clear your browser cache (optional but recommended)
3. Have the test account credentials ready
4. Have this document available for reference (printed or on a second screen)

---

## 3. Test Scenarios

### Scenario 1: User Login

**Objective:** Verify that users can log in to the application securely.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Open your web browser and navigate to the application URL | Login page displays with email and password fields |
| 1.2 | Leave both fields empty and click "Sign In" | Error message appears indicating fields are required |
| 1.3 | Enter an invalid email (e.g., "notanemail") and any password, then click "Sign In" | Error message appears about invalid email format |
| 1.4 | Enter your valid test email but an incorrect password, then click "Sign In" | Error message appears: "Invalid login credentials" or similar |
| 1.5 | Enter your valid test email and correct password, then click "Sign In" | You are redirected to the Command Center dashboard |

**Pass Criteria:** All steps complete as described. You are now logged in.

---

### Scenario 2: Session Persistence

**Objective:** Verify that your login session remains active across page refreshes.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | While logged in, press F5 (or Refresh button) to reload the page | Dashboard reloads and you remain logged in |
| 2.2 | Close the browser tab (not the entire browser) | Tab closes |
| 2.3 | Open a new tab and navigate to the application URL | You are either still logged in OR redirected to login (both are acceptable depending on browser settings) |
| 2.4 | If logged out, log in again using your credentials | Successfully logged in to Command Center |

**Pass Criteria:** Page refresh keeps you logged in. New tabs may require re-login depending on security settings.

---

### Scenario 3: User Logout

**Objective:** Verify that users can log out and their session is properly terminated.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | While on the Command Center dashboard, locate the "Sign Out" or "Logout" button | Button is visible (typically in the header or user menu) |
| 3.2 | Click the logout button | You are redirected to the login page |
| 3.3 | Click the browser's back button | You should NOT be able to access the dashboard; you are redirected to login |
| 3.4 | Navigate directly to the dashboard URL | You are redirected to the login page |

**Pass Criteria:** Logout completely ends your session. You cannot access protected pages after logging out.

---

### Scenario 4: Command Center Dashboard Layout

**Objective:** Verify the Command Center displays all required sections correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Log in and view the Command Center dashboard | Page displays with title "Command Center" visible in header |
| 4.2 | Identify the "Daily Action List" section | Section displays with heading "Daily Action List" and shows placeholder text "Coming in Epic 3" |
| 4.3 | Identify the "Live Pulse" section | Section displays with heading "Live Pulse" and shows placeholder text "Coming in Epic 2"; may have a pulsing or animated indicator |
| 4.4 | Identify the "Financial Intelligence" section | Section displays with heading "Financial Intelligence" and shows placeholder text "Coming in Epic 2" |
| 4.5 | Observe the overall layout | All three sections are clearly visible and separated from each other |

**Pass Criteria:** All three sections are present with correct headings and placeholder messages.

---

### Scenario 5: Responsive Design (Tablet View)

**Objective:** Verify the dashboard adapts correctly to tablet-sized screens.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | If using a computer, resize your browser window to approximately 768px wide (tablet width) | Layout adjusts to show sections stacked or in 2 columns |
| 5.2 | If using a tablet, rotate between portrait and landscape orientations | Layout adapts appropriately to each orientation |
| 5.3 | Check text readability | All text remains readable; no text is cut off or overlapping |
| 5.4 | Check button usability | All buttons are easily tappable; not too small |

**Pass Criteria:** Dashboard remains usable and readable on tablet-sized screens.

---

### Scenario 6: Factory Floor Visibility

**Objective:** Verify the interface meets "Industrial Clarity" standards for factory floor use.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | View the dashboard on a tablet or large monitor | Display is visible |
| 6.2 | Step back approximately 3 feet from the screen | Section headings remain clearly readable |
| 6.3 | Observe the color contrast | Text stands out clearly against backgrounds; no strain to read |
| 6.4 | Look for any use of bright red color | **IMPORTANT:** Red should NOT appear anywhere on this dashboard (red is reserved for safety incidents only, which are not yet implemented) |

**Pass Criteria:** Content is readable from 3 feet away. No bright red colors are visible.

---

### Scenario 7: Dark Mode Support (if available)

**Objective:** Verify the application supports different lighting conditions.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Look for a theme toggle button (sun/moon icon) in the header or settings | Toggle button is visible (if implemented) |
| 7.2 | Click the toggle to switch modes | Colors invert appropriately (dark background for dark mode, light background for light mode) |
| 7.3 | Verify text remains readable in both modes | High contrast is maintained in both modes |
| 7.4 | Switch back to your preferred mode | Toggle works in both directions |

**Pass Criteria:** Both light and dark modes are readable with good contrast. If toggle is not visible, this test is not applicable for this epic.

---

### Scenario 8: Health Check Verification

**Objective:** Verify the system health status endpoint is accessible.

**Automated Verification:**
```bash
npm run test:run --prefix apps/web -- --reporter=verbose src/app/api/health/route.test.ts
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | In a new browser tab, navigate to: {YOUR-APP-URL}/api/health | A response appears (may show as JSON text) |
| 8.2 | Look for status information | Response includes "status": "healthy" or similar positive indicator |
| 8.3 | If database status is shown, note it | Database status shows "healthy", "not configured", or connection information |

**Pass Criteria:** Health endpoint responds and shows system is operational.

---

### Scenario 9: Error Handling

**Objective:** Verify the application handles errors gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | While logged out, try to navigate directly to `/dashboard` | You are redirected to the login page (not an error screen) |
| 9.2 | On the login page, rapidly click "Sign In" multiple times with incorrect credentials | The system handles this gracefully; may show rate limiting message or simply continue showing error |
| 9.3 | Navigate to a non-existent page (e.g., `/nonexistent-page`) | A friendly "Page Not Found" or 404 error displays (not a technical error) |

**Pass Criteria:** Errors are handled gracefully without exposing technical details or crashing.

---

## 4. Success Criteria Checklist

### Authentication & Security

- [ ] Users can log in with valid credentials
- [ ] Invalid login attempts show appropriate error messages
- [ ] User sessions persist across page refreshes
- [ ] Users can log out successfully
- [ ] Logged-out users cannot access the dashboard
- [ ] No sensitive information (passwords, tokens) visible in the interface

### User Interface

- [ ] Command Center dashboard loads successfully
- [ ] "Daily Action List" section is visible with placeholder
- [ ] "Live Pulse" section is visible with placeholder
- [ ] "Financial Intelligence" section is visible with placeholder
- [ ] Page title shows "Command Center"
- [ ] Layout is responsive on different screen sizes
- [ ] Text is readable from 3 feet away on tablet
- [ ] No red color is used in the current interface

### System Health

- [ ] Health check endpoint responds successfully
- [ ] Error pages are user-friendly (no technical jargon)

---

## 5. Known Limitations

The following are expected behaviors for this epic and are **not** defects:

1. **Placeholder Sections:** The Daily Action List, Live Pulse, and Financial Intelligence sections show "Coming in Epic X" placeholders. These will be populated with real data in future epics.

2. **No Real-Time Data:** The Live Pulse section does not yet show actual real-time data. This will be implemented in Epic 2.

3. **No Action Items:** The Daily Action List does not yet display actual action items. This will be implemented in Epic 3.

4. **Database Status:** The health check may show database as "not configured" if the manufacturing database connection is not yet set up in the test environment. This is expected.

---

## 6. Defect Reporting

If you encounter any issues during testing, please document them with:

1. **Test Scenario Number** (e.g., Scenario 3, Step 3.2)
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
| **Tester Name** | Dmitri Spiropoulos |
| **Role/Title** | QA |
| **Test Date** | January 2026 |
| **Test Environment** | Test |
| **Browser/Device Used** | Desktop + Tablet (simulation app) |

### Test Results Summary

| Category | Pass | Fail | Not Tested | Notes |
|----------|------|------|------------|-------|
| Authentication (Scenarios 1-3) | [x] | [ ] | [ ] | All passed |
| Dashboard Layout (Scenario 4) | [x] | [ ] | [ ] | All passed |
| Responsive Design (Scenario 5) | [x] | [ ] | [ ] | All passed |
| Factory Visibility (Scenario 6) | [x] | [ ] | [ ] | All passed |
| Dark Mode (Scenario 7) | [x] | [ ] | [ ] | All passed |
| Health Check (Scenario 8) | [x] | [ ] | [ ] | All passed |
| Error Handling (Scenario 9) | [x] | [ ] | [ ] | All passed |

### Overall Assessment

- [x] **APPROVED** - All critical scenarios pass. Epic 1 is ready for production deployment.
- [ ] **APPROVED WITH CONDITIONS** - Minor issues noted but do not block deployment.
- [ ] **NOT APPROVED** - Critical issues found. Requires fixes before deployment.

### Comments/Notes

All Epic 1 scenarios passed testing successfully.

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
| 1.0 | January 6, 2026 | QA Specialist | Initial UAT document for Epic 1 |

---

*End of UAT Document*
