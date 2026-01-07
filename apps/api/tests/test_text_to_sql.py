"""
Tests for Text-to-SQL Service (Story 4.2)

Unit and integration tests for SQL validation, response formatting,
and Text-to-SQL service functionality.

AC#9: Write Tests - Unit tests for all components
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, date

from app.services.ai.text_to_sql.query_validator import (
    QueryValidator,
    QueryValidationError,
    SQLInjectionError,
    TableAccessError,
    QueryComplexityError,
    ALLOWED_TABLES,
)
from app.services.ai.text_to_sql.response_formatter import (
    ResponseFormatter,
    Citation,
)
from app.services.ai.text_to_sql.service import (
    TextToSQLService,
    TextToSQLError,
    QueryExecutionError,
    QueryTimeoutError,
    LLMGenerationError,
)
from app.services.ai.text_to_sql.prompts import (
    get_sql_system_prompt,
    get_table_descriptions,
    get_example_queries,
    TABLE_DESCRIPTIONS,
    EXAMPLE_QUERIES,
)


# ============================================================================
# Query Validator Tests (AC#5)
# ============================================================================

class TestQueryValidator:
    """Tests for QueryValidator - SQL security and validation."""

    @pytest.fixture
    def validator(self):
        """Create a QueryValidator instance."""
        return QueryValidator()

    # --- Input Validation Tests ---

    def test_validate_input_valid(self, validator):
        """Test validation of normal natural language input."""
        result = validator.validate_input("What was the OEE yesterday?")
        assert result == "What was the OEE yesterday?"

    def test_validate_input_with_whitespace(self, validator):
        """Test input whitespace is trimmed."""
        result = validator.validate_input("  What was the OEE?  ")
        assert result == "What was the OEE?"

    def test_validate_input_empty(self, validator):
        """Test empty input raises error."""
        with pytest.raises(QueryValidationError, match="Empty input"):
            validator.validate_input("")

    def test_validate_input_whitespace_only(self, validator):
        """Test whitespace-only input raises error."""
        with pytest.raises(QueryValidationError, match="Empty input"):
            validator.validate_input("   ")

    def test_validate_input_sql_injection_attempt(self, validator):
        """Test SQL injection in input is blocked."""
        with pytest.raises(SQLInjectionError):
            validator.validate_input("Show me assets; DROP TABLE assets")

    def test_validate_input_union_injection(self, validator):
        """Test UNION injection in input is blocked."""
        with pytest.raises(SQLInjectionError):
            validator.validate_input("assets UNION SELECT * FROM users")

    def test_validate_input_or_1_equals_1(self, validator):
        """Test OR 1=1 injection is blocked."""
        with pytest.raises(SQLInjectionError):
            validator.validate_input("assets OR 1=1")

    # --- SQL Validation Tests ---

    def test_validate_sql_valid_select(self, validator):
        """Test validation of valid SELECT query."""
        sql = "SELECT name FROM assets WHERE id = '123'"
        result = validator.validate_sql(sql)
        assert "SELECT" in result
        assert "LIMIT" in result  # Should add LIMIT

    def test_validate_sql_with_join(self, validator):
        """Test validation of query with JOIN."""
        sql = """
        SELECT a.name, ds.oee_percentage
        FROM daily_summaries ds
        JOIN assets a ON ds.asset_id = a.id
        """
        result = validator.validate_sql(sql)
        assert "JOIN" in result

    def test_validate_sql_preserves_existing_limit(self, validator):
        """Test that existing LIMIT is preserved."""
        sql = "SELECT name FROM assets LIMIT 5"
        result = validator.validate_sql(sql)
        assert "LIMIT 5" in result
        # Should not add another LIMIT
        assert result.count("LIMIT") == 1

    def test_validate_sql_removes_markdown(self, validator):
        """Test that markdown code blocks are removed."""
        sql = "```sql\nSELECT * FROM assets\n```"
        result = validator.validate_sql(sql)
        assert "```" not in result
        assert "SELECT" in result

    def test_validate_sql_rejects_insert(self, validator):
        """Test INSERT statement is rejected."""
        with pytest.raises(QueryValidationError, match="SELECT"):
            validator.validate_sql("INSERT INTO assets (name) VALUES ('test')")

    def test_validate_sql_rejects_update(self, validator):
        """Test UPDATE statement is rejected."""
        with pytest.raises(QueryValidationError, match="SELECT"):
            validator.validate_sql("UPDATE assets SET name = 'test' WHERE id = '1'")

    def test_validate_sql_rejects_delete(self, validator):
        """Test DELETE statement is rejected."""
        with pytest.raises(QueryValidationError, match="SELECT"):
            validator.validate_sql("DELETE FROM assets WHERE id = '1'")

    def test_validate_sql_rejects_drop(self, validator):
        """Test DROP statement is rejected."""
        with pytest.raises(QueryValidationError, match="SELECT"):
            validator.validate_sql("DROP TABLE assets")

    def test_validate_sql_rejects_truncate(self, validator):
        """Test TRUNCATE statement is rejected."""
        with pytest.raises(QueryValidationError, match="SELECT"):
            validator.validate_sql("TRUNCATE TABLE assets")

    def test_validate_sql_rejects_unauthorized_table(self, validator):
        """Test access to unauthorized tables is rejected."""
        with pytest.raises(TableAccessError, match="not allowed"):
            validator.validate_sql("SELECT * FROM auth.users")

    def test_validate_sql_rejects_information_schema(self, validator):
        """Test access to INFORMATION_SCHEMA is rejected."""
        with pytest.raises(SQLInjectionError, match="Schema information"):
            validator.validate_sql("SELECT * FROM INFORMATION_SCHEMA.tables")

    def test_validate_sql_rejects_comment_injection(self, validator):
        """Test SQL comment injection is rejected."""
        with pytest.raises(SQLInjectionError, match="comment"):
            validator.validate_sql("SELECT * FROM assets -- WHERE id = '1'")

    def test_validate_sql_rejects_union_injection(self, validator):
        """Test UNION injection is rejected."""
        with pytest.raises(SQLInjectionError, match="UNION"):
            validator.validate_sql("SELECT name FROM assets UNION SELECT password FROM users")

    def test_validate_sql_rejects_multiple_statements(self, validator):
        """Test multiple statements are rejected."""
        with pytest.raises(SQLInjectionError, match="Multiple statements"):
            validator.validate_sql("SELECT * FROM assets; DELETE FROM assets")

    def test_validate_sql_complexity_too_many_joins(self, validator):
        """Test query with too many JOINs is rejected."""
        sql = """
        SELECT * FROM assets a
        JOIN cost_centers cc ON a.id = cc.asset_id
        JOIN daily_summaries ds ON a.id = ds.asset_id
        JOIN live_snapshots ls ON a.id = ls.asset_id
        JOIN safety_events se ON a.id = se.asset_id
        JOIN cost_centers cc2 ON a.id = cc2.asset_id
        JOIN daily_summaries ds2 ON a.id = ds2.asset_id
        """
        with pytest.raises(QueryComplexityError, match="JOINs"):
            validator.validate_sql(sql)

    def test_validate_sql_allows_all_whitelisted_tables(self, validator):
        """Test all whitelisted tables are accessible."""
        for table in ALLOWED_TABLES:
            sql = f"SELECT * FROM {table}"
            result = validator.validate_sql(sql)
            assert table in result.lower()

    def test_validate_sql_query_length_limit(self):
        """Test query length limit is enforced."""
        validator = QueryValidator(max_query_length=100)
        long_sql = "SELECT " + "a" * 200 + " FROM assets"
        with pytest.raises(QueryComplexityError, match="length"):
            validator.validate_sql(long_sql)

    # --- Table Extraction Tests ---

    def test_extract_tables_simple(self, validator):
        """Test table extraction from simple query."""
        sql = "SELECT * FROM assets"
        tables = validator._extract_tables(sql)
        assert "assets" in tables

    def test_extract_tables_with_join(self, validator):
        """Test table extraction with JOIN."""
        sql = "SELECT * FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id"
        tables = validator._extract_tables(sql)
        assert "daily_summaries" in tables
        assert "assets" in tables

    def test_extract_tables_multiple_joins(self, validator):
        """Test table extraction with multiple JOINs."""
        sql = """
        SELECT * FROM daily_summaries ds
        JOIN assets a ON ds.asset_id = a.id
        LEFT JOIN cost_centers cc ON a.id = cc.asset_id
        """
        tables = validator._extract_tables(sql)
        assert "daily_summaries" in tables
        assert "assets" in tables
        assert "cost_centers" in tables


# ============================================================================
# Response Formatter Tests (AC#3, AC#4)
# ============================================================================

class TestResponseFormatter:
    """Tests for ResponseFormatter - result formatting and citations."""

    @pytest.fixture
    def formatter(self):
        """Create a ResponseFormatter instance."""
        return ResponseFormatter()

    # --- No Results Tests ---

    def test_format_no_results(self, formatter):
        """Test formatting when no results found."""
        answer, citations = formatter.format_response(
            [], "SELECT * FROM assets", "What assets are there?"
        )
        assert "No data found" in answer
        assert citations == []

    def test_format_no_results_with_suggestions(self, formatter):
        """Test no results includes helpful suggestions."""
        answer, citations = formatter.format_response(
            [], "SELECT * FROM assets WHERE name = 'Unknown'",
            "Show me Grinder 99 data"
        )
        assert "No data found" in answer
        assert any(word in answer.lower() for word in ["suggestion", "try", "verify"])

    # --- Single Result Tests ---

    def test_format_single_oee_result(self, formatter):
        """Test formatting OEE query result."""
        results = [{"asset_name": "Grinder 5", "oee_percentage": 87.5, "report_date": date(2026, 1, 5)}]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "What was Grinder 5's OEE yesterday?"
        )

        assert "Grinder 5" in answer
        assert "87" in answer or "OEE" in answer
        assert len(citations) > 0

    def test_format_single_downtime_result(self, formatter):
        """Test formatting downtime query result."""
        results = [{"asset_name": "Press Line 1", "downtime_minutes": 120}]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "How much downtime did Press Line 1 have?"
        )

        assert "Press Line 1" in answer
        assert "120" in answer or "downtime" in answer.lower()

    def test_format_financial_loss_result(self, formatter):
        """Test formatting financial loss result."""
        results = [{"asset_name": "Grinder 5", "financial_loss_dollars": 5000.50}]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "What was the financial loss for Grinder 5?"
        )

        assert "Grinder 5" in answer
        assert "$" in answer or "5000" in answer or "5,000" in answer

    # --- Multiple Results Tests ---

    def test_format_multiple_results(self, formatter):
        """Test formatting multiple result rows."""
        results = [
            {"asset_name": "Grinder 1", "oee_percentage": 85.0},
            {"asset_name": "Grinder 2", "oee_percentage": 90.0},
            {"asset_name": "Grinder 3", "oee_percentage": 78.5},
        ]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "Compare OEE across all grinders"
        )

        assert "3 results" in answer or "Found" in answer
        assert "Grinder 1" in answer
        assert "Grinder 2" in answer

    def test_format_limits_result_display(self, formatter):
        """Test that large result sets are limited in display."""
        results = [
            {"asset_name": f"Asset {i}", "oee_percentage": 80 + i}
            for i in range(20)
        ]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "Show all assets"
        )

        # Should show "more results" indicator
        assert "more" in answer.lower() or "20" in answer

    # --- Citation Tests ---

    def test_citations_include_value(self, formatter):
        """Test that citations include the value."""
        results = [{"asset_name": "Grinder 5", "oee_percentage": 87.5}]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "What was Grinder 5's OEE?"
        )

        assert len(citations) > 0
        oee_citation = next((c for c in citations if "oee" in c.field.lower()), None)
        if oee_citation:
            assert "87" in oee_citation.value

    def test_citations_include_table(self, formatter):
        """Test that citations include source table."""
        results = [{"asset_name": "Grinder 5", "oee_percentage": 87.5}]
        sql = "SELECT * FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id"

        answer, citations = formatter.format_response(
            results, sql, "What was Grinder 5's OEE?"
        )

        assert len(citations) > 0
        # Should extract 'daily_summaries' as source table
        assert any(c.table in ["daily_summaries", "unknown"] for c in citations)

    def test_citations_include_context(self, formatter):
        """Test that citations include business context."""
        results = [{
            "asset_name": "Grinder 5",
            "oee_percentage": 87.5,
            "report_date": date(2026, 1, 5)
        }]
        sql = "SELECT * FROM daily_summaries"

        answer, citations = formatter.format_response(
            results, sql, "What was Grinder 5's OEE yesterday?"
        )

        assert len(citations) > 0
        # Context should include asset name and/or date
        assert any(
            "Grinder 5" in c.context or "2026" in c.context
            for c in citations
        )

    # --- Value Formatting Tests ---

    def test_format_percentage_value(self, formatter):
        """Test percentage formatting."""
        formatted = formatter._format_value("oee_percentage", 87.5)
        assert "%" in formatted
        assert "87.5" in formatted

    def test_format_currency_value(self, formatter):
        """Test currency formatting."""
        formatted = formatter._format_value("financial_loss_dollars", 5000.50)
        assert "$" in formatted
        assert "5,000" in formatted or "5000" in formatted

    def test_format_integer_value(self, formatter):
        """Test integer formatting."""
        formatted = formatter._format_value("downtime_minutes", 1500)
        assert "1,500" in formatted or "1500" in formatted

    def test_format_null_value(self, formatter):
        """Test null value handling."""
        formatted = formatter._format_value("oee_percentage", None)
        assert formatted is None


# ============================================================================
# Prompts Tests (Task 10)
# ============================================================================

class TestPrompts:
    """Tests for manufacturing domain prompts."""

    def test_table_descriptions_exist(self):
        """Test all required tables have descriptions."""
        required_tables = ["assets", "cost_centers", "daily_summaries",
                          "live_snapshots", "safety_events"]
        for table in required_tables:
            assert table in TABLE_DESCRIPTIONS
            assert len(TABLE_DESCRIPTIONS[table]) > 50  # Has meaningful description

    def test_example_queries_exist(self):
        """Test example queries are defined."""
        assert len(EXAMPLE_QUERIES) >= 5  # At least 5 examples

        for example in EXAMPLE_QUERIES:
            assert "question" in example
            assert "sql" in example
            assert "SELECT" in example["sql"].upper()

    def test_get_sql_system_prompt(self):
        """Test system prompt generation."""
        prompt = get_sql_system_prompt()

        # Should include key instructions
        assert "SELECT" in prompt
        assert "ONLY" in prompt or "only" in prompt
        assert "PostgreSQL" in prompt.lower() or "sql" in prompt.lower()

        # Should include table descriptions
        assert "assets" in prompt.lower()
        assert "daily_summaries" in prompt.lower()

    def test_get_table_descriptions(self):
        """Test table descriptions formatting."""
        descriptions = get_table_descriptions()

        assert "assets" in descriptions.lower()
        assert "oee_percentage" in descriptions.lower()
        assert "safety_events" in descriptions.lower()

    def test_get_example_queries(self):
        """Test example queries formatting."""
        examples = get_example_queries()

        assert "Example 1" in examples or "example" in examples.lower()
        assert "SELECT" in examples


# ============================================================================
# Text-to-SQL Service Tests (Integration)
# ============================================================================

class TestTextToSQLService:
    """Tests for TextToSQLService - main service functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.services.ai.text_to_sql.service.get_settings') as mock:
            settings = MagicMock()
            settings.supabase_db_url = "postgresql://user:pass@localhost/db"
            settings.openai_api_key = "test-key"
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def service(self, mock_settings):
        """Create a TextToSQLService instance for testing."""
        return TextToSQLService()

    def test_service_is_configured_true(self, service, mock_settings):
        """Test is_configured returns True when settings present."""
        assert service.is_configured() is True

    def test_service_is_configured_false(self):
        """Test is_configured returns False when settings missing."""
        with patch('app.services.ai.text_to_sql.service.get_settings') as mock:
            settings = MagicMock()
            settings.supabase_db_url = ""
            settings.openai_api_key = ""
            mock.return_value = settings

            service = TextToSQLService()
            assert service.is_configured() is False

    def test_service_not_initialized_by_default(self, service):
        """Test service is not initialized until initialize() called."""
        assert service.is_initialized() is False

    def test_allowed_tables(self, service):
        """Test allowed tables list."""
        expected = ["assets", "cost_centers", "daily_summaries",
                    "live_snapshots", "safety_events"]
        assert service.ALLOWED_TABLES == expected

    @pytest.mark.asyncio
    async def test_query_without_initialization_raises_error(self):
        """Test query fails if service not initialized."""
        with patch('app.services.ai.text_to_sql.service.get_settings') as mock_get:
            settings = MagicMock()
            settings.supabase_db_url = ""
            settings.openai_api_key = ""
            mock_get.return_value = settings

            service = TextToSQLService()
            # Should raise TextToSQLError when not configured
            with pytest.raises(TextToSQLError, match="not configured"):
                await service.query("Test question", "user-123")

    @pytest.mark.asyncio
    async def test_query_handles_sql_injection(self, mock_settings):
        """Test SQL injection attempts are handled by validator before service init."""
        # Create a properly configured service but with mocked internals
        service = TextToSQLService()

        # SQL injection is caught at input validation level
        # which happens before the service tries to initialize
        # For this test, we need to mock the service to be initialized
        # and verify the validator catches the injection
        with patch.object(service, '_ensure_initialized'):
            with patch.object(service, '_generate_sql') as mock_gen:
                mock_gen.return_value = "SELECT * FROM assets"

                result = await service.query(
                    "Show me assets; DROP TABLE assets",
                    "user-123"
                )

                # Should return error response from SQL injection detection
                assert result.get("error") is True
                assert "malicious" in result.get("answer", "").lower() or "rephrase" in result.get("answer", "").lower()

    def test_error_response_format(self, service):
        """Test error response has correct format."""
        response = service._error_response(
            "Test error message",
            "Test question"
        )

        assert "answer" in response
        assert response["answer"] == "Test error message"
        assert response["sql"] is None
        assert response["data"] == []
        assert response["citations"] == []
        assert response["error"] is True
        assert "suggestions" in response

    def test_get_suggestions(self, service):
        """Test suggestion generation for different queries."""
        # Date-related question
        suggestions = service._get_suggestions("What was yesterday's OEE?")
        assert len(suggestions) > 0

        # Asset-related question
        suggestions = service._get_suggestions("Tell me about Grinder 5")
        assert any("asset" in s.lower() or "name" in s.lower() for s in suggestions)

    def test_clean_sql_response(self, service):
        """Test SQL response cleaning."""
        # With markdown
        dirty_sql = "```sql\nSELECT * FROM assets\n```"
        clean = service._clean_sql_response(dirty_sql)
        assert "```" not in clean
        assert "SELECT" in clean

        # Already clean
        clean_sql = "SELECT * FROM assets"
        result = service._clean_sql_response(clean_sql)
        assert result == clean_sql

    def test_extract_columns_from_sql(self, service):
        """Test column name extraction from SQL."""
        sql = "SELECT name, oee_percentage AS oee FROM daily_summaries"
        columns = service._extract_columns_from_sql(sql)

        assert "name" in columns
        assert "oee" in columns

    def test_extract_columns_with_table_prefix(self, service):
        """Test column extraction with table prefixes."""
        sql = "SELECT a.name, ds.oee_percentage FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id"
        columns = service._extract_columns_from_sql(sql)

        assert "name" in columns
        assert "oee_percentage" in columns


# ============================================================================
# Integration Helper Tests
# ============================================================================

class TestServiceHelpers:
    """Tests for service helper functions."""

    def test_tuples_to_dicts(self):
        """Test conversion of result tuples to dicts."""
        service = TextToSQLService()
        tuples = [
            ("Grinder 5", 87.5, 100),
            ("Press Line 1", 90.0, 150),
        ]
        sql = "SELECT name, oee_percentage, output FROM daily_summaries"

        result = service._tuples_to_dicts(tuples, sql)

        assert len(result) == 2
        assert result[0]["name"] == "Grinder 5"
        assert result[0]["oee_percentage"] == 87.5
        assert result[1]["name"] == "Press Line 1"

    def test_split_columns(self):
        """Test column splitting with nested parentheses."""
        service = TextToSQLService()

        # Simple case
        result = service._split_columns("a, b, c")
        assert result == ["a", "b", "c"]

        # With function
        result = service._split_columns("name, SUM(value) AS total, count")
        assert len(result) == 3
        assert "SUM(value) AS total" in result
