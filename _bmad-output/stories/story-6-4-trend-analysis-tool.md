# Story 6.4: Trend Analysis Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to see how an asset's performance has changed over time**,
so that **I can identify patterns, anomalies, and the impact of changes**.

## Acceptance Criteria

1. **Basic Trend Query**
   - Given a user asks "How has Grinder 5 performed over the last 30 days?"
   - When the Trend Analysis tool is invoked
   - Then the response includes:
     - Trend direction (improving/declining/stable)
     - Average metric value over the period
     - Min and max values with dates
     - Notable anomalies (values >2 std dev from mean)
     - Comparison to baseline (first week of period)
   - And data supports the trend conclusion

2. **Metric-Specific Trend Query**
   - Given a user asks about a specific metric (e.g., "OEE trend for Grinding area")
   - When the Trend Analysis tool is invoked
   - Then the response focuses on that metric
   - And shows the metric-specific trend

3. **Custom Time Range Query**
   - Given a user asks for trend over a custom time range (e.g., "last 90 days")
   - When the Trend Analysis tool is invoked
   - Then the response covers the specified range
   - And adjusts granularity appropriately (daily vs weekly)

4. **Insufficient Data Handling**
   - Given insufficient data exists for trend analysis (<7 days)
   - When the Trend Analysis tool is invoked
   - Then the response states "Not enough data for trend analysis - need at least 7 days"
   - And shows available point-in-time data instead

5. **Anomaly Detection**
   - Anomalies are defined as values >2 standard deviations from the mean
   - Each anomaly includes: date, value, deviation from mean, possible cause (if available)
   - Anomalies are highlighted in the response

6. **Citation Compliance**
   - All trend analysis responses include citations with source table and date range
   - Citations follow format: [Source: daily_summaries @ date_range]
   - Response includes data freshness indicator

7. **Performance Requirements**
   - Response time < 2 seconds (p95)
   - Cache TTL: 15 minutes (daily data)

## Tasks / Subtasks

- [ ] Task 1: Create Trend Analysis Pydantic Schemas (AC: #1, #5, #6)
  - [ ] 1.1 Define TrendAnalysisInput schema: asset_id (optional), area (optional), metric (default: "oee"), time_range_days (7/14/30/60/90, default: 30)
  - [ ] 1.2 Define MetricType enum: OEE, OUTPUT, DOWNTIME, WASTE, AVAILABILITY, PERFORMANCE, QUALITY
  - [ ] 1.3 Define TrendDirection enum: IMPROVING, DECLINING, STABLE
  - [ ] 1.4 Define TrendStatistics schema: mean, min (value + date), max (value + date), std_dev, trend_slope
  - [ ] 1.5 Define Anomaly schema: date, value, expected_value, deviation, deviation_std_devs, possible_cause
  - [ ] 1.6 Define BaselineComparison schema: baseline_period, baseline_value, current_value, change_amount, change_percent
  - [ ] 1.7 Define TrendAnalysisOutput schema: trend_direction, statistics, data_points (optional), anomalies list, baseline_comparison, conclusion_text, citations, data_freshness

- [ ] Task 2: Implement Trend Analysis Tool (AC: #1, #2, #3, #4)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/trend_analysis.py`
  - [ ] 2.2 Inherit from ManufacturingTool base class (from Story 5.1)
  - [ ] 2.3 Implement tool description for intent matching: "Analyze performance trends over time with anomaly detection"
  - [ ] 2.4 Implement `_arun` method with data source abstraction layer
  - [ ] 2.5 Implement time range support (7, 14, 30, 60, 90 days)
  - [ ] 2.6 Implement metric selection (OEE, output, downtime, waste)
  - [ ] 2.7 Implement asset-level and area-level trend analysis
  - [ ] 2.8 Implement minimum data validation (7+ days required)

- [ ] Task 3: Data Access Layer Integration (AC: #1, #2)
  - [ ] 3.1 Add `get_trend_data()` method to DataSource Protocol
  - [ ] 3.2 Implement `get_trend_data()` in SupabaseDataSource
  - [ ] 3.3 Query daily_summaries time series with metric selection
  - [ ] 3.4 Return DataResult with source metadata for citations

- [ ] Task 4: Implement Statistical Calculations (AC: #1, #5)
  - [ ] 4.1 Calculate mean, min, max for selected metric
  - [ ] 4.2 Calculate standard deviation
  - [ ] 4.3 Calculate trend slope using linear regression
  - [ ] 4.4 Implement numpy/pandas for statistical operations

- [ ] Task 5: Implement Trend Direction Detection (AC: #1)
  - [ ] 5.1 Calculate trend slope from linear regression
  - [ ] 5.2 Determine trend direction based on slope threshold
  - [ ] 5.3 Use 5% threshold for "stable" classification
  - [ ] 5.4 Generate supporting evidence for trend conclusion

- [ ] Task 6: Implement Anomaly Detection (AC: #5)
  - [ ] 6.1 Calculate standard deviation for time series
  - [ ] 6.2 Identify values >2 std dev from mean
  - [ ] 6.3 Include date, value, and deviation for each anomaly
  - [ ] 6.4 Cross-reference with downtime_reasons for possible cause
  - [ ] 6.5 Limit anomalies to most significant (top 5)

- [ ] Task 7: Implement Baseline Comparison (AC: #1)
  - [ ] 7.1 Define baseline as first week (7 days) of period
  - [ ] 7.2 Calculate baseline average
  - [ ] 7.3 Compare current period to baseline
  - [ ] 7.4 Calculate change amount and percentage

- [ ] Task 8: Implement Granularity Adjustment (AC: #3)
  - [ ] 8.1 Use daily granularity for periods <= 30 days
  - [ ] 8.2 Use weekly aggregation for periods > 30 days
  - [ ] 8.3 Adjust statistical calculations for weekly data
  - [ ] 8.4 Include granularity in response metadata

- [ ] Task 9: Implement Insufficient Data Handling (AC: #4)
  - [ ] 9.1 Check data point count before analysis
  - [ ] 9.2 Return honest response if < 7 days of data
  - [ ] 9.3 Show available point-in-time data as alternative
  - [ ] 9.4 Suggest time range that would have sufficient data

- [ ] Task 10: Implement Caching (AC: #7)
  - [ ] 10.1 Add 15-minute TTL cache for trend analysis queries
  - [ ] 10.2 Use cache key pattern: `trend_analysis:{user_id}:{params_hash}`
  - [ ] 10.3 Include `cached_at` timestamp in response metadata
  - [ ] 10.4 Support `force_refresh=true` parameter for cache bypass

- [ ] Task 11: Citation Generation (AC: #6)
  - [ ] 11.1 Generate citations for daily_summaries data range
  - [ ] 11.2 Include date range in citation
  - [ ] 11.3 Format citations per Story 4.5 patterns
  - [ ] 11.4 Include data freshness timestamp in response

- [ ] Task 12: Tool Registration (AC: #1)
  - [ ] 12.1 Register TrendAnalysisTool with agent tool registry
  - [ ] 12.2 Verify auto-discovery picks up the new tool
  - [ ] 12.3 Test intent matching with sample queries

- [ ] Task 13: Testing (AC: #1-7)
  - [ ] 13.1 Unit tests for TrendAnalysisTool with mock data source
  - [ ] 13.2 Test trend direction calculation (improving/declining/stable)
  - [ ] 13.3 Test statistical calculations (mean, std dev, slope)
  - [ ] 13.4 Test anomaly detection (>2 std dev)
  - [ ] 13.5 Test baseline comparison
  - [ ] 13.6 Test granularity adjustment (daily vs weekly)
  - [ ] 13.7 Test insufficient data handling
  - [ ] 13.8 Test metric-specific queries
  - [ ] 13.9 Test area-level aggregation
  - [ ] 13.10 Test citation generation
  - [ ] 13.11 Test caching behavior
  - [ ] 13.12 Integration test with actual Supabase connection

## Dev Notes

### Architecture Patterns

- **Tool Base Class:** Inherit from ManufacturingTool (from Story 5.1)
- **Data Access:** Use DataSource Protocol abstraction layer (from Story 5.2)
- **Statistical Analysis:** Use numpy for calculations (mean, std dev, linear regression)
- **Caching:** Use cachetools TTLCache with 15-minute TTL (from Story 5.8)
- **Citations:** Follow CitedResponse pattern (from Story 4.5)
- **Response Format:** NFR6 compliance with structured JSON output

### Technical Requirements

**Supported Metrics:**
```python
class MetricType(str, Enum):
    OEE = "oee"                    # Overall Equipment Effectiveness
    OUTPUT = "output"              # Production output (units)
    DOWNTIME = "downtime"          # Downtime minutes
    WASTE = "waste"                # Waste/scrap count
    AVAILABILITY = "availability"  # OEE availability component
    PERFORMANCE = "performance"    # OEE performance component
    QUALITY = "quality"            # OEE quality component
```

**Trend Direction Thresholds:**
```python
TREND_THRESHOLD = 0.05  # 5% change threshold for stable classification

class TrendDirection(str, Enum):
    IMPROVING = "improving"   # Slope > +5% normalized
    DECLINING = "declining"   # Slope < -5% normalized
    STABLE = "stable"         # Slope within +/- 5%
```

**Anomaly Detection Threshold:**
```python
ANOMALY_THRESHOLD_STD_DEV = 2.0  # Values >2 std dev from mean
```

**Trend Analysis Tool Implementation Pattern:**
```python
import numpy as np
from apps.api.app.services.agent.base import ManufacturingTool
from apps.api.app.services.agent.data_source import get_data_source
from apps.api.app.models.agent import TrendAnalysisInput, TrendAnalysisOutput

class TrendAnalysisTool(ManufacturingTool):
    name: str = "trend_analysis"
    description: str = """Analyze performance trends over time with anomaly detection.
    Use this tool when users ask about:
    - How an asset has performed over time
    - Performance trends (improving/declining)
    - Historical performance patterns
    - Anomalies or unusual performance
    - Comparison to baseline

    Supports:
    - Multiple metrics (OEE, output, downtime, waste)
    - Time ranges: 7, 14, 30, 60, 90 days
    - Asset-level or area-level analysis
    - Anomaly detection (>2 std dev)
    - Baseline comparison (first week vs current)
    """
    args_schema: Type[BaseModel] = TrendAnalysisInput
    citations_required: bool = True
    cache_ttl: int = 900  # 15 minutes for daily data

    async def _arun(self, **kwargs) -> TrendAnalysisOutput:
        data_source = get_data_source()

        # Parse parameters
        time_range_days = kwargs.get("time_range_days", 30)
        metric = kwargs.get("metric", MetricType.OEE)

        # Fetch time series data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_range_days)

        result = await data_source.get_trend_data(
            start_date=start_date,
            end_date=end_date,
            asset_id=kwargs.get("asset_id"),
            area=kwargs.get("area"),
            metric=metric
        )

        # Check minimum data requirement
        if len(result.data) < 7:
            return self._format_insufficient_data_response(result)

        # Extract metric values as time series
        values = np.array([r[metric.value] for r in result.data])
        dates = [r["date"] for r in result.data]

        # Calculate statistics
        statistics = self._calculate_statistics(values, dates)

        # Determine trend direction
        trend_direction = self._determine_trend_direction(values)

        # Detect anomalies
        anomalies = self._detect_anomalies(values, dates, result.data)

        # Calculate baseline comparison
        baseline = self._calculate_baseline_comparison(values, dates)

        # Adjust granularity for long periods
        granularity = "daily" if time_range_days <= 30 else "weekly"

        # Generate conclusion text
        conclusion = self._generate_conclusion(
            trend_direction, statistics, anomalies, metric
        )

        # Generate citations
        citations = self._generate_citations(result.source_metadata, start_date, end_date)

        return TrendAnalysisOutput(
            trend_direction=trend_direction,
            statistics=statistics,
            anomalies=anomalies,
            baseline_comparison=baseline,
            conclusion_text=conclusion,
            granularity=granularity,
            citations=citations,
            data_freshness=result.timestamp
        )
```

**Statistical Calculations:**
```python
import numpy as np
from scipy import stats

def _calculate_statistics(self, values: np.ndarray, dates: list) -> TrendStatistics:
    """Calculate descriptive statistics for time series."""
    mean = np.mean(values)
    std_dev = np.std(values)
    min_idx = np.argmin(values)
    max_idx = np.argmax(values)

    # Calculate trend slope using linear regression
    x = np.arange(len(values))
    slope, _, _, _, _ = stats.linregress(x, values)

    return TrendStatistics(
        mean=float(mean),
        min={"value": float(values[min_idx]), "date": dates[min_idx]},
        max={"value": float(values[max_idx]), "date": dates[max_idx]},
        std_dev=float(std_dev),
        trend_slope=float(slope)
    )

def _determine_trend_direction(self, values: np.ndarray) -> TrendDirection:
    """
    Determine trend direction based on linear regression slope.

    Uses 5% threshold normalized by mean to determine stability.
    """
    x = np.arange(len(values))
    slope, _, _, _, _ = stats.linregress(x, values)

    # Normalize slope by mean for percentage-based threshold
    mean = np.mean(values)
    if mean == 0:
        return TrendDirection.STABLE

    # Total change over period as percentage of mean
    total_change = slope * len(values)
    change_percent = total_change / mean

    if change_percent > TREND_THRESHOLD:
        return TrendDirection.IMPROVING
    elif change_percent < -TREND_THRESHOLD:
        return TrendDirection.DECLINING
    else:
        return TrendDirection.STABLE

def _detect_anomalies(
    self,
    values: np.ndarray,
    dates: list,
    raw_data: list
) -> list[Anomaly]:
    """
    Detect anomalies as values >2 standard deviations from mean.
    """
    mean = np.mean(values)
    std_dev = np.std(values)

    anomalies = []
    for i, (value, date) in enumerate(zip(values, dates)):
        deviation = abs(value - mean)
        std_devs_away = deviation / std_dev if std_dev > 0 else 0

        if std_devs_away > ANOMALY_THRESHOLD_STD_DEV:
            # Try to find possible cause from downtime_reasons
            possible_cause = None
            if raw_data[i].get("downtime_reasons"):
                # Get top downtime reason for that day
                reasons = raw_data[i]["downtime_reasons"]
                if reasons:
                    top_reason = max(reasons, key=reasons.get)
                    possible_cause = top_reason

            anomalies.append(Anomaly(
                date=date,
                value=float(value),
                expected_value=float(mean),
                deviation=float(deviation),
                deviation_std_devs=float(std_devs_away),
                possible_cause=possible_cause
            ))

    # Return top 5 most significant anomalies
    anomalies.sort(key=lambda x: x.deviation_std_devs, reverse=True)
    return anomalies[:5]

def _calculate_baseline_comparison(
    self,
    values: np.ndarray,
    dates: list
) -> BaselineComparison:
    """
    Compare current performance to baseline (first 7 days).
    """
    baseline_values = values[:7]
    current_values = values[-7:] if len(values) >= 14 else values[7:]

    baseline_avg = np.mean(baseline_values)
    current_avg = np.mean(current_values)

    change_amount = current_avg - baseline_avg
    change_percent = (change_amount / baseline_avg * 100) if baseline_avg > 0 else 0

    return BaselineComparison(
        baseline_period={"start": dates[0], "end": dates[6]},
        baseline_value=float(baseline_avg),
        current_value=float(current_avg),
        change_amount=float(change_amount),
        change_percent=float(change_percent)
    )
```

**Supabase Query Pattern:**
```python
async def get_trend_data(
    self,
    start_date: datetime,
    end_date: datetime,
    asset_id: Optional[str] = None,
    area: Optional[str] = None,
    metric: MetricType = MetricType.OEE
) -> DataResult:
    """
    Query daily_summaries for trend analysis.

    Returns time series data for specified metric.
    """
    # Select appropriate columns based on metric
    columns = "date, " + metric.value
    if metric == MetricType.OEE:
        columns = "date, oee, availability, performance, quality"

    query = (
        self.client
        .from_("daily_summaries")
        .select(f"{columns}, downtime_reasons, assets!inner(id, name, area)")
        .gte("date", start_date.date().isoformat())
        .lte("date", end_date.date().isoformat())
        .order("date", desc=False)  # Chronological order for time series
    )

    if asset_id:
        query = query.eq("asset_id", asset_id)
    if area:
        query = query.eq("assets.area", area)

    result = await query.execute()

    # For area queries, aggregate by date
    if area and not asset_id:
        result.data = self._aggregate_by_date(result.data, metric)

    return DataResult(
        data=result.data,
        source_metadata={
            "table": "daily_summaries",
            "query_time": datetime.utcnow(),
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "metric": metric.value
        }
    )
```

**Response Format Example:**
```json
{
  "trend_direction": "improving",
  "statistics": {
    "mean": 78.5,
    "min": {"value": 62.3, "date": "2025-12-15"},
    "max": {"value": 89.2, "date": "2026-01-05"},
    "std_dev": 6.8,
    "trend_slope": 0.42
  },
  "anomalies": [
    {
      "date": "2025-12-15",
      "value": 62.3,
      "expected_value": 78.5,
      "deviation": 16.2,
      "deviation_std_devs": 2.38,
      "possible_cause": "Material Jam"
    }
  ],
  "baseline_comparison": {
    "baseline_period": {"start": "2025-12-10", "end": "2025-12-16"},
    "baseline_value": 74.2,
    "current_value": 82.8,
    "change_amount": 8.6,
    "change_percent": 11.6
  },
  "conclusion_text": "Grinder 5's OEE has been improving over the last 30 days, increasing from an average of 74.2% in the first week to 82.8% recently (+11.6%). One anomaly was detected on Dec 15 (62.3% OEE) likely due to Material Jam.",
  "granularity": "daily",
  "citations": [
    {
      "source_type": "database",
      "source_table": "daily_summaries",
      "record_id": "2025-12-10 to 2026-01-08",
      "timestamp": "2026-01-09T09:00:00Z",
      "confidence": 1.0
    }
  ],
  "data_freshness": "2026-01-09T09:00:00Z"
}
```

**Insufficient Data Response:**
```python
def _format_insufficient_data_response(self, result: DataResult) -> TrendAnalysisOutput:
    """Format response when insufficient data for trend analysis."""
    return TrendAnalysisOutput(
        trend_direction=None,
        statistics=None,
        anomalies=[],
        baseline_comparison=None,
        conclusion_text=f"Not enough data for trend analysis - need at least 7 days (found {len(result.data)} days). Here's the available point-in-time data:",
        available_data=result.data,
        suggestion="Try requesting a longer time range to enable trend analysis.",
        citations=self._generate_citations(result.source_metadata),
        data_freshness=result.timestamp
    )
```

### Project Structure Notes

**Files to Create:**
```
apps/api/app/
  services/agent/tools/
    trend_analysis.py         # TrendAnalysisTool implementation
  models/
    agent.py                  # Add TrendAnalysisInput/Output schemas (extend existing)

apps/api/tests/
  test_trend_analysis_tool.py  # Unit and integration tests
```

**Files to Modify:**
```
apps/api/app/services/agent/data_source/protocol.py  # Add get_trend_data method
apps/api/app/services/agent/data_source/supabase.py  # Implement get_trend_data
```

**Dependencies to Add:**
```
# requirements.txt
numpy>=1.24.0
scipy>=1.10.0  # For linear regression
```

### Dependencies

**Requires (must be completed):**
- Story 5.1: Agent Framework & Tool Registry (ManufacturingTool base class)
- Story 5.2: Data Access Abstraction Layer (DataSource Protocol)
- Story 5.8: Tool Response Caching (caching infrastructure)
- Story 1.4: Analytical Cache Schema (daily_summaries table with time series data)

**Enables:**
- Story 7.5: Recommendation Engine (identify patterns for recommendations)
- Advanced analytics and reporting features

### NFR Compliance

- **NFR4 (Agent Honesty):** Clearly state when insufficient data; show available data as alternative
- **NFR6 (Response Structure):** Return structured JSON with statistical evidence
- **NFR7 (Caching):** 15-minute TTL for daily data reduces database load

### Testing Guidance

**Unit Tests:**
```python
import numpy as np
import pytest

@pytest.mark.asyncio
async def test_trend_analysis_improving():
    """Test detection of improving trend."""
    tool = TrendAnalysisTool()
    # Create improving trend data
    mock_data = [{"date": f"2026-01-{i:02d}", "oee": 70 + i} for i in range(1, 31)]

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert result.trend_direction == TrendDirection.IMPROVING

@pytest.mark.asyncio
async def test_trend_analysis_declining():
    """Test detection of declining trend."""
    tool = TrendAnalysisTool()
    # Create declining trend data
    mock_data = [{"date": f"2026-01-{i:02d}", "oee": 90 - i} for i in range(1, 31)]

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert result.trend_direction == TrendDirection.DECLINING

@pytest.mark.asyncio
async def test_trend_analysis_stable():
    """Test detection of stable trend."""
    tool = TrendAnalysisTool()
    # Create stable data with small variance
    mock_data = [{"date": f"2026-01-{i:02d}", "oee": 80 + (i % 3 - 1)} for i in range(1, 31)]

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert result.trend_direction == TrendDirection.STABLE

@pytest.mark.asyncio
async def test_trend_analysis_anomaly_detection():
    """Test anomaly detection (>2 std dev)."""
    tool = TrendAnalysisTool()
    # Create data with one clear anomaly
    values = [80] * 29 + [50]  # Last value is anomaly

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert len(result.anomalies) >= 1
    assert result.anomalies[0].deviation_std_devs > 2.0

@pytest.mark.asyncio
async def test_trend_analysis_baseline_comparison():
    """Test baseline comparison calculation."""
    tool = TrendAnalysisTool()

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert result.baseline_comparison is not None
    assert result.baseline_comparison.baseline_value > 0
    assert result.baseline_comparison.change_percent is not None

@pytest.mark.asyncio
async def test_trend_analysis_insufficient_data():
    """Test honest response when insufficient data."""
    tool = TrendAnalysisTool()
    mock_data = [{"date": "2026-01-01", "oee": 80}]  # Only 1 day

    result = await tool._arun(asset_id="ast-001", time_range_days=30)

    assert result.trend_direction is None
    assert "Not enough data" in result.conclusion_text

@pytest.mark.asyncio
async def test_trend_analysis_granularity_adjustment():
    """Test granularity switches to weekly for long periods."""
    tool = TrendAnalysisTool()

    # 30 days = daily
    result_30 = await tool._arun(asset_id="ast-001", time_range_days=30)
    assert result_30.granularity == "daily"

    # 60 days = weekly
    result_60 = await tool._arun(asset_id="ast-001", time_range_days=60)
    assert result_60.granularity == "weekly"

@pytest.mark.asyncio
async def test_trend_analysis_metric_selection():
    """Test different metric selections."""
    tool = TrendAnalysisTool()

    for metric in [MetricType.OEE, MetricType.OUTPUT, MetricType.DOWNTIME]:
        result = await tool._arun(asset_id="ast-001", metric=metric)
        assert result.statistics is not None

@pytest.mark.asyncio
async def test_trend_analysis_statistical_accuracy():
    """Test statistical calculations are accurate."""
    tool = TrendAnalysisTool()
    values = np.array([70, 75, 80, 85, 90, 72, 78, 82])

    expected_mean = np.mean(values)
    expected_std = np.std(values)

    result = await tool._arun(asset_id="ast-001")

    assert result.statistics.mean == pytest.approx(expected_mean, rel=0.01)
    assert result.statistics.std_dev == pytest.approx(expected_std, rel=0.01)
```

### References

- [Source: _bmad-output/planning-artifacts/epic-6.md#Story 6.4] - Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.3] - Trend Analysis tool specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.1] - ManufacturingTool base class pattern
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.2] - Data Access Abstraction Layer
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation format patterns
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - daily_summaries time series schema

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
