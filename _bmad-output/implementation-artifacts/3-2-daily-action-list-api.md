# Story 3.2: Daily Action List API

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **a backend API endpoint that generates a prioritized list of action items based on safety events, OEE performance, and financial impact**,
so that **I can immediately see the most critical issues requiring my attention when I log in each morning**.

## Acceptance Criteria

1. **AC1: Action List Endpoint Exists**
   - GIVEN the backend API is running
   - WHEN a GET request is made to `/api/v1/actions/daily`
   - THEN a JSON response is returned with HTTP 200 status

2. **AC2: Data Source Integration**
   - GIVEN the API endpoint is called
   - WHEN generating action items
   - THEN the system queries `daily_summaries`, `safety_events`, and `cost_centers` tables from Supabase

3. **AC3: Safety Prioritization Filter**
   - GIVEN action items are being generated
   - WHEN any `safety_events` exist for the current day
   - THEN those safety-related actions appear FIRST in the response list (Safety > 0 filter)

4. **AC4: OEE Below Target Filter**
   - GIVEN action items are being generated
   - WHEN an asset's OEE from `daily_summaries` is below its target from `shift_targets`
   - THEN an action item is generated for that asset flagging underperformance

5. **AC5: Financial Loss Threshold Filter**
   - GIVEN action items are being generated
   - WHEN calculated financial loss exceeds a configurable threshold
   - THEN an action item is generated highlighting the financial impact

6. **AC6: Sorting Order**
   - GIVEN multiple action items are generated
   - WHEN the response is constructed
   - THEN items are sorted: (1) Safety issues first, (2) Then by Financial Impact descending

7. **AC7: Response Schema**
   - GIVEN the endpoint returns successfully
   - WHEN the response is parsed
   - THEN each action item contains: `id`, `priority_rank`, `category` (safety|oee|financial), `asset_id`, `asset_name`, `title`, `description`, `financial_impact_usd`, `evidence_refs[]`, `created_at`

8. **AC8: Authentication Required**
   - GIVEN an unauthenticated request
   - WHEN the endpoint is called without a valid JWT
   - THEN HTTP 401 Unauthorized is returned

9. **AC9: Evidence Citations (NFR1 Compliance)**
   - GIVEN an action item is generated
   - WHEN the response includes that item
   - THEN `evidence_refs` array contains specific data point references (table, column, value) to prevent AI hallucination

## Tasks / Subtasks

- [ ] Task 1: Create Action Item Pydantic Models (AC: 7)
  - [ ] 1.1 Define `ActionItem` response model with all required fields
  - [ ] 1.2 Define `ActionCategory` enum (safety, oee, financial)
  - [ ] 1.3 Define `EvidenceRef` model for data citations
  - [ ] 1.4 Define `DailyActionListResponse` wrapper model

- [ ] Task 2: Implement Action Engine Service (AC: 2, 3, 4, 5, 6)
  - [ ] 2.1 Create `apps/api/app/services/action_engine.py` service file
  - [ ] 2.2 Implement `get_safety_actions()` - query safety_events, return safety action items
  - [ ] 2.3 Implement `get_oee_actions()` - compare daily_summaries OEE vs shift_targets
  - [ ] 2.4 Implement `get_financial_actions()` - calculate financial loss from cost_centers
  - [ ] 2.5 Implement `generate_daily_actions()` - orchestrate all filters and apply sorting logic
  - [ ] 2.6 Implement evidence reference generation for each action item

- [ ] Task 3: Create API Endpoint (AC: 1, 7, 8)
  - [ ] 3.1 Create `apps/api/app/api/endpoints/actions.py` router file
  - [ ] 3.2 Implement `GET /api/v1/actions/daily` endpoint
  - [ ] 3.3 Add Supabase Auth JWT dependency for authentication
  - [ ] 3.4 Register router in main FastAPI app

- [ ] Task 4: Write Unit Tests (AC: All)
  - [ ] 4.1 Test action item model serialization
  - [ ] 4.2 Test safety prioritization logic with mock data
  - [ ] 4.3 Test OEE filtering logic
  - [ ] 4.4 Test financial threshold logic
  - [ ] 4.5 Test sorting algorithm (safety first, then financial)
  - [ ] 4.6 Test authentication requirement (401 for missing token)

- [ ] Task 5: Write Integration Tests (AC: 1, 2)
  - [ ] 5.1 Test endpoint with seeded database data
  - [ ] 5.2 Test response matches expected schema
  - [ ] 5.3 Test evidence_refs contain valid table/column references

## Dev Notes

### Architecture Compliance

**API Location:** This endpoint MUST be created in `apps/api/app/api/endpoints/actions.py`

**Service Location:** Business logic MUST be in `apps/api/app/services/action_engine.py`

**Pattern:** Follow the "Sidebar Architecture" - FastAPI backend is the system's brain, orchestrating data from Supabase.

**Authentication:** Use Supabase Auth JWT validation as a FastAPI dependency. Example pattern:
```python
from fastapi import Depends, HTTPException
from app.core.security import get_current_user

@router.get("/daily")
async def get_daily_actions(current_user = Depends(get_current_user)):
    # current_user is validated via Supabase JWT
    ...
```

### Database Schema Context

**Tables to Query (Supabase PostgreSQL):**

1. **`daily_summaries`** - Contains T-1 processed report data
   - Fields: asset_id, date, oee_percentage, waste_percentage, financial_loss_usd

2. **`safety_events`** - Persistent log of safety issues
   - Fields: id, asset_id, event_type, reason_code, detected_at, resolved, severity

3. **`cost_centers`** - Financial calculation reference
   - Fields: id, asset_id, standard_hourly_rate

4. **`shift_targets`** - Target OEE values
   - Fields: id, asset_id, target_output, target_oee

5. **`assets`** - Asset reference data
   - Fields: id, name, source_id, area

### Action Engine Logic (from Architecture doc Section 7)

```python
# Pseudo-code for action generation
def generate_daily_actions():
    actions = []

    # Priority 1: Safety Events (ALWAYS first)
    safety_events = query_safety_events(date=today, resolved=False)
    for event in safety_events:
        actions.append(ActionItem(
            category="safety",
            priority_rank=0,  # Highest priority
            ...
        ))

    # Priority 2: OEE Below Target
    for summary in daily_summaries:
        target = get_shift_target(summary.asset_id)
        if summary.oee_percentage < target.target_oee:
            actions.append(ActionItem(
                category="oee",
                financial_impact=calculate_loss(summary, cost_center),
                ...
            ))

    # Priority 3: Financial Loss Above Threshold
    FINANCIAL_THRESHOLD = 1000.00  # USD - make configurable
    for summary in daily_summaries:
        if summary.financial_loss_usd > FINANCIAL_THRESHOLD:
            actions.append(ActionItem(
                category="financial",
                ...
            ))

    # Sort: Safety first (priority_rank=0), then by financial_impact descending
    actions.sort(key=lambda x: (x.priority_rank, -x.financial_impact_usd))

    return actions
```

### NFR1 Compliance: Evidence Citations

Every action item MUST include `evidence_refs` array with specific data citations:

```python
evidence_refs = [
    EvidenceRef(
        table="daily_summaries",
        column="oee_percentage",
        value="72.5",
        record_id="uuid-here"
    ),
    EvidenceRef(
        table="shift_targets",
        column="target_oee",
        value="85.0",
        record_id="uuid-here"
    )
]
```

This prevents AI hallucination by linking every recommendation to raw data.

### Technical Stack Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Required for FastAPI async |
| FastAPI | 0.109+ | Use async endpoints |
| Pydantic | v2 | For request/response models |
| SQLAlchemy | Latest | For Supabase PostgreSQL queries |
| supabase-py | Latest | Alternative to raw SQLAlchemy if preferred |

### Project Structure Notes

- Alignment with unified project structure: `apps/api/` for all backend code
- Endpoint pattern: `/api/v1/{resource}/{action}`
- Service layer separation: Keep business logic in `services/`, HTTP logic in `api/endpoints/`
- Config via environment variables (Railway Secrets in production, `.env` local)

### File Creation Checklist

```
apps/api/app/
├── api/
│   └── endpoints/
│       └── actions.py          # NEW - Daily Action List endpoint
├── models/
│   └── action.py               # NEW - Pydantic models for actions
├── services/
│   └── action_engine.py        # NEW - Action generation business logic
└── tests/
    ├── test_action_models.py   # NEW - Unit tests for models
    ├── test_action_engine.py   # NEW - Unit tests for service
    └── test_actions_api.py     # NEW - Integration tests for endpoint
```

### Dependencies on Prior Stories

- **Story 3.1 (Action Engine Logic):** Contains the core filter/sort algorithm. This story implements the API wrapper around that logic.
- **Epic 2 Stories:** Must have `daily_summaries`, `safety_events` tables populated with data
- **Epic 1 Stories:** Database schemas and Supabase connection must be configured

### References

- [Source: _bmad/bmm/data/architecture.md#Section-7-AI-Memory-Architecture] - Action Engine Logic definition
- [Source: _bmad/bmm/data/architecture.md#Section-5-Data-Models] - Database schema definitions
- [Source: _bmad/bmm/data/architecture.md#Section-8-Security] - JWT authentication pattern
- [Source: _bmad/bmm/data/prd.md#Section-2-Requirements] - FR3 (Action Engine), NFR1 (Accuracy)
- [Source: _bmad-output/planning-artifacts/epic-3.md] - Epic 3 stories and dependencies
- [Source: _bmad/bmm/data/ux-design.md#Section-2] - "Action First" design principle

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

(To be filled during implementation - list all files created/modified)
