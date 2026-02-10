# Story 7.2: Comparative Analysis Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to compare two or more assets or areas side-by-side**,
so that I can **identify best performers, understand differences, and make informed decisions about resource allocation**.

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

2. **Multi-Asset Comparison**
   - Given a user asks "Compare all grinders this week"
   - When the Comparative Analysis tool is invoked
   - Then the response compares all assets matching "grinder"
   - And ranks them by overall performance
   - And supports 2-10 assets in a single comparison

3. **Area-Level Comparison**
   - Given a user asks to compare areas (e.g., "Compare Grinding vs Packaging")
   - When the Comparative Analysis tool is invoked
   - Then the response aggregates metrics at the area level
   - And shows area-level totals and averages
   - And identifies top/bottom performers within each area

4. **Incompatible Metrics Handling**
   - Given assets have incompatible metrics (different units or targets)
   - When the Comparative Analysis tool is invoked
   - Then the response includes a note about comparability
   - And uses percentage-based comparisons where appropriate
   - And normalizes metrics for fair comparison

5. **Default Time Range**
   - Comparison defaults to last 7 days unless specified
   - User can specify custom time ranges (e.g., "this shift", "last month")
   - Time range is clearly stated in response

6. **Citation & Data Freshness**
   - All comparison metrics include source citations
   - Data freshness timestamp included in response
   - Cache TTL: 15 minutes for comparison results

## Tasks / Subtasks

- [ ] Task 1: Define Comparative Analysis Schemas (AC: #1, #2)
  - [ ] 1.1 Create `ComparativeAnalysisInput` Pydantic model with fields: `subjects` (List[str]), `comparison_type` ('asset' | 'area'), `metrics` (optional filter), `time_range` (default: 7 days)
  - [ ] 1.2 Create `ComparisonMetric` model with fields: `metric_name`, `values` (dict keyed by subject), `unit`, `best_performer`, `variance_pct`
  - [ ] 1.3 Create `ComparativeAnalysisOutput` model with fields: `subjects`, `metrics`, `summary`, `recommendation`, `citations`, `data_as_of`
  - [ ] 1.4 Add schemas to `apps/api/app/models/agent.py`

- [ ] Task 2: Implement Comparative Analysis Tool (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/comparative_analysis.py`
  - [ ] 2.2 Implement asset name resolution (fuzzy match "grinder" to all grinder assets)
  - [ ] 2.3 Implement single asset vs single asset comparison
  - [ ] 2.4 Implement multi-asset comparison (2-10 assets)
  - [ ] 2.5 Implement area-level aggregation for area comparisons
  - [ ] 2.6 Query `daily_summaries`, `assets`, `shift_targets` for metrics

- [ ] Task 3: Implement Metric Normalization (AC: #4)
  - [ ] 3.1 Detect incompatible units across assets
  - [ ] 3.2 Normalize metrics to percentages for fair comparison
  - [ ] 3.3 Calculate variance percentages between subjects
  - [ ] 3.4 Add comparability notes when normalization applied

- [ ] Task 4: Implement Result Formatting (AC: #1, #2, #5)
  - [ ] 4.1 Generate side-by-side metrics table (markdown)
  - [ ] 4.2 Add variance highlighting indicators (+/- with color hints)
  - [ ] 4.3 Identify and highlight best/worst performers
  - [ ] 4.4 Generate summary of key differences
  - [ ] 4.5 Generate recommendation when clear winner exists

- [ ] Task 5: Integrate with LangChain Agent (AC: #1, #2)
  - [ ] 5.1 Create LangChain Tool wrapper for ComparativeAnalysisTool
  - [ ] 5.2 Define tool description for agent selection
  - [ ] 5.3 Register tool with ManufacturingAgent
  - [ ] 5.4 Test tool selection for comparison queries

- [ ] Task 6: Implement Caching (AC: #6)
  - [ ] 6.1 Add 15-minute cache for comparison results
  - [ ] 6.2 Cache key includes: subjects, time_range, metrics
  - [ ] 6.3 Include `cached_at` in response metadata
  - [ ] 6.4 Support `force_refresh` parameter

- [ ] Task 7: Testing and Validation (AC: #1-6)
  - [ ] 7.1 Unit tests for two-asset comparison
  - [ ] 7.2 Unit tests for multi-asset comparison
  - [ ] 7.3 Unit tests for area-level aggregation
  - [ ] 7.4 Unit tests for metric normalization
  - [ ] 7.5 Integration tests for LangChain tool registration
  - [ ] 7.6 Performance tests (< 2 second response time)

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain AgentExecutor with tool registration
- **Data Access:** Supabase PostgreSQL via existing data access layer
- **Citation System:** Integrate with existing citation infrastructure from Story 4-5

### Technical Requirements

**Comparative Analysis Schemas:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime

class ComparativeAnalysisInput(BaseModel):
    """Input schema for Comparative Analysis tool"""
    subjects: List[str] = Field(
        description="Asset names or area names to compare (2-10 items)",
        min_length=2,
        max_length=10
    )
    comparison_type: Literal["asset", "area"] = Field(
        default="asset",
        description="Whether comparing individual assets or areas"
    )
    metrics: Optional[List[str]] = Field(
        default=None,
        description="Specific metrics to compare (OEE, output, downtime, waste). Defaults to all."
    )
    time_range_days: int = Field(
        default=7,
        description="Number of days for comparison period"
    )

class ComparisonMetric(BaseModel):
    """A single metric compared across subjects"""
    metric_name: str
    values: Dict[str, float]  # subject_name -> value
    unit: str
    best_performer: str
    worst_performer: str
    variance_pct: float  # Difference between best and worst as percentage
    normalized: bool = False  # True if percentage normalization applied

class ComparativeAnalysisOutput(BaseModel):
    """Output schema for Comparative Analysis tool"""
    subjects: List[str]
    comparison_type: str
    time_range: str
    metrics: List[ComparisonMetric]
    summary: str
    recommendation: Optional[str]  # Only if clear winner
    comparability_notes: List[str]  # Notes about metric compatibility
    citations: List[dict]
    data_as_of: datetime
```

**Comparative Analysis Tool Implementation:**
```python
from langchain.tools import BaseTool
from typing import Type

class ComparativeAnalysisTool(BaseTool):
    name: str = "comparative_analysis"
    description: str = """Compare two or more assets or areas side-by-side on key metrics
    (OEE, output, downtime, waste). Use this when the user wants to compare performance,
    find the best performer, or understand differences between assets/areas.
    Examples: 'Compare Grinder 5 vs Grinder 3', 'Compare all grinders this week',
    'Compare Grinding vs Packaging areas', 'Which asset is performing better?'"""
    args_schema: Type[ComparativeAnalysisInput] = ComparativeAnalysisInput

    async def _arun(
        self,
        subjects: List[str],
        comparison_type: str = "asset",
        metrics: Optional[List[str]] = None,
        time_range_days: int = 7
    ) -> ComparativeAnalysisOutput:

        # Resolve subject names to actual assets/areas
        resolved_subjects = await self._resolve_subjects(subjects, comparison_type)

        # Default metrics if not specified
        metric_names = metrics or ["oee", "output", "downtime_minutes", "waste_pct"]

        # Fetch data for each subject
        subject_data = {}
        citations = []
        for subject in resolved_subjects:
            data, source = await self._fetch_metrics(
                subject,
                comparison_type,
                metric_names,
                time_range_days
            )
            subject_data[subject] = data
            citations.append(source)

        # Compare and analyze
        comparison_metrics = self._compute_comparisons(subject_data, metric_names)
        comparability_notes = self._check_comparability(subject_data)
        summary = self._generate_summary(comparison_metrics, resolved_subjects)
        recommendation = self._generate_recommendation(comparison_metrics)

        return ComparativeAnalysisOutput(
            subjects=resolved_subjects,
            comparison_type=comparison_type,
            time_range=f"Last {time_range_days} days",
            metrics=comparison_metrics,
            summary=summary,
            recommendation=recommendation,
            comparability_notes=comparability_notes,
            citations=citations,
            data_as_of=datetime.now()
        )

    async def _resolve_subjects(
        self,
        subjects: List[str],
        comparison_type: str
    ) -> List[str]:
        """Resolve fuzzy names like 'all grinders' to actual asset list"""
        resolved = []
        for subject in subjects:
            if "all" in subject.lower():
                # Extract asset type and find all matching
                asset_type = subject.lower().replace("all", "").strip()
                matches = await self.data_source.find_assets_by_type(asset_type)
                resolved.extend(matches)
            else:
                # Single asset lookup
                asset = await self.data_source.find_asset(subject)
                if asset:
                    resolved.append(asset.name)
        return resolved[:10]  # Cap at 10 for readability

    def _compute_comparisons(
        self,
        subject_data: Dict[str, Dict],
        metric_names: List[str]
    ) -> List[ComparisonMetric]:
        """Compute comparison metrics with variance analysis"""
        results = []
        for metric in metric_names:
            values = {s: data.get(metric, 0) for s, data in subject_data.items()}
            sorted_by_value = sorted(values.items(), key=lambda x: x[1], reverse=True)

            best = sorted_by_value[0]
            worst = sorted_by_value[-1]
            variance = ((best[1] - worst[1]) / worst[1] * 100) if worst[1] > 0 else 0

            results.append(ComparisonMetric(
                metric_name=metric,
                values=values,
                unit=self._get_unit(metric),
                best_performer=best[0],
                worst_performer=worst[0],
                variance_pct=round(variance, 1)
            ))
        return results
```

**Response Formatting:**
```python
def format_comparison_table(output: ComparativeAnalysisOutput) -> str:
    """Format comparison as markdown table with variance indicators"""
    lines = [f"## Comparison: {' vs '.join(output.subjects)}"]
    lines.append(f"*Period: {output.time_range}*\n")

    # Build table header
    header = "| Metric |"
    for subject in output.subjects:
        header += f" {subject} |"
    header += " Best |"
    lines.append(header)

    # Separator
    sep = "|--------|" + "---------|" * len(output.subjects) + "------|"
    lines.append(sep)

    # Data rows with variance indicators
    for metric in output.metrics:
        row = f"| {metric.metric_name.replace('_', ' ').title()} |"
        for subject in output.subjects:
            value = metric.values.get(subject, 0)
            indicator = ""
            if subject == metric.best_performer:
                indicator = " [+]"
            elif subject == metric.worst_performer:
                indicator = " [-]"
            row += f" {value}{metric.unit}{indicator} |"
        row += f" {metric.best_performer} |"
        lines.append(row)

    return "\n".join(lines)
```

### Database Tables Referenced

| Table | Usage |
|-------|-------|
| `assets` | Asset metadata and area assignments |
| `daily_summaries` | OEE, output, downtime, waste metrics |
| `shift_targets` | Target values for variance calculation |
| `cost_centers` | Financial context for areas |

### Dependencies

**Requires (must be completed):**
- Story 5.1: Agent Framework & Tool Registry (provides tool registration pattern)
- Story 5.2: Data Access Abstraction Layer (provides data source interface)
- Story 5.4: OEE Query Tool (provides OEE calculation patterns)
- Story 4.5: Cited Response Generation (provides citation infrastructure)

**Enables:**
- FR7.3: Comparative Analysis capability for multi-asset comparison
- Story 7.5: Recommendation Engine can use comparison insights
- Enhanced decision-making for resource allocation

### Project Structure Notes

```
apps/api/app/
  services/
    agent/
      tools/
        comparative_analysis.py   # Comparative Analysis tool (NEW)
  models/
    agent.py                      # Add ComparativeAnalysisInput/Output (MODIFY)

apps/api/tests/
  test_comparative_analysis_tool.py  # Unit and integration tests (NEW)
```

### NFR Compliance

- **NFR1 (Accuracy):** All metrics include citations to source data
- **NFR6 (Response Structure):** Structured table output with clear indicators
- **NFR7 (Caching):** 15-minute cache for comparison results

### Testing Guidance

**Unit Tests:**
```python
import pytest
from datetime import datetime

@pytest.mark.asyncio
async def test_two_asset_comparison():
    """Test basic two-asset comparison"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)
    result = await tool._arun(
        subjects=["Grinder 5", "Grinder 3"],
        comparison_type="asset"
    )

    assert len(result.subjects) == 2
    assert len(result.metrics) >= 4  # OEE, output, downtime, waste
    assert result.summary != ""
    for metric in result.metrics:
        assert metric.best_performer in result.subjects

@pytest.mark.asyncio
async def test_multi_asset_comparison():
    """Test comparison with 'all grinders' expansion"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)
    result = await tool._arun(
        subjects=["all grinders"],
        comparison_type="asset"
    )

    # Should expand to actual grinder assets
    assert len(result.subjects) > 1
    assert len(result.subjects) <= 10

@pytest.mark.asyncio
async def test_area_comparison():
    """Test area-level aggregation"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)
    result = await tool._arun(
        subjects=["Grinding", "Packaging"],
        comparison_type="area"
    )

    assert result.comparison_type == "area"
    assert "Grinding" in result.subjects
    assert "Packaging" in result.subjects

@pytest.mark.asyncio
async def test_metric_normalization():
    """Test percentage normalization for different units"""
    # Mock data with different target values
    tool = ComparativeAnalysisTool(data_source=mock_data_different_targets)
    result = await tool._arun(
        subjects=["Grinder 5", "CAMA 800"],
        comparison_type="asset"
    )

    # Should include normalization note
    assert len(result.comparability_notes) > 0

@pytest.mark.asyncio
async def test_variance_calculation():
    """Test variance percentage calculation"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)
    result = await tool._arun(
        subjects=["Grinder 5", "Grinder 3"],
        comparison_type="asset"
    )

    for metric in result.metrics:
        # Variance should be calculated correctly
        best_val = metric.values[metric.best_performer]
        worst_val = metric.values[metric.worst_performer]
        if worst_val > 0:
            expected_variance = (best_val - worst_val) / worst_val * 100
            assert abs(metric.variance_pct - expected_variance) < 0.1

@pytest.mark.asyncio
async def test_caching():
    """Test 15-minute cache for comparison results"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)

    # First call
    result1 = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    # Second call should be cached
    result2 = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    # Data should be same (from cache)
    assert result1.data_as_of == result2.data_as_of
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_tool_agent_integration():
    """Test tool is correctly selected by agent"""
    agent = ManufacturingAgent(tools=[comparative_analysis_tool])
    response = await agent.invoke("Compare Grinder 5 vs Grinder 3")

    assert "comparative_analysis" in response.tool_calls

@pytest.mark.asyncio
async def test_citations_included():
    """Test all metrics include citations"""
    tool = ComparativeAnalysisTool(data_source=mock_data_source)
    result = await tool._arun(subjects=["Grinder 5", "Grinder 3"])

    assert len(result.citations) > 0
    for citation in result.citations:
        assert "source_table" in citation
```

### Response Format Examples

**Two-Asset Comparison:**
```markdown
## Comparison: Grinder 5 vs Grinder 3
*Period: Last 7 days*

| Metric | Grinder 5 | Grinder 3 | Best |
|--------|-----------|-----------|------|
| OEE | 78.3% [+] | 72.1% [-] | Grinder 5 |
| Output | 4,820 units | 4,950 units [+] | Grinder 3 |
| Downtime | 4.2 hrs [-] | 2.8 hrs [+] | Grinder 3 |
| Waste | 3.2% | 4.1% [-] | Grinder 5 |

**Summary:**
- Grinder 5 has better OEE (8.6% higher) and lower waste
- Grinder 3 has higher output despite more downtime
- Key difference: Grinder 5's downtime is significantly higher (50% more)

**Recommendation:**
Investigate Grinder 5's downtime causes - addressing this could improve output significantly while maintaining its efficiency advantage.

[Citations: daily_summaries 2026-01-02 to 2026-01-09, shift_targets]
```

**Area Comparison:**
```markdown
## Comparison: Grinding vs Packaging
*Period: Last 7 days (Area-level aggregation)*

| Metric | Grinding (avg) | Packaging (avg) | Best |
|--------|----------------|-----------------|------|
| OEE | 75.2% | 82.4% [+] | Packaging |
| Output | 19,400 units | 18,900 units | Grinding |
| Downtime | 18.5 hrs [-] | 8.2 hrs [+] | Packaging |
| Waste | 3.8% | 2.1% [+] | Packaging |

**Summary:**
- Packaging area outperforms Grinding on efficiency and quality metrics
- Grinding has 2.3x more downtime than Packaging
- Grinding produces slightly more output but at lower efficiency

**Note:** Comparing aggregated area metrics - individual asset performance varies.

[Citations: daily_summaries (5 grinding assets, 3 packaging assets), assets]
```

### References

- [Source: _bmad-output/planning-artifacts/epic-7.md#Story 7.2] - Comparative Analysis Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.3] - Intelligence & Memory Tools specification
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Plant Object Model with assets and areas
- [Source: _bmad-output/implementation-artifacts/5-4-oee-query-tool.md] - OEE calculation patterns (assumed)
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation infrastructure

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
