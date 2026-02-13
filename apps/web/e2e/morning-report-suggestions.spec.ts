/**
 * E2E Tests: Context-Aware Follow-Up Suggestions (Story 19.3)
 *
 * TDD tests — these MUST FAIL until the suggestion chip feature is implemented.
 * Tests the end-to-end flow from suggestion chip click to AI response in chat sidebar.
 *
 * NOTE: Playwright is not yet installed in this project. These tests serve as
 * the E2E test specification and will be runnable once Playwright is configured.
 * Install with: npx playwright install && npm i -D @playwright/test
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #1 - Suggestion chips rendered below "Ask about this" button
 * @see AC #2 - Clicking chip opens chat with question
 */

import { test, expect } from '@playwright/test'

// ---------------------------------------------------------------------------
// Test Configuration
// ---------------------------------------------------------------------------

const MORNING_REPORT_URL = '/morning-report'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

test.describe('Feature: Context-Aware Follow-Up Suggestions (Story 19.3)', () => {
  // =========================================================================
  // AC2: End-to-end flow from suggestion chip click to AI response
  // =========================================================================
  test.describe('AC2: End-to-end suggestion chip flow', () => {
    test('19-3-context-aware-followup-suggestions-E2E-001: End-to-end flow from suggestion chip click to AI response', async ({ page }) => {
      // Given: The morning report page is loaded with a smart summary and action items
      await page.goto(MORNING_REPORT_URL)

      // Wait for the smart summary to load
      await page.waitForSelector('text=AI Summary', { timeout: 15000 })

      // And: Suggested question chips are visible below the "Ask about this" button
      const suggestionGroup = page.locator('[role="group"][aria-label*="Suggested follow-up questions"]')
      await expect(suggestionGroup).toBeVisible({ timeout: 10000 })

      // Verify 2-3 suggestion chips are present
      const chipButtons = suggestionGroup.locator('button')
      const chipCount = await chipButtons.count()
      expect(chipCount).toBeGreaterThanOrEqual(2)
      expect(chipCount).toBeLessThanOrEqual(3)

      // Capture the first chip's text
      const firstChipText = await chipButtons.first().textContent()
      expect(firstChipText).toBeTruthy()
      expect(firstChipText!.trim().length).toBeGreaterThan(10)

      // When: The user clicks the first suggestion chip
      await chipButtons.first().click()

      // Then: The chat sidebar opens
      const chatSidebar = page.locator('#chat-sidebar')
      await expect(chatSidebar).toBeVisible({ timeout: 5000 })

      // And: The report context intro message is shown
      const contextMessage = chatSidebar.locator('text=/morning report context/i')
      await expect(contextMessage).toBeVisible({ timeout: 3000 })

      // And: The question appears as a user message in the chat
      // Strip the ChevronRight icon text and trim
      const cleanedQuestion = firstChipText!.replace(/[^\w\s?$%.,'"]/g, '').trim()
      const userMessage = chatSidebar.locator(`text=${cleanedQuestion}`)
      await expect(userMessage).toBeVisible({ timeout: 5000 })

      // And: An AI response begins streaming (loading indicator or assistant message appears)
      const assistantResponse = chatSidebar.locator('[class*="assistant"], text=Thinking...')
      await expect(assistantResponse).toBeVisible({ timeout: 10000 })
    })
  })
})
