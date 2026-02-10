# Story 16.6: AI Summary with Action Plan Context

Status: ready-for-dev

## Story

As a Plant Manager,
I want the smart summary to mention active action plans when relevant assets appear,
so that I know the team is already working on recurring issues.

## Acceptance Criteria

1. **AC1: Active action plan mention in summary** — Given the smart summary is generated for a date, when an asset in the action items has an active action plan (status = 'open' or 'in_progress'), then the summary mentions it contextually (e.g., "Grinder 5 OEE is still below target -- note that a corrective action plan is in progress (bearing replacement, due Friday)").

2. **AC2: Recently verified plan correlation** — Given an action plan was recently verified (completed within last 7 days), when the summary is generated and the asset's metric improved, then the summary may note the correlation (e.g., "Grinder 5 OEE improved 5 points since bearing replacement last Monday").

3. **AC3: Context builder fetches action plans** — Given the ContextBuilder assembles data for summary generation, when action plans exist for assets appearing in today's action items, then the active action plans are included in the `SummaryContext` object passed to the LLM.

4. **AC4: Prompt template updated** — Given the prompt template is rendered with data, when action plan context is available, then a new `=== ACTION PLAN STATUS ===` section is included in the data prompt with plan titles, statuses, due dates, and associated asset names.

5. **AC5: Fallback summary includes action plan badges** — Given the LLM is unavailable and a fallback summary is generated, when assets have active action plans, then the fallback summary includes a brief action plan note under the relevant asset entry.

6. **AC6: No action plan data graceful handling** — Given no action plans exist or the `action_plans` table query fails, when the summary is generated, then the summary generates normally without action plan references and no errors are raised.

## Tasks / Subtasks

- [ ] Task 1: Add `action_plans` field to `SummaryContext` model (AC: #3)
  - [ ] 1.1 Add `action_plans: List[Dict[str, Any]]` field to `SummaryContext` in `context_builder.py`
  - [ ] 1.2 Add `recently_verified_plans: List[Dict[str, Any]]` field for 7-day lookback
- [ ] Task 2: Implement `fetch_active_action_plans()` in `ContextBuilder` (AC: #3)
  - [ ] 2.1 Query `action_plans` table for plans with status IN ('open', 'in_progress') joined to assets appearing in today's action items
  - [ ] 2.2 Query `action_plans` table for recently verified plans (verified_at within last 7 days)
  - [ ] 2.3 Enrich plans with asset names via existing `_enrich_with_asset_names()` helper
  - [ ] 2.4 Call the new fetch method in `build_context()` alongside other data fetches
  - [ ] 2.5 Handle graceful failure if `action_plans` table does not exist (AC: #6)
- [ ] Task 3: Add `format_action_plans()` to prompt templates (AC: #4)
  - [ ] 3.1 Create `format_action_plans(action_plans, recently_verified_plans)` function in `prompts.py`
  - [ ] 3.2 Format active plans: title, asset name, category, status, due date, days until due
  - [ ] 3.3 Format recently verified plans: title, asset name, verified date, corrective action taken
  - [ ] 3.4 Add `{action_plan_data}` placeholder to `DATA_TEMPLATE_DEFAULT`
  - [ ] 3.5 Pass action plan data to `render_data_prompt()` function
- [ ] Task 4: Update system prompt for action plan awareness (AC: #1, #2)
  - [ ] 4.1 Add instruction to `SYSTEM_PROMPT_DEFAULT` telling the LLM to reference active action plans when discussing assets that have them
  - [ ] 4.2 Add instruction to correlate recently verified plans with metric improvements
- [ ] Task 5: Update fallback summary to include action plan notes (AC: #5)
  - [ ] 5.1 In `generate_fallback_summary()`, query action plans for assets in below-target list
  - [ ] 5.2 Append action plan status note to relevant asset bullets (e.g., "Action plan: bearing replacement (due Fri)")
- [ ] Task 6: Update `render_data_prompt()` signature and callers (AC: #4)
  - [ ] 6.1 Add `action_plans` and `recently_verified_plans` parameters to `render_data_prompt()`
  - [ ] 6.2 Update `_generate_with_llm()` in `smart_summary.py` to pass action plan context from `SummaryContext`
- [ ] Task 7: Write tests (AC: #1-#6)
  - [ ] 7.1 Unit test: `fetch_active_action_plans()` returns active plans for matching asset_ids
  - [ ] 7.2 Unit test: `fetch_active_action_plans()` returns empty list gracefully when table missing
  - [ ] 7.3 Unit test: `format_action_plans()` produces expected prompt text
  - [ ] 7.4 Unit test: `render_data_prompt()` includes action plan section when plans exist
  - [ ] 7.5 Unit test: `render_data_prompt()` omits action plan section when no plans exist
  - [ ] 7.6 Unit test: fallback summary includes action plan notes for relevant assets
  - [ ] 7.7 Integration test: full `generate_smart_summary()` flow with action plan context

## Dev Notes

### Architecture & Patterns

This story modifies three existing files in the smart summary pipeline. No new files are created. The changes follow the established pattern of the existing context builder / prompt / service architecture.

**Key principle:** The action plan data flows through the same pipeline as all other summary context:
1. `ContextBuilder.build_context()` fetches data from Supabase
2. Data is stored in `SummaryContext` Pydantic model
3. `prompts.py` formats data into the LLM prompt string
4. `SmartSummaryService` orchestrates generation

### Critical Dependencies

- **Story 16.1 (Action Plans Data Model)** must be completed first -- the `action_plans` table with its columns (`id`, `title`, `status`, `asset_id`, `due_date`, `corrective_action`, `verified_at`, `verified_by`, `category`) must exist in Supabase.
- **Story 16.2 (Action Plans CRUD API)** should be completed so that action plans can actually be created and populated.
- The `action_plans` table schema is defined in Epic 16.1 with migration `supabase/migrations/0031_action_plans.sql`.

### Project Structure Notes

All changes are within the existing `apps/api/app/services/ai/` directory:

| File | Change Type | Purpose |
|------|-------------|---------|
| `apps/api/app/services/ai/context_builder.py` | Modify | Add `action_plans` + `recently_verified_plans` to `SummaryContext`; add `fetch_active_action_plans()` method |
| `apps/api/app/services/ai/prompts.py` | Modify | Add `format_action_plans()` function; update `DATA_TEMPLATE_DEFAULT` and `render_data_prompt()` |
| `apps/api/app/services/ai/smart_summary.py` | Modify | Pass action plan data through `_generate_with_llm()` and update fallback summary |

Test files:

| File | Change Type | Purpose |
|------|-------------|---------|
| `apps/api/tests/services/ai/test_context_builder.py` | Modify/Create | Tests for action plan fetching |
| `apps/api/tests/services/ai/test_prompts.py` | Modify/Create | Tests for action plan formatting |
| `apps/api/tests/services/ai/test_smart_summary.py` | Modify/Create | Tests for end-to-end integration |

### Implementation Details

#### 1. SummaryContext Model Changes (`context_builder.py`)

Add two new fields to the existing `SummaryContext` Pydantic model:

```python
action_plans: List[Dict[str, Any]] = Field(
    default_factory=list,
    description="Active action plans (open/in_progress) for assets in today's action items"
)
recently_verified_plans: List[Dict[str, Any]] = Field(
    default_factory=list,
    description="Action plans verified within last 7 days for correlation analysis"
)
```

#### 2. New Fetch Method (`context_builder.py`)

Add `fetch_active_action_plans()` to `ContextBuilder`:

```python
async def fetch_active_action_plans(
    self,
    target_date: date_type,
    asset_ids: List[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch active and recently verified action plans for given assets."""
    try:
        client = self._get_client()

        # Active plans (open or in_progress)
        active_response = client.table("action_plans").select(
            "id, title, asset_id, category, status, priority, "
            "due_date, corrective_action, root_cause"
        ).in_("asset_id", asset_ids).in_(
            "status", ["open", "in_progress"]
        ).execute()

        # Recently verified plans (within last 7 days)
        seven_days_ago = (target_date - timedelta(days=7)).isoformat()
        verified_response = client.table("action_plans").select(
            "id, title, asset_id, corrective_action, verified_at, "
            "completed_at, status"
        ).in_("asset_id", asset_ids).eq(
            "status", "verified"
        ).gte("verified_at", seven_days_ago).execute()

        return (active_response.data or [], verified_response.data or [])

    except Exception as e:
        logger.error(f"Failed to fetch action plans: {e}")
        return ([], [])
```

**Important:** The `try/except` with empty-list return ensures the summary pipeline does not break if the `action_plans` table does not exist yet (AC#6). This matches the existing error handling pattern used by `fetch_safety_events()` and other fetch methods.

#### 3. Call in `build_context()` (`context_builder.py`)

After fetching action items (which contain `asset_id` references), extract the unique asset_ids and pass them to the action plan fetch:

```python
# After action_items are fetched:
action_item_asset_ids = list(set(
    item.get("asset_id") for item in action_items if item.get("asset_id")
))
active_plans, verified_plans = await self.fetch_active_action_plans(
    target_date, action_item_asset_ids
)
# Enrich with asset names
enriched_active = self._enrich_with_asset_names(active_plans, assets)
enriched_verified = self._enrich_with_asset_names(verified_plans, assets)
```

Then include in the SummaryContext constructor:
```python
action_plans=enriched_active,
recently_verified_plans=enriched_verified,
```

#### 4. Prompt Template Changes (`prompts.py`)

Add `format_action_plans()`:

```python
def format_action_plans(
    action_plans: list,
    recently_verified_plans: list,
) -> str:
    if not action_plans and not recently_verified_plans:
        return "No active action plans for assets on today's report."

    lines = []
    if action_plans:
        lines.append("Active action plans for assets on today's report:\n")
        for plan in action_plans:
            asset_name = plan.get("asset_name", "Unknown")
            title = plan.get("title", "Untitled")
            status = plan.get("status", "unknown")
            due_date = plan.get("due_date", "no date")
            category = plan.get("category", "")
            lines.append(
                f"- {asset_name}: \"{title}\" ({category}, {status}, due {due_date})"
            )

    if recently_verified_plans:
        lines.append("\nRecently completed action plans (last 7 days):\n")
        for plan in recently_verified_plans:
            asset_name = plan.get("asset_name", "Unknown")
            title = plan.get("title", "Untitled")
            corrective = plan.get("corrective_action", "")
            verified_at = plan.get("verified_at", "")
            lines.append(
                f"- {asset_name}: \"{title}\" completed — {corrective} (verified {verified_at})"
            )

    return "\n".join(lines)
```

Update `DATA_TEMPLATE_DEFAULT` to add:

```
=== ACTION PLAN STATUS ===
{action_plan_data}
```

Add to `render_data_prompt()`:
- New parameters: `action_plans`, `recently_verified_plans`
- Call `format_action_plans()` and inject into template

#### 5. System Prompt Update (`prompts.py`)

Add to `SYSTEM_PROMPT_DEFAULT` critical requirements:

```
7. When an asset has an active action plan, mention it alongside the asset's issues
   (e.g., "Grinder 5 OEE is still below target — note that a corrective action plan
   is in progress (bearing replacement, due Friday)")
8. When a recently verified action plan exists and the asset's metrics improved,
   note the possible correlation (e.g., "Grinder 5 OEE improved 5 points since
   bearing replacement completed last Monday")
```

#### 6. Fallback Summary Update (`smart_summary.py`)

In `generate_fallback_summary()`, after building the productivity section, check if any below-target assets have active action plans:

```python
# Build action plan lookup by asset_id
plans_by_asset: dict[str, list] = {}
for plan in context.action_plans:
    aid = plan.get("asset_id", "")
    plans_by_asset.setdefault(aid, []).append(plan)

# In the productivity section loop, after building the bullet:
asset_plans = plans_by_asset.get(s.get("asset_id", ""), [])
if asset_plans:
    plan = asset_plans[0]
    bullet += f" · Action plan: {plan.get('title', '')} (due {plan.get('due_date', 'TBD')})"
```

#### 7. Wire Through `_generate_with_llm()` (`smart_summary.py`)

Update the call to `render_data_prompt()` to include the new fields:

```python
data_prompt = render_data_prompt(
    target_date=context.target_date,
    safety_events=context.safety_events,
    daily_summaries=context.daily_summaries,
    action_items=context.action_items,
    cost_centers=context.cost_centers,
    target_oee=context.target_oee,
    action_plans=context.action_plans,                       # NEW
    recently_verified_plans=context.recently_verified_plans,  # NEW
)
```

### Testing Strategy

Follow existing test patterns in `apps/api/tests/`. Use `pytest` with `unittest.mock.patch` for Supabase client mocking.

**Key test scenarios:**
1. `SummaryContext` correctly includes action plan fields (default empty)
2. `fetch_active_action_plans()` returns matching plans by asset_id
3. `fetch_active_action_plans()` returns `([], [])` on exception (table missing)
4. `format_action_plans()` formats active plans correctly
5. `format_action_plans()` formats verified plans correctly
6. `format_action_plans()` returns "No active action plans..." when both lists empty
7. `render_data_prompt()` includes `ACTION PLAN STATUS` section when plans exist
8. `render_data_prompt()` excludes section when no plans exist
9. Fallback summary includes action plan note when plans exist for below-target assets
10. End-to-end: `generate_smart_summary()` with mocked action plans produces summary referencing them

### Anti-Patterns to Avoid

- **DO NOT** create a new service file for action plan queries -- use the existing `ContextBuilder` pattern
- **DO NOT** modify the `ActionEngine` or `action_engine.py` -- this story only touches the smart summary pipeline
- **DO NOT** add a new API endpoint -- the action plan data is consumed internally by the summary generator
- **DO NOT** break the existing `render_data_prompt()` signature for callers that do not pass action plans -- use default parameter values (`action_plans=None, recently_verified_plans=None`)
- **DO NOT** fail the summary pipeline if action_plans table does not exist -- graceful degradation is critical (AC#6)

### Supabase Query Patterns

Follow the exact same Supabase client query patterns used in existing `ContextBuilder` methods:
- Use `client.table("action_plans").select(...)` pattern
- Use `.in_()` for filtering by multiple asset_ids
- Use `.eq()` / `.gte()` for status and date filters
- Return `response.data or []` pattern for empty handling
- Wrap in `try/except` with `logger.error()` and empty return

### References

- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.6] - Story requirements and acceptance criteria
- [Source: apps/api/app/services/ai/context_builder.py] - SummaryContext model and ContextBuilder class
- [Source: apps/api/app/services/ai/prompts.py] - Prompt templates and formatting functions
- [Source: apps/api/app/services/ai/smart_summary.py] - SmartSummaryService with fallback logic
- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.1] - action_plans table schema
- [Source: supabase/migrations/0025_action_followups.sql] - RLS pattern reference for action tables
- [Source: docs/architecture-api.md] - API directory structure and patterns
- [Source: docs/data-models.md] - Supabase schema patterns

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
