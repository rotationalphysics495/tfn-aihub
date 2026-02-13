/**
 * Asset Name Linkification Utility (Story 19.2)
 *
 * Provides functions to identify and wrap asset names in summary text
 * with marker tokens for rendering as clickable links.
 *
 * @see Story 19.2 - Clickable Asset Links in Smart Summary
 */

function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Builds a boundary-aware regex pattern for an asset name.
 * Uses \b for word characters at boundaries, and lookahead/lookbehind
 * for non-word characters (e.g., parentheses) at boundaries.
 */
function buildBoundaryPattern(escaped: string, original: string): string {
  const isWordChar = (ch: string) => /\w/.test(ch)
  const prefix = isWordChar(original[0]) ? '\\b' : '(?<=\\s|^)'
  const suffix = isWordChar(original[original.length - 1]) ? '\\b' : '(?=\\s|$|[.,;:!?])'
  return `${prefix}${escaped}${suffix}`
}

/**
 * Wraps known asset names in text with [[ASSET:name]] marker tokens.
 * These markers are later parsed by the ReactMarkdown custom renderer
 * to produce clickable link elements.
 *
 * @param text - The summary text to process
 * @param assetNames - Array of known asset names to match
 * @returns The text with matched asset names wrapped in [[ASSET:...]] markers
 */
export function linkifyAssetNames(text: string, assetNames: string[]): string {
  if (!text || assetNames.length === 0) return text

  // Sort by length descending to prevent partial matches (e.g., "CAMA 2400" before "CAMA")
  const sorted = [...assetNames].sort((a, b) => b.length - a.length)

  // Build a single regex with alternation, each name having appropriate boundaries
  const pattern = sorted
    .map((name) => buildBoundaryPattern(escapeRegExp(name), name))
    .join('|')
  const regex = new RegExp(`(${pattern})`, 'gi')

  return text.replace(regex, (match) => `[[ASSET:${match}]]`)
}

/**
 * Extracts unique, non-empty asset names from an array of action items.
 *
 * @param actions - Array of objects with asset_name field
 * @returns Deduplicated array of asset name strings
 */
export function extractAssetNames(actions: Array<{ asset_name: string }>): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const action of actions) {
    const name = action.asset_name
    if (name && !seen.has(name)) {
      seen.add(name)
      result.push(name)
    }
  }
  return result
}
