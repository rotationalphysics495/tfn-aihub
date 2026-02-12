/**
 * E2E Tests: Trend Indicators on Action Cards (Story 14.4)
 *
 * TDD tests — these MUST FAIL until the trend indicator feature is implemented.
 * Tests verify that trend indicators render correctly at different viewport sizes.
 *
 * NOTE: Playwright is not yet installed in this project. These tests serve as
 * the E2E test specification and will be runnable once Playwright is configured.
 * Install with: npx playwright install && npm i -D @playwright/test
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #7 - Responsive layout on tablet viewport
 */

import { test, expect } from '@playwright/test'

// ---------------------------------------------------------------------------
// Test Configuration
// ---------------------------------------------------------------------------

const ACTION_ITEMS_URL = '/dashboard' // Adjust to actual route with action items

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

test.describe('Feature: Trend Indicators on Action Cards (Story 14.4)', () => {
  // =========================================================================
  // AC7: Responsive layout on tablet viewport
  // =========================================================================
  test.describe('AC7: Responsive Layout', () => {
    test('E2E-001: Trend indicators visible on tablet viewport without scrolling', async ({ page }) => {
      // Given: The action items page is loaded with items containing trend data
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto(ACTION_ITEMS_URL)

      // Wait for action cards to load
      await page.waitForSelector('[role="article"]', { timeout: 10000 })

      // When: Viewed on a tablet viewport (768px-1024px width)
      const firstCard = page.locator('[role="article"]').first()

      // Then: The trend arrow is visible within the card
      const trendArrow = firstCard.locator('[data-testid="trend-arrow"]')
      await expect(trendArrow).toBeVisible()

      // And: The sparkline chart is visible within the card
      const sparkline = firstCard.locator('[data-testid="sparkline-chart"]')
      await expect(sparkline).toBeVisible()

      // And: The repeat offender badge is visible (for items with consecutive_days >= 3)
      // Note: Not all items will have this badge, so we check on a card that has trend data
      const badge = firstCard.locator('text=/day in a row|of 7 days|New/i')
      await expect(badge).toBeVisible()

      // And: No horizontal scrolling is needed
      const cardBox = await firstCard.boundingBox()
      const viewportWidth = 768
      expect(cardBox).toBeTruthy()
      expect(cardBox!.width).toBeLessThanOrEqual(viewportWidth)
    })

    test('E2E-002: Trend indicators render correctly on desktop viewport', async ({ page }) => {
      // Given: The action items page is loaded with items containing trend data
      await page.setViewportSize({ width: 1280, height: 800 })
      await page.goto(ACTION_ITEMS_URL)

      // Wait for action cards to load
      await page.waitForSelector('[role="article"]', { timeout: 10000 })

      // When: Viewed on a desktop viewport (1280px+ width)
      const firstCard = page.locator('[role="article"]').first()

      // Then: Trend indicators are rendered inline and proportionally sized
      const trendArrow = firstCard.locator('[data-testid="trend-arrow"]')
      await expect(trendArrow).toBeVisible()

      const sparkline = firstCard.locator('[data-testid="sparkline-chart"]')
      await expect(sparkline).toBeVisible()

      // And: The sparkline has reasonable dimensions
      const sparklineBox = await sparkline.boundingBox()
      expect(sparklineBox).toBeTruthy()
      expect(sparklineBox!.width).toBeGreaterThanOrEqual(60)
      expect(sparklineBox!.width).toBeLessThanOrEqual(120)
      expect(sparklineBox!.height).toBeGreaterThanOrEqual(16)
      expect(sparklineBox!.height).toBeLessThanOrEqual(40)

      // And: No horizontal overflow on desktop
      const cardBox = await firstCard.boundingBox()
      expect(cardBox).toBeTruthy()
      expect(cardBox!.width).toBeLessThanOrEqual(1280)
    })
  })
})
