# Story 19.2: Clickable Asset Links in Smart Summary

Status: ready-for-dev

## Story

As a Plant Manager reading the smart summary,
I want asset names mentioned in the summary to be clickable links,
so that I can quickly navigate to the asset's detail page or its action item.

## Acceptance Criteria

1. **Given** the smart summary text mentions an asset name (e.g., "Grinder 5"), **When** the summary is rendered, **Then** the asset name is displayed as a clickable link, **And** clicking it scrolls to or highlights that asset's action item on the current report.

2. **Given** the smart summary mentions an asset that has an asset detail page, **When** the user clicks the asset name while holding Ctrl/Cmd, **Then** the asset detail page opens in a new tab.

3. **Given** the summary text contains an asset name that doesn't match any known asset, **When** the summary renders, **Then** the text is rendered as plain text (no link).

## Tasks / Subtasks

- [ ] Task 1: Create `linkifyAssets` utility function (AC: #1, #3)
  - [ ] 1.1 Create `apps/web/src/lib/linkifyAssets.ts` with `linkifyAssetNames()` function
  - [ ] 1.2 Accept summary text (string) and list of known asset names (from action items) as inputs
  - [ ] 1.3 Use regex replacement to wrap matched asset names with a marker token (e.g., `[[ASSET:Grinder 5]]`)
  - [ ] 1.4 Sort asset names by length descending before matching to prevent partial matches (e.g., "CAMA 2400" before "CAMA")
  - [ ] 1.5 Implement case-insensitive matching with original case preservation
  - [ ] 1.6 Return the modified string with asset markers embedded
  - [ ] 1.7 Export a helper to extract unique asset names from `ActionItem[]` array
  - [ ] 1.8 Write unit tests in `apps/web/src/__tests__/linkifyAssets.test.ts`

- [ ] Task 2: Create custom ReactMarkdown renderer for asset links (AC: #1, #2)
  - [ ] 2.1 In `MorningSummarySection.tsx`, add a custom `components` prop to the existing `<ReactMarkdown>` instance
  - [ ] 2.2 Create a custom text renderer that detects `[[ASSET:name]]` tokens in text nodes
  - [ ] 2.3 Render matched tokens as `<button>` or `<a>` elements styled as links
  - [ ] 2.4 On click: scroll to the matching action item card using DOM `id` attribute or `scrollIntoView()`
  - [ ] 2.5 On Ctrl/Cmd+click: open `/morning-report/action/{id}` in a new tab (use `window.open()`)
  - [ ] 2.6 Style the link with `text-info-blue hover:underline cursor-pointer` to match existing link patterns

- [ ] Task 3: Wire asset name data from action items into the summary renderer (AC: #1, #3)
  - [ ] 3.1 Extract asset names from `useDailyActions` hook data (`data.actions.map(a => a.asset_name)`)
  - [ ] 3.2 Build a lookup map: `assetName -> actionItemId` for scroll targeting
  - [ ] 3.3 Pass the processed summary text (with asset markers) to ReactMarkdown
  - [ ] 3.4 Ensure unmatched asset names render as plain text (no markers inserted = no links)

- [ ] Task 4: Implement scroll-to-action-item behavior (AC: #1)
  - [ ] 4.1 Add `data-asset-name` or `id` attribute to `InsightEvidenceCard` for scroll targeting
  - [ ] 4.2 Implement smooth scroll with highlight flash animation on the target card
  - [ ] 4.3 Use `scrollIntoView({ behavior: 'smooth', block: 'center' })` for reliable scrolling

- [ ] Task 5: Write tests (AC: #1, #2, #3)
  - [ ] 5.1 Unit tests for `linkifyAssets.ts`: matching, non-matching, partial match prevention, case insensitivity
  - [ ] 5.2 Component test: verify asset links render in summary when asset names match action items
  - [ ] 5.3 Component test: verify plain text renders when asset names don't match

## Dev Notes

### Architecture & Patterns

- **Framework:** Next.js 14 with App Router, React 18, TypeScript 5.x
- **Styling:** Tailwind CSS 3.4+ with Shadcn/UI components
- **Markdown rendering:** `react-markdown@9.0.1` with `remark-gfm@4.0.0` (already installed)
- **Testing:** Vitest + Testing Library (run with `cd apps/web && npm run test:run`)
- **Component organization:** Domain-based folders under `apps/web/src/components/`
- **Utility location:** `apps/web/src/lib/` for shared utilities

### Key Existing Code to Reuse (DO NOT REINVENT)

1. **`MorningSummarySection.tsx`** (`apps/web/src/components/action-list/MorningSummarySection.tsx`):
   - Already renders the smart summary using `<ReactMarkdown remarkPlugins={[remarkGfm]}>` at line 252
   - Already has `cleanSummaryText()` function that strips inline citation tags -- linkification should run AFTER cleaning
   - Already imports `useDailyActions` hook which provides action items with `asset_name` field
   - Already imports `useSmartSummary` hook which provides `summary_text`

2. **`ChatMessage.tsx`** (`apps/web/src/components/chat/ChatMessage.tsx`):
   - Shows the ESTABLISHED PATTERN for custom ReactMarkdown `components` prop (lines 167-233)
   - Custom renderers for `table`, `strong`, `a`, `ul`, `ol`, `code` -- follow this exact pattern
   - Use this as the reference for how to add custom component overrides to ReactMarkdown

3. **`useDailyActions` hook** (`apps/web/src/hooks/useDailyActions.ts`):
   - Returns `data.actions[]` where each action has `asset_name: string` and `id: string`
   - The `ActionItem` type (line 31-47) has `asset_name`, `id`, `asset_id` fields
   - Use `data?.actions` to get the current day's action items for asset name matching

4. **`InsightEvidenceCard.tsx`** (`apps/web/src/components/action-engine/InsightEvidenceCard.tsx`):
   - This is the card that renders each action item in the list below the summary
   - Add a `data-asset-name={item.asset.name}` attribute to the Card element for scroll targeting
   - Or use `id={`action-${item.id}`}` for ID-based targeting

5. **`ActionItemCard.tsx`** (`apps/web/src/components/action-list/ActionItemCard.tsx`):
   - Legacy action item card -- NOT used on the morning report page
   - The morning report page uses `InsightEvidenceCardList` from `action-engine/`

6. **Link styling pattern:** `text-info-blue hover:underline` used in `ChatMessage.tsx` line 209

### Implementation Strategy

**Step 1: Create the linkify utility (`apps/web/src/lib/linkifyAssets.ts`)**

```typescript
// Core function: takes summary text and known asset names, returns text with asset markers
export function linkifyAssetNames(text: string, assetNames: string[]): string
// Helper: extract unique asset names from action items
export function extractAssetNames(actions: Array<{ asset_name: string }>): string[]
```

- Sort asset names by length DESC before regex matching to prevent "CAMA" matching before "CAMA 2400"
- Use word boundary or lookahead/lookbehind for precise matching
- Marker format: `[[ASSET:Grinder 5]]` -- chosen because it won't conflict with markdown syntax
- The marker approach means ReactMarkdown parses the markdown first, then a custom text renderer splits on markers

**Step 2: Add custom text renderer to ReactMarkdown in MorningSummarySection**

The `components` prop on ReactMarkdown supports a custom `text` renderer (or override `p` to process children). The cleanest approach:

1. Pre-process the summary text with `linkifyAssetNames()` to embed `[[ASSET:name]]` markers
2. Add a custom `p` or `text` component renderer that splits text on the marker pattern
3. Render markers as clickable `<button>` elements (not `<a>` to avoid href requirements)
4. Non-marker text renders as normal `<span>`

**Step 3: Handle click behavior**

- Default click: `document.querySelector(`[data-asset-name="Grinder 5"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })`
- Ctrl/Cmd click: Check `event.metaKey || event.ctrlKey`, then `window.open(`/morning-report/action/${actionId}`, '_blank')`
- Build a `Map<string, string>` of `assetName -> actionId` from the actions data for Ctrl+click navigation

**Step 4: Add scroll target attributes to InsightEvidenceCard**

- Add `data-asset-name={item.asset.name}` to the root `<Card>` element in `InsightEvidenceCard.tsx`
- Optionally add a brief highlight animation class (e.g., `ring-2 ring-info-blue`) toggled via a CSS animation or temporary state

### Critical Constraints

- **DO NOT modify the smart summary text stored in the database** -- linkification is a purely client-side rendering concern
- **DO NOT add new npm dependencies** -- `react-markdown` and `remark-gfm` already handle markdown; custom renderers handle the rest
- **DO NOT break existing markdown rendering** -- the `cleanSummaryText()` call must still run; linkification adds to it, doesn't replace it
- **Maintain the existing CSS class structure** on the ReactMarkdown wrapper div (line 251): `text-sm text-foreground space-y-2 [&_ul]:list-disc [&_ul]:pl-4 ...`
- **Case-insensitive matching but preserve original case** in the displayed link text
- **Handle empty/null action data gracefully** -- if no actions loaded yet, render summary as plain text (no links)

### Project Structure Notes

- New file: `apps/web/src/lib/linkifyAssets.ts` -- follows existing pattern of utilities in `lib/`
- New file: `apps/web/src/__tests__/linkifyAssets.test.ts` -- follows existing test location pattern
- Modified: `apps/web/src/components/action-list/MorningSummarySection.tsx` -- the primary component
- Modified: `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` -- add data attribute for scroll target

### References

- [Source: _bmad-output/planning-artifacts/epic-19.md#Story 19.2] - Story requirements and acceptance criteria
- [Source: apps/web/src/components/action-list/MorningSummarySection.tsx] - Primary component to modify
- [Source: apps/web/src/components/chat/ChatMessage.tsx#lines 167-233] - ReactMarkdown custom renderer pattern
- [Source: apps/web/src/hooks/useDailyActions.ts#ActionItem type] - Asset name data source
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx] - Scroll target card component
- [Source: apps/web/src/components/action-engine/types.ts#AssetReference] - Asset type definition
- [Source: docs/architecture-web.md] - Frontend architecture, tech stack, directory structure
- [Source: apps/web/package.json] - Confirmed react-markdown@9.0.1, remark-gfm@4.0.0 already installed

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
