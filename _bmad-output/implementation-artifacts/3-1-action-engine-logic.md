# Story 3.1: Action Engine Logic

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **a prioritization algorithm that filters and sorts operational issues by Safety first, then OEE below target, then Financial Loss above threshold**,
so that **my Daily Action List highlights the most critical issues requiring immediate attention, ensuring safety takes absolute priority followed by business impact**.

## Acceptance Criteria

1. **Action Engine Service Exists**
   - GIVEN the FastAPI backend is running
   - WHEN action prioritization is requested
   - THEN a dedicated Action Engine service processes `daily_summaries`, `safety_events`, and `cost_centers` data
   - AND returns a prioritized list of action items

2. **Safety Priority Filter (Tier 1 - Highest)**
   - GIVEN there are entries in the `safety_events` table with `is_resolved = FALSE`
   - WHEN the Action Engine processes data
   - THEN all unresolved safety events are included in the action list
   - AND they are placed at the TOP of the prioritized list regardless of other metrics
   - AND they are marked with priority level "critical"

3. **OEE Below Target Filter (Tier 2)**
   - GIVEN there are entries in `daily_summaries` where `oee_percentage < target_oee`
   - WHEN the Action Engine processes data
   - THEN assets with OEE below target are included in the action list
   - AND they are sorted by the magnitude of the gap (worst performers first)
   - AND they appear AFTER all safety items
   - AND they are marked with priority level "high" or "medium" based on gap severity

4. **Financial Loss Above Threshold Filter (Tier 3)**
   - GIVEN there are entries in `daily_summaries` where `financial_loss_dollars > configured_threshold`
   - WHEN the Action Engine processes data
   - THEN assets with financial loss above threshold are included
   - AND they are sorted by `financial_loss_dollars` descending (highest loss first)
   - AND they appear AFTER safety and OEE items
   - AND they are marked with priority level "medium" or "low" based on loss amount

5. **Combined Sorting Logic**
   - GIVEN multiple action items across all three categories
   - WHEN the final action list is generated
   - THEN items are sorted: Safety (by severity) > OEE Gap (by % gap) > Financial Loss (by $ amount)
   - AND within each category, items are sorted by their respective severity/impact metric
   - AND duplicate assets appearing in multiple categories are consolidated with the highest priority reason shown first

6. **Configurable Thresholds**
   - GIVEN environment configuration exists
   - WHEN thresholds are evaluated
   - THEN `TARGET_OEE_PERCENTAGE` (default: 85.0) is used for OEE comparison
   - AND `FINANCIAL_LOSS_THRESHOLD` (default: $1000) is used for financial filtering
   - AND thresholds can be overridden via environment variables or API parameters

7. **Action Item Data Structure**
   - GIVEN an action item is generated
   - WHEN it is returned in the list
   - THEN it includes: `asset_id`, `asset_name`, `priority_level`, `category` (safety/oee/financial), `primary_metric_value`, `recommendation_text`, `evidence_summary`, `source_data_refs`
   - AND the structure supports the Evidence Card UI pattern from UX design

8. **API Endpoint for Action List**
   - GIVEN the API is running
   - WHEN a GET request is made to `/api/actions/daily`
   - THEN it returns the prioritized action list as JSON
   - AND supports optional query parameters: `date` (default: T-1), `limit`, `category_filter`
   - AND the response includes metadata: `generated_at`, `total_count`, `counts_by_category`

9. **Integration with Daily Pipeline**
   - GIVEN the Morning Report pipeline (Pipeline A) runs at 06:00 AM
   - WHEN T-1 data processing completes
   - THEN the Action Engine can be invoked to generate the daily action list
   - AND results can be cached for fast retrieval throughout the day

10. **Empty State Handling**
    - GIVEN no items match the priority filters
    - WHEN the Action Engine processes data
    - THEN it returns an empty action list with appropriate metadata
    - AND does not error or return null

## Tasks / Subtasks

- [ ] Task 1: Create Action Engine Service Module (AC: #1, #5)
  - [ ] 1.1 Create `apps/api/app/services/action_engine.py` service module
  - [ ] 1.2 Implement `ActionEngine` class with configurable thresholds
  - [ ] 1.3 Implement `generate_action_list(date: date) -> List[ActionItem]` main method
  - [ ] 1.4 Add dependency injection for Supabase client and configuration

- [ ] Task 2: Implement Safety Priority Filter (AC: #2)
  - [ ] 2.1 Create `_get_safety_actions()` method
  - [ ] 2.2 Query `safety_events` WHERE `is_resolved = FALSE` AND `event_timestamp >= target_date`
  - [ ] 2.3 Join with `assets` table for asset name/details
  - [ ] 2.4 Map to ActionItem with priority_level="critical", category="safety"
  - [ ] 2.5 Sort by severity (critical > high > medium > low) then by timestamp (newest first)

- [ ] Task 3: Implement OEE Gap Filter (AC: #3)
  - [ ] 3.1 Create `_get_oee_actions(target_oee: Decimal)` method
  - [ ] 3.2 Query `daily_summaries` WHERE `oee_percentage < target_oee` AND `report_date = target_date`
  - [ ] 3.3 Calculate OEE gap: `gap = target_oee - oee_percentage`
  - [ ] 3.4 Map to ActionItem with priority based on gap severity (>20% = high, >10% = medium, else low)
  - [ ] 3.5 Sort by gap percentage descending

- [ ] Task 4: Implement Financial Loss Filter (AC: #4)
  - [ ] 4.1 Create `_get_financial_actions(threshold: Decimal)` method
  - [ ] 4.2 Query `daily_summaries` WHERE `financial_loss_dollars > threshold` AND `report_date = target_date`
  - [ ] 4.3 Join with `cost_centers` for context if needed
  - [ ] 4.4 Map to ActionItem with priority based on loss amount (>$5000 = high, >$2000 = medium, else low)
  - [ ] 4.5 Sort by financial_loss_dollars descending

- [ ] Task 5: Implement Combined Sorting and Deduplication (AC: #5)
  - [ ] 5.1 Create `_merge_and_prioritize(safety, oee, financial)` method
  - [ ] 5.2 Implement tier-based ordering: all safety items first, then OEE, then financial
  - [ ] 5.3 Implement asset deduplication - if asset appears in multiple categories, keep highest priority
  - [ ] 5.4 Add secondary evidence_refs for deduplicated items (shows all reasons)

- [ ] Task 6: Create ActionItem Data Model (AC: #7)
  - [ ] 6.1 Create `apps/api/app/schemas/action.py` with Pydantic models
  - [ ] 6.2 Define `ActionItem` model with all required fields
  - [ ] 6.3 Define `ActionListResponse` model with metadata
  - [ ] 6.4 Define `ActionCategory` and `PriorityLevel` enums

- [ ] Task 7: Create Configuration (AC: #6)
  - [ ] 7.1 Add threshold constants to `apps/api/app/core/config.py`
  - [ ] 7.2 Add environment variables: `TARGET_OEE_PERCENTAGE`, `FINANCIAL_LOSS_THRESHOLD`
  - [ ] 7.3 Add `.env.example` entries for new configuration
  - [ ] 7.4 Support runtime override via API parameters

- [ ] Task 8: Create API Endpoints (AC: #8)
  - [ ] 8.1 Create `apps/api/app/api/endpoints/actions.py` router
  - [ ] 8.2 Implement `GET /api/actions/daily` endpoint
  - [ ] 8.3 Add query parameters: `date`, `limit`, `category_filter`
  - [ ] 8.4 Register router in main.py
  - [ ] 8.5 Add OpenAPI documentation

- [ ] Task 9: Implement Caching Strategy (AC: #9)
  - [ ] 9.1 Add optional caching layer for action list results
  - [ ] 9.2 Cache key based on date to serve consistent results throughout day
  - [ ] 9.3 Cache invalidation on new data ingestion (via Pipeline A completion hook)

- [ ] Task 10: Handle Edge Cases and Empty States (AC: #10)
  - [ ] 10.1 Handle empty results gracefully - return valid empty list structure
  - [ ] 10.2 Handle missing data (no daily_summaries for date) with clear error message
  - [ ] 10.3 Add logging for filter results (how many items from each category)

- [ ] Task 11: Write Tests (AC: All)
  - [ ] 11.1 Unit tests for each filter method with mock data
  - [ ] 11.2 Unit tests for combined sorting logic
  - [ ] 11.3 Unit tests for threshold configuration
  - [ ] 11.4 Unit tests for deduplication logic
  - [ ] 11.5 Integration tests for API endpoint
  - [ ] 11.6 Test empty state handling
  - [ ] 11.7 Test edge cases: all safety, no safety, mixed categories

## Dev Notes

### Architecture Compliance

This story implements **FR3 (Action Engine)** from the PRD:
> "Generate a natural-language 'Daily Action List' prioritizing issues based on Financial Impact and Safety Risk."

**Location:** `apps/api/` (Python FastAPI Backend)
- **Service Module:** `app/services/action_engine.py` - Core prioritization logic
- **API Endpoints:** `app/api/endpoints/actions.py` - REST API
- **Schemas:** `app/schemas/action.py` - Pydantic data models

### Technical Requirements

**Priority Tier System:**

```python
# Priority levels (highest to lowest)
class PriorityLevel(str, Enum):
    CRITICAL = "critical"  # Safety events only
    HIGH = "high"          # Severe OEE gap (>20%) or high financial loss (>$5000)
    MEDIUM = "medium"      # Moderate gaps/losses
    LOW = "low"            # Minor issues still above threshold

# Category ordering (absolute priority)
class ActionCategory(str, Enum):
    SAFETY = "safety"      # Tier 1 - Always first
    OEE = "oee"            # Tier 2 - After all safety
    FINANCIAL = "financial" # Tier 3 - After all OEE
```

**Action Engine Logic Implementation:**

```python
from decimal import Decimal
from datetime import date
from typing import List, Optional
from enum import Enum

class ActionEngine:
    def __init__(
        self,
        supabase_client,
        target_oee: Decimal = Decimal("85.0"),
        financial_threshold: Decimal = Decimal("1000.0")
    ):
        self.supabase = supabase_client
        self.target_oee = target_oee
        self.financial_threshold = financial_threshold

    def generate_action_list(self, target_date: date) -> List[ActionItem]:
        # Step 1: Gather actions from each category
        safety_actions = self._get_safety_actions(target_date)
        oee_actions = self._get_oee_actions(target_date)
        financial_actions = self._get_financial_actions(target_date)

        # Step 2: Merge with tier-based priority and deduplication
        return self._merge_and_prioritize(
            safety_actions,
            oee_actions,
            financial_actions
        )

    def _merge_and_prioritize(
        self,
        safety: List[ActionItem],
        oee: List[ActionItem],
        financial: List[ActionItem]
    ) -> List[ActionItem]:
        # Deduplicate: if asset appears in multiple, keep highest priority
        seen_assets = set()
        result = []

        # Process in priority order: Safety > OEE > Financial
        for actions in [safety, oee, financial]:
            for action in actions:
                if action.asset_id not in seen_assets:
                    result.append(action)
                    seen_assets.add(action.asset_id)
                else:
                    # Add as secondary evidence to existing item
                    existing = next(a for a in result if a.asset_id == action.asset_id)
                    existing.evidence_refs.extend(action.evidence_refs)

        return result
```

**Response Schema:**

```python
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

class ActionCategory(str, Enum):
    SAFETY = "safety"
    OEE = "oee"
    FINANCIAL = "financial"

class PriorityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EvidenceRef(BaseModel):
    source_table: str  # "safety_events", "daily_summaries"
    record_id: str
    metric_name: str
    metric_value: str
    context: Optional[str]

class ActionItem(BaseModel):
    id: str  # Generated UUID
    asset_id: str
    asset_name: str
    priority_level: PriorityLevel
    category: ActionCategory
    primary_metric_value: str  # e.g., "OEE: 72.5%" or "Loss: $3,240"
    recommendation_text: str   # Brief action recommendation
    evidence_summary: str      # One-line evidence description
    evidence_refs: List[EvidenceRef]
    created_at: datetime

class ActionListResponse(BaseModel):
    actions: List[ActionItem]
    generated_at: datetime
    report_date: date
    total_count: int
    counts_by_category: dict  # {"safety": 2, "oee": 5, "financial": 3}
```

### Data Sources and Queries

**Safety Events Query:**
```python
# Get unresolved safety events for target date
safety_query = """
SELECT
    se.id,
    se.asset_id,
    a.name as asset_name,
    se.event_timestamp,
    se.reason_code,
    se.severity,
    se.description
FROM safety_events se
JOIN assets a ON se.asset_id = a.id
WHERE se.is_resolved = FALSE
  AND DATE(se.event_timestamp) = :target_date
ORDER BY
    CASE se.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    se.event_timestamp DESC
"""
```

**OEE Gap Query:**
```python
# Get assets with OEE below target
oee_query = """
SELECT
    ds.id,
    ds.asset_id,
    a.name as asset_name,
    ds.oee_percentage,
    :target_oee - ds.oee_percentage as oee_gap,
    ds.actual_output,
    ds.target_output
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE ds.report_date = :target_date
  AND ds.oee_percentage < :target_oee
ORDER BY (ds.target_output - ds.actual_output) DESC
"""
```

**Financial Loss Query:**
```python
# Get assets with financial loss above threshold
financial_query = """
SELECT
    ds.id,
    ds.asset_id,
    a.name as asset_name,
    ds.financial_loss_dollars,
    ds.downtime_minutes,
    ds.waste_count,
    cc.standard_hourly_rate
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
LEFT JOIN cost_centers cc ON ds.asset_id = cc.asset_id
WHERE ds.report_date = :target_date
  AND ds.financial_loss_dollars > :threshold
ORDER BY ds.financial_loss_dollars DESC
"""
```

### UX Integration Requirements

**Evidence Card Pattern:**
From UX Design - Design Principle #2 (Insight + Evidence):
> "Action items are presented as cards: Recommendation (Left) + Supporting Metric/Chart (Right)."

The ActionItem structure supports this by providing:
- `recommendation_text` - The action to take (left side of card)
- `primary_metric_value` - The key metric (right side highlight)
- `evidence_refs` - Links to supporting data for drill-down

**Priority Color Mapping:**
```
critical -> Safety Red (#DC2626) - EXCLUSIVE to safety
high     -> Orange (#EA580C)
medium   -> Yellow (#CA8A04)
low      -> Blue (#2563EB)
```

### Environment Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TARGET_OEE_PERCENTAGE` | Threshold for OEE filtering | No | 85.0 |
| `FINANCIAL_LOSS_THRESHOLD` | Min $ loss to include | No | 1000.0 |
| `OEE_HIGH_GAP_THRESHOLD` | Gap % for "high" priority | No | 20.0 |
| `OEE_MEDIUM_GAP_THRESHOLD` | Gap % for "medium" priority | No | 10.0 |
| `FINANCIAL_HIGH_THRESHOLD` | $ loss for "high" priority | No | 5000.0 |
| `FINANCIAL_MEDIUM_THRESHOLD` | $ loss for "medium" priority | No | 2000.0 |

### Project Structure Notes

Files to create:
```
apps/api/
├── app/
│   ├── services/
│   │   └── action_engine.py    # NEW: Action Engine service
│   ├── api/
│   │   └── endpoints/
│   │       └── actions.py      # NEW: Action list endpoints
│   ├── schemas/
│   │   └── action.py           # NEW: ActionItem, ActionListResponse
│   └── core/
│       └── config.py           # MODIFY: Add threshold settings
├── tests/
│   ├── services/
│   │   └── test_action_engine.py  # NEW: Unit tests
│   └── api/
│       └── test_actions.py        # NEW: Integration tests
└── .env.example                    # ADD: Threshold config vars
```

### NFR Compliance

- **NFR1 (Accuracy):** Each action item includes `evidence_refs` linking to specific source data records - prevents AI hallucination by grounding recommendations in data
- **NFR2 (Latency):** Queries should complete within seconds; consider caching for repeated requests within same day
- **NFR3 (Read-Only):** All source data from MSSQL remains read-only; action engine reads only from Supabase analytical cache

### Dependencies

**Story Dependencies (Required before this story):**
- Story 1.3 (Plant Object Model Schema) - Provides `assets` table
- Story 1.4 (Analytical Cache Schema) - Provides `daily_summaries`, `safety_events` tables
- Story 2.6 (Safety Alert System) - Populates `safety_events` table
- Story 2.7 (Financial Impact Calculator) - Populates `financial_loss_dollars` in `daily_summaries`
- Story 2.1 (Batch Data Pipeline) - Populates `daily_summaries` with OEE data

**Enables (Stories that depend on this):**
- Story 3.2 (Daily Action List API) - Uses this engine to serve the frontend
- Story 3.3 (Action List Primary View) - Displays the action list in UI
- Story 3.4 (Insight + Evidence Cards) - Consumes action item structure
- Story 3.5 (Smart Summary Generator) - Uses action list as context input

### Anti-Patterns to Avoid

1. **DO NOT** hardcode threshold values - use configuration for flexibility
2. **DO NOT** mix priority levels across categories - Safety is ALWAYS first
3. **DO NOT** ignore deduplication - same asset should not appear multiple times
4. **DO NOT** return raw database records - transform to ActionItem structure
5. **DO NOT** omit evidence_refs - NFR1 requires data citations
6. **DO NOT** use "Safety Red" color for non-safety items (UX requirement)
7. **DO NOT** block on LLM calls in this story - natural language generation is Story 3.5

### Testing Strategy

1. **Unit Tests - Filter Methods:**
   - Test safety filter with mock safety_events data
   - Test OEE filter with various gap scenarios
   - Test financial filter with various loss amounts
   - Test threshold boundary conditions (exactly at threshold)

2. **Unit Tests - Prioritization:**
   - Test that safety always appears before OEE
   - Test that OEE always appears before financial
   - Test deduplication keeps highest priority category
   - Test sorting within each category

3. **Integration Tests:**
   - Test API endpoint with test database
   - Test query parameter handling (date, limit, category_filter)
   - Test empty state response structure

4. **Test Data Scenarios:**
   ```python
   # Scenario 1: All categories have items
   # Expected: Safety first, then OEE, then Financial

   # Scenario 2: Only safety events
   # Expected: All items marked critical, sorted by severity

   # Scenario 3: No items match filters
   # Expected: Empty list with valid metadata

   # Scenario 4: Same asset in safety + OEE
   # Expected: Asset appears once as safety (critical),
   #           OEE data added to evidence_refs
   ```

### Previous Story Intelligence

From Epic 2 stories, the following patterns were established:
- Supabase queries use the service pattern in `app/services/`
- API endpoints follow RESTful conventions in `app/api/endpoints/`
- Pydantic models go in `app/schemas/`
- Environment config in `app/core/config.py`
- Tests mirror the source structure in `tests/`

### References

- [Source: _bmad/bmm/data/prd.md#FR3 (Action Engine)] - Functional requirement definition
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture - Action Engine Logic] - Algorithm specification
- [Source: _bmad/bmm/data/ux-design.md#2. Design Principles] - Insight + Evidence card pattern
- [Source: _bmad/bmm/data/ux-design.md#2. Design Principles] - Industrial High-Contrast, Safety Red exclusivity
- [Source: _bmad-output/planning-artifacts/epic-3.md#Story 3.1] - Story definition
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3] - Epic context and scope
- [Source: _bmad-output/implementation-artifacts/2-6-safety-alert-system.md] - Safety events table structure
- [Source: _bmad-output/implementation-artifacts/2-7-financial-impact-calculator.md] - Financial calculation patterns
- [Source: _bmad-output/implementation-artifacts/1-4-analytical-cache-schema.md] - Database schema definitions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
