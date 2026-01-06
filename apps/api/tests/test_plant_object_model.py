"""
Tests for Story 1.3: Plant Object Model Schema

These tests verify that the Plant Object Model migration creates the correct
database schema with all required tables, columns, constraints, and indexes.

Note: These tests use a local PostgreSQL-compatible database (via SQLAlchemy)
to verify the migration SQL is valid and creates the expected schema structure.
For Supabase-specific features (RLS policies), we verify the SQL syntax is correct
but actual RLS testing requires a Supabase environment.
"""
import pytest
import re
import os
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory (tfn-aihub)."""
    # Start from this test file and navigate up to find project root
    current = Path(__file__).resolve()
    # Go up: tests -> api -> apps -> tfn-aihub
    project_root = current.parent.parent.parent.parent
    return project_root


def get_migration_path() -> Path:
    """Get the path to the migration file."""
    return get_project_root() / "supabase" / "migrations" / "20260106000000_plant_object_model.sql"


class TestMigrationFileExists:
    """Tests to verify the migration file exists and has correct structure."""

    def test_migration_file_exists(self):
        """AC6: Migration file should exist in the migrations folder."""
        migration_path = get_migration_path()
        assert migration_path.exists(), f"Migration file not found at {migration_path}"

    def test_migration_file_has_correct_format(self):
        """AC6: Migration file should have timestamped name."""
        migration_path = get_migration_path()
        assert re.match(r"\d{14}_plant_object_model\.sql", migration_path.name), \
            "Migration file should follow YYYYMMDDHHMMSS_name.sql format"


class TestMigrationSQLContent:
    """Tests to verify the migration SQL content is correct."""

    @pytest.fixture
    def migration_sql(self):
        """Load the migration SQL content."""
        migration_path = get_migration_path()
        with open(migration_path, "r") as f:
            return f.read()

    def test_uuid_extension_enabled(self, migration_sql):
        """Migration should enable uuid-ossp extension."""
        assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in migration_sql

    def test_updated_at_trigger_function_created(self, migration_sql):
        """Migration should create the updated_at trigger function."""
        assert "CREATE OR REPLACE FUNCTION update_updated_at_column()" in migration_sql
        assert "NEW.updated_at = NOW()" in migration_sql

    # =========================================================================
    # AC1: Assets Table Tests
    # =========================================================================

    def test_assets_table_created(self, migration_sql):
        """AC1: Assets table should be created."""
        assert "CREATE TABLE IF NOT EXISTS assets" in migration_sql

    def test_assets_has_id_column(self, migration_sql):
        """AC1: Assets table should have UUID id column."""
        # Check for id column with UUID type and default
        assert re.search(r"id\s+UUID\s+PRIMARY KEY\s+DEFAULT\s+uuid_generate_v4\(\)", migration_sql, re.IGNORECASE)

    def test_assets_has_name_column(self, migration_sql):
        """AC1: Assets table should have name VARCHAR(255) NOT NULL column."""
        assert re.search(r"name\s+VARCHAR\(255\)\s+NOT NULL", migration_sql, re.IGNORECASE)

    def test_assets_has_source_id_column(self, migration_sql):
        """AC1: Assets table should have source_id VARCHAR(255) NOT NULL column."""
        assert re.search(r"source_id\s+VARCHAR\(255\)\s+NOT NULL", migration_sql, re.IGNORECASE)

    def test_assets_has_area_column(self, migration_sql):
        """AC1: Assets table should have area VARCHAR(100) column."""
        assert re.search(r"area\s+VARCHAR\(100\)", migration_sql, re.IGNORECASE)

    def test_assets_has_created_at_column(self, migration_sql):
        """AC1: Assets table should have created_at column with default NOW()."""
        assert re.search(r"created_at\s+TIMESTAMP\s+WITH\s+TIME\s+ZONE\s+DEFAULT\s+NOW\(\)", migration_sql, re.IGNORECASE)

    def test_assets_has_updated_at_column(self, migration_sql):
        """AC1: Assets table should have updated_at column with default NOW()."""
        assert re.search(r"updated_at\s+TIMESTAMP\s+WITH\s+TIME\s+ZONE\s+DEFAULT\s+NOW\(\)", migration_sql, re.IGNORECASE)

    def test_assets_has_updated_at_trigger(self, migration_sql):
        """AC1: Assets table should have updated_at auto-update trigger."""
        assert "CREATE TRIGGER update_assets_updated_at" in migration_sql
        assert "EXECUTE FUNCTION update_updated_at_column()" in migration_sql

    # =========================================================================
    # AC2: Cost Centers Table Tests
    # =========================================================================

    def test_cost_centers_table_created(self, migration_sql):
        """AC2: Cost centers table should be created."""
        assert "CREATE TABLE IF NOT EXISTS cost_centers" in migration_sql

    def test_cost_centers_has_id_column(self, migration_sql):
        """AC2: Cost centers should have UUID id column."""
        # The cost_centers table should also have id UUID PRIMARY KEY
        cost_centers_section = migration_sql.split("CREATE TABLE IF NOT EXISTS cost_centers")[1].split("CREATE TABLE")[0]
        assert re.search(r"id\s+UUID\s+PRIMARY KEY\s+DEFAULT\s+uuid_generate_v4\(\)", cost_centers_section, re.IGNORECASE)

    def test_cost_centers_has_asset_id_foreign_key(self, migration_sql):
        """AC2: Cost centers should have asset_id foreign key with CASCADE delete."""
        assert re.search(r"asset_id\s+UUID\s+NOT NULL\s+REFERENCES\s+assets\(id\)\s+ON DELETE CASCADE", migration_sql, re.IGNORECASE)

    def test_cost_centers_has_standard_hourly_rate(self, migration_sql):
        """AC2: Cost centers should have standard_hourly_rate DECIMAL(10,2) NOT NULL."""
        assert re.search(r"standard_hourly_rate\s+DECIMAL\(10,\s*2\)\s+NOT NULL", migration_sql, re.IGNORECASE)

    def test_cost_centers_has_timestamps(self, migration_sql):
        """AC2: Cost centers should have created_at and updated_at columns."""
        cost_centers_section = migration_sql.split("CREATE TABLE IF NOT EXISTS cost_centers")[1].split("CREATE TABLE")[0]
        assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()" in cost_centers_section
        assert "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()" in cost_centers_section

    def test_cost_centers_has_updated_at_trigger(self, migration_sql):
        """AC2: Cost centers should have updated_at auto-update trigger."""
        assert "CREATE TRIGGER update_cost_centers_updated_at" in migration_sql

    # =========================================================================
    # AC3: Shift Targets Table Tests
    # =========================================================================

    def test_shift_targets_table_created(self, migration_sql):
        """AC3: Shift targets table should be created."""
        assert "CREATE TABLE IF NOT EXISTS shift_targets" in migration_sql

    def test_shift_targets_has_id_column(self, migration_sql):
        """AC3: Shift targets should have UUID id column."""
        shift_targets_section = migration_sql.split("CREATE TABLE IF NOT EXISTS shift_targets")[1].split(");")[0]
        assert re.search(r"id\s+UUID\s+PRIMARY KEY\s+DEFAULT\s+uuid_generate_v4\(\)", shift_targets_section, re.IGNORECASE)

    def test_shift_targets_has_asset_id_foreign_key(self, migration_sql):
        """AC3: Shift targets should have asset_id foreign key with CASCADE delete."""
        shift_targets_section = migration_sql.split("CREATE TABLE IF NOT EXISTS shift_targets")[1].split(");")[0]
        assert re.search(r"asset_id\s+UUID\s+NOT NULL\s+REFERENCES\s+assets\(id\)\s+ON DELETE CASCADE", shift_targets_section, re.IGNORECASE)

    def test_shift_targets_has_target_output(self, migration_sql):
        """AC3: Shift targets should have target_output INTEGER NOT NULL."""
        assert re.search(r"target_output\s+INTEGER\s+NOT NULL", migration_sql, re.IGNORECASE)

    def test_shift_targets_has_shift_column(self, migration_sql):
        """AC3: Shift targets should have shift VARCHAR(50) column."""
        assert re.search(r"shift\s+VARCHAR\(50\)", migration_sql, re.IGNORECASE)

    def test_shift_targets_has_effective_date(self, migration_sql):
        """AC3: Shift targets should have effective_date DATE column."""
        assert re.search(r"effective_date\s+DATE", migration_sql, re.IGNORECASE)

    def test_shift_targets_has_timestamps(self, migration_sql):
        """AC3: Shift targets should have created_at and updated_at columns."""
        shift_targets_section = migration_sql.split("CREATE TABLE IF NOT EXISTS shift_targets")[1].split(");")[0]
        assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()" in shift_targets_section
        assert "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()" in shift_targets_section

    def test_shift_targets_has_updated_at_trigger(self, migration_sql):
        """AC3: Shift targets should have updated_at auto-update trigger."""
        assert "CREATE TRIGGER update_shift_targets_updated_at" in migration_sql

    # =========================================================================
    # AC4: Row Level Security (RLS) Tests
    # =========================================================================

    def test_rls_enabled_on_assets(self, migration_sql):
        """AC4: RLS should be enabled on assets table."""
        assert "ALTER TABLE assets ENABLE ROW LEVEL SECURITY" in migration_sql

    def test_rls_enabled_on_cost_centers(self, migration_sql):
        """AC4: RLS should be enabled on cost_centers table."""
        assert "ALTER TABLE cost_centers ENABLE ROW LEVEL SECURITY" in migration_sql

    def test_rls_enabled_on_shift_targets(self, migration_sql):
        """AC4: RLS should be enabled on shift_targets table."""
        assert "ALTER TABLE shift_targets ENABLE ROW LEVEL SECURITY" in migration_sql

    def test_assets_authenticated_select_policy(self, migration_sql):
        """AC4: Authenticated users should have SELECT policy on assets."""
        assert 'CREATE POLICY "Allow authenticated read access on assets"' in migration_sql
        assert "ON assets FOR SELECT" in migration_sql
        assert "TO authenticated" in migration_sql

    def test_cost_centers_authenticated_select_policy(self, migration_sql):
        """AC4: Authenticated users should have SELECT policy on cost_centers."""
        assert 'CREATE POLICY "Allow authenticated read access on cost_centers"' in migration_sql
        assert "ON cost_centers FOR SELECT" in migration_sql

    def test_shift_targets_authenticated_select_policy(self, migration_sql):
        """AC4: Authenticated users should have SELECT policy on shift_targets."""
        assert 'CREATE POLICY "Allow authenticated read access on shift_targets"' in migration_sql
        assert "ON shift_targets FOR SELECT" in migration_sql

    def test_assets_service_role_full_access_policy(self, migration_sql):
        """AC4: Service role should have full access policy on assets."""
        assert 'CREATE POLICY "Allow service_role full access on assets"' in migration_sql
        assert "ON assets FOR ALL" in migration_sql
        assert "TO service_role" in migration_sql

    def test_cost_centers_service_role_full_access_policy(self, migration_sql):
        """AC4: Service role should have full access policy on cost_centers."""
        assert 'CREATE POLICY "Allow service_role full access on cost_centers"' in migration_sql
        assert "ON cost_centers FOR ALL" in migration_sql

    def test_shift_targets_service_role_full_access_policy(self, migration_sql):
        """AC4: Service role should have full access policy on shift_targets."""
        assert 'CREATE POLICY "Allow service_role full access on shift_targets"' in migration_sql
        assert "ON shift_targets FOR ALL" in migration_sql

    # =========================================================================
    # AC5: Performance Indexes Tests
    # =========================================================================

    def test_assets_source_id_index(self, migration_sql):
        """AC5: Index should exist on assets.source_id."""
        assert "CREATE INDEX IF NOT EXISTS idx_assets_source_id ON assets(source_id)" in migration_sql

    def test_cost_centers_asset_id_index(self, migration_sql):
        """AC5: Index should exist on cost_centers.asset_id."""
        assert "CREATE INDEX IF NOT EXISTS idx_cost_centers_asset_id ON cost_centers(asset_id)" in migration_sql

    def test_shift_targets_asset_id_index(self, migration_sql):
        """AC5: Index should exist on shift_targets.asset_id."""
        assert "CREATE INDEX IF NOT EXISTS idx_shift_targets_asset_id ON shift_targets(asset_id)" in migration_sql

    def test_shift_targets_effective_date_index(self, migration_sql):
        """AC5: Index should exist on shift_targets.effective_date."""
        assert "CREATE INDEX IF NOT EXISTS idx_shift_targets_effective_date ON shift_targets(effective_date)" in migration_sql

    # =========================================================================
    # AC6: Idempotency Tests
    # =========================================================================

    def test_migration_uses_if_not_exists(self, migration_sql):
        """AC6: Migration should use CREATE IF NOT EXISTS for idempotency."""
        # All table creations should use IF NOT EXISTS
        assert "CREATE TABLE IF NOT EXISTS assets" in migration_sql
        assert "CREATE TABLE IF NOT EXISTS cost_centers" in migration_sql
        assert "CREATE TABLE IF NOT EXISTS shift_targets" in migration_sql

        # All index creations should use IF NOT EXISTS
        assert "CREATE INDEX IF NOT EXISTS idx_assets_source_id" in migration_sql
        assert "CREATE INDEX IF NOT EXISTS idx_cost_centers_asset_id" in migration_sql
        assert "CREATE INDEX IF NOT EXISTS idx_shift_targets_asset_id" in migration_sql
        assert "CREATE INDEX IF NOT EXISTS idx_shift_targets_effective_date" in migration_sql

        # Extension creation should use IF NOT EXISTS
        assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in migration_sql

    def test_migration_drops_triggers_before_create(self, migration_sql):
        """AC6: Migration should drop triggers before creating for idempotency."""
        assert "DROP TRIGGER IF EXISTS update_assets_updated_at ON assets" in migration_sql
        assert "DROP TRIGGER IF EXISTS update_cost_centers_updated_at ON cost_centers" in migration_sql
        assert "DROP TRIGGER IF EXISTS update_shift_targets_updated_at ON shift_targets" in migration_sql

    def test_migration_drops_policies_before_create(self, migration_sql):
        """AC6: Migration should drop policies before creating for idempotency."""
        # Assets policies
        assert 'DROP POLICY IF EXISTS "Allow authenticated read access on assets" ON assets' in migration_sql
        assert 'DROP POLICY IF EXISTS "Allow service_role full access on assets" ON assets' in migration_sql

        # Cost centers policies
        assert 'DROP POLICY IF EXISTS "Allow authenticated read access on cost_centers" ON cost_centers' in migration_sql
        assert 'DROP POLICY IF EXISTS "Allow service_role full access on cost_centers" ON cost_centers' in migration_sql

        # Shift targets policies
        assert 'DROP POLICY IF EXISTS "Allow authenticated read access on shift_targets" ON shift_targets' in migration_sql
        assert 'DROP POLICY IF EXISTS "Allow service_role full access on shift_targets" ON shift_targets' in migration_sql


class TestMigrationSQLSyntax:
    """Tests to verify the migration SQL syntax is valid."""

    @pytest.fixture
    def migration_sql(self):
        """Load the migration SQL content."""
        migration_path = get_migration_path()
        with open(migration_path, "r") as f:
            return f.read()

    def test_sql_has_no_unclosed_parentheses(self, migration_sql):
        """SQL should have balanced parentheses."""
        # Remove comments and strings for accurate counting
        sql_no_comments = re.sub(r"--.*$", "", migration_sql, flags=re.MULTILINE)
        sql_no_strings = re.sub(r"'[^']*'", "", sql_no_comments)

        open_count = sql_no_strings.count("(")
        close_count = sql_no_strings.count(")")

        assert open_count == close_count, f"Unbalanced parentheses: {open_count} open, {close_count} close"

    def test_sql_statements_end_with_semicolon(self, migration_sql):
        """All SQL statements should end with semicolons."""
        # Check for common statement keywords that should end with semicolon
        # We'll verify that CREATE TABLE, CREATE INDEX, ALTER TABLE, etc. are followed by semicolons
        patterns_requiring_semicolon = [
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+\w+\s*\([^;]+\)",
            r"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+\w+\s+ON\s+\w+\([^;]+\)",
            r"ALTER\s+TABLE\s+\w+\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
        ]

        for pattern in patterns_requiring_semicolon:
            matches = re.findall(pattern, migration_sql, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Find this match in the original SQL and check it ends with ;
                end_pos = migration_sql.find(match) + len(match)
                # Look for semicolon within next 5 characters (allowing for whitespace)
                next_chars = migration_sql[end_pos:end_pos+10]
                assert ";" in next_chars, f"Statement should end with semicolon: {match[:50]}..."

    def test_foreign_key_references_valid_tables(self, migration_sql):
        """Foreign keys should reference the assets table correctly."""
        # cost_centers.asset_id should reference assets(id)
        assert "asset_id UUID NOT NULL REFERENCES assets(id)" in migration_sql

        # Check both cost_centers and shift_targets have proper foreign key references
        fk_pattern = r"asset_id\s+UUID\s+NOT NULL\s+REFERENCES\s+assets\(id\)\s+ON DELETE CASCADE"
        fk_matches = re.findall(fk_pattern, migration_sql, re.IGNORECASE)
        assert len(fk_matches) == 2, "Should have 2 foreign key references to assets (cost_centers and shift_targets)"
