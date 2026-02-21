#!/usr/bin/env node
/**
 * Epic 10 UAT Empty-State Helper
 *
 * Usage:
 *   node _bmad/scripts/clear-epic10-uat.mjs clear-snapshots
 *     → Deletes all live_snapshots rows so Live Pulse shows empty/zero state
 *       (Scenario 8 Step 3)
 *
 *   node _bmad/scripts/clear-epic10-uat.mjs clear-financials
 *     → Deletes all daily_summaries rows for the most recent report_date so
 *       the Cost of Loss widget shows "No financial data available for this period"
 *       (Scenario 8 Step 4)
 *
 *   node _bmad/scripts/clear-epic10-uat.mjs reseed
 *     → Re-runs the full seed script to restore all UAT data
 */

import { createClient } from '@supabase/supabase-js';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';

const SUPABASE_URL = 'https://gfmalixorurasjrlgicq.supabase.co';
const SUPABASE_KEY = 'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const command = process.argv[2];

if (!command || !['clear-snapshots', 'clear-financials', 'reseed'].includes(command)) {
  console.error('Usage:');
  console.error('  node _bmad/scripts/clear-epic10-uat.mjs clear-snapshots');
  console.error('  node _bmad/scripts/clear-epic10-uat.mjs clear-financials');
  console.error('  node _bmad/scripts/clear-epic10-uat.mjs reseed');
  process.exit(1);
}

// ============================================================================
// CLEAR SNAPSHOTS (Scenario 8 Step 3: Live Pulse empty state)
// ============================================================================

async function clearSnapshots() {
  console.log('🗑️  Clearing live_snapshots for Scenario 8 Step 3...\n');

  // Count existing rows first
  const { count: before } = await supabase
    .from('live_snapshots')
    .select('id', { count: 'exact', head: true });

  console.log(`  Before: ${before || 0} snapshot rows`);

  // Delete ALL snapshots — using a always-true filter
  const { error } = await supabase
    .from('live_snapshots')
    .delete()
    .gte('snapshot_timestamp', '2000-01-01');

  if (error) {
    console.error('  ✗ Error clearing live_snapshots:', error.message);
    process.exit(1);
  }

  const { count: after } = await supabase
    .from('live_snapshots')
    .select('id', { count: 'exact', head: true });

  console.log(`  After:  ${after || 0} snapshot rows`);
  console.log('\n✅ live_snapshots cleared.');
  console.log('\nNow test Scenario 8 Step 3:');
  console.log('  1. Refresh the dashboard (http://localhost:3000)');
  console.log('  2. The Live Pulse ticker should still load (no crash/500)');
  console.log('  3. Production Status shows 0% throughput, 0 machines — graceful empty state');
  console.log('\nWhen done, restore data with:');
  console.log('  node _bmad/scripts/clear-epic10-uat.mjs reseed');
}

// ============================================================================
// CLEAR FINANCIALS (Scenario 8 Step 4: Cost of Loss empty state)
// ============================================================================

async function clearFinancials() {
  console.log('🗑️  Clearing daily_summaries for Scenario 8 Step 4...\n');

  // Find the most recent report_date
  const { data: latest } = await supabase
    .from('daily_summaries')
    .select('report_date')
    .order('report_date', { ascending: false })
    .limit(1);

  if (!latest || latest.length === 0) {
    console.log('  No daily_summaries rows found — already empty.');
    return;
  }

  const latestDate = latest[0].report_date;
  console.log(`  Most recent report_date: ${latestDate}`);

  // Count rows for that date
  const { count: before } = await supabase
    .from('daily_summaries')
    .select('id', { count: 'exact', head: true })
    .eq('report_date', latestDate);

  console.log(`  Rows for ${latestDate}: ${before || 0}`);

  // Delete all rows for the most recent date
  const { error } = await supabase
    .from('daily_summaries')
    .delete()
    .eq('report_date', latestDate);

  if (error) {
    console.error(`  ✗ Error deleting daily_summaries for ${latestDate}:`, error.message);
    process.exit(1);
  }

  const { count: after } = await supabase
    .from('daily_summaries')
    .select('id', { count: 'exact', head: true })
    .eq('report_date', latestDate);

  console.log(`  Rows for ${latestDate} after delete: ${after || 0}`);
  console.log('\n✅ daily_summaries cleared for most recent date.');
  console.log('\nNow test Scenario 8 Step 4:');
  console.log('  1. Refresh the dashboard (http://localhost:3000)');
  console.log('  2. The Cost of Loss widget (T-1 mode) should show:');
  console.log('     "No financial data available for this period"');
  console.log('  3. No crash, no server error — clean empty state');
  console.log('\nWhen done, restore data with:');
  console.log('  node _bmad/scripts/clear-epic10-uat.mjs reseed');
}

// ============================================================================
// RESEED (Restore UAT data)
// ============================================================================

async function reseed() {
  console.log('🌱 Re-seeding all Epic 10 UAT data...\n');
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const seedScript = path.join(__dirname, 'seed-epic10-uat.mjs');
  execSync(`node "${seedScript}"`, { stdio: 'inherit' });
}

// ============================================================================
// MAIN
// ============================================================================

if (command === 'clear-snapshots') {
  await clearSnapshots();
} else if (command === 'clear-financials') {
  await clearFinancials();
} else if (command === 'reseed') {
  await reseed();
}
