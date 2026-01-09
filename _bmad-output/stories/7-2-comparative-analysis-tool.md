# Story 7.2: Comparative Analysis Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to compare two or more assets or areas side-by-side**,
so that I can **identify best performers, understand differences, and make data-driven decisions about where to focus improvement efforts**.

## Acceptance Criteria

1. **Two-Asset Comparison**
   - Given a user asks "Compare Grinder 5 vs Grinder 3"
   - When the Comparative Analysis tool is invoked
   - Then the response includes:
     - Side-by-side metrics table (OEE, output, downtime, waste)
     - Variance highlighting (better/worse indicators)
     - Summary of key differences
     - Winner/recommendation if one is clearly better
   - And all metrics include citations

2. **Multi-Asset Category Comparison**
   - Given a user asks "Compare all grinders this week"
   - When the Comparative Analysis tool is invoked
   - Then the response compares all assets matching "grinder"
   - And ranks them by overall performance
   - And limits to maximum 10 assets in comparison
   - And provides aggregate statistics across the category

3. **Area-Level Comparison**
   - Given a user asks to compare areas (e.g., "Compare Grinding vs Packaging")
   - When the Comparative Analysis tool is invoked
   - Then the response aggregates metrics at the area level
   - And shows area-level totals and averages
   - And identifies best/worst performing assets within each area

4. **Incompatible Metrics Handling**
   - Given assets have incompatible metrics (different units or targets)
   - When the Comparative Analysis tool is invoked
   - Then the response includes a note about comparability
   - And uses percentage-based comparisons where appropriate
   - And normalizes metrics to a common baseline (e.g., % of target)

5. **Default Time Range & Customization**
   - Default comparison uses last 7 days of data
   - User can specify custom time range (e.g., "Compare ... this month")
   - Time range is explicitly stated in response

6. **Performance & Caching Requirements**
   - Comparison completes within 3 seconds (p95)
   - Cache TTL: 15 minutes for comparison results
   - Supports 2-10 assets/areas in a single comparison

## Tasks / Subtasks

- [ ] Task 1: Define Comparative Analysis Schemas (AC: #1, #4)
  - [ ] 1.1 Create `ComparativeAnalysisInput` Pydantic model with fields: `subjects` (list of asset/area names), `comparison_type` (asset|area), `time_range_days` (default: 7), `metrics` (optional, default: all)
  - [ ] 1.2 Create `ComparisonSubject` model with fields: `name`, `type`, `id`, `metrics` (dict)
  - [ ] 1.3 Create `MetricComparison` model with fields: `metric_name`, `values` (dict by subject), `unit`, `best_performer`, `variance_pct`, `comparability_note`
  - [ ] 1.4 Create `ComparativeAnalysisOutput` model with fields: `subjects`, `metrics`, `summary`, `winner`, `recommendations`, `citations`
  - [ ] 1.5 Add schemas to `apps/api/app/models/agent.py`

- [ ] Task 2: Implement Data Retrieval Layer (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/comparative_analysis.py`
  - [ ] 2.2 Implement asset lookup by name with fuzzy matching (leverage existing Asset Lookup patterns)
  - [ ] 2.3 Implement area detection and asset aggregation
  - [ ] 2.4 Query `daily_summaries` for OEE, output, downtime metrics
  - [ ] 2.5 Query `assets` table for asset metadata and targets
  - [ ] 2.6 Query `shift_targets` for target values
  - [ ] 2.7 Apply time range filtering (default: last 7 days)

- [ ] Task 3: Implement Comparison Logic (AC: #1, #2, #4)
  - [ ] 3.1 Calculate per-subject metrics (OEE avg, total output, total downtime, waste)
  - [ ] 3.2 Normalize metrics to percentages for fair comparison
  - [ ] 3.3 Calculate variance between subjects (absolute and percentage)
  - [ ] 3.4 Determine best/worst performer per metric
  - [ ] 3.5 Generate overall winner based on weighted composite score
  - [ ] 3.6 Detect incompatible metrics and add comparability notes

- [ ] Task 4: Implement Ranking for Multi-Asset (AC: #2)
  - [ ] 4.1 Implement asset name pattern matching (e.g., "grinder" matches all grinder assets)
  - [ ] 4.2 Limit results to 10 assets maximum
  - [ ] 4.3 Rank assets by composite performance score
  - [ ] 4.4 Generate ranked comparison table

- [ ] Task 5: Implement Area Aggregation (AC: #3)
  - [ ] 5.1 Group assets by area attribute
  - [ ] 5.2 Calculate area-level aggregates (sum for output/downtime, weighted avg for OEE)
  - [ ] 5.3 Identify top/bottom performers within each area
  - [ ] 5.4 Generate area summary with drill-down hints

- [ ] Task 6: Integrate with LangChain Agent (AC: #1)
  - [ ] 6.1 Create LangChain Tool wrapper for ComparativeAnalysisTool
  - [ ] 6.2 Define tool description for agent selection (comparison, versus, side-by-side keywords)
  - [ ] 6.3 Register tool with ManufacturingAgent
  - [ ] 6.4 Test tool selection accuracy with varied comparison queries

- [ ] Task 7: Implement Caching (AC: #6)
  - [ ] 7.1 Generate cache key from subjects, time_range, and comparison_type
  - [ ] 7.2 Implement 15-minute TTL caching
  - [ ] 7.3 Include `cached_at` timestamp in response metadata
  - [ ] 7.4 Support `force_refresh=true` parameter

- [ ] Task 8: Implement Citation Generation (AC: #1)
  - [ ] 8.1 Integrate with CitationGenerator from Story 4-5
  - [ ] 8.2 Generate citations for each data source used
  - [ ] 8.3 Include query details and timestamps in citations

- [ ] Task 9: Testing and Validation (AC: #1-6)
  - [ ] 9.1 Unit tests for two-asset comparison
  - [ ] 9.2 Unit tests for multi-asset category matching and ranking
  - [ ] 9.3 Unit tests for area aggregation
  - [ ] 9.4 Unit tests for incompatible metrics handling
  - [ ] 9.5 Unit tests for time range filtering
  - [ ] 9.6 Integration tests for LangChain tool registration
  - [ ] 9.7 Performance tests for 3-second latency requirement

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain AgentExecutor with tool registration (Story 5.1)
- **Data Access:** Use DataSource abstraction layer (Story 5.2)
- **Citation System:** Integrate with CitationGenerator from Story 4-5
- **Caching:** Align with Tool Response Caching patterns (Story 5.8)

### Technical Requirements

**Input/Output Schemas:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

class ComparativeAnalysisInput(BaseModel):
    """Input schema for Comparative Analysis tool"""
    subjects: List[str] = Field(
        description="List of asset names or area names to compare (2-10 items)",
        min_items=2,
        max_items=10
    )
    comparison_type: Literal["asset", "area", "auto"] = Field(
        default="auto",
        description="Type of comparison: asset (specific assets), area (aggregate by area), auto (detect from input)"
    )
    time_range_days: int = Field(
        default=7,
        description="Number of days to include in comparison",
        ge=1,
        le=90
    )
    metrics: Optional[List[str]] = Field(
        default=None,
        description="Specific metrics to compare (default: OEE, output, downtime, waste)"
    )

class MetricComparison(BaseModel):
    """Comparison data for a single metric across subjects"""
    metric_name: str
    unit: str
    values: Dict[str, float]  # subject_name -> value
    best_performer: str
    worst_performer: str
    variance_pct: float  # % difference between best and worst
    comparability_note: Optional[str] = None  # e.g., "Different targets - using % of target"

class SubjectSummary(BaseModel):
    """Summary data for a comparison subject"""
    name: str
    type: Literal["asset", "area"]
    id: Optional[str]
    area: Optional[str]
    metrics: Dict[str, float]  # metric_name -> value
    rank: int
    score: float  # Composite performance score (0-100)

class ComparativeAnalysisOutput(BaseModel):
    """Output schema for Comparative Analysis tool"""
    subjects: List[SubjectSummary]
    metrics: List[MetricComparison]
    summary: str  # Natural language summary of key differences
    winner: Optional[str]  # Best overall performer (if clear)
    recommendations: List[str]  # Actionable insights
    time_range: str  # e.g., "Jan 2-9, 2026"
    cached_at: Optional[datetime]
    citations: List[dict]
```

**Comparative Analysis Tool Implementation:**
```python
from langchain.tools import BaseTool
from typing import Type, Optional, List
from datetime import datetime, timedelta

DEFAULT_METRICS = ["oee", "output", "downtime_hours", "waste_pct"]
CACHE_TTL_MINUTES = 15

class ComparativeAnalysisTool(BaseTool):
    name: str = "comparative_analysis"
    description: str = """Compare two or more assets or areas side-by-side to identify
    best performers and understand differences. Use this when the user wants to compare
    performance metrics between assets (e.g., 'Compare Grinder 5 vs Grinder 3'),
    compare all assets of a type (e.g., 'Compare all grinders'), or compare areas
    (e.g., 'Compare Grinding vs Packaging'). Returns side-by-side metrics,
    variance highlighting, and recommendations."""
    args_schema: Type[ComparativeAnalysisInput] = ComparativeAnalysisInput

    data_source: DataSource  # Injected dependency
    cache: Cache  # Injected dependency

    async def _arun(
        self,
        subjects: List[str],
        comparison_type: str = "auto",
        time_range_days: int = 7,
        metrics: Optional[List[str]] = None
    ) -> ComparativeAnalysisOutput:
        # Check cache first
        cache_key = self._generate_cache_key(subjects, comparison_type, time_range_days)
        cached = await self.cache.get(cache_key)
        if cached:
            cached.cached_at = cached.cached_at  # Mark as cached
            return cached

        # Detect comparison type if auto
        if comparison_type == "auto":
            comparison_type = await self._detect_comparison_type(subjects)

        # Resolve subjects to actual assets/areas
        resolved_subjects = await self._resolve_subjects(subjects, comparison_type)

        if len(resolved_subjects) < 2:
            return self._insufficient_subjects_response(subjects)

        if len(resolved_subjects) > 10:
            resolved_subjects = resolved_subjects[:10]  # Limit to 10

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=time_range_days)

        # Fetch metrics for each subject
        subject_data = []
        all_citations = []

        for subject in resolved_subjects:
            if comparison_type == "area":
                data, citations = await self._fetch_area_metrics(
                    subject, start_date, end_date, metrics or DEFAULT_METRICS
                )
            else:
                data, citations = await self._fetch_asset_metrics(
                    subject, start_date, end_date, metrics or DEFAULT_METRICS
                )
            subject_data.append(data)
            all_citations.extend(citations)

        # Build metric comparisons
        metric_comparisons = self._build_metric_comparisons(
            subject_data, metrics or DEFAULT_METRICS
        )

        # Rank subjects by composite score
        ranked_subjects = self._rank_subjects(subject_data)

        # Determine winner if clear
        winner = self._determine_winner(ranked_subjects)

        # Generate summary and recommendations
        summary = self._generate_summary(ranked_subjects, metric_comparisons)
        recommendations = self._generate_recommendations(metric_comparisons)

        result = ComparativeAnalysisOutput(
            subjects=ranked_subjects,
            metrics=metric_comparisons,
            summary=summary,
            winner=winner,
            recommendations=recommendations,
            time_range=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
            cached_at=None,
            citations=all_citations
        )

        # Cache result
        await self.cache.set(cache_key, result, ttl=CACHE_TTL_MINUTES * 60)

        return result

    async def _resolve_subjects(
        self, subjects: List[str], comparison_type: str
    ) -> List[dict]:
        """Resolve subject names to actual assets or areas"""
        resolved = []

        for name in subjects:
            if comparison_type == "area":
                # Resolve area by name
                area = await self.data_source.get_area_by_name(name)
                if area:
                    resolved.append({"name": name, "type": "area", "data": area})
            else:
                # Check for pattern match (e.g., "all grinders")
                if name.lower().startswith("all "):
                    pattern = name[4:].strip()  # Remove "all "
                    assets = await self.data_source.get_assets_by_pattern(pattern)
                    for asset in assets[:10]:  # Limit expansion
                        resolved.append({
                            "name": asset.name, "type": "asset", "data": asset
                        })
                else:
                    # Single asset lookup with fuzzy matching
                    asset = await self.data_source.get_asset_by_name(name)
                    if asset:
                        resolved.append({
                            "name": asset.name, "type": "asset", "data": asset
                        })

        return resolved

    def _build_metric_comparisons(
        self, subject_data: List[dict], metrics: List[str]
    ) -> List[MetricComparison]:
        """Build comparison objects for each metric"""
        comparisons = []

        metric_config = {
            "oee": {"unit": "%", "higher_is_better": True},
            "output": {"unit": "units", "higher_is_better": True},
            "downtime_hours": {"unit": "hours", "higher_is_better": False},
            "waste_pct": {"unit": "%", "higher_is_better": False}
        }

        for metric in metrics:
            config = metric_config.get(metric, {"unit": "", "higher_is_better": True})
            values = {s["name"]: s["metrics"].get(metric, 0) for s in subject_data}

            # Handle empty or all-zero values
            non_zero_values = [v for v in values.values() if v > 0]
            if not non_zero_values:
                comparability_note = f"No data available for {metric}"
                best = worst = list(values.keys())[0] if values else None
                variance = 0
            else:
                if config["higher_is_better"]:
                    best = max(values, key=values.get)
                    worst = min(values, key=values.get)
                else:
                    best = min(values, key=values.get)
                    worst = max(values, key=values.get)

                # Calculate variance
                max_val = max(values.values())
                min_val = min(values.values())
                if max_val > 0:
                    variance = ((max_val - min_val) / max_val) * 100
                else:
                    variance = 0

                comparability_note = None

            comparisons.append(MetricComparison(
                metric_name=metric,
                unit=config["unit"],
                values=values,
                best_performer=best,
                worst_performer=worst,
                variance_pct=round(variance, 1),
                comparability_note=comparability_note
            ))

        return comparisons

    def _rank_subjects(self, subject_data: List[dict]) -> List[SubjectSummary]:
        """Rank subjects by composite performance score"""
        # Weight: OEE 40%, Output vs Target 30%, Low Downtime 20%, Low Waste 10%
        for subject in subject_data:
            metrics = subject["metrics"]
            score = 0

            # OEE component (0-100 scale)
            oee = metrics.get("oee", 0)
            score += oee * 0.4

            # Output vs target (normalize to 0-100)
            output_pct = metrics.get("output_pct_target", 100)
            score += min(output_pct, 100) * 0.3

            # Downtime (inverse, normalized)
            downtime = metrics.get("downtime_hours", 0)
            max_downtime = 24 * 7  # 168 hours in a week
            downtime_score = max(0, 100 - (downtime / max_downtime * 100))
            score += downtime_score * 0.2

            # Waste (inverse)
            waste = metrics.get("waste_pct", 0)
            waste_score = max(0, 100 - waste)
            score += waste_score * 0.1

            subject["score"] = round(score, 1)

        # Sort by score descending
        ranked = sorted(subject_data, key=lambda x: x["score"], reverse=True)

        return [
            SubjectSummary(
                name=s["name"],
                type=s["type"],
                id=s.get("id"),
                area=s.get("area"),
                metrics=s["metrics"],
                rank=i + 1,
                score=s["score"]
            )
            for i, s in enumerate(ranked)
        ]

    def _determine_winner(self, ranked: List[SubjectSummary]) -> Optional[str]:
        """Determine clear winner if score gap is significant"""
        if len(ranked) < 2:
            return None

        score_gap = ranked[0].score - ranked[1].score
        if score_gap >= 5:  # 5 point gap = clear winner
            return ranked[0].name
        return None

    def _generate_summary(
        self, ranked: List[SubjectSummary], metrics: List[MetricComparison]
    ) -> str:
        """Generate natural language summary"""
        if not ranked:
            return "Unable to compare - no valid subjects found."

        lines = []

        # Overall ranking
        if len(ranked) == 2:
            lines.append(f"**{ranked[0].name}** outperforms **{ranked[1].name}** overall.")
        else:
            top3 = [s.name for s in ranked[:3]]
            lines.append(f"**Top performers:** {', '.join(top3)}")

        # Key differences
        largest_gap = max(metrics, key=lambda m: m.variance_pct)
        if largest_gap.variance_pct > 10:
            lines.append(
                f"Largest difference in **{largest_gap.metric_name}**: "
                f"{largest_gap.variance_pct:.0f}% gap between best and worst."
            )

        return " ".join(lines)

    def _generate_recommendations(
        self, metrics: List[MetricComparison]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recs = []

        for m in metrics:
            if m.variance_pct > 20 and m.worst_performer:
                recs.append(
                    f"Investigate {m.metric_name} gap: {m.worst_performer} is "
                    f"{m.variance_pct:.0f}% behind {m.best_performer}."
                )

        return recs[:3]  # Max 3 recommendations
```

### Database Tables Referenced

| Table | Usage |
|-------|-------|
| `daily_summaries` | OEE, output, downtime, waste metrics |
| `assets` | Asset metadata, area grouping, fuzzy name matching |
| `shift_targets` | Target values for % of target calculations |
| `cost_centers` | Financial context if cost comparison requested |

### Dependencies

**Requires (must be completed):**
- Story 5.1: Agent Framework & Tool Registry (provides ManufacturingTool base class and registration)
- Story 5.2: Data Access Abstraction Layer (provides DataSource protocol for Supabase queries)
- Story 5.3: Asset Lookup Tool (provides fuzzy matching patterns to reuse)
- Story 5.4: OEE Query Tool (provides OEE calculation patterns)
- Story 5.8: Tool Response Caching (provides caching infrastructure)
- Story 4.5: Cited Response Generation (provides CitationGenerator)
- Story 7.1: Memory Recall Tool (establishes Epic 7 tool patterns)

**Enables:**
- FR7.3: Comparative Analysis capability for side-by-side metrics
- Story 7.3: Action List can use comparative insights
- Story 7.5: Recommendation Engine builds on comparison patterns

### Project Structure Notes

```
apps/api/app/
  services/
    agent/
      tools/
        comparative_analysis.py    # Comparative Analysis tool (NEW)
  models/
    agent.py                       # Add ComparativeAnalysisInput/Output (MODIFY)

apps/api/tests/
  test_comparative_analysis_tool.py  # Unit and integration tests (NEW)
```

### NFR Compliance

- **NFR1 (Accuracy):** All metrics sourced from database with citations; no estimates
- **NFR4 (Agent Honesty):** Clear handling when subjects not found or data unavailable
- **NFR5 (Tool Extensibility):** Uses DataSource abstraction for future MSSQL support
- **NFR6 (Response Structure):** Structured output with citations array, metrics breakdown
- **NFR7 (Caching):** 15-minute TTL with cache key strategy

### Testing Guidance

**Unit Tests:**
```python
import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_two_asset_comparison():
    """Test basic two-asset comparison"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)
    result = await tool._arun(
        subjects=["Grinder 5", "Grinder 3"],
        time_range_days=7
    )

    assert len(result.subjects) == 2
    assert len(result.metrics) == 4  # OEE, output, downtime, waste
    assert result.winner in ["Grinder 5", "Grinder 3", None]
    assert len(result.citations) > 0

@pytest.mark.asyncio
async def test_multi_asset_pattern_matching():
    """Test 'all grinders' pattern expands to multiple assets"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)
    result = await tool._arun(
        subjects=["all grinders"],
        time_range_days=7
    )

    assert len(result.subjects) >= 2
    assert len(result.subjects) <= 10  # Max limit
    # Subjects should be ranked
    for i, s in enumerate(result.subjects):
        assert s.rank == i + 1

@pytest.mark.asyncio
async def test_area_comparison():
    """Test area-level aggregation"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)
    result = await tool._arun(
        subjects=["Grinding", "Packaging"],
        comparison_type="area",
        time_range_days=7
    )

    assert all(s.type == "area" for s in result.subjects)
    assert "Grinding" in [s.name for s in result.subjects]
    assert "Packaging" in [s.name for s in result.subjects]

@pytest.mark.asyncio
async def test_incompatible_metrics_handling():
    """Test handling when metrics have different units/targets"""
    # Mock assets with different target scales
    tool = ComparativeAnalysisTool(
        data_source=mock_data_source_different_targets,
        cache=mock_cache
    )
    result = await tool._arun(
        subjects=["Grinder 5", "CAMA 800-1"],  # Different asset types
        time_range_days=7
    )

    # Should have comparability notes where applicable
    output_metric = next(m for m in result.metrics if m.metric_name == "output")
    # Uses % of target for fair comparison

@pytest.mark.asyncio
async def test_cache_hit():
    """Test caching returns cached result"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)

    # First call
    result1 = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    # Second call should hit cache
    result2 = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    assert result2.cached_at is not None

@pytest.mark.asyncio
async def test_insufficient_subjects():
    """Test handling when < 2 subjects resolve"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source_sparse, cache=mock_cache)
    result = await tool._arun(
        subjects=["NonexistentAsset1", "NonexistentAsset2"]
    )

    assert "Unable to compare" in result.summary or len(result.subjects) < 2

@pytest.mark.asyncio
async def test_ranking_order():
    """Test subjects are correctly ranked by composite score"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)
    result = await tool._arun(subjects=["all grinders"])

    scores = [s.score for s in result.subjects]
    assert scores == sorted(scores, reverse=True)  # Descending order
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_tool_agent_selection():
    """Test agent correctly selects comparative_analysis tool"""
    agent = ManufacturingAgent(tools=[comparative_analysis_tool, other_tools])

    # Test various comparison phrasings
    queries = [
        "Compare Grinder 5 vs Grinder 3",
        "How does Grinding compare to Packaging?",
        "Which grinder performs best?",
        "Show me a side-by-side of all grinders"
    ]

    for query in queries:
        response = await agent.invoke(query)
        assert "comparative_analysis" in response.tool_calls

@pytest.mark.asyncio
async def test_citation_format():
    """Test citations follow Story 4-5 standards"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source, cache=mock_cache)
    result = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    for citation in result.citations:
        assert "source" in citation
        assert "timestamp" in citation
```

### Response Format Examples

**Two-Asset Comparison:**
```markdown
## Comparison: Grinder 5 vs Grinder 3

**Time Range:** Jan 2 - Jan 9, 2026

| Metric | Grinder 5 | Grinder 3 | Winner | Variance |
|--------|-----------|-----------|--------|----------|
| OEE | 78.3% | 85.1% | Grinder 3 | 8% |
| Output | 4,230 units | 4,890 units | Grinder 3 | 14% |
| Downtime | 4.2 hours | 2.1 hours | Grinder 3 | 50% |
| Waste | 2.8% | 1.9% | Grinder 3 | 32% |

**Summary:** Grinder 3 outperforms Grinder 5 overall, with significantly less downtime and higher output.

**Recommendations:**
- Investigate downtime gap: Grinder 5 has 50% more downtime than Grinder 3
- Review waste patterns on Grinder 5

[Citations: daily_summaries Jan 2-9, 2026; assets table]

Would you like me to dig into the specific downtime reasons for Grinder 5?
```

**Multi-Asset Ranking:**
```markdown
## All Grinders Performance Ranking

**Time Range:** Jan 2 - Jan 9, 2026

| Rank | Asset | OEE | Output | Score |
|------|-------|-----|--------|-------|
| 1 | Grinder 3 | 85.1% | 4,890 | 82.4 |
| 2 | Grinder 1 | 81.2% | 4,560 | 78.9 |
| 3 | Grinder 2 | 79.5% | 4,340 | 76.1 |
| 4 | Grinder 5 | 78.3% | 4,230 | 74.8 |

**Summary:** Top performers: Grinder 3, Grinder 1, Grinder 2. Largest difference in downtime: 42% gap between best and worst.

**Recommendations:**
- Focus improvement efforts on Grinder 5 (lowest ranked)
- Apply Grinder 3 practices to other grinders

[Citations: daily_summaries Jan 2-9, 2026; assets table]
```

**Area Comparison:**
```markdown
## Area Comparison: Grinding vs Packaging

**Time Range:** Jan 2 - Jan 9, 2026

| Metric | Grinding (4 assets) | Packaging (3 assets) | Winner |
|--------|---------------------|---------------------|--------|
| Avg OEE | 81.0% | 77.3% | Grinding |
| Total Output | 18,020 units | 12,450 units | Grinding |
| Total Downtime | 12.3 hours | 18.7 hours | Grinding |

**Summary:** Grinding outperforms Packaging overall, with higher OEE and significantly less downtime.

**Top Performers by Area:**
- Grinding: Grinder 3 (85.1% OEE)
- Packaging: CAMA 800-1 (79.2% OEE)

[Citations: daily_summaries Jan 2-9, 2026; assets table grouped by area]
```

### References

- [Source: _bmad-output/planning-artifacts/epic-7.md#Story 7.2] - Comparative Analysis Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.3] - Intelligence & Memory Tools specification
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.4] - Supabase tables: daily_summaries, assets, shift_targets
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Plant Object Model and data structure
- [Source: _bmad-output/implementation-artifacts/7-1-memory-recall-tool.md] - Epic 7 tool implementation patterns
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#NFR7] - Caching requirements (15-min TTL)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
