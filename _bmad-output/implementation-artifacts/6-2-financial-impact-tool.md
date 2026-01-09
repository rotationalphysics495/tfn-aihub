# Story 6.2: Financial Impact Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to understand the financial cost of downtime and waste for any asset or area**,
so that **I can prioritize issues by business impact, not just operational metrics**.

## Acceptance Criteria

1. **Asset-Level Financial Impact Query**
   - Given a user asks "What's the cost of downtime for Grinder 5 yesterday?"
   - When the Financial Impact tool is invoked
   - Then the response includes:
     - Total financial loss (dollars)
     - Breakdown by category (downtime cost, waste cost)
     - Hourly rate used for calculation (from cost_centers)
     - Comparison to average loss for this asset
   - And all calculations include citations with formulas

2. **Area-Level Financial Impact Query**
   - Given a user asks "What's the financial impact for the Grinding area this week?"
   - When the Financial Impact tool is invoked
   - Then the response aggregates across all assets in the area
   - And shows per-asset breakdown
   - And identifies the highest-cost asset

3. **Missing Cost Center Data Handling**
   - Given cost_centers data is missing for an asset
   - When the Financial Impact tool is invoked
   - Then the response indicates "Unable to calculate financial impact for [asset] - no cost center data"
   - And returns available non-financial metrics

4. **Transparent Calculations**
   - All financial impact responses show calculation formulas
   - Downtime cost formula: downtime_minutes * standard_hourly_rate / 60
   - Waste cost formula: waste_count * cost_per_unit
   - Citations reference both source data and calculation basis

5. **Citation Compliance**
   - All financial impact responses include citations with source tables
   - Citations follow format: [Source: daily_summaries @ date], [Evidence: cost_centers calculation]
   - Response includes data freshness indicator

6. **Performance Requirements**
   - Response time < 2 seconds (p95)
   - Cache TTL: 15 minutes (daily data)

## Tasks / Subtasks

- [ ] Task 1: Create Financial Impact Pydantic Schemas (AC: #1, #4, #5)
  - [ ] 1.1 Define FinancialImpactInput schema: time_range (default: "yesterday"), asset_id (optional), area (optional), include_breakdown (default: true)
  - [ ] 1.2 Define CostBreakdown schema: category, amount, calculation_basis, formula_used
  - [ ] 1.3 Define AssetFinancialSummary schema: asset_id, asset_name, total_loss, downtime_cost, waste_cost, hourly_rate, downtime_minutes, waste_count
  - [ ] 1.4 Define FinancialImpactOutput schema: total_loss, breakdown list, per_asset_breakdown (for area queries), highest_cost_asset, average_comparison, citations, data_freshness

- [ ] Task 2: Implement Financial Impact Tool (AC: #1, #2, #3, #4)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/financial_impact.py`
  - [ ] 2.2 Inherit from ManufacturingTool base class (from Story 5.1)
  - [ ] 2.3 Implement tool description for intent matching: "Calculate financial impact of downtime and waste for assets or areas"
  - [ ] 2.4 Implement `_arun` method with data source abstraction layer
  - [ ] 2.5 Implement time range parsing (yesterday, today, this week, last N days, date range)
  - [ ] 2.6 Implement asset-level calculation with cost_centers lookup
  - [ ] 2.7 Implement area-level aggregation with per-asset breakdown
  - [ ] 2.8 Implement highest-cost asset identification
  - [ ] 2.9 Implement average loss comparison calculation

- [ ] Task 3: Data Access Layer Integration (AC: #1, #3)
  - [ ] 3.1 Add `get_financial_metrics()` method to DataSource Protocol
  - [ ] 3.2 Implement `get_financial_metrics()` in SupabaseDataSource
  - [ ] 3.3 Query daily_summaries joined with cost_centers and assets
  - [ ] 3.4 Return DataResult with source metadata for citations
  - [ ] 3.5 Handle missing cost_centers data gracefully

- [ ] Task 4: Implement Financial Calculations (AC: #1, #4)
  - [ ] 4.1 Implement downtime cost calculation: `downtime_minutes * standard_hourly_rate / 60`
  - [ ] 4.2 Implement waste cost calculation: `waste_count * cost_per_unit`
  - [ ] 4.3 Include calculation formulas in response for transparency
  - [ ] 4.4 Store calculation basis (rates used) for citation

- [ ] Task 5: Implement Missing Data Handling (AC: #3)
  - [ ] 5.1 Detect when cost_centers data is missing for asset
  - [ ] 5.2 Return honest response: "Unable to calculate financial impact for [asset] - no cost center data"
  - [ ] 5.3 Return available non-financial metrics (downtime_minutes, waste_count) when cost data unavailable

- [ ] Task 6: Implement Caching (AC: #6)
  - [ ] 6.1 Add 15-minute TTL cache for financial impact queries
  - [ ] 6.2 Use cache key pattern: `financial_impact:{user_id}:{params_hash}`
  - [ ] 6.3 Include `cached_at` timestamp in response metadata
  - [ ] 6.4 Support `force_refresh=true` parameter for cache bypass

- [ ] Task 7: Citation Generation (AC: #5)
  - [ ] 7.1 Generate citations for daily_summaries data sources
  - [ ] 7.2 Generate citations for cost_centers calculation basis
  - [ ] 7.3 Format citations per Story 4.5 patterns
  - [ ] 7.4 Include calculation evidence citations

- [ ] Task 8: Tool Registration (AC: #1)
  - [ ] 8.1 Register FinancialImpactTool with agent tool registry
  - [ ] 8.2 Verify auto-discovery picks up the new tool
  - [ ] 8.3 Test intent matching with sample queries

- [ ] Task 9: Testing (AC: #1-6)
  - [ ] 9.1 Unit tests for FinancialImpactTool with mock data source
  - [ ] 9.2 Test asset-level financial calculation
  - [ ] 9.3 Test area-level aggregation and highest-cost identification
  - [ ] 9.4 Test missing cost_centers handling
  - [ ] 9.5 Test calculation formula transparency
  - [ ] 9.6 Test citation generation
  - [ ] 9.7 Test caching behavior (TTL, force_refresh)
  - [ ] 9.8 Integration test with actual Supabase connection

## Dev Notes

### Architecture Patterns

- **Tool Base Class:** Inherit from ManufacturingTool (from Story 5.1)
- **Data Access:** Use DataSource Protocol abstraction layer (from Story 5.2)
- **Caching:** Use cachetools TTLCache with 15-minute TTL (from Story 5.8)
- **Citations:** Follow CitedResponse pattern (from Story 4.5)
- **Response Format:** NFR6 compliance with structured JSON output

### Technical Requirements

**Financial Calculation Formulas:**
```python
def calculate_downtime_cost(
    downtime_minutes: float,
    standard_hourly_rate: float
) -> tuple[float, str]:
    """
    Calculate cost of downtime.

    Returns:
        (cost, formula_string) for transparency
    """
    cost = downtime_minutes * standard_hourly_rate / 60
    formula = f"{downtime_minutes} min * ${standard_hourly_rate}/hr / 60 = ${cost:.2f}"
    return cost, formula

def calculate_waste_cost(
    waste_count: int,
    cost_per_unit: float
) -> tuple[float, str]:
    """
    Calculate cost of waste/scrap.

    Returns:
        (cost, formula_string) for transparency
    """
    cost = waste_count * cost_per_unit
    formula = f"{waste_count} units * ${cost_per_unit}/unit = ${cost:.2f}"
    return cost, formula
```

**Financial Impact Tool Implementation Pattern:**
```python
from apps.api.app.services.agent.base import ManufacturingTool
from apps.api.app.services.agent.data_source import get_data_source
from apps.api.app.models.agent import FinancialImpactInput, FinancialImpactOutput

class FinancialImpactTool(ManufacturingTool):
    name: str = "financial_impact"
    description: str = """Calculate the financial impact of downtime and waste.
    Use this tool when users ask about:
    - Cost of downtime for an asset or area
    - Financial impact of waste or scrap
    - Dollar loss from production issues
    - What something is "costing us"

    Supports queries for:
    - Specific assets ("cost for Grinder 5")
    - Areas ("financial impact for Grinding area")
    - Time ranges ("yesterday", "this week", "last 7 days")
    """
    args_schema: Type[BaseModel] = FinancialImpactInput
    citations_required: bool = True
    cache_ttl: int = 900  # 15 minutes for daily data

    async def _arun(self, **kwargs) -> FinancialImpactOutput:
        data_source = get_data_source()

        # Parse time range (default: yesterday for T-1 data)
        time_range = self._parse_time_range(kwargs.get("time_range", "yesterday"))

        # Get financial metrics with cost_centers data
        result = await data_source.get_financial_metrics(
            start_date=time_range.start,
            end_date=time_range.end,
            asset_id=kwargs.get("asset_id"),
            area=kwargs.get("area")
        )

        # Handle missing cost center data
        if not result.has_cost_data:
            return self._format_missing_cost_response(result)

        # Calculate financial impact
        breakdown = self._calculate_breakdown(result.data)

        # For area queries, add per-asset breakdown
        per_asset = None
        highest_cost = None
        if kwargs.get("area"):
            per_asset = self._calculate_per_asset_breakdown(result.data)
            highest_cost = max(per_asset, key=lambda x: x.total_loss)

        # Calculate average comparison
        avg_comparison = await self._calculate_average_comparison(
            data_source, result.data, kwargs
        )

        # Generate citations
        citations = self._generate_citations(result.source_metadata, breakdown)

        return FinancialImpactOutput(
            total_loss=sum(b.amount for b in breakdown),
            breakdown=breakdown,
            per_asset_breakdown=per_asset,
            highest_cost_asset=highest_cost,
            average_comparison=avg_comparison,
            citations=citations,
            data_freshness=result.timestamp
        )
```

**Supabase Query Pattern:**
```python
async def get_financial_metrics(
    self,
    start_date: datetime,
    end_date: datetime,
    asset_id: Optional[str] = None,
    area: Optional[str] = None
) -> DataResult:
    """
    Query daily_summaries with cost_centers for financial calculations.

    Joins with assets for area resolution and cost_centers for rates.
    """
    query = (
        self.client
        .from_("daily_summaries")
        .select("""
            *,
            assets!inner(id, name, area),
            cost_centers(standard_hourly_rate, cost_per_unit)
        """)
        .gte("date", start_date.date().isoformat())
        .lte("date", end_date.date().isoformat())
    )

    if asset_id:
        query = query.eq("asset_id", asset_id)
    if area:
        query = query.eq("assets.area", area)

    result = await query.execute()

    # Check if cost_centers data is available
    has_cost_data = all(
        r.get("cost_centers") and r["cost_centers"].get("standard_hourly_rate")
        for r in result.data
    )

    return DataResult(
        data=result.data,
        has_cost_data=has_cost_data,
        source_metadata={
            "tables": ["daily_summaries", "cost_centers", "assets"],
            "query_time": datetime.utcnow(),
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()}
        }
    )
```

**Response Format Example:**
```json
{
  "total_loss": 2340.50,
  "breakdown": [
    {
      "category": "downtime",
      "amount": 1875.00,
      "calculation_basis": {
        "downtime_minutes": 47,
        "standard_hourly_rate": 2393.62
      },
      "formula_used": "47 min * $2393.62/hr / 60 = $1875.00"
    },
    {
      "category": "waste",
      "amount": 465.50,
      "calculation_basis": {
        "waste_count": 23,
        "cost_per_unit": 20.24
      },
      "formula_used": "23 units * $20.24/unit = $465.50"
    }
  ],
  "per_asset_breakdown": [
    {
      "asset_id": "ast-grd-005",
      "asset_name": "Grinder 5",
      "total_loss": 2340.50,
      "downtime_cost": 1875.00,
      "waste_cost": 465.50,
      "hourly_rate": 2393.62,
      "downtime_minutes": 47,
      "waste_count": 23
    }
  ],
  "highest_cost_asset": {
    "asset_name": "Grinder 5",
    "total_loss": 2340.50
  },
  "average_comparison": {
    "average_daily_loss": 1850.00,
    "variance": 490.50,
    "variance_percent": 26.5,
    "comparison_text": "$490.50 (26.5%) above average"
  },
  "citations": [
    {
      "source_type": "database",
      "source_table": "daily_summaries",
      "record_id": "2026-01-08",
      "timestamp": "2026-01-08T23:59:59Z",
      "confidence": 1.0
    },
    {
      "source_type": "calculation",
      "source_table": "cost_centers",
      "excerpt": "standard_hourly_rate: $2393.62/hr",
      "confidence": 1.0
    }
  ],
  "data_freshness": "2026-01-09T09:00:00Z"
}
```

**Missing Cost Center Response:**
```python
def _format_missing_cost_response(self, result: DataResult) -> FinancialImpactOutput:
    """Format honest response when cost center data is missing."""
    metrics_available = []
    for record in result.data:
        metrics_available.append({
            "asset": record["assets"]["name"],
            "downtime_minutes": record.get("downtime_minutes"),
            "waste_count": record.get("waste_count"),
            "note": "Unable to calculate financial impact - no cost center data"
        })

    return FinancialImpactOutput(
        total_loss=None,
        breakdown=[],
        message="Unable to calculate financial impact - no cost center data configured for these assets. Available metrics: downtime and waste counts.",
        non_financial_metrics=metrics_available,
        citations=self._generate_citations(result.source_metadata),
        data_freshness=result.timestamp
    )
```

### Database Schema Reference

**daily_summaries table (from Story 1.4):**
```sql
-- Contains aggregated daily metrics per asset
- asset_id: UUID (FK to assets)
- date: DATE
- total_output: INTEGER
- target_output: INTEGER
- downtime_minutes: DECIMAL
- downtime_reasons: JSONB  -- {"reason": minutes}
- waste_count: INTEGER
- oee: DECIMAL
- availability: DECIMAL
- performance: DECIMAL
- quality: DECIMAL
```

**cost_centers table (from Story 1.3):**
```sql
CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    standard_hourly_rate DECIMAL(10, 2),  -- $/hour for downtime calc
    cost_per_unit DECIMAL(10, 2),         -- $/unit for waste calc
    effective_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Project Structure Notes

**Files to Create:**
```
apps/api/app/
  services/agent/tools/
    financial_impact.py       # FinancialImpactTool implementation
  models/
    agent.py                  # Add FinancialImpactInput/Output schemas (extend existing)

apps/api/tests/
  test_financial_impact_tool.py  # Unit and integration tests
```

**Files to Modify:**
```
apps/api/app/services/agent/data_source/protocol.py  # Add get_financial_metrics method
apps/api/app/services/agent/data_source/supabase.py  # Implement get_financial_metrics
```

### Dependencies

**Requires (must be completed):**
- Story 5.1: Agent Framework & Tool Registry (ManufacturingTool base class)
- Story 5.2: Data Access Abstraction Layer (DataSource Protocol)
- Story 5.8: Tool Response Caching (caching infrastructure)
- Story 1.3: Plant Object Model Schema (cost_centers table)
- Story 1.4: Analytical Cache Schema (daily_summaries table)
- Story 2.7: Financial Impact Calculator (calculation logic reference)

**Enables:**
- Story 6.3: Cost of Loss Tool (can reuse financial calculation patterns)
- Story 7.3: Action List Tool (can include financial impact in prioritization)

### NFR Compliance

- **NFR4 (Agent Honesty):** Clearly state when cost data unavailable; return non-financial metrics as alternative
- **NFR6 (Response Structure):** Return structured JSON with calculation transparency
- **NFR7 (Caching):** 15-minute TTL for daily data reduces database load

### Testing Guidance

**Unit Tests:**
```python
@pytest.mark.asyncio
async def test_financial_impact_asset_query():
    """Test asset-level financial impact calculation."""
    tool = FinancialImpactTool()
    mock_data_source = MockDataSource(
        daily_summaries=[{
            "asset_id": "ast-001",
            "downtime_minutes": 47,
            "waste_count": 23,
            "cost_centers": {"standard_hourly_rate": 2393.62, "cost_per_unit": 20.24}
        }]
    )

    result = await tool._arun(time_range="yesterday", asset_id="ast-001")

    assert result.total_loss == pytest.approx(2340.50, rel=0.01)
    assert len(result.breakdown) == 2
    assert any(b.category == "downtime" for b in result.breakdown)
    assert any(b.category == "waste" for b in result.breakdown)

@pytest.mark.asyncio
async def test_financial_impact_area_aggregation():
    """Test area-level aggregation with per-asset breakdown."""
    tool = FinancialImpactTool()

    result = await tool._arun(time_range="this week", area="Grinding")

    assert result.per_asset_breakdown is not None
    assert result.highest_cost_asset is not None
    assert result.highest_cost_asset.total_loss == max(a.total_loss for a in result.per_asset_breakdown)

@pytest.mark.asyncio
async def test_financial_impact_missing_cost_center():
    """Test honest response when cost center data is missing."""
    tool = FinancialImpactTool()
    mock_data_source = MockDataSource(
        daily_summaries=[{
            "asset_id": "ast-001",
            "downtime_minutes": 47,
            "waste_count": 23,
            "cost_centers": None  # Missing cost data
        }]
    )

    result = await tool._arun(asset_id="ast-001")

    assert result.total_loss is None
    assert "Unable to calculate financial impact" in result.message
    assert result.non_financial_metrics is not None

@pytest.mark.asyncio
async def test_financial_impact_formula_transparency():
    """Test that calculation formulas are included in response."""
    tool = FinancialImpactTool()

    result = await tool._arun(time_range="yesterday", asset_id="ast-001")

    for breakdown in result.breakdown:
        assert breakdown.formula_used is not None
        assert "$" in breakdown.formula_used  # Contains dollar amounts
```

### References

- [Source: _bmad-output/planning-artifacts/epic-6.md#Story 6.2] - Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.2] - Financial Impact tool specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.1] - ManufacturingTool base class pattern
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.2] - Data Access Abstraction Layer
- [Source: _bmad-output/implementation-artifacts/2-7-financial-impact-calculator.md] - Financial calculation patterns
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation format patterns
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - cost_centers and daily_summaries schemas

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
