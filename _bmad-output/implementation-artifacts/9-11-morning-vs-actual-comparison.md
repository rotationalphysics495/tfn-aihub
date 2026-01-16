# Story 9.11: Morning vs Actual Comparison

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **the EOD summary to compare morning predictions to actual outcomes**,
So that **I can assess prediction accuracy and learn from variances**.

## Acceptance Criteria

1. **AC#1: Morning Briefing Retrieval** - Given a morning briefing was generated today, when the EOD summary is generated (FR32), then it retrieves the morning briefing record and compares flagged concerns to actual outcomes.

2. **AC#2: Concern Outcome Classification** - Given a concern was flagged in the morning, when comparing to actuals (FR33), then the summary indicates one of:
   - "Materialized" - issue occurred as predicted
   - "Averted" - issue was prevented/resolved
   - "Escalated" - worse than predicted
   - "Unexpected" - new issue not predicted

3. **AC#3: Accuracy Metrics Display** - Given comparison data is available, when displayed, then accuracy metrics are shown:
   - Prediction accuracy percentage
   - False positives (flagged but didn't occur)
   - Misses (occurred but not flagged)

4. **AC#4: Accuracy Trend Tracking** - Given this is tracked over time (FR57), when queried, then prediction accuracy trends are available and inform Action Engine tuning.

5. **AC#5: No Morning Briefing Handling** - Given no morning briefing was generated today, when EOD comparison is requested, then the system shows day's performance without comparison and notes "No morning briefing to compare".

## Tasks / Subtasks

- [ ] Task 1: Define EODComparisonResult schema (AC: #2, #3)
  - [ ] 1.1: Create `ConcernOutcome` enum with Materialized/Averted/Escalated/Unexpected values
  - [ ] 1.2: Create `ConcernComparison` model linking morning concern to actual outcome
  - [ ] 1.3: Create `AccuracyMetrics` model with accuracy_percentage, false_positives, misses
  - [ ] 1.4: Create `EODComparisonResult` model aggregating comparisons and metrics

- [ ] Task 2: Implement morning briefing retrieval (AC: #1, #5)
  - [ ] 2.1: Add method to retrieve today's morning briefing record by user_id and date
  - [ ] 2.2: Extract flagged concerns from morning briefing sections
  - [ ] 2.3: Handle missing morning briefing gracefully (return None, not error)

- [ ] Task 3: Implement comparison logic (AC: #2)
  - [ ] 3.1: Create concern matcher to link morning concerns to actual outcomes by asset/issue type
  - [ ] 3.2: Implement classification logic for each concern outcome status
  - [ ] 3.3: Detect unexpected issues (actual issues not predicted in morning)

- [ ] Task 4: Implement accuracy metrics calculation (AC: #3)
  - [ ] 4.1: Calculate prediction accuracy percentage
  - [ ] 4.2: Count false positives (predicted but didn't occur)
  - [ ] 4.3: Count misses (occurred but not predicted)
  - [ ] 4.4: Build AccuracyMetrics response object

- [ ] Task 5: Implement accuracy trend storage (AC: #4)
  - [ ] 5.1: Store daily accuracy metrics in analytics table
  - [ ] 5.2: Create query for accuracy trends over time
  - [ ] 5.3: Add feedback mechanism for Action Engine weight tuning

- [ ] Task 6: Integrate into EOD service (AC: #1-5)
  - [ ] 6.1: Add `compare_to_morning_briefing()` method to eod.py
  - [ ] 6.2: Integrate comparison results into EOD summary response
  - [ ] 6.3: Add unit tests for comparison logic

## Dev Notes

### Architecture Context

This story extends the EOD Summary feature (Story 9.10) with prediction accuracy feedback. The comparison creates a closed-loop learning system where morning predictions can be validated against actual outcomes.

### Critical Implementation Patterns

**BriefingService Extension:**
- This is NOT a new ManufacturingTool - it extends the `BriefingService` in `services/briefing/eod.py`
- Follow the existing BriefingService pattern from Epic 8 architecture
- All comparison data must include citations from underlying tools (NFR1, NFR15)

**Concern Matching Algorithm:**
```python
# Match concerns by:
# 1. Asset ID (exact match)
# 2. Issue type/category (safety, downtime, quality)
# 3. Area (if asset-level match not found)
```

**Outcome Classification Logic:**
```python
ConcernOutcome.MATERIALIZED  # threshold_exceeded && concern_type_matched
ConcernOutcome.AVERTED       # threshold_not_exceeded && concern_flagged
ConcernOutcome.ESCALATED     # actual_severity > predicted_severity
ConcernOutcome.UNEXPECTED    # actual_issue && !predicted
```

### Data Storage Architecture

**Morning Briefing Reference:**
- Story 9.10 creates morning briefing records with concerns
- This story reads those records for comparison
- Link: morning_briefing_id stored on EOD summary record

**Accuracy Analytics Table:**
```sql
CREATE TABLE briefing_accuracy_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    date DATE NOT NULL,
    morning_briefing_id UUID,  -- nullable if no morning briefing
    eod_summary_id UUID,
    accuracy_percentage DECIMAL(5,2),
    false_positives INTEGER,
    misses INTEGER,
    total_predictions INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date)
);
```

### Project Structure Notes

**Files to Create:**
- `apps/api/app/models/briefing.py` - Add EODComparisonResult, ConcernComparison, AccuracyMetrics schemas
- `supabase/migrations/20260116_briefing_accuracy.sql` - Accuracy metrics table (if not already created in 9.10)

**Files to Modify:**
- `apps/api/app/services/briefing/eod.py` - Add comparison logic (primary implementation file)

**Alignment with Architecture:**
- Uses existing `daily_summaries` cache for actual outcome data
- Follows BriefingService orchestration pattern (not ManufacturingTool)
- Pydantic models in `app/models/briefing.py`
- Service logic in `app/services/briefing/eod.py`

### Testing Requirements

**Unit Tests Required:**
- Test concern matching with exact asset match
- Test concern matching with area-level fallback
- Test each outcome classification scenario
- Test accuracy metrics calculation
- Test handling of no morning briefing
- Test handling of no concerns flagged

**Integration Tests:**
- Test full EOD comparison flow with mocked daily_summaries
- Test accuracy storage and retrieval

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#BriefingService Architecture]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR32-FR33]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.11]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#BriefingService Pattern]

### Dependencies

- **Story 9.10 (EOD Summary Trigger):** Must be implemented first - provides the EOD summary framework and morning briefing storage structure
- **Epic 8 (Voice Briefing Foundation):** Provides BriefingService base patterns
- **Existing Tools:** Uses production_status, safety_events, oee_query, downtime_analysis tools for actual outcome data

### External API Considerations

None - this story uses only internal data (morning briefings and daily_summaries cache).

### Performance Considerations

- Comparison logic should execute within the 30-second briefing generation budget (NFR8)
- Cache morning briefing lookup (same-day queries common)
- Accuracy trend queries should use indexed columns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

