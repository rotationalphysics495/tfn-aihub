#!/usr/bin/env node
/**
 * Run migration to add downtime_reasons column
 * Uses direct PostgreSQL connection via Supabase REST API
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://gfmalixorurasjrlgicq.supabase.co';
const SUPABASE_KEY = 'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false }
});

async function runMigration() {
  console.log('🔧 Running migration to add downtime_reasons column...\n');

  // Try to run the migration using rpc
  const { data, error } = await supabase.rpc('exec_sql', {
    sql: `
      ALTER TABLE daily_summaries
      ADD COLUMN IF NOT EXISTS downtime_reasons JSONB DEFAULT NULL;
    `
  });

  if (error) {
    console.log('  Note: Could not run migration via RPC (expected if exec_sql function does not exist)');
    console.log('  Error:', error.message);
    console.log('\n  Please run this SQL manually in the Supabase dashboard SQL editor:');
    console.log('  ------------------------------------------------------------------');
    console.log('  ALTER TABLE daily_summaries ADD COLUMN IF NOT EXISTS downtime_reasons JSONB DEFAULT NULL;');
    console.log('  ------------------------------------------------------------------');
    return false;
  }

  console.log('  ✓ Migration completed successfully');
  return true;
}

runMigration().catch(console.error);
