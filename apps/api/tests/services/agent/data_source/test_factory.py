"""
Tests for Factory Function (Story 5.2)

AC#9: Factory Function for Data Source Injection
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.agent.data_source import (
    get_data_source,
    reset_data_source,
    SupabaseDataSource,
    CompositeDataSource,
)


class TestGetDataSource:
    """Tests for get_data_source factory function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_data_source()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_data_source()

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_returns_supabase_by_default(self, mock_settings, mock_supabase_class):
        """AC#9: Default returns SupabaseDataSource."""
        mock_settings.return_value.data_source_type = "supabase"
        mock_instance = MagicMock()
        mock_supabase_class.return_value = mock_instance

        result = get_data_source()

        assert result is mock_instance
        mock_supabase_class.assert_called_once()

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.CompositeDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_returns_composite_when_configured(self, mock_settings, mock_composite_class, mock_supabase_class):
        """AC#9: Returns CompositeDataSource when configured."""
        mock_settings.return_value.data_source_type = "composite"
        mock_supabase_instance = MagicMock()
        mock_supabase_class.return_value = mock_supabase_instance
        mock_composite_instance = MagicMock()
        mock_composite_class.return_value = mock_composite_instance

        result = get_data_source()

        assert result is mock_composite_instance
        mock_composite_class.assert_called_once_with(primary=mock_supabase_instance)

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_defaults_to_supabase_for_unknown_type(self, mock_settings, mock_supabase_class):
        """AC#9: Unknown type defaults to Supabase."""
        mock_settings.return_value.data_source_type = "unknown"
        mock_instance = MagicMock()
        mock_supabase_class.return_value = mock_instance

        result = get_data_source()

        assert result is mock_instance

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_singleton_pattern(self, mock_settings, mock_supabase_class):
        """AC#9: Same instance is reused (singleton pattern)."""
        mock_settings.return_value.data_source_type = "supabase"
        mock_instance = MagicMock()
        mock_supabase_class.return_value = mock_instance

        result1 = get_data_source()
        result2 = get_data_source()

        assert result1 is result2
        # Only called once due to singleton
        mock_supabase_class.assert_called_once()

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_handles_missing_data_source_type_attribute(self, mock_settings, mock_supabase_class):
        """AC#9: Handles missing data_source_type gracefully."""
        # Settings without data_source_type attribute
        mock_settings_obj = MagicMock(spec=[])
        mock_settings.return_value = mock_settings_obj
        mock_instance = MagicMock()
        mock_supabase_class.return_value = mock_instance

        result = get_data_source()

        # Should default to supabase
        assert result is mock_instance


class TestResetDataSource:
    """Tests for reset_data_source function."""

    @patch("app.services.agent.data_source.SupabaseDataSource")
    @patch("app.services.agent.data_source.get_settings")
    def test_reset_clears_singleton(self, mock_settings, mock_supabase_class):
        """reset_data_source clears the singleton for testing."""
        mock_settings.return_value.data_source_type = "supabase"
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()
        mock_supabase_class.side_effect = [mock_instance1, mock_instance2]

        result1 = get_data_source()
        reset_data_source()
        result2 = get_data_source()

        assert result1 is not result2
        assert mock_supabase_class.call_count == 2

    def test_reset_is_safe_when_not_initialized(self):
        """reset_data_source is safe to call when not initialized."""
        # Should not raise
        reset_data_source()
        reset_data_source()
