/**
 * Unit Tests for linkifyAssets utility (Story 19.2: Clickable Asset Links in Smart Summary)
 *
 * Tests the linkifyAssetNames() and extractAssetNames() utility functions that
 * identify and wrap asset names in summary text with marker tokens for rendering
 * as clickable links.
 *
 * @see Story 19.2 - Clickable Asset Links in Smart Summary
 * @see AC #1 - Asset names displayed as clickable links
 * @see AC #3 - Unknown asset names rendered as plain text
 */

import { describe, it, expect } from 'vitest'
import { linkifyAssetNames, extractAssetNames } from '@/lib/linkifyAssets'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Clickable Asset Links in Smart Summary (Story 19.2)', () => {
  // =========================================================================
  // AC1: Asset names displayed as clickable links
  // =========================================================================
  describe('AC1: linkifyAssetNames wraps known asset names with marker tokens', () => {
    it('UNIT-001: linkifyAssetNames wraps a single known asset name with marker token', () => {
      // Given: Summary text mentioning a known asset name
      const text = 'Grinder 5 needs immediate attention'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called with the text and asset names
      const result = linkifyAssetNames(text, assetNames)

      // Then: The returned string contains the asset name wrapped with [[ASSET:...]] marker
      expect(result).toBe('[[ASSET:Grinder 5]] needs immediate attention')
    })

    it('UNIT-002: linkifyAssetNames wraps multiple known asset names with marker tokens', () => {
      // Given: Summary text mentioning multiple known asset names
      const text = 'Grinder 5 and CAMA 2400 require maintenance'
      const assetNames = ['Grinder 5', 'CAMA 2400']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: Both asset names are wrapped with [[ASSET:...]] markers
      expect(result).toBe(
        '[[ASSET:Grinder 5]] and [[ASSET:CAMA 2400]] require maintenance'
      )
    })

    it('UNIT-003: linkifyAssetNames performs case-insensitive matching with original case preservation', () => {
      // Given: Summary text contains a lowercase variant of a known asset name
      const text = 'grinder 5 needs work'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: The matched text preserves the original case from the source text
      expect(result).toBe('[[ASSET:grinder 5]] needs work')
    })

    it('UNIT-004: linkifyAssetNames sorts names by length descending to prevent partial matches', () => {
      // Given: Known asset names include both "CAMA" and "CAMA 2400"
      const text = 'CAMA 2400 is down'
      const assetNames = ['CAMA', 'CAMA 2400']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: "CAMA 2400" is matched as a whole, not "CAMA" alone
      expect(result).toBe('[[ASSET:CAMA 2400]] is down')
      expect(result).not.toBe('[[ASSET:CAMA]] 2400 is down')
    })

    it('UNIT-005: linkifyAssetNames handles multiple occurrences of the same asset name', () => {
      // Given: Summary text mentions the same asset name twice
      const text = 'Grinder 5 failed. Check Grinder 5 immediately.'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: Both occurrences are wrapped with [[ASSET:...]] markers
      expect(result).toBe(
        '[[ASSET:Grinder 5]] failed. Check [[ASSET:Grinder 5]] immediately.'
      )
    })

    it('UNIT-006: linkifyAssetNames escapes regex special characters in asset names', () => {
      // Given: Known asset name contains regex special characters
      const text = 'Line (A+B) is running'
      const assetNames = ['Line (A+B)']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: The name is correctly matched and wrapped without regex errors
      expect(result).toBe('[[ASSET:Line (A+B)]] is running')
    })

    it('UNIT-007: linkifyAssetNames returns original text unchanged when asset names list is empty', () => {
      // Given: An empty asset names array
      const text = 'Grinder 5 needs attention'
      const assetNames: string[] = []

      // When: linkifyAssetNames() is called with empty assetNames
      const result = linkifyAssetNames(text, assetNames)

      // Then: The original text is returned unmodified with no markers
      expect(result).toBe('Grinder 5 needs attention')
    })

    it('UNIT-008: linkifyAssetNames returns empty string when input text is empty', () => {
      // Given: Empty summary text
      const text = ''
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: An empty string is returned
      expect(result).toBe('')
    })

    it('UNIT-009: linkifyAssetNames respects word boundaries', () => {
      // Given: Summary text contains "Grinder 50" but only "Grinder 5" is a known asset
      const text = 'Grinder 50 is running'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: "Grinder 50" is NOT matched (word boundary prevents partial number match)
      expect(result).toBe('Grinder 50 is running')
    })

    it('UNIT-013: linkifyAssetNames does not match asset name embedded in the middle of a word', () => {
      // Given: Summary text contains "TheGrinder 5" where "Grinder 5" is a known asset
      const text = 'TheGrinder 5 model'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: "TheGrinder 5" is NOT matched due to word boundary
      expect(result).toBe('TheGrinder 5 model')
    })
  })

  // =========================================================================
  // AC1: extractAssetNames utility
  // =========================================================================
  describe('AC1: extractAssetNames extracts unique asset names from action items', () => {
    it('UNIT-010: extractAssetNames extracts unique asset names from action items', () => {
      // Given: An array of action items with asset_name fields, some duplicated
      const actions = [
        { asset_name: 'Grinder 5' },
        { asset_name: 'CAMA 2400' },
        { asset_name: 'Grinder 5' },
      ]

      // When: extractAssetNames() is called
      const result = extractAssetNames(actions)

      // Then: A deduplicated array of asset name strings is returned
      expect(result).toEqual(['Grinder 5', 'CAMA 2400'])
    })

    it('UNIT-011: extractAssetNames filters out empty and null asset names', () => {
      // Given: An array of action items where some have empty string or null asset_name
      const actions = [
        { asset_name: 'Grinder 5' },
        { asset_name: '' },
        { asset_name: null as unknown as string },
      ]

      // When: extractAssetNames() is called
      const result = extractAssetNames(actions)

      // Then: Only non-empty, non-null asset names are returned
      expect(result).toEqual(['Grinder 5'])
    })

    it('UNIT-012: extractAssetNames returns empty array for empty input', () => {
      // Given: An empty array of action items
      const actions: Array<{ asset_name: string }> = []

      // When: extractAssetNames() is called
      const result = extractAssetNames(actions)

      // Then: An empty array is returned
      expect(result).toEqual([])
    })
  })

  // =========================================================================
  // AC3: Unknown asset names rendered as plain text
  // =========================================================================
  describe('AC3: linkifyAssetNames does not wrap unmatched names', () => {
    it('UNIT-014: linkifyAssetNames does not wrap unmatched names with markers', () => {
      // Given: Summary text contains names not in the known asset names list
      const text = 'Unknown Machine X needs repair'
      const assetNames = ['Grinder 5', 'CAMA 2400']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: The text is returned unchanged with no [[ASSET:...]] markers
      expect(result).toBe('Unknown Machine X needs repair')
    })

    it('UNIT-015: linkifyAssetNames only wraps matched names, leaving all other text intact', () => {
      // Given: Summary text with a mix of matched and unmatched names
      const text = 'Grinder 5 and Unknown Machine need work'
      const assetNames = ['Grinder 5']

      // When: linkifyAssetNames() is called
      const result = linkifyAssetNames(text, assetNames)

      // Then: Only known asset names get markers; other text remains plain
      expect(result).toBe(
        '[[ASSET:Grinder 5]] and Unknown Machine need work'
      )
    })
  })
})
