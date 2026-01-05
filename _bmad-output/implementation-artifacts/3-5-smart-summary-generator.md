# Story 3.5: Smart Summary Generator

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **an AI-generated natural language summary that explains why production targets were missed and recommends specific corrective actions**,
so that **I can quickly understand the root causes of issues and take immediate action during my morning meeting without manually analyzing multiple data sources**.

## Acceptance Criteria

1. **LLM Integration Setup**
   - GIVEN the Smart Summary service is initialized
   - WHEN the LangChain configuration is loaded
   - THEN the service connects to the configured LLM provider (OpenAI GPT-4 or Claude)
   - AND environment variables control model selection and API keys
   - AND the connection is validated on startup with a health check

2. **Data Context Assembly**
   - GIVEN the Morning Report pipeline has completed (Story 2.1)
   - WHEN the Smart Summary generation is triggered
   - THEN the service retrieves data from:
     - `daily_summaries` table for the target date
     - `safety_events` table for any safety incidents
     - `cost_centers` table for financial context
     - Action items from the Action Engine (Story 3.1)
   - AND the data is formatted into a structured context object for the LLM

3. **Prompt Engineering for Manufacturing Context**
   - GIVEN the data context is assembled
   - WHEN the LLM prompt is constructed
   - THEN the prompt includes:
     - Role instruction: "You are an experienced manufacturing analyst"
     - Specific data points with values (not vague references)
     - Instructions to cite data sources in the response
     - Requirement to prioritize safety issues first
     - Request for actionable recommendations with estimated impact
   - AND the prompt template is externalized (not hardcoded) for easy iteration

4. **Smart Summary Generation**
   - GIVEN the prompt is constructed with context
   - WHEN the LLM generates the summary
   - THEN the summary includes:
     - Executive overview (2-3 sentences max)
     - Top issues ranked by priority (Safety > Financial Impact > OEE Gap)
     - For each issue: What happened, Why it matters ($ impact), What to do
     - Specific citations linking to raw data (e.g., "[Asset: Grinder 5, OEE: 72%]")
   - AND the summary is structured in markdown format for UI rendering
   - AND generation completes within 30 seconds

5. **Data Citation Requirement (NFR1 Compliance)**
   - GIVEN the LLM generates recommendations
   - WHEN each claim or recommendation is made
   - THEN it must include a verifiable data citation
   - AND citations reference specific asset names, timestamps, or metric values
   - AND the UI can hyperlink citations to drill-down views
   - Example: "Grinder 5 OEE dropped to 72% [Source: daily_summaries, 2024-01-15]"

6. **Summary Storage and Caching**
   - GIVEN a Smart Summary is generated
   - WHEN the summary is complete
   - THEN it is stored in a new `smart_summaries` table with:
     - id, date, summary_text, citations_json, generated_at, model_used, prompt_tokens, completion_tokens
   - AND summaries are cached to avoid regeneration for the same date
   - AND cache invalidation occurs if source data is updated

7. **API Endpoint for Summary Retrieval**
   - GIVEN a Smart Summary exists for a date
   - WHEN the frontend requests `GET /api/summaries/{date}`
   - THEN the endpoint returns the cached summary if available
   - AND returns 404 if no summary exists for that date
   - AND supports `?regenerate=true` parameter to force new generation
   - AND the endpoint is protected with Supabase JWT authentication

8. **Fallback Behavior for LLM Failures**
   - GIVEN the LLM service is unavailable or times out
   - WHEN summary generation is attempted
   - THEN the system falls back to a template-based summary
   - AND the fallback clearly indicates "AI summary unavailable - showing key metrics"
   - AND critical metrics (Safety events, OEE gaps, Financial losses) are still displayed
   - AND the error is logged with details for debugging

9. **Integration with Morning Report Pipeline**
   - GIVEN the batch pipeline (Story 2.1) completes daily processing
   - WHEN the pipeline execution finishes successfully
   - THEN Smart Summary generation is triggered automatically
   - AND the summary is available before 06:30 AM (within 30 min of pipeline start)
   - AND the summary references only the freshly processed T-1 data

10. **Token Usage Monitoring**
    - GIVEN the LLM is called for summary generation
    - WHEN the response is received
    - THEN token usage (prompt + completion) is logged
    - AND daily/monthly token usage is tracked for cost management
    - AND alerts can be configured for usage thresholds

## Tasks / Subtasks

- [ ] Task 1: Create Smart Summary Service Structure (AC: #1, #3)
  - [ ] Create `apps/api/app/services/ai/` directory
  - [ ] Create `apps/api/app/services/ai/__init__.py`
  - [ ] Create `apps/api/app/services/ai/smart_summary.py` - main service
  - [ ] Create `apps/api/app/services/ai/prompts.py` - prompt templates
  - [ ] Create `apps/api/app/services/ai/context_builder.py` - data assembly

- [ ] Task 2: Implement LangChain LLM Integration (AC: #1)
  - [ ] Add LangChain dependencies to `requirements.txt`
  - [ ] Create LLM client factory supporting OpenAI and Anthropic
  - [ ] Implement configuration via environment variables
  - [ ] Add health check function for LLM connectivity
  - [ ] Handle API key validation and error messaging

- [ ] Task 3: Implement Data Context Builder (AC: #2)
  - [ ] Create function to fetch `daily_summaries` for target date
  - [ ] Create function to fetch `safety_events` for target date
  - [ ] Create function to fetch relevant `cost_centers` data
  - [ ] Create function to retrieve action items from Action Engine (Story 3.1)
  - [ ] Build structured context object with all data points

- [ ] Task 4: Create Manufacturing-Optimized Prompt Templates (AC: #3, #5)
  - [ ] Design system prompt with manufacturing analyst persona
  - [ ] Create data injection template with citation requirements
  - [ ] Add prioritization logic (Safety > Financial > OEE)
  - [ ] Include example output format in prompt
  - [ ] Externalize prompts to YAML/JSON config file

- [ ] Task 5: Implement Summary Generation Service (AC: #4, #5)
  - [ ] Create main `generate_smart_summary()` function
  - [ ] Implement LLM call with timeout handling (30 sec max)
  - [ ] Parse and validate LLM response structure
  - [ ] Extract citations from response for verification
  - [ ] Format output as structured markdown

- [ ] Task 6: Create Database Schema for Summaries (AC: #6)
  - [ ] Create SQL migration for `smart_summaries` table
  - [ ] Add indexes for date and created_at columns
  - [ ] Create Pydantic model for SmartSummary
  - [ ] Implement upsert function for storing summaries
  - [ ] Add RLS policies for authenticated access

- [ ] Task 7: Implement Caching and Invalidation (AC: #6)
  - [ ] Create cache lookup by date before generation
  - [ ] Implement cache invalidation when source data updates
  - [ ] Add `regenerate` flag to bypass cache
  - [ ] Track cache hits/misses in logs

- [ ] Task 8: Create API Endpoints (AC: #7)
  - [ ] Create `GET /api/summaries/{date}` endpoint
  - [ ] Create `POST /api/summaries/generate` for manual trigger
  - [ ] Add query parameter for `?regenerate=true`
  - [ ] Implement Supabase JWT authentication middleware
  - [ ] Return appropriate HTTP status codes (200, 404, 500)

- [ ] Task 9: Implement Fallback Template (AC: #8)
  - [ ] Create template-based summary for LLM failures
  - [ ] Include critical metrics in fallback format
  - [ ] Add clear indicator that AI summary is unavailable
  - [ ] Log LLM failures with error details

- [ ] Task 10: Integrate with Morning Report Pipeline (AC: #9)
  - [ ] Add post-processing hook to batch pipeline (Story 2.1)
  - [ ] Trigger Smart Summary generation after pipeline success
  - [ ] Handle pipeline failures gracefully (don't block on summary)
  - [ ] Verify summary availability by 06:30 AM

- [ ] Task 11: Implement Token Usage Tracking (AC: #10)
  - [ ] Log token usage per generation (prompt + completion)
  - [ ] Create `llm_usage` table or add columns to `smart_summaries`
  - [ ] Aggregate daily/monthly token counts
  - [ ] Add environment variable for usage alert threshold

- [ ] Task 12: Write Tests (AC: All)
  - [ ] Unit tests for context builder with mock data
  - [ ] Unit tests for prompt template rendering
  - [ ] Integration test with mocked LLM responses
  - [ ] Test fallback behavior on LLM timeout
  - [ ] Test cache hit/miss scenarios
  - [ ] Test API endpoint authentication

## Dev Notes

### Architecture Compliance

This story implements the **Smart Summary text generation via LLM** component specified in the architecture document under Pipeline A (Morning Report). It is the final piece of the Action Engine (Epic 3), providing the AI-powered natural language layer.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/ai/` for AI/LLM services
**Pattern:** Service-layer with LangChain orchestration

### Technical Requirements

**Smart Summary Architecture:**
```
Morning Report Pipeline (Story 2.1)
    |
    | [Pipeline completes at ~06:00 AM]
    v
smart_summary.py (Orchestrator)
    |
    +---> context_builder.py
    |         |
    |         +---> Fetch daily_summaries
    |         +---> Fetch safety_events
    |         +---> Fetch cost_centers
    |         +---> Get Action Engine items (Story 3.1)
    |         |
    |         v
    |     [Structured Context]
    |
    +---> prompts.py (Template Rendering)
    |         |
    |         v
    |     [Formatted Prompt]
    |
    +---> LangChain LLM Call
    |         |
    |         v
    |     [AI-Generated Summary]
    |
    +---> Supabase Write
          - smart_summaries (upsert)
```

**LangChain Configuration:**
```python
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

def get_llm_client():
    """Factory for LLM client based on config."""
    provider = os.getenv("LLM_PROVIDER", "openai")

    if provider == "openai":
        return ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.3,  # Low for factual analysis
            max_tokens=1500,
            timeout=30,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            max_tokens=1500,
            timeout=30,
        )
```

**Prompt Template Structure:**
```python
SYSTEM_PROMPT = """
You are an experienced manufacturing operations analyst reviewing daily production data.
Your role is to provide concise, actionable insights for Plant Managers.

CRITICAL REQUIREMENTS:
1. ALWAYS cite specific data points in your analysis (e.g., [Asset: Grinder 5, OEE: 72%])
2. Prioritize issues in this order: Safety > Financial Impact > OEE Gaps
3. Provide specific, actionable recommendations with estimated impact
4. Keep the executive summary to 2-3 sentences maximum
5. Use bullet points for clarity

OUTPUT FORMAT:
## Executive Summary
[2-3 sentence overview]

## Priority Issues
### 1. [Issue Title]
- **What Happened:** [Description with data citation]
- **Impact:** [Financial or safety impact]
- **Recommended Action:** [Specific action to take]

### 2. [Next Issue]
...

## Data Sources Referenced
[List of data tables and timestamps used]
"""

DATA_TEMPLATE = """
Today's Date: {date}

=== SAFETY EVENTS ===
{safety_events_data}

=== OEE PERFORMANCE ===
{oee_data}

=== FINANCIAL LOSSES ===
{financial_data}

=== ACTION ENGINE PRIORITIES ===
{action_items}

Based on this data, provide your analysis following the format specified.
"""
```

### Database Schema

**smart_summaries table:**
```sql
CREATE TABLE smart_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    citations_json JSONB,  -- Structured citation references
    model_used VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    generation_duration_ms INTEGER,
    is_fallback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast date lookup
CREATE INDEX idx_smart_summaries_date ON smart_summaries(date);

-- RLS Policy
ALTER TABLE smart_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read summaries"
    ON smart_summaries FOR SELECT
    USING (auth.role() = 'authenticated');
```

**llm_usage table (optional for detailed tracking):**
```sql
CREATE TABLE llm_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost_usd DECIMAL(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LLM_PROVIDER` | LLM provider (openai or anthropic) | No | "openai" |
| `OPENAI_API_KEY` | OpenAI API key | Conditional | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | Conditional | - |
| `LLM_MODEL` | Specific model to use | No | Provider default |
| `LLM_TEMPERATURE` | Response creativity (0-1) | No | 0.3 |
| `LLM_TIMEOUT_SECONDS` | Max wait for response | No | 30 |
| `LLM_MAX_TOKENS` | Max response tokens | No | 1500 |
| `TOKEN_USAGE_ALERT_THRESHOLD` | Daily token alert level | No | 100000 |

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── smart_summary.py   # Main service
│   │       ├── prompts.py         # Prompt templates
│   │       ├── context_builder.py # Data assembly
│   │       └── llm_client.py      # LangChain client factory
│   ├── api/
│   │   └── summaries.py           # API endpoints
│   └── models/
│       └── summary.py             # Pydantic models
├── migrations/
│   └── XXXXXX_create_smart_summaries.sql
```

**Dependencies to add to requirements.txt:**
```
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
tiktoken>=0.5.0  # For token counting
```

### Dependencies

**Story Dependencies:**
- Story 2.1 (Batch Data Pipeline T-1) - Source of daily_summaries data
- Story 3.1 (Action Engine Logic) - Provides prioritized action items
- Story 3.2 (Daily Action List API) - Integrates with action endpoints
- Story 3.4 (Insight + Evidence Cards) - UI will display generated summaries

**Blocked By:** Stories 2.1, 3.1, 3.2, 3.4 must be complete

**Enables:**
- Epic 4 (AI Chat & Memory) - Chat can reference and expand on summaries
- Future iterations can enhance summary quality based on user feedback

### Testing Strategy

1. **Unit Tests:**
   - Context builder assembles data correctly
   - Prompt templates render with proper data substitution
   - Citation extraction parses LLM responses correctly
   - Fallback template generates valid output

2. **Integration Tests (Mock LLM):**
   - Full flow from data fetch to summary storage
   - Cache hit returns existing summary
   - Cache miss triggers generation
   - Regenerate flag bypasses cache
   - API authentication works correctly

3. **Manual Testing:**
   - Generate summary with real LLM (dev environment)
   - Verify citations link to actual data
   - Test timeout behavior (simulate slow response)
   - Verify pipeline integration triggers summary
   - Check summary is available by 06:30 AM

### LLM Response Validation

```python
from pydantic import BaseModel, validator
from typing import List, Optional

class Citation(BaseModel):
    asset_name: Optional[str]
    metric_name: str
    value: str
    source_table: str
    timestamp: Optional[str]

class SmartSummaryResponse(BaseModel):
    executive_summary: str
    priority_issues: List[dict]
    data_sources_referenced: List[str]

    @validator('executive_summary')
    def validate_summary_length(cls, v):
        sentences = v.split('.')
        if len(sentences) > 4:
            raise ValueError("Executive summary should be 2-3 sentences")
        return v
```

### Error Handling Patterns

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_smart_summary(date: date) -> SmartSummary:
    """Generate with automatic retry on transient failures."""
    try:
        context = await build_context(date)
        prompt = render_prompt(context)
        response = await llm_client.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        return parse_and_store_response(response, date)
    except TimeoutError:
        logger.warning(f"LLM timeout for date {date}, using fallback")
        return generate_fallback_summary(date)
    except Exception as e:
        logger.error(f"Smart summary generation failed: {e}")
        raise
```

### NFR Compliance

- **NFR1 (Accuracy):** All recommendations require data citations in `[Asset: X, Metric: Y]` format. Prompt engineering enforces this requirement.
- **NFR2 (Latency):** Not directly applicable (batch process), but summary generation capped at 30 seconds.
- **NFR3 (Read-Only):** No MSSQL access in this story - reads from Supabase analytical cache only.

### Security Considerations

- **API Keys:** LLM provider keys stored in Railway secrets, never in code
- **Data Privacy:** Only aggregate metrics sent to LLM, no PII
- **Rate Limiting:** Daily token budget prevents runaway costs
- **Access Control:** Summary endpoints require Supabase JWT authentication

### Prompt Engineering Best Practices

1. **Be Specific:** Include exact format requirements in system prompt
2. **Show Examples:** Provide sample output in prompt when needed
3. **Constrain Output:** Set max_tokens and guide response length
4. **Temperature Control:** Use 0.3 for factual analysis (less creative)
5. **Iterate:** Store prompts externally for easy A/B testing

### References

- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Pipeline A Smart Summary specification
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 and Action Engine logic
- [Source: _bmad/bmm/data/prd.md#Functional] - FR3 Action Engine requirement
- [Source: _bmad/bmm/data/prd.md#Non-Functional] - NFR1 Accuracy (citation) requirement
- [Source: _bmad-output/planning-artifacts/epic-3.md] - Epic 3 context (Action Engine & AI Synthesis)
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3] - Story 3.5 scope
- [Source: _bmad-output/implementation-artifacts/2-1-batch-data-pipeline-t1.md] - Pipeline integration point
- [Source: _bmad-output/implementation-artifacts/1-1-turborepo-monorepo-scaffold.md] - Project structure

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List

