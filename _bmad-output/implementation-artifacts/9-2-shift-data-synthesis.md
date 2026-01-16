# Story 9.2: Shift Data Synthesis

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system component**,
I want **to automatically synthesize shift data into a handoff summary**,
So that **Supervisors don't have to manually compile information**.

## Acceptance Criteria

1. **AC#1: Tool Composition for Synthesis**
   - Given a handoff is initiated
   - When the system generates the summary (FR22)
   - Then it calls existing LangChain tools:
     - Production Status (shift output vs target)
     - Downtime Analysis (shift downtime reasons)
     - Safety Events (any incidents during shift)
     - Alert Check (active issues to watch)
   - And results are formatted into a narrative summary

2. **AC#2: Narrative Summary Structure**
   - Given synthesis completes
   - When the summary is displayed
   - Then it includes:
     - Shift performance overview
     - Issues encountered and status
     - Ongoing concerns (unresolved alerts)
     - Recommended focus for incoming shift
   - And all data includes citations (FR51, FR52)

3. **AC#3: Graceful Degradation on Tool Failure**
   - Given a tool fails during synthesis
   - When the failure is detected
   - Then the summary continues with available data
   - And missing sections are noted with "[Data unavailable]" placeholder
   - And the failure is logged for troubleshooting

4. **AC#4: Progressive Loading (15-Second Timeout)**
   - Given synthesis takes longer than expected
   - When 15 seconds elapse
   - Then partial results are shown immediately
   - And background continues to populate remaining sections
   - And UI indicates "Loading more data..." for incomplete sections

5. **AC#5: Supervisor Scope Filtering**
   - Given the outgoing supervisor has assigned assets
   - When synthesis is performed
   - Then all tool queries are filtered to supervisor's assigned assets only (FR54)
   - And the summary only includes data relevant to their scope

6. **AC#6: Citation Compliance**
   - Given any data is included in the summary
   - When displayed to the user
   - Then each data point includes a citation with source table and timestamp
   - And citations follow the established `Citation` model pattern

7. **AC#7: Shift Time Range Detection**
   - Given a handoff is initiated
   - When determining the time range
   - Then the system auto-detects shift boundaries (last 8 hours)
   - And uses shift start to current time for all tool queries

## Tasks / Subtasks

- [ ] Task 1: Create HandoffSynthesisService (AC: #1, #3, #5, #7)
  - [ ] 1.1 Create `apps/api/app/services/briefing/handoff.py` with `HandoffSynthesisService` class
  - [ ] 1.2 Implement shift time range detection (8-hour window from current time)
  - [ ] 1.3 Implement tool composition method that calls all four tools in parallel
  - [ ] 1.4 Add supervisor scope filtering via `supervisor_assignments` table lookup
  - [ ] 1.5 Implement graceful degradation with try/except per tool

- [ ] Task 2: Create Pydantic Models for Handoff Synthesis (AC: #2, #6)
  - [ ] 2.1 Add `HandoffSynthesisRequest` model to `apps/api/app/models/handoff.py`
  - [ ] 2.2 Add `HandoffSynthesisResponse` model with sections structure
  - [ ] 2.3 Add `HandoffSection` model for narrative sections
  - [ ] 2.4 Ensure all models support citation embedding

- [ ] Task 3: Implement Narrative Formatting (AC: #2)
  - [ ] 3.1 Create `apps/api/app/services/briefing/narrative.py` if not exists
  - [ ] 3.2 Implement `format_handoff_narrative()` function
  - [ ] 3.3 Create section templates for:
        - Shift performance overview
        - Issues encountered and status
        - Ongoing concerns (unresolved alerts)
        - Recommended focus for incoming shift
  - [ ] 3.4 Implement LLM-based narrative generation with consistent tone

- [ ] Task 4: Implement Progressive Loading (AC: #4)
  - [ ] 4.1 Create async task wrapper with 15-second timeout
  - [ ] 4.2 Implement partial result assembly when timeout occurs
  - [ ] 4.3 Add background task continuation for remaining tools
  - [ ] 4.4 Add streaming support or polling endpoint for completion

- [ ] Task 5: Add Synthesis Endpoint to Handoff API (AC: #1, #2)
  - [ ] 5.1 Add `POST /api/v1/briefing/handoff/synthesize` endpoint to `apps/api/app/api/handoff.py`
  - [ ] 5.2 Wire up to `HandoffSynthesisService`
  - [ ] 5.3 Add authentication and authorization middleware
  - [ ] 5.4 Return structured `HandoffSynthesisResponse`

- [ ] Task 6: Write Unit Tests (AC: #1-7)
  - [ ] 6.1 Create `apps/api/tests/services/briefing/test_handoff_synthesis.py`
  - [ ] 6.2 Test tool composition with mocked tools
  - [ ] 6.3 Test graceful degradation (simulate tool failures)
  - [ ] 6.4 Test progressive loading timeout behavior
  - [ ] 6.5 Test supervisor scope filtering
  - [ ] 6.6 Test citation generation

- [ ] Task 7: Integration Testing (AC: #1, #2, #5)
  - [ ] 7.1 Add integration test for end-to-end synthesis flow
  - [ ] 7.2 Test with real tool implementations (using test data)
  - [ ] 7.3 Verify citation integrity through the pipeline

## Dev Notes

### Relevant Architecture Patterns and Constraints

**BriefingService Pattern (from Epic 8 Architecture):**
This story should reuse the `BriefingService` pattern established in Epic 8 for morning briefings:
- NOT a `ManufacturingTool` - it's a dedicated orchestration service
- Deterministic tool sequencing for predictable narratives
- Section-based output with natural pause points
- More testable than LLM-driven tool selection

**Key Difference from Morning Briefing:**
- Morning briefing is plant-wide or supervisor-scoped, but covers ALL areas
- Handoff synthesis is supervisor-scoped and covers only THEIR shift period (last 8 hours)
- Handoff is more action-oriented ("what the next shift needs to know")

**Tool Composition Pattern:**
```python
# Pattern from implementation-patterns.md
class HandoffSynthesisService:
    """Orchestrates handoff synthesis by composing existing tools."""

    async def synthesize_shift_data(
        self,
        user_id: str,
        supervisor_assignments: List[str]  # Asset IDs
    ) -> HandoffSynthesisResponse:
        # 1. Calculate shift time range (last 8 hours)
        # 2. Call tools in parallel with timeout
        # 3. Assemble sections from tool results
        # 4. Format narrative via LLM
        # 5. Return with citations
```

### Source Tree Components to Touch

**New Files:**
- `apps/api/app/services/briefing/handoff.py` - HandoffSynthesisService
- `apps/api/app/models/handoff.py` - Pydantic models (may already exist from 9.1)
- `apps/api/tests/services/briefing/test_handoff_synthesis.py` - Unit tests

**Modified Files:**
- `apps/api/app/api/handoff.py` - Add synthesis endpoint
- `apps/api/app/services/briefing/__init__.py` - Export new service
- `apps/api/app/services/briefing/service.py` - Add handoff synthesis method (optional)

### Testing Standards Summary

**Unit Tests Required:**
- Test each tool composition independently
- Test graceful degradation with simulated tool failures
- Test timeout behavior with mocked async delays
- Test supervisor scope filtering with fixture data
- Test citation generation matches `Citation` model

**Integration Tests Required:**
- End-to-end synthesis with real tools (mocked data sources)
- Verify JSON response structure matches Pydantic models
- Verify authentication/authorization works correctly

**Test Patterns (from existing codebase):**
```python
# Pattern from test_production_status.py, test_alert_check.py
@pytest.mark.asyncio
async def test_synthesis_success(mock_data_source):
    """Test successful synthesis with all tools returning data."""
    service = HandoffSynthesisService()
    result = await service.synthesize_shift_data(
        user_id="test-user",
        supervisor_assignments=["asset-1", "asset-2"]
    )
    assert result.sections is not None
    assert len(result.citations) > 0
```

### Project Structure Notes

**Alignment with Unified Project Structure:**
- Services go in `apps/api/app/services/briefing/` (already defined in architecture)
- Models go in `apps/api/app/models/` (established pattern)
- API endpoints go in `apps/api/app/api/` (established pattern)
- Tests mirror source structure in `apps/api/tests/`

**Detected Conflicts or Variances:**
- None - this story follows established patterns exactly
- Story 9.1 creates the handoff trigger; 9.2 provides the synthesis engine

### Key Technical Decisions

**1. Tool Execution Strategy:**
- Run all four tools in parallel using `asyncio.gather()` with `return_exceptions=True`
- This allows partial results even if some tools fail
- 15-second overall timeout with individual tool timeouts of 10 seconds

**2. Shift Time Range Detection:**
- Default to 8-hour windows (standard shift)
- Detect shift boundaries: Day (6AM-2PM), Swing (2PM-10PM), Night (10PM-6AM)
- Use current time to determine which shift and calculate start time

**3. Narrative Generation:**
- Use LLM for natural language formatting, not just concatenation
- Keep narrative concise and action-focused
- Include specific numbers and percentages for credibility

**4. Progressive Loading Implementation:**
- Use `asyncio.wait_for()` with 15-second timeout
- Return partial results immediately on timeout
- Background task continues and updates stored handoff record
- Frontend polls for completion or uses WebSocket notification

### Existing Tools to Compose

**Production Status Tool (`production_status.py`):**
- Input: `area: Optional[str]`
- Output: `ProductionStatusOutput` with assets, summary, variance data
- For handoff: Filter by supervisor's assigned assets

**Downtime Analysis Tool (`downtime_analysis.py`):**
- Input: `scope: str`, `time_range: str`
- Output: `DowntimeAnalysisOutput` with Pareto analysis
- For handoff: Use "today" or shift-specific time range

**Safety Events Tool (`safety_events.py`):**
- Input: `time_range: str`, `area: Optional[str]`, `severity_filter: Optional[str]`
- Output: `SafetyEventsOutput` with events list and summary
- For handoff: Filter to shift time range

**Alert Check Tool (`alert_check.py`):**
- Input: `severity_filter: Optional[str]`, `area_filter: Optional[str]`
- Output: `AlertCheckOutput` with active alerts
- For handoff: All severities for assigned assets

### Dependencies

**Story Dependencies:**
- Story 9.1 (Shift Handoff Trigger) - Creates handoff record that triggers synthesis
- Epic 8 architecture decisions (BriefingService pattern)

**Technical Dependencies:**
- Existing tools from Epics 5-7 (all implemented and tested)
- `supervisor_assignments` table (created in Story 9.1 or 8.5)
- LLM integration for narrative formatting (already in place)

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#BriefingService Architecture] - Service pattern
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Backend Tool Pattern] - Tool patterns
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR22] - Synthesis requirement
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR51-FR54] - Citation requirements
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.2] - Story definition
- [Source: apps/api/app/services/agent/tools/production_status.py] - Production tool implementation
- [Source: apps/api/app/services/agent/tools/downtime_analysis.py] - Downtime tool implementation
- [Source: apps/api/app/services/agent/tools/safety_events.py] - Safety tool implementation
- [Source: apps/api/app/services/agent/tools/alert_check.py] - Alert tool implementation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
