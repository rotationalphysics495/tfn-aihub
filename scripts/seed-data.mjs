#!/usr/bin/env node
/**
 * Seed script to populate Supabase with test data
 * Uses the service role key to bypass RLS
 *
 * Usage: node scripts/seed-data.mjs
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://gfmalixorurasjrlgicq.supabase.co';
const SUPABASE_KEY = 'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false }
});

// Helper to get date offset from today
const daysAgo = (days) => {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
};

const hoursAgo = (hours) => {
  const d = new Date();
  d.setTime(d.getTime() - hours * 60 * 60 * 1000);
  return d.toISOString();
};

const minutesAgo = (mins) => {
  const d = new Date();
  d.setTime(d.getTime() - mins * 60 * 1000);
  return d.toISOString();
};

async function seed() {
  console.log('🌱 Starting seed...\n');

  // 0. Clear existing data that needs to be refreshed
  console.log('🧹 Clearing existing data...');
  await supabase.from('safety_events').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('live_snapshots').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  console.log('  ✓ Cleared safety_events and live_snapshots');

  // 1. Assets
  console.log('📦 Inserting assets...');
  const assets = [
    { id: 'a0000001-0000-0000-0000-000000000001', name: 'Roaster 1', source_id: 'ROAST-001', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000002', name: 'Roaster 2', source_id: 'ROAST-002', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000003', name: 'Roaster 3', source_id: 'ROAST-003', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000004', name: 'Grinder 1', source_id: 'GRND-001', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000005', name: 'Grinder 2', source_id: 'GRND-002', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000006', name: 'Grinder 3', source_id: 'GRND-003', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000007', name: 'Grinder 4', source_id: 'GRND-004', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000008', name: 'Filler Line A', source_id: 'FILL-001', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000009', name: 'Filler Line B', source_id: 'FILL-002', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000010', name: 'Filler Line C', source_id: 'FILL-003', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000011', name: 'Packaging Line 1', source_id: 'PACK-001', area: 'Packaging' },
    { id: 'a0000001-0000-0000-0000-000000000012', name: 'Packaging Line 2', source_id: 'PACK-002', area: 'Packaging' },
    { id: 'a0000001-0000-0000-0000-000000000013', name: 'Packaging Line 3', source_id: 'PACK-003', area: 'Packaging' },
  ];

  const { error: assetsErr } = await supabase.from('assets').upsert(assets, { onConflict: 'id' });
  if (assetsErr) console.error('  Assets error:', assetsErr.message);
  else console.log('  ✓ 13 assets inserted');

  // 2. Cost Centers
  console.log('💰 Inserting cost centers...');
  const costCenters = [
    { asset_id: 'a0000001-0000-0000-0000-000000000001', standard_hourly_rate: 250.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', standard_hourly_rate: 250.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000003', standard_hourly_rate: 250.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000004', standard_hourly_rate: 175.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000005', standard_hourly_rate: 175.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000006', standard_hourly_rate: 175.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000007', standard_hourly_rate: 175.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000008', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000009', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000010', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', standard_hourly_rate: 95.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', standard_hourly_rate: 95.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000013', standard_hourly_rate: 95.00 },
  ];

  const { error: costErr } = await supabase.from('cost_centers').upsert(costCenters, { onConflict: 'asset_id' });
  if (costErr) console.error('  Cost centers error:', costErr.message);
  else console.log('  ✓ 13 cost centers inserted');

  // 3. Daily Summaries (last 7 days)
  // Epic 3 UAT: Ensure all three action item categories are represented
  // - OEE: Assets below 85% target
  // - Financial: Assets with loss > $1,000
  // - Safety: Handled separately in safety_events table
  console.log('📊 Inserting daily summaries...');
  const dailySummaries = [
    // Roaster 1 - FINANCIAL action item (loss > $1,000, but OEE still above 85%)
    { asset_id: 'a0000001-0000-0000-0000-000000000001', report_date: daysAgo(1), oee_percentage: 87.50, actual_output: 125, target_output: 143, downtime_minutes: 45, waste_count: 8, financial_loss_dollars: 1450.00, smart_summary_text: 'Roaster 1 experienced cooling system issues causing extended batch cycle times. 8 batches discarded due to over-roasting. Maintenance investigating root cause.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000001', report_date: daysAgo(2), oee_percentage: 94.20, actual_output: 135, target_output: 143, downtime_minutes: 18, waste_count: 1, financial_loss_dollars: 75.00, smart_summary_text: 'Outstanding roasting day. Colombian single-origin profile nailed consistently.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000001', report_date: daysAgo(3), oee_percentage: 75.80, actual_output: 108, target_output: 143, downtime_minutes: 95, waste_count: 8, financial_loss_dollars: 395.83, smart_summary_text: 'Drum temperature sensor malfunction caused extended downtime.' },
    // Roaster 2 - Good performance
    { asset_id: 'a0000001-0000-0000-0000-000000000002', report_date: daysAgo(1), oee_percentage: 96.10, actual_output: 137, target_output: 143, downtime_minutes: 10, waste_count: 1, financial_loss_dollars: 41.67, smart_summary_text: 'Best performing roaster yesterday. Dark roast blend running flawlessly.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', report_date: daysAgo(2), oee_percentage: 85.30, actual_output: 122, target_output: 143, downtime_minutes: 55, waste_count: 6, financial_loss_dollars: 229.17, smart_summary_text: 'Burner ignition issue caused startup delays.' },
    // Grinder 1 - Good performance
    { asset_id: 'a0000001-0000-0000-0000-000000000004', report_date: daysAgo(1), oee_percentage: 91.20, actual_output: 1780, target_output: 1950, downtime_minutes: 30, waste_count: 25, financial_loss_dollars: 87.50, smart_summary_text: 'Grinder 1 running well. Espresso grind consistency excellent.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000004', report_date: daysAgo(2), oee_percentage: 88.50, actual_output: 1725, target_output: 1950, downtime_minutes: 48, waste_count: 35, financial_loss_dollars: 140.00, smart_summary_text: 'Slight throughput dip due to harder bean batch.' },
    // Filler A - OEE action item (below 85%, but loss under $1,000)
    { asset_id: 'a0000001-0000-0000-0000-000000000008', report_date: daysAgo(1), oee_percentage: 72.50, actual_output: 3335, target_output: 4600, downtime_minutes: 95, waste_count: 120, financial_loss_dollars: 265.00, smart_summary_text: 'Filler A experiencing valve sticking issues. Multiple stoppages throughout shift. Maintenance called - awaiting parts for full repair.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000008', report_date: daysAgo(2), oee_percentage: 92.30, actual_output: 4246, target_output: 4600, downtime_minutes: 28, waste_count: 45, financial_loss_dollars: 58.33, smart_summary_text: 'Strong filling performance. New bag stock feeding well.' },
    // Packaging 1 - Good performance
    { asset_id: 'a0000001-0000-0000-0000-000000000011', report_date: daysAgo(1), oee_percentage: 89.50, actual_output: 5549, target_output: 6200, downtime_minutes: 42, waste_count: 65, financial_loss_dollars: 66.50, smart_summary_text: 'Good day on Packaging Line 1. Minor label changeover delays. All cases passed QC.' },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', report_date: daysAgo(2), oee_percentage: 94.80, actual_output: 5878, target_output: 6200, downtime_minutes: 18, waste_count: 42, financial_loss_dollars: 28.50, smart_summary_text: 'Outstanding day. Holiday blend cases flowing smoothly.' },
  ];

  const { error: summariesErr } = await supabase.from('daily_summaries').upsert(dailySummaries, { onConflict: 'asset_id,report_date' });
  if (summariesErr) console.error('  Daily summaries error:', summariesErr.message);
  else console.log('  ✓ Daily summaries inserted');

  // 4. Live Snapshots
  console.log('⚡ Inserting live snapshots...');
  const liveSnapshots = [
    { asset_id: 'a0000001-0000-0000-0000-000000000001', snapshot_timestamp: minutesAgo(15), current_output: 6, target_output: 6, status: 'on_target', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000001', snapshot_timestamp: minutesAgo(30), current_output: 11, target_output: 12, status: 'behind', financial_loss_dollars: 62.50 },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', snapshot_timestamp: minutesAgo(15), current_output: 7, target_output: 6, status: 'ahead', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000004', snapshot_timestamp: minutesAgo(15), current_output: 245, target_output: 250, status: 'behind', financial_loss_dollars: 14.58 },
    { asset_id: 'a0000001-0000-0000-0000-000000000005', snapshot_timestamp: minutesAgo(15), current_output: 252, target_output: 250, status: 'ahead', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000008', snapshot_timestamp: minutesAgo(15), current_output: 285, target_output: 300, status: 'behind', financial_loss_dollars: 31.25 },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', snapshot_timestamp: minutesAgo(15), current_output: 380, target_output: 400, status: 'behind', financial_loss_dollars: 31.67 },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', snapshot_timestamp: minutesAgo(15), current_output: 400, target_output: 400, status: 'on_target', financial_loss_dollars: 0 },
  ];

  const { error: snapshotsErr } = await supabase.from('live_snapshots').insert(liveSnapshots);
  if (snapshotsErr) console.error('  Live snapshots error:', snapshotsErr.message);
  else console.log('  ✓ Live snapshots inserted');

  // 5. Safety Events
  // Epic 3 UAT: At least one unresolved SAFETY action item
  console.log('🚨 Inserting safety events...');
  const safetyEvents = [
    { asset_id: 'a0000001-0000-0000-0000-000000000001', event_timestamp: hoursAgo(72), reason_code: 'Safety Issue', severity: 'medium', description: 'Chaff fire detected in cooling tray. Suppression system activated. No injuries.', is_resolved: true, resolved_at: hoursAgo(71) },
    // SAFETY action item - unresolved
    { asset_id: 'a0000001-0000-0000-0000-000000000005', event_timestamp: hoursAgo(2), reason_code: 'Safety Issue', severity: 'medium', description: 'Grinder 2 vibration alarm - potential imbalance detected. Machine stopped for inspection. Awaiting maintenance assessment.', is_resolved: false },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', event_timestamp: hoursAgo(24), reason_code: 'Safety Issue', severity: 'low', description: 'Light curtain triggered on case erector. Safety system worked correctly.', is_resolved: true, resolved_at: hoursAgo(23.5) },
  ];

  const { error: safetyErr } = await supabase.from('safety_events').insert(safetyEvents);
  if (safetyErr) console.error('  Safety events error:', safetyErr.message);
  else console.log('  ✓ Safety events inserted');

  // 6. Create test user if not exists
  console.log('👤 Creating test user...');
  const { data: existingUser } = await supabase.auth.admin.listUsers();
  const testUserExists = existingUser?.users?.some(u => u.email === 'heimdall@test.com');

  if (!testUserExists) {
    const { data: newUser, error: userErr } = await supabase.auth.admin.createUser({
      email: 'heimdall@test.com',
      password: 'Test1234!@#$',
      email_confirm: true,
    });
    if (userErr) console.error('  User creation error:', userErr.message);
    else console.log('  ✓ Test user created: heimdall@test.com');
  } else {
    console.log('  ✓ Test user already exists');
  }

  console.log('\n✅ Seed complete!');
  console.log('\nYou can now log in with:');
  console.log('  Email: heimdall@test.com');
  console.log('  Password: Test1234!@#$');
}

seed().catch(console.error);
