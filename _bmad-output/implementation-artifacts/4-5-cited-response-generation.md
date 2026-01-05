# Story 4.5: Cited Response Generation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager or Line Supervisor**,
I want **all AI-generated responses to include specific citations to data sources and evidence**,
so that I can **trust the AI recommendations and quickly verify claims against actual production data (NFR1 compliance)**.

## Acceptance Criteria

1. **Response Citation Format**
   - All AI responses include inline citations linking claims to specific data sources
   - Citations follow format: [Source: table_name/record_id] or [Evidence: metric_name at timestamp]
   - Each factual claim is grounded with at least one verifiable citation
   - Non-grounded claims are explicitly marked as "AI inference" or omitted

2. **Data Source Integration**
   - Citations link to actual database records (daily_summaries, live_snapshots, safety_events)
   - Asset-specific claims cite the specific asset_id and relevant timestamp
   - Financial impact claims cite cost_centers data and calculation basis
   - Historical pattern claims cite Mem0 memory entries with memory_id

3. **Grounding Validation**
   - Implement grounding score threshold (minimum 0.6) for claim validation
   - Responses below grounding threshold trigger fallback to "insufficient evidence" message
   - Each response includes meta.grounding_score indicating confidence level
   - Grounding validation logs are captured for observability

4. **Citation UI Rendering**
   - Citations render as clickable links in Chat UI (Story 4.3)
   - Clicking citation opens side panel showing source data
   - Visual distinction between data citations (blue) and memory citations (purple)
   - Hover tooltip shows citation summary without requiring click

5. **Multi-Source Response Synthesis**
   - Responses can cite multiple sources when synthesizing insights
   - Cross-reference validation ensures cited sources support the claim
   - Conflicting data sources are explicitly noted in response
   - Primary source is indicated when multiple sources support same claim

6. **Mem0 Memory Citations**
   - Historical context from Mem0 includes memory provenance
   - Past resolution citations include original timestamp and context
   - User preference citations include when preference was learned
   - Asset history citations link to specific past events

7. **NFR1 Compliance Validation**
   - 100% of factual recommendations include at least one citation
   - Citation accuracy verified against source data (no hallucinated references)
   - Audit log records all citation-response pairs for compliance review
   - Grounding failures trigger alert for manual review

8. **Performance Requirements**
   - Citation generation adds no more than 500ms to response time
   - Grounding validation completes within 200ms per claim
   - Citation links resolve within 100ms (cached data)
   - Meets overall NFR2 latency requirements

## Tasks / Subtasks

- [ ] Task 1: Design Citation Data Model (AC: #1, #2)
  - [ ] 1.1 Define Citation schema in Pydantic: `{source_type, source_table, record_id, timestamp, excerpt, confidence}`
  - [ ] 1.2 Define CitedResponse schema: `{response_text, citations: List[Citation], grounding_score, meta}`
  - [ ] 1.3 Create citation_logs table migration in Supabase for audit trail
  - [ ] 1.4 Define GroundingResult schema for validation results

- [ ] Task 2: Implement Grounding Validation Service (AC: #3, #7)
  - [ ] 2.1 Create `apps/api/app/services/grounding_service.py`
  - [ ] 2.2 Implement claim extraction from LLM response using LangChain
  - [ ] 2.3 Implement source retrieval for each claim from relevant tables
  - [ ] 2.4 Calculate grounding score using semantic similarity (claim vs source)
  - [ ] 2.5 Implement threshold-based validation (0.6 minimum)
  - [ ] 2.6 Log grounding results to citation_logs for observability
  - [ ] 2.7 Implement fallback response for low-grounding claims

- [ ] Task 3: Implement Citation Generator (AC: #1, #2, #5)
  - [ ] 3.1 Create `apps/api/app/services/citation_generator.py`
  - [ ] 3.2 Integrate with LangChain response chain to inject citation context
  - [ ] 3.3 Implement database citation lookup (daily_summaries, live_snapshots, safety_events)
  - [ ] 3.4 Implement cost_centers citation for financial claims
  - [ ] 3.5 Implement multi-source citation aggregation
  - [ ] 3.6 Add primary source selection logic for redundant citations
  - [ ] 3.7 Format citations as inline markdown with source links

- [ ] Task 4: Integrate Mem0 Memory Citations (AC: #6)
  - [ ] 4.1 Extend Mem0 retrieval (Story 4.1) to include memory provenance
  - [ ] 4.2 Add memory_id to citation format for Mem0 sources
  - [ ] 4.3 Implement timestamp extraction from Mem0 memory entries
  - [ ] 4.4 Create memory citation formatter for asset history
  - [ ] 4.5 Add user preference attribution to memory citations

- [ ] Task 5: Create Citation API Endpoint (AC: #1, #4, #8)
  - [ ] 5.1 Create `apps/api/app/api/citations.py` router
  - [ ] 5.2 Implement `GET /api/citations/{citation_id}` for citation detail lookup
  - [ ] 5.3 Implement `GET /api/citations/source/{source_type}/{record_id}` for source data
  - [ ] 5.4 Return source data formatted for UI display
  - [ ] 5.5 Add caching for frequently accessed citation sources
  - [ ] 5.6 Register router in `apps/api/app/main.py`

- [ ] Task 6: Update Chat Response Chain (AC: #1, #3, #5)
  - [ ] 6.1 Modify chat response chain (Story 4.3) to use citation generator
  - [ ] 6.2 Add grounding validation step before returning response
  - [ ] 6.3 Implement response rewriting for low-confidence claims
  - [ ] 6.4 Add citation injection to final response format
  - [ ] 6.5 Include grounding_score in response metadata

- [ ] Task 7: Implement Citation UI Components (AC: #4)
  - [ ] 7.1 Create `apps/web/src/components/chat/CitationLink.tsx`
  - [ ] 7.2 Create `apps/web/src/components/chat/CitationPanel.tsx` for side panel
  - [ ] 7.3 Implement citation parsing from markdown response
  - [ ] 7.4 Add hover tooltip with citation summary
  - [ ] 7.5 Style data citations (blue) vs memory citations (purple)
  - [ ] 7.6 Integrate with Chat Sidebar UI (Story 4.3)

- [ ] Task 8: Implement Audit Logging (AC: #7)
  - [ ] 8.1 Create citation_logs table migration with fields: `response_id, citations, grounding_score, validated_at`
  - [ ] 8.2 Implement async logging service for citation audit
  - [ ] 8.3 Add alert trigger for grounding_score < 0.6
  - [ ] 8.4 Create admin endpoint for citation audit review (optional)

- [ ] Task 9: Testing and Validation (AC: #7, #8)
  - [ ] 9.1 Unit tests for grounding_service with mock data sources
  - [ ] 9.2 Unit tests for citation_generator with various claim types
  - [ ] 9.3 Integration tests for citation API endpoints
  - [ ] 9.4 E2E test for chat response with citations rendering
  - [ ] 9.5 Performance tests for latency requirements (500ms total, 200ms grounding)
  - [ ] 9.6 NFR1 compliance validation test suite

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router
- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain with structured output chains
- **Memory Layer:** Mem0 for historical context and memory citations
- **Styling:** Tailwind CSS + Shadcn/UI with Industrial Clarity theme
- **Data Source:** Supabase PostgreSQL

### Technical Requirements

**Grounding Architecture (Per LangChain Best Practices):**
```python
# Three-step grounding approach to reduce hallucination
# 1. Extract claims from LLM response
# 2. Retrieve supporting sources for each claim
# 3. Validate grounding and generate citations

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

class Claim(BaseModel):
    """A single factual claim extracted from response"""
    text: str
    claim_type: str  # 'factual', 'recommendation', 'inference'
    requires_grounding: bool = True

class Citation(BaseModel):
    """A citation linking a claim to source data"""
    source_type: str  # 'database', 'memory', 'calculation'
    source_table: Optional[str]  # 'daily_summaries', 'live_snapshots', etc.
    record_id: Optional[str]
    memory_id: Optional[str]  # For Mem0 citations
    timestamp: Optional[str]
    excerpt: str  # Key supporting text from source
    confidence: float  # 0.0 - 1.0

class CitedResponse(BaseModel):
    """Response with embedded citations"""
    response_text: str
    citations: List[Citation]
    grounding_score: float  # Overall grounding confidence
    ungrounded_claims: List[str]  # Claims that couldn't be grounded
```

**Grounding Score Calculation:**
```python
# Grounding score thresholds (per LangChain VertexAI patterns)
GROUNDING_THRESHOLD_HIGH = 0.8   # Strong citations
GROUNDING_THRESHOLD_MIN = 0.6   # Minimum acceptable
GROUNDING_THRESHOLD_LOW = 0.4   # Weak/insufficient

def calculate_grounding_score(claims: List[Claim], citations: List[Citation]) -> float:
    """
    Calculate overall grounding score for response.

    Score = (sum of claim confidence scores) / total claims
    Claims without citations receive 0.0 confidence.
    """
    if not claims:
        return 1.0  # No claims = fully grounded (nothing to verify)

    total_confidence = sum(
        max((c.confidence for c in citations if c.supports_claim(claim)), default=0.0)
        for claim in claims
        if claim.requires_grounding
    )
    groundable_claims = sum(1 for c in claims if c.requires_grounding)

    return total_confidence / groundable_claims if groundable_claims > 0 else 1.0
```

**Citation Format in Responses:**
```markdown
# Example AI Response with Citations

Based on yesterday's data, Grinder 5 had the highest downtime at 47 minutes
[Source: daily_summaries/2026-01-04/asset-grinder-5], costing approximately
$2,350 in lost production [Evidence: cost_centers calculation @ $3000/hr].

This is consistent with the pattern we've seen over the past week
[Memory: asset-history/grinder-5/mem-id-abc123] where similar issues
occurred on Monday and Wednesday.

**Recommendation:** Schedule preventive maintenance before next shift.
[AI Inference - based on pattern analysis]
```

**Frontend Citation Rendering:**
```typescript
// Citation link component
interface CitationLinkProps {
  citation: {
    id: string;
    sourceType: 'database' | 'memory' | 'calculation';
    displayText: string;
  };
  onClick: (citationId: string) => void;
}

// Citation styling per Industrial Clarity
const citationStyles = {
  database: 'text-blue-600 hover:text-blue-800 underline',  // Data citations
  memory: 'text-purple-600 hover:text-purple-800 underline', // Memory citations
  calculation: 'text-gray-600 hover:text-gray-800 italic',   // Derived values
  inference: 'text-amber-600 italic',                        // AI inference (no link)
};
```

**Mem0 Citation Integration:**
```python
# Extend Mem0 retrieval to include provenance
from mem0 import MemoryClient

async def retrieve_memory_with_provenance(
    user_id: str,
    query: str,
    asset_id: Optional[str] = None
) -> List[dict]:
    """
    Retrieve memories with full provenance for citation.

    Returns:
        List of memories with memory_id, timestamp, and source context.
    """
    memories = await mem0_client.search(
        query=query,
        user_id=user_id,
        filters={"asset_id": asset_id} if asset_id else None,
        limit=5
    )

    return [
        {
            "memory_id": m.id,
            "content": m.content,
            "created_at": m.created_at,
            "source_event": m.metadata.get("source_event"),
            "confidence": m.score
        }
        for m in memories
    ]
```

### Database Schema Additions

```sql
-- Citation audit log table
CREATE TABLE citation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    session_id UUID,
    query_text TEXT,
    response_text TEXT,
    citations JSONB,  -- Array of Citation objects
    grounding_score DECIMAL(3,2),
    ungrounded_claims JSONB,  -- Claims that couldn't be grounded
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_citation_logs_grounding ON citation_logs(grounding_score);
CREATE INDEX idx_citation_logs_user ON citation_logs(user_id);
CREATE INDEX idx_citation_logs_created ON citation_logs(created_at);

-- Alert function for low grounding scores
CREATE OR REPLACE FUNCTION alert_low_grounding()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.grounding_score < 0.6 THEN
        -- Insert into alerts table or trigger notification
        INSERT INTO system_alerts (alert_type, severity, message, metadata)
        VALUES (
            'low_grounding_score',
            'warning',
            format('Response %s has low grounding score: %s', NEW.response_id, NEW.grounding_score),
            jsonb_build_object('response_id', NEW.response_id, 'score', NEW.grounding_score)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER citation_grounding_alert
AFTER INSERT ON citation_logs
FOR EACH ROW EXECUTE FUNCTION alert_low_grounding();
```

### Project Structure Notes

```
apps/api/app/
  services/
    grounding_service.py      # Grounding validation logic (NEW)
    citation_generator.py     # Citation generation from sources (NEW)
    citation_formatter.py     # Format citations for response (NEW)
  api/
    citations.py              # Citation lookup endpoints (NEW)
  models/
    citation.py               # Pydantic models for citations (NEW)

apps/web/src/
  components/
    chat/
      CitationLink.tsx        # Inline citation component (NEW)
      CitationPanel.tsx       # Side panel for source view (NEW)
      CitationTooltip.tsx     # Hover tooltip component (NEW)
      ChatMessage.tsx         # Update to parse/render citations

migrations/
  YYYYMMDD_create_citation_logs.sql  # Audit table migration (NEW)
```

### Dependencies

**Requires (must be completed):**
- Story 4.1: Mem0 Vector Memory Integration (provides memory storage and retrieval)
- Story 4.2: LangChain Text-to-SQL (provides query translation base)
- Story 4.3: Chat Sidebar UI (provides chat interface to render citations)
- Story 4.4: Asset History Memory (provides asset-specific memory context)
- Story 1.4: Analytical Cache Schema (provides source tables for citations)
- Story 2.7: Financial Impact Calculator (provides calculation basis for financial citations)

**Enables:**
- Full NFR1 compliance: All AI recommendations cite specific data points
- User trust through transparent AI: Every claim is verifiable
- Audit and compliance review capabilities

### NFR Compliance

- **NFR1 (Accuracy):** This story directly implements NFR1 - AI must cite specific data points for every recommendation to prevent hallucination
- **NFR2 (Latency):** Citation generation must not exceed 500ms additional latency
- **NFR3 (Read-Only):** All citation sources are read from Supabase; no writes to MSSQL

### Testing Guidance

**Unit Tests:**
```python
# Test grounding service
def test_grounding_score_calculation():
    claims = [Claim(text="Grinder 5 had 47 min downtime", requires_grounding=True)]
    citations = [Citation(confidence=0.85, source_table="daily_summaries")]
    score = calculate_grounding_score(claims, citations)
    assert score >= 0.6

def test_low_grounding_triggers_fallback():
    claims = [Claim(text="Unverifiable claim", requires_grounding=True)]
    citations = []  # No supporting citations
    result = validate_and_respond(claims, citations)
    assert "insufficient evidence" in result.response_text.lower()

def test_citation_format_generation():
    record = {"table": "daily_summaries", "id": "abc123", "timestamp": "2026-01-04"}
    citation = generate_citation(record)
    assert citation.source_table == "daily_summaries"
    assert citation.record_id == "abc123"
```

**Integration Tests:**
```python
# Test full citation pipeline
def test_chat_response_includes_citations():
    response = await chat_service.generate_response(
        query="Why did Grinder 5 fail yesterday?",
        user_id="test-user"
    )
    assert response.citations is not None
    assert len(response.citations) > 0
    assert response.grounding_score >= 0.6

def test_citation_api_returns_source_data():
    response = await client.get("/api/citations/source/daily_summaries/abc123")
    assert response.status_code == 200
    assert "asset_id" in response.json()
```

**E2E Tests:**
```typescript
// Test citation rendering in UI
test('citations render as clickable links', async () => {
  render(<ChatMessage message={mockMessageWithCitations} />);
  const citationLink = screen.getByText(/Source: daily_summaries/);
  expect(citationLink).toHaveClass('text-blue-600');

  await userEvent.click(citationLink);
  expect(screen.getByTestId('citation-panel')).toBeInTheDocument();
});

test('memory citations use purple styling', async () => {
  render(<CitationLink citation={mockMemoryCitation} />);
  const link = screen.getByRole('link');
  expect(link).toHaveClass('text-purple-600');
});
```

### API Response Schema

```typescript
interface ChatResponseWithCitations {
  id: string;
  responseText: string;  // Markdown with inline citation markers
  citations: Array<{
    id: string;
    sourceType: 'database' | 'memory' | 'calculation';
    sourceTable?: string;
    recordId?: string;
    memoryId?: string;
    timestamp?: string;
    excerpt: string;
    confidence: number;
    displayText: string;  // Human-readable citation text
  }>;
  groundingScore: number;
  ungroundedClaims: string[];
  meta: {
    responseTime: number;
    groundingTime: number;
    citationCount: number;
  };
}

interface CitationDetailResponse {
  id: string;
  sourceType: string;
  sourceData: Record<string, any>;  // Full source record
  relatedCitations: string[];       // Other citations from same source
  fetchedAt: string;
}
```

### References

- [Source: _bmad/bmm/data/prd.md#2. Requirements] - NFR1: AI must cite specific data points for every recommendation
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 integration patterns and Action Engine logic
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Trust & Transparency: AI recommendations link to raw data evidence
- [Source: _bmad-output/planning-artifacts/epic-4.md] - Epic 4 scope: Cited response generation for NFR1 compliance
- [Source: LangChain Documentation] - VertexAICheckGroundingWrapper for grounding validation patterns
- [Source: Mem0 Research Paper (arXiv:2504.19413)] - Memory provenance and timestamping architecture
- [Source: _bmad-output/implementation-artifacts/2-9-live-pulse-ticker.md] - Reference implementation patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
