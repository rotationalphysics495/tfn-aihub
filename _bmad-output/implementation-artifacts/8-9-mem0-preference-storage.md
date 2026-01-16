# Story 8.9: Mem0 Preference Storage

Status: ready-for-dev

## Story

As a **system component**,
I want **user preferences stored in both Supabase and Mem0**,
So that **preferences are queryable AND available for AI context**.

## Acceptance Criteria

1. **Given** a user saves preferences **When** the save operation completes **Then** preferences are written to `user_preferences` table immediately (FR40) **And** relevant context is synced to Mem0 within 5 seconds

2. **Given** preferences are stored in Mem0 **When** the AI agent processes a request **Then** Mem0 context includes semantic descriptions like "User prefers grinding updates first because that's where most issues occur" **And** preferences influence response personalization (FR41)

3. **Given** a user updates their area order **When** the update is saved **Then** Supabase record is updated immediately **And** Mem0 context reflects the change **And** next briefing uses new order

4. **Given** the user has a conversation history **When** preferences sync to Mem0 **Then** the sync includes semantic context about why preferences were set **And** historical preference versions are maintained (NFR26)

5. **Given** Mem0 sync fails **When** preferences are saved **Then** Supabase save succeeds (primary storage) **And** sync is retried via background job **And** no user-facing error is shown

## Tasks / Subtasks

- [ ] Task 1: Create Supabase `user_preferences` table (AC: #1, #3)
  - [ ] 1.1 Create migration file `20260116_001_user_preferences.sql`
  - [ ] 1.2 Define schema: user_id (PK, FK auth.users), role, area_order[], detail_level, voice_enabled, updated_at
  - [ ] 1.3 Add RLS policies: users can only read/write their own preferences
  - [ ] 1.4 Add updated_at trigger using existing `update_updated_at_column()` function

- [ ] Task 2: Create preference Pydantic models (AC: #1, #2)
  - [ ] 2.1 Create `apps/api/app/models/preferences.py`
  - [ ] 2.2 Define `UserPreferences` schema with validation
  - [ ] 2.3 Define `PreferenceUpdate` schema for partial updates
  - [ ] 2.4 Define `Mem0PreferenceContext` schema for AI-ready format

- [ ] Task 3: Implement PreferenceService CRUD (AC: #1, #3)
  - [ ] 3.1 Create `apps/api/app/services/preferences/__init__.py`
  - [ ] 3.2 Create `apps/api/app/services/preferences/service.py`
  - [ ] 3.3 Implement `get_preferences(user_id)` - returns defaults if not found
  - [ ] 3.4 Implement `save_preferences(user_id, preferences)` - upsert pattern
  - [ ] 3.5 Implement `update_preferences(user_id, partial)` - merge updates

- [ ] Task 4: Implement Mem0 sync logic (AC: #2, #4)
  - [ ] 4.1 Create `apps/api/app/services/preferences/sync.py`
  - [ ] 4.2 Implement `sync_preferences_to_mem0(user_id, preferences)` - creates semantic context
  - [ ] 4.3 Implement semantic formatting: convert structured prefs to natural language
  - [ ] 4.4 Implement retry logic for Mem0 failures with exponential backoff
  - [ ] 4.5 Implement version history via Mem0 metadata timestamps

- [ ] Task 5: Create Preference API endpoints (AC: #1, #3, #5)
  - [ ] 5.1 Create `apps/api/app/api/preferences.py`
  - [ ] 5.2 Implement `GET /api/v1/preferences` - get current user preferences
  - [ ] 5.3 Implement `PUT /api/v1/preferences` - save full preferences
  - [ ] 5.4 Implement `PATCH /api/v1/preferences` - partial update
  - [ ] 5.5 Wire sync_to_mem0 as background task after Supabase write

- [ ] Task 6: Write tests (All AC)
  - [ ] 6.1 Create `apps/api/tests/services/preferences/test_service.py`
  - [ ] 6.2 Create `apps/api/tests/services/preferences/test_sync.py`
  - [ ] 6.3 Create `apps/api/tests/api/test_preferences.py`
  - [ ] 6.4 Test graceful degradation when Mem0 unavailable

## Dev Notes

### Architecture Patterns

**Dual Storage Strategy (from architecture/voice-briefing.md):**
- Supabase `user_preferences` for structured queries (role filtering, area order sorting)
- Mem0 for AI context enrichment (semantic preference descriptions)
- Sync pattern: Write to Supabase immediately, background job syncs to Mem0 within 5 seconds (NFR11)

**Service Organization:**
```
apps/api/app/services/preferences/
├── __init__.py          # Package init, exports PreferenceService
├── service.py           # PreferenceService class - Supabase CRUD
└── sync.py              # Mem0 sync logic - semantic context formatting
```

### Database Schema (from architecture/voice-briefing.md)

```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    role TEXT,  -- Denormalized for quick access
    area_order TEXT[],  -- ['Grinding', 'Packing', ...]
    detail_level TEXT CHECK (detail_level IN ('summary', 'detailed')),
    voice_enabled BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**RLS Policies:**
- Users can SELECT/UPDATE only their own row (WHERE user_id = auth.uid())
- Service role has full access for admin operations

### Existing Mem0 Integration Patterns

**REUSE existing MemoryService** from `apps/api/app/services/memory/mem0_service.py`:
- Singleton pattern with lazy initialization
- Uses `memory_service.add_memory()` for storing context
- Stores messages with `user_id` from JWT claims
- Uses metadata for additional context (asset_id, timestamp, etc.)

**Key patterns to follow:**
```python
# From mem0_service.py - REUSE this pattern
await memory_service.add_memory(
    messages=[{"role": "system", "content": semantic_context}],
    user_id=user_id,
    metadata={"preference_type": "area_order", "timestamp": datetime.utcnow().isoformat()}
)
```

### Semantic Context Formatting

**DO NOT store raw key-value pairs in Mem0.** Transform to natural language:

| Structured Preference | Semantic Mem0 Content |
|-----------------------|----------------------|
| `area_order: ["Grinding", "Packing", "Roasting"]` | "User prefers to hear about Grinding first, then Packing, then Roasting in their briefings" |
| `detail_level: "summary"` | "User prefers concise summary briefings rather than detailed reports" |
| `voice_enabled: true` | "User prefers voice delivery for briefings" |
| `role: "supervisor"` | "User is a Supervisor with scoped access to assigned assets only" |

**Include WHY when available** (from onboarding or conversation):
- "User prefers grinding updates first because that's where most issues occur"
- "User disabled voice because they usually review in quiet office settings"

### API Endpoint Patterns

**Follow existing FastAPI patterns from `apps/api/app/api/`:**

```python
# apps/api/app/api/preferences.py
from fastapi import APIRouter, Depends, BackgroundTasks
from app.core.auth import get_current_user
from app.services.preferences.service import PreferenceService
from app.services.preferences.sync import sync_preferences_to_mem0

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])

@router.get("")
async def get_preferences(user = Depends(get_current_user)):
    """Get current user preferences."""
    service = PreferenceService()
    return await service.get_preferences(user.id)

@router.put("")
async def save_preferences(
    preferences: UserPreferences,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Save user preferences, sync to Mem0 in background."""
    service = PreferenceService()
    result = await service.save_preferences(user.id, preferences)
    # Fire-and-forget Mem0 sync
    background_tasks.add_task(sync_preferences_to_mem0, user.id, preferences)
    return result
```

### Error Handling & Graceful Degradation

**Mem0 failures must NOT block preference saves:**
1. Write to Supabase first (primary, synchronous)
2. Trigger Mem0 sync as background task
3. If Mem0 fails: log error, schedule retry, but return success to user
4. Implement exponential backoff: 1s, 2s, 4s, 8s, max 3 retries

**Follow MemoryService error pattern:**
```python
# From mem0_service.py - graceful degradation
except Exception as e:
    logger.error(f"Memory search failed for user {user_id}: {e}")
    return []  # Return empty on failure, don't raise
```

### Testing Requirements

**Unit Tests:**
- `test_preference_crud()` - CRUD operations with Supabase mocked
- `test_semantic_formatting()` - verify natural language transformation
- `test_mem0_sync_success()` - verify Mem0 integration
- `test_mem0_sync_failure_graceful()` - verify graceful degradation
- `test_preference_defaults()` - verify defaults when no record exists

**Integration Tests:**
- `test_api_get_preferences()` - GET endpoint with auth
- `test_api_save_preferences()` - PUT endpoint triggers sync
- `test_api_partial_update()` - PATCH merges correctly

### Project Structure Notes

**File Locations (MUST follow):**
- Models: `apps/api/app/models/preferences.py`
- Service: `apps/api/app/services/preferences/service.py`
- Sync: `apps/api/app/services/preferences/sync.py`
- API: `apps/api/app/api/preferences.py`
- Migration: `supabase/migrations/20260116_001_user_preferences.sql`
- Tests: `apps/api/tests/services/preferences/` and `apps/api/tests/api/`

**Naming Conventions:**
- Python files: `snake_case.py`
- Classes: `PascalCase` (e.g., `PreferenceService`, `UserPreferences`)
- Database tables: `snake_case` (e.g., `user_preferences`)
- API routes: `/api/v1/preferences`

### Default Preferences

When `user_preferences` record doesn't exist, return defaults:
```python
DEFAULT_PREFERENCES = {
    "role": "plant_manager",  # Safest default
    "area_order": [
        "Packing", "Rychigers", "Grinding", "Powder",
        "Roasting", "Green Bean", "Flavor Room"
    ],
    "detail_level": "summary",
    "voice_enabled": True
}
```

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#User-Preferences-Architecture]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Consistency-Rules]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR35-FR41]
- [Source: apps/api/app/services/memory/mem0_service.py - existing Mem0 patterns]
- [Source: supabase/migrations/20260106000000_plant_object_model.sql - RLS patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

