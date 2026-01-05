# Story 3.4: Insight + Evidence Cards

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **action recommendations displayed as cards that visually link each insight to its supporting metric or chart evidence**,
so that I can **trust the AI recommendations by immediately seeing the raw data that supports each prioritized action item**.

## Acceptance Criteria

1. **Insight + Evidence Card Component**
   - Card displays a recommendation/insight on the left side and supporting metric/chart on the right side
   - Card design follows "Industrial Clarity" high-contrast theme for factory floor visibility
   - Cards are responsive: side-by-side on desktop/tablet, stacked on mobile
   - Each card clearly shows the action priority level (Safety/Financial/OEE-based)

2. **Recommendation/Insight Display (Left Side)**
   - Shows natural language recommendation text (e.g., "Address Grinder 5 downtime - 45 min unplanned stoppage")
   - Displays priority badge: "SAFETY" (red), "FINANCIAL" (amber), or "OEE" (yellow)
   - Shows estimated financial impact in dollars when applicable
   - Includes timestamp of when the insight was generated
   - Shows asset name/location for context

3. **Evidence Display (Right Side)**
   - Shows the supporting data that generated this recommendation
   - For Safety insights: display safety_events details (time, reason code, asset)
   - For OEE insights: display OEE vs Target mini-chart or metric comparison
   - For Financial insights: display cost breakdown (downtime cost + waste cost)
   - Evidence section links to detailed view for drill-down (NFR1 compliance - AI cites specific data)

4. **Visual Hierarchy and Priority Styling**
   - Safety cards use "Safety Red" (#DC2626) border/accent (reserved exclusively for safety per UX)
   - Financial impact cards use amber accent color
   - OEE threshold cards use yellow accent color
   - Cards sorted by priority: Safety first, then Financial Impact ($), then OEE deviation
   - Priority badge is prominently visible and readable from 3 feet (Glanceability requirement)

5. **Data Source Integration**
   - Cards consume action items from Action Engine API (Story 3.2)
   - Evidence data pulled from daily_summaries, safety_events, and cost_centers tables
   - Each card includes source reference for traceability (NFR1: AI must cite specific data points)

6. **Interactivity**
   - Clicking evidence section expands to show more detailed data
   - Clicking asset name navigates to Asset Detail View
   - Cards can be dismissed/acknowledged (optional future enhancement)
   - Hover state provides additional context tooltip

7. **Performance and Accessibility**
   - Cards render within 500ms of data availability
   - Accessible color contrast ratios (WCAG AA minimum)
   - Screen reader friendly with proper ARIA labels
   - Keyboard navigable

## Tasks / Subtasks

- [ ] Task 1: Create InsightEvidenceCard React component (AC: #1, #4, #7)
  - [ ] 1.1 Create `apps/web/src/components/action-engine/InsightEvidenceCard.tsx`
  - [ ] 1.2 Implement two-column layout (insight left, evidence right)
  - [ ] 1.3 Apply Industrial Clarity styling with high-contrast colors
  - [ ] 1.4 Add responsive breakpoints (side-by-side on tablet+, stacked on mobile)
  - [ ] 1.5 Implement priority-based border/accent colors (Safety Red, Amber, Yellow)
  - [ ] 1.6 Add ARIA labels and keyboard navigation support

- [ ] Task 2: Create InsightSection subcomponent (AC: #2)
  - [ ] 2.1 Create `apps/web/src/components/action-engine/InsightSection.tsx`
  - [ ] 2.2 Display recommendation text with proper typography (readable from 3ft)
  - [ ] 2.3 Implement priority badge component (SAFETY/FINANCIAL/OEE)
  - [ ] 2.4 Display financial impact in prominent format (e.g., "$1,250 loss")
  - [ ] 2.5 Show timestamp and asset/location context
  - [ ] 2.6 Style priority badges with correct colors per type

- [ ] Task 3: Create EvidenceSection subcomponent (AC: #3, #5)
  - [ ] 3.1 Create `apps/web/src/components/action-engine/EvidenceSection.tsx`
  - [ ] 3.2 Implement safety evidence display (safety_events details)
  - [ ] 3.3 Implement OEE evidence display (target vs actual mini-visualization)
  - [ ] 3.4 Implement financial evidence display (cost breakdown)
  - [ ] 3.5 Add source reference citation (e.g., "Source: daily_summaries 2026-01-05")
  - [ ] 3.6 Add "View Details" link for drill-down navigation

- [ ] Task 4: Create PriorityBadge component (AC: #4)
  - [ ] 4.1 Create `apps/web/src/components/action-engine/PriorityBadge.tsx`
  - [ ] 4.2 Implement SAFETY badge (Safety Red #DC2626, white text)
  - [ ] 4.3 Implement FINANCIAL badge (Amber, dark text)
  - [ ] 4.4 Implement OEE badge (Yellow, dark text)
  - [ ] 4.5 Ensure badge size is glanceable (minimum 16px text)

- [ ] Task 5: Create ActionCardList container component (AC: #4, #5)
  - [ ] 5.1 Create `apps/web/src/components/action-engine/ActionCardList.tsx`
  - [ ] 5.2 Consume action items from Daily Action List API (Story 3.2)
  - [ ] 5.3 Sort cards by priority (Safety > Financial > OEE)
  - [ ] 5.4 Handle empty state (no action items - "All systems operating normally")
  - [ ] 5.5 Handle loading state with skeleton cards
  - [ ] 5.6 Handle error state with retry option

- [ ] Task 6: Implement card interactivity (AC: #6)
  - [ ] 6.1 Add expandable evidence section with animation
  - [ ] 6.2 Implement click handler for asset name navigation
  - [ ] 6.3 Add hover state with tooltip showing additional context
  - [ ] 6.4 Implement focus states for keyboard navigation

- [ ] Task 7: Integrate with Action List Primary View (AC: #5)
  - [ ] 7.1 Update Morning Report view (Story 3.3) to use ActionCardList
  - [ ] 7.2 Ensure cards load from Action Engine API endpoint
  - [ ] 7.3 Verify data flow: API -> ActionCardList -> InsightEvidenceCard
  - [ ] 7.4 Test with realistic action item data

- [ ] Task 8: Testing (AC: #7)
  - [ ] 8.1 Unit tests for InsightEvidenceCard with various priority types
  - [ ] 8.2 Unit tests for PriorityBadge color logic
  - [ ] 8.3 Integration test for ActionCardList with mock API data
  - [ ] 8.4 Visual regression test for high-contrast readability
  - [ ] 8.5 Accessibility audit (contrast ratios, ARIA labels, keyboard nav)

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router
- **Styling:** Tailwind CSS + Shadcn/UI with Industrial Clarity theme extensions
- **Component Pattern:** Compound components (Card > InsightSection + EvidenceSection)
- **Data Fetching:** Server Components for initial load, client-side for interactivity
- **State Management:** React Query/SWR for API data caching

### Technical Requirements

**Frontend (apps/web):**
- Use Shadcn/UI Card component as base, extend with custom styling
- Implement responsive grid: `grid-cols-1 md:grid-cols-2` for card layout
- Apply Industrial Clarity color tokens:
  - `safety-red: #DC2626` (ONLY for safety incidents)
  - `financial-amber: #F59E0B` (for financial priority)
  - `oee-yellow: #EAB308` (for OEE threshold priority)
  - `text-primary: #1F2937` (high contrast text)
  - `bg-card: #FFFFFF` (card background)
- Typography: Minimum 16px for body text, 24px+ for key metrics, 48px+ for primary values
- Border styling: 4px left border with priority color

**Card Data Structure:**
```typescript
interface ActionItem {
  id: string;
  priority: 'SAFETY' | 'FINANCIAL' | 'OEE';
  priorityScore: number;           // For sorting
  recommendation: {
    text: string;                  // Natural language recommendation
    summary: string;               // Short version for card
  };
  asset: {
    id: string;
    name: string;
    area: string;
  };
  evidence: {
    type: 'safety_event' | 'oee_deviation' | 'financial_loss';
    data: SafetyEvidence | OEEEvidence | FinancialEvidence;
    source: {
      table: string;               // e.g., "daily_summaries"
      date: string;                // e.g., "2026-01-05"
      recordId: string;
    };
  };
  financialImpact: number;         // Total $ impact
  timestamp: string;               // When insight was generated
}

interface SafetyEvidence {
  eventId: string;
  detectedAt: string;
  reasonCode: string;
  severity: string;
  assetName: string;
}

interface OEEEvidence {
  targetOEE: number;
  actualOEE: number;
  deviation: number;
  timeframe: string;
}

interface FinancialEvidence {
  downtimeCost: number;
  wasteCost: number;
  totalLoss: number;
  breakdown: Array<{ category: string; amount: number }>;
}
```

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Insight + Evidence | Two-column card: Recommendation (Left) + Supporting Metric/Chart (Right) |
| Action First | Cards are the primary content on Morning Report landing page |
| Trust & Transparency | Every recommendation includes source citation (NFR1) |
| Glanceability | Priority badges 16px+, key metrics 24px+, readable from 3 feet |
| Industrial Clarity | High-contrast colors, Safety Red reserved for incidents only |
| Visual Hierarchy | Cards sorted by priority with color-coded accents |

### Project Structure Notes

```
apps/web/src/
  components/
    action-engine/
      InsightEvidenceCard.tsx     # Main card component (NEW)
      InsightSection.tsx          # Left side - recommendation (NEW)
      EvidenceSection.tsx         # Right side - supporting data (NEW)
      PriorityBadge.tsx           # Priority indicator (NEW)
      ActionCardList.tsx          # Container for cards (NEW)
      index.ts                    # Barrel export (NEW)
    dashboard/
      MorningReportView.tsx       # Update to use ActionCardList
```

### Dependencies

**Requires (must be completed):**
- Story 1.6: Industrial Clarity Design System (provides color tokens and typography)
- Story 1.7: Command Center UI Shell (provides page layout structure)
- Story 3.2: Daily Action List API (provides action items data endpoint)
- Story 3.3: Action List Primary View (provides Morning Report view to integrate with)

**Enables:**
- Story 3.5: Smart Summary Generator (can display LLM summaries in card format)
- Epic 4: AI Chat can reference specific action cards in conversations

### NFR Compliance

- **NFR1 (Accuracy):** Every card includes `evidence.source` with table, date, and record ID for traceability. Users can click through to verify raw data.
- **NFR2 (Latency):** Cards render within 500ms of API response, using skeleton loading states during fetch.

### Testing Guidance

**Unit Tests:**
- Test PriorityBadge renders correct colors for each priority type
- Test InsightSection displays all required fields
- Test EvidenceSection renders correct layout for each evidence type
- Test ActionCardList sorts items by priority correctly

**Integration Tests:**
- Test full card renders with mock ActionItem data
- Test expand/collapse behavior for evidence section
- Test navigation to asset detail view

**Visual Tests:**
- Verify high-contrast readability on tablet viewport (768px-1024px)
- Verify Safety Red only appears for SAFETY priority items
- Verify responsive layout transitions correctly
- Verify priority badges are visible from 3-foot distance (simulate with zoom)

**Accessibility Tests:**
- WCAG AA contrast ratio compliance (4.5:1 for text)
- Screen reader announces priority and recommendation
- Keyboard navigation through cards works correctly
- Focus indicators are visible

### API Data Source (from Story 3.2)

The cards consume data from the Daily Action List API endpoint:

```
GET /api/actions/daily
Response: {
  date: string;
  generatedAt: string;
  items: ActionItem[];
  summary: {
    totalItems: number;
    safetyCount: number;
    financialCount: number;
    oeeCount: number;
    totalFinancialImpact: number;
  };
}
```

### Color Reference

| Priority | Border Color | Badge BG | Badge Text | Usage |
|----------|--------------|----------|------------|-------|
| SAFETY | #DC2626 (Safety Red) | #DC2626 | White | Safety incidents ONLY |
| FINANCIAL | #F59E0B (Amber) | #F59E0B | #1F2937 | High $ impact items |
| OEE | #EAB308 (Yellow) | #EAB308 | #1F2937 | OEE below target |

### References

- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - "Insight + Evidence" design principle, Glanceability, Trust & Transparency
- [Source: _bmad/bmm/data/ux-design.md#2. Design Principles] - "Action items presented as cards: Recommendation (Left) + Supporting Metric/Chart (Right)"
- [Source: _bmad/bmm/data/prd.md#2. Requirements] - NFR1 (AI must cite specific data points), FR3 (Action Engine)
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Action Engine Logic (Safety first, then Financial Impact)
- [Source: _bmad-output/planning-artifacts/epic-3.md] - Story 3.4 definition: "Card design linking each recommendation to supporting metric/chart evidence"
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3] - "Insight + Evidence card design (recommendation + supporting data)"
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Industrial Clarity color palette and typography guidelines

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
