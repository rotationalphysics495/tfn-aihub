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

  // 1. Assets (Epic 5 UAT: 5-8 assets required, including Grinder 5)
  console.log('📦 Inserting assets...');
  const assets = [
    { id: 'a0000001-0000-0000-0000-000000000001', name: 'Roaster 1', source_id: 'ROAST-001', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000002', name: 'Roaster 2', source_id: 'ROAST-002', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000003', name: 'Roaster 3', source_id: 'ROAST-003', area: 'Roasting' },
    { id: 'a0000001-0000-0000-0000-000000000004', name: 'Grinder 1', source_id: 'GRND-001', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000005', name: 'Grinder 2', source_id: 'GRND-002', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000006', name: 'Grinder 3', source_id: 'GRND-003', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000007', name: 'Grinder 4', source_id: 'GRND-004', area: 'Grinding' },
    // Epic 5 UAT requires "Grinder 5" specifically for test scenarios
    { id: 'a0000001-0000-0000-0000-000000000014', name: 'Grinder 5', source_id: 'GRND-005', area: 'Grinding' },
    { id: 'a0000001-0000-0000-0000-000000000008', name: 'Filler Line A', source_id: 'FILL-001', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000009', name: 'Filler Line B', source_id: 'FILL-002', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000010', name: 'Filler Line C', source_id: 'FILL-003', area: 'Filling' },
    { id: 'a0000001-0000-0000-0000-000000000011', name: 'Packaging Line 1', source_id: 'PACK-001', area: 'Packaging' },
    { id: 'a0000001-0000-0000-0000-000000000012', name: 'Packaging Line 2', source_id: 'PACK-002', area: 'Packaging' },
    { id: 'a0000001-0000-0000-0000-000000000013', name: 'Packaging Line 3', source_id: 'PACK-003', area: 'Packaging' },
  ];

  const { error: assetsErr } = await supabase.from('assets').upsert(assets, { onConflict: 'id' });
  if (assetsErr) console.error('  Assets error:', assetsErr.message);
  else console.log('  ✓ 14 assets inserted (including Grinder 5)');

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
    // Grinder 5 cost center
    { asset_id: 'a0000001-0000-0000-0000-000000000014', standard_hourly_rate: 175.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000008', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000009', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000010', standard_hourly_rate: 125.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', standard_hourly_rate: 95.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', standard_hourly_rate: 95.00 },
    { asset_id: 'a0000001-0000-0000-0000-000000000013', standard_hourly_rate: 95.00 },
  ];

  // Insert cost centers, ignoring conflicts (cost_centers may not have unique constraint on asset_id)
  for (const cc of costCenters) {
    const { error } = await supabase.from('cost_centers').upsert(cc, { ignoreDuplicates: true });
    if (error && !error.message.includes('duplicate')) {
      console.error('  Cost center error:', error.message);
    }
  }
  console.log('  ✓ Cost centers processed');

  // 3. Daily Summaries (last 7 days)
  // Epic 5 UAT: Production data from the past 7 days with downtime_reasons for Pareto analysis
  // Grinder 5 is key asset for UAT scenarios
  console.log('📊 Inserting daily summaries...');
  const dailySummaries = [
    // ============ GRINDER 5 - Key UAT Asset (7 days of data) ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(1),
      oee_percentage: 82.50,
      actual_output: 1608,
      target_output: 1950,
      downtime_minutes: 72,
      waste_count: 35,
      financial_loss_dollars: 210.00,
      downtime_reasons: { "Mechanical Failure": 35, "Changeover": 22, "Material Shortage": 15 },
      smart_summary_text: 'Grinder 5 had mechanical issues with the burr assembly causing 35 minutes of downtime. Changeover for espresso grind took longer than planned.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(2),
      oee_percentage: 88.30,
      actual_output: 1722,
      target_output: 1950,
      downtime_minutes: 45,
      waste_count: 28,
      financial_loss_dollars: 131.25,
      downtime_reasons: { "Mechanical Failure": 25, "Operator Break": 20 },
      smart_summary_text: 'Grinder 5 running better. Minor mechanical adjustment needed mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(3),
      oee_percentage: 76.80,
      actual_output: 1498,
      target_output: 1950,
      downtime_minutes: 98,
      waste_count: 45,
      financial_loss_dollars: 285.83,
      downtime_reasons: { "Mechanical Failure": 55, "Safety Stop": 28, "Changeover": 15 },
      smart_summary_text: 'Rough day for Grinder 5. Burr replacement required after vibration alarm. Safety stop triggered during inspection.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(4),
      oee_percentage: 91.20,
      actual_output: 1778,
      target_output: 1950,
      downtime_minutes: 32,
      waste_count: 22,
      financial_loss_dollars: 93.33,
      downtime_reasons: { "Changeover": 18, "Operator Break": 14 },
      smart_summary_text: 'Solid performance on Grinder 5. Standard changeover for medium roast batch.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(5),
      oee_percentage: 85.60,
      actual_output: 1669,
      target_output: 1950,
      downtime_minutes: 58,
      waste_count: 30,
      financial_loss_dollars: 169.17,
      downtime_reasons: { "Material Shortage": 30, "Mechanical Failure": 18, "Cleanup": 10 },
      smart_summary_text: 'Bean hopper ran empty twice waiting on roaster output. Some mechanical adjustments needed.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(6),
      oee_percentage: 89.40,
      actual_output: 1743,
      target_output: 1950,
      downtime_minutes: 40,
      waste_count: 25,
      financial_loss_dollars: 116.67,
      downtime_reasons: { "Changeover": 25, "Cleanup": 15 },
      smart_summary_text: 'Good day. Multiple changeovers for different grind sizes but handled well.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(7),
      oee_percentage: 87.10,
      actual_output: 1698,
      target_output: 1950,
      downtime_minutes: 52,
      waste_count: 28,
      financial_loss_dollars: 151.67,
      downtime_reasons: { "Mechanical Failure": 32, "Operator Break": 20 },
      smart_summary_text: 'Steady performance with minor mechanical hiccups.'
    },

    // ============ GRINDER 1 - 7 days with downtime reasons ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(1),
      oee_percentage: 91.20,
      actual_output: 1780,
      target_output: 1950,
      downtime_minutes: 30,
      waste_count: 25,
      financial_loss_dollars: 87.50,
      downtime_reasons: { "Changeover": 20, "Cleanup": 10 },
      smart_summary_text: 'Grinder 1 running well. Espresso grind consistency excellent.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(2),
      oee_percentage: 88.50,
      actual_output: 1725,
      target_output: 1950,
      downtime_minutes: 48,
      waste_count: 35,
      financial_loss_dollars: 140.00,
      downtime_reasons: { "Material Issue": 28, "Changeover": 20 },
      smart_summary_text: 'Slight throughput dip due to harder bean batch.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(3),
      oee_percentage: 94.80,
      actual_output: 1848,
      target_output: 1950,
      downtime_minutes: 15,
      waste_count: 18,
      financial_loss_dollars: 43.75,
      downtime_reasons: { "Cleanup": 15 },
      smart_summary_text: 'Outstanding grinding day. Medium roast flowing at optimal rate.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(4),
      oee_percentage: 72.30,
      actual_output: 1409,
      target_output: 1950,
      downtime_minutes: 125,
      waste_count: 65,
      financial_loss_dollars: 364.58,
      downtime_reasons: { "Mechanical Failure": 95, "Changeover": 30 },
      smart_summary_text: 'Burr replacement required after detecting uneven particle distribution. Extended downtime for maintenance.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(5),
      oee_percentage: 93.20,
      actual_output: 1817,
      target_output: 1950,
      downtime_minutes: 20,
      waste_count: 22,
      financial_loss_dollars: 58.33,
      downtime_reasons: { "Changeover": 12, "Cleanup": 8 },
      smart_summary_text: 'Post-maintenance performance excellent. New burrs producing consistent grind.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(6),
      oee_percentage: 90.10,
      actual_output: 1756,
      target_output: 1950,
      downtime_minutes: 35,
      waste_count: 27,
      financial_loss_dollars: 102.08,
      downtime_reasons: { "Operator Break": 20, "Changeover": 15 },
      smart_summary_text: 'Consistent grinding. Brief pause for shift handover.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(7),
      oee_percentage: 86.50,
      actual_output: 1687,
      target_output: 1950,
      downtime_minutes: 55,
      waste_count: 32,
      financial_loss_dollars: 160.42,
      downtime_reasons: { "Material Issue": 35, "Cleanup": 20 },
      smart_summary_text: 'Some issues with bean moisture affecting grind quality.'
    },

    // ============ GRINDER 2 - 7 days (good uptime asset for Scenario 9) ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(1),
      oee_percentage: 95.80,
      actual_output: 1868,
      target_output: 1950,
      downtime_minutes: 0,
      waste_count: 15,
      financial_loss_dollars: 0,
      downtime_reasons: {},
      smart_summary_text: 'Perfect uptime day! Grinder 2 running flawlessly on French press coarse grind.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(2),
      oee_percentage: 95.50,
      actual_output: 1862,
      target_output: 1950,
      downtime_minutes: 12,
      waste_count: 15,
      financial_loss_dollars: 35.00,
      downtime_reasons: { "Cleanup": 12 },
      smart_summary_text: 'Top performance. Coarse grind for French press line running smoothly.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(3),
      oee_percentage: 90.30,
      actual_output: 1760,
      target_output: 1950,
      downtime_minutes: 35,
      waste_count: 28,
      financial_loss_dollars: 102.08,
      downtime_reasons: { "Changeover": 20, "Operator Break": 15 },
      smart_summary_text: 'Steady performance. Bean hopper sensor calibrated during shift change.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(4),
      oee_percentage: 92.40,
      actual_output: 1802,
      target_output: 1950,
      downtime_minutes: 25,
      waste_count: 20,
      financial_loss_dollars: 72.92,
      downtime_reasons: { "Changeover": 25 },
      smart_summary_text: 'Smooth operation with single changeover.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(5),
      oee_percentage: 94.10,
      actual_output: 1835,
      target_output: 1950,
      downtime_minutes: 18,
      waste_count: 18,
      financial_loss_dollars: 52.50,
      downtime_reasons: { "Cleanup": 18 },
      smart_summary_text: 'Excellent grinding consistency throughout the shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(6),
      oee_percentage: 91.80,
      actual_output: 1790,
      target_output: 1950,
      downtime_minutes: 28,
      waste_count: 22,
      financial_loss_dollars: 81.67,
      downtime_reasons: { "Operator Break": 18, "Cleanup": 10 },
      smart_summary_text: 'Reliable performance on dark roast batch.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(7),
      oee_percentage: 93.50,
      actual_output: 1823,
      target_output: 1950,
      downtime_minutes: 20,
      waste_count: 19,
      financial_loss_dollars: 58.33,
      downtime_reasons: { "Changeover": 20 },
      smart_summary_text: 'Consistent week-opener with quick changeover.'
    },

    // ============ GRINDER 3 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(1),
      oee_percentage: 84.20,
      actual_output: 1642,
      target_output: 1950,
      downtime_minutes: 62,
      waste_count: 38,
      financial_loss_dollars: 180.83,
      downtime_reasons: { "Mechanical Failure": 40, "Changeover": 22 },
      smart_summary_text: 'Grinder 3 had bearing noise issues requiring adjustment.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(2),
      oee_percentage: 89.70,
      actual_output: 1749,
      target_output: 1950,
      downtime_minutes: 38,
      waste_count: 25,
      financial_loss_dollars: 110.83,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Better day with routine changeovers.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(3),
      oee_percentage: 87.30,
      actual_output: 1702,
      target_output: 1950,
      downtime_minutes: 48,
      waste_count: 30,
      financial_loss_dollars: 140.00,
      downtime_reasons: { "Material Issue": 30, "Operator Break": 18 },
      smart_summary_text: 'Bean quality variance caused some adjustments.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(4),
      oee_percentage: 91.50,
      actual_output: 1784,
      target_output: 1950,
      downtime_minutes: 28,
      waste_count: 20,
      financial_loss_dollars: 81.67,
      downtime_reasons: { "Changeover": 18, "Cleanup": 10 },
      smart_summary_text: 'Good throughput on espresso grind setting.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(5),
      oee_percentage: 86.80,
      actual_output: 1693,
      target_output: 1950,
      downtime_minutes: 52,
      waste_count: 33,
      financial_loss_dollars: 151.67,
      downtime_reasons: { "Mechanical Failure": 35, "Cleanup": 17 },
      smart_summary_text: 'Burr alignment check required mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(6),
      oee_percentage: 90.20,
      actual_output: 1759,
      target_output: 1950,
      downtime_minutes: 35,
      waste_count: 24,
      financial_loss_dollars: 102.08,
      downtime_reasons: { "Changeover": 22, "Operator Break": 13 },
      smart_summary_text: 'Standard operation day.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(7),
      oee_percentage: 88.40,
      actual_output: 1724,
      target_output: 1950,
      downtime_minutes: 45,
      waste_count: 28,
      financial_loss_dollars: 131.25,
      downtime_reasons: { "Material Issue": 25, "Changeover": 20 },
      smart_summary_text: 'Some bean inconsistency from upstream roasting.'
    },

    // ============ ROASTER 1 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(1),
      oee_percentage: 87.50,
      actual_output: 125,
      target_output: 143,
      downtime_minutes: 45,
      waste_count: 8,
      financial_loss_dollars: 187.50,
      downtime_reasons: { "Cooling System": 30, "Changeover": 15 },
      smart_summary_text: 'Roaster 1 experienced cooling system issues causing extended batch cycle times.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(2),
      oee_percentage: 94.20,
      actual_output: 135,
      target_output: 143,
      downtime_minutes: 18,
      waste_count: 1,
      financial_loss_dollars: 75.00,
      downtime_reasons: { "Changeover": 18 },
      smart_summary_text: 'Outstanding roasting day. Colombian single-origin profile nailed consistently.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(3),
      oee_percentage: 75.80,
      actual_output: 108,
      target_output: 143,
      downtime_minutes: 95,
      waste_count: 8,
      financial_loss_dollars: 395.83,
      downtime_reasons: { "Sensor Malfunction": 65, "Calibration": 30 },
      smart_summary_text: 'Drum temperature sensor malfunction caused extended downtime.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(4),
      oee_percentage: 91.50,
      actual_output: 131,
      target_output: 143,
      downtime_minutes: 25,
      waste_count: 2,
      financial_loss_dollars: 104.17,
      downtime_reasons: { "Changeover": 15, "Cleanup": 10 },
      smart_summary_text: 'Strong recovery post-maintenance. Ethiopian Yirgacheffe roast profile optimized.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(5),
      oee_percentage: 87.20,
      actual_output: 125,
      target_output: 143,
      downtime_minutes: 42,
      waste_count: 4,
      financial_loss_dollars: 175.00,
      downtime_reasons: { "Material Issue": 27, "Changeover": 15 },
      smart_summary_text: 'Green bean moisture variance caused adjustments mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(6),
      oee_percentage: 92.80,
      actual_output: 133,
      target_output: 143,
      downtime_minutes: 22,
      waste_count: 2,
      financial_loss_dollars: 91.67,
      downtime_reasons: { "Changeover": 22 },
      smart_summary_text: 'Smooth operation. New Brazilian beans roasting beautifully.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(7),
      oee_percentage: 88.40,
      actual_output: 126,
      target_output: 143,
      downtime_minutes: 38,
      waste_count: 5,
      financial_loss_dollars: 158.33,
      downtime_reasons: { "Cleanup": 25, "Chaff Collection": 13 },
      smart_summary_text: 'Chaff collection system cleaned during shift. Brief stoppage prevented longer issue.'
    },

    // ============ ROASTER 2 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(1),
      oee_percentage: 96.10,
      actual_output: 137,
      target_output: 143,
      downtime_minutes: 10,
      waste_count: 1,
      financial_loss_dollars: 41.67,
      downtime_reasons: { "Changeover": 10 },
      smart_summary_text: 'Best performing roaster yesterday. Dark roast blend running flawlessly.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(2),
      oee_percentage: 85.30,
      actual_output: 122,
      target_output: 143,
      downtime_minutes: 55,
      waste_count: 6,
      financial_loss_dollars: 229.17,
      downtime_reasons: { "Burner Issue": 40, "Startup Delay": 15 },
      smart_summary_text: 'Burner ignition issue caused startup delays.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(3),
      oee_percentage: 93.00,
      actual_output: 133,
      target_output: 143,
      downtime_minutes: 20,
      waste_count: 2,
      financial_loss_dollars: 83.33,
      downtime_reasons: { "Changeover": 20 },
      smart_summary_text: 'Consistent performance. Decaf Swiss Water batch processed successfully.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(4),
      oee_percentage: 90.50,
      actual_output: 129,
      target_output: 143,
      downtime_minutes: 30,
      waste_count: 3,
      financial_loss_dollars: 125.00,
      downtime_reasons: { "Changeover": 18, "Cleanup": 12 },
      smart_summary_text: 'Steady roasting with routine maintenance.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(5),
      oee_percentage: 94.40,
      actual_output: 135,
      target_output: 143,
      downtime_minutes: 15,
      waste_count: 1,
      financial_loss_dollars: 62.50,
      downtime_reasons: { "Cleanup": 15 },
      smart_summary_text: 'Outstanding performance on medium roast blend.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(6),
      oee_percentage: 89.50,
      actual_output: 128,
      target_output: 143,
      downtime_minutes: 35,
      waste_count: 4,
      financial_loss_dollars: 145.83,
      downtime_reasons: { "Changeover": 22, "Operator Break": 13 },
      smart_summary_text: 'Good day with extended changeover for new blend.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(7),
      oee_percentage: 91.20,
      actual_output: 130,
      target_output: 143,
      downtime_minutes: 28,
      waste_count: 3,
      financial_loss_dollars: 116.67,
      downtime_reasons: { "Changeover": 18, "Cleanup": 10 },
      smart_summary_text: 'Reliable start to the week.'
    },

    // ============ FILLER A - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(1),
      oee_percentage: 72.50,
      actual_output: 3335,
      target_output: 4600,
      downtime_minutes: 95,
      waste_count: 120,
      financial_loss_dollars: 197.92,
      downtime_reasons: { "Valve Issue": 55, "Jam": 25, "Changeover": 15 },
      smart_summary_text: 'Filler A experiencing valve sticking issues. Multiple stoppages throughout shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(2),
      oee_percentage: 92.30,
      actual_output: 4246,
      target_output: 4600,
      downtime_minutes: 28,
      waste_count: 45,
      financial_loss_dollars: 58.33,
      downtime_reasons: { "Changeover": 18, "Cleanup": 10 },
      smart_summary_text: 'Strong filling performance. New bag stock feeding well.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(3),
      oee_percentage: 78.60,
      actual_output: 3616,
      target_output: 4600,
      downtime_minutes: 82,
      waste_count: 95,
      financial_loss_dollars: 170.83,
      downtime_reasons: { "Valve Issue": 45, "Jam": 22, "Cleanup": 15 },
      smart_summary_text: 'Valve sticking issue continued. Cleaned and reseated during break.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(4),
      oee_percentage: 95.10,
      actual_output: 4374,
      target_output: 4600,
      downtime_minutes: 15,
      waste_count: 35,
      financial_loss_dollars: 31.25,
      downtime_reasons: { "Changeover": 15 },
      smart_summary_text: 'Excellent recovery. K-Cup filling mode achieving target weights.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(5),
      oee_percentage: 88.40,
      actual_output: 4066,
      target_output: 4600,
      downtime_minutes: 42,
      waste_count: 58,
      financial_loss_dollars: 87.50,
      downtime_reasons: { "Jam": 27, "Changeover": 15 },
      smart_summary_text: 'Some jamming issues with new bag material.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(6),
      oee_percentage: 91.20,
      actual_output: 4195,
      target_output: 4600,
      downtime_minutes: 32,
      waste_count: 48,
      financial_loss_dollars: 66.67,
      downtime_reasons: { "Changeover": 22, "Cleanup": 10 },
      smart_summary_text: 'Solid performance on 2lb bag line.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(7),
      oee_percentage: 89.80,
      actual_output: 4131,
      target_output: 4600,
      downtime_minutes: 38,
      waste_count: 52,
      financial_loss_dollars: 79.17,
      downtime_reasons: { "Changeover": 25, "Operator Break": 13 },
      smart_summary_text: 'Good week opener for filling operations.'
    },

    // ============ PACKAGING LINE 1 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(1),
      oee_percentage: 89.50,
      actual_output: 5549,
      target_output: 6200,
      downtime_minutes: 42,
      waste_count: 65,
      financial_loss_dollars: 66.50,
      downtime_reasons: { "Label Changeover": 28, "Jam": 14 },
      smart_summary_text: 'Good day on Packaging Line 1. Minor label changeover delays.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(2),
      oee_percentage: 94.80,
      actual_output: 5878,
      target_output: 6200,
      downtime_minutes: 18,
      waste_count: 42,
      financial_loss_dollars: 28.50,
      downtime_reasons: { "Changeover": 18 },
      smart_summary_text: 'Outstanding day. Holiday blend cases flowing smoothly.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(3),
      oee_percentage: 79.30,
      actual_output: 4917,
      target_output: 6200,
      downtime_minutes: 88,
      waste_count: 145,
      financial_loss_dollars: 139.33,
      downtime_reasons: { "Case Erector Jam": 58, "Carton Issue": 30 },
      smart_summary_text: 'Case erector jam caused significant downtime. Maintenance cleared cardboard buildup.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(4),
      oee_percentage: 92.50,
      actual_output: 5735,
      target_output: 6200,
      downtime_minutes: 25,
      waste_count: 55,
      financial_loss_dollars: 39.58,
      downtime_reasons: { "Changeover": 15, "Cleanup": 10 },
      smart_summary_text: 'Strong recovery. Automated case packing running efficiently.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(5),
      oee_percentage: 87.20,
      actual_output: 5406,
      target_output: 6200,
      downtime_minutes: 52,
      waste_count: 78,
      financial_loss_dollars: 82.33,
      downtime_reasons: { "Label Changeover": 35, "Jam": 17 },
      smart_summary_text: 'Multiple SKU changeovers slowed throughput.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(6),
      oee_percentage: 91.80,
      actual_output: 5692,
      target_output: 6200,
      downtime_minutes: 30,
      waste_count: 52,
      financial_loss_dollars: 47.50,
      downtime_reasons: { "Changeover": 20, "Operator Break": 10 },
      smart_summary_text: 'Consistent packaging output.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(7),
      oee_percentage: 88.90,
      actual_output: 5512,
      target_output: 6200,
      downtime_minutes: 45,
      waste_count: 68,
      financial_loss_dollars: 71.25,
      downtime_reasons: { "Changeover": 30, "Cleanup": 15 },
      smart_summary_text: 'Solid week start with routine changeovers.'
    },

    // ============ TODAY (daysAgo(0)) - Partial day data for all key assets ============
    // Grinder 5 — running rough this morning, carryover from yesterday's issues
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(0),
      oee_percentage: 68.30,
      actual_output: 890,
      target_output: 1950,
      downtime_minutes: 48,
      waste_count: 42,
      financial_loss_dollars: 285.00,
      downtime_reasons: { "Mechanical Failure": 30, "Material Shortage": 18 },
      smart_summary_text: 'Grinder 5 struggling this morning. Burr assembly vibration returning — may need full replacement. Bean hopper ran dry during shift change.'
    },
    // Grinder 1 — solid morning
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(0),
      oee_percentage: 93.50,
      actual_output: 1218,
      target_output: 1950,
      downtime_minutes: 12,
      waste_count: 15,
      financial_loss_dollars: 45.00,
      downtime_reasons: { "Changeover": 12 },
      smart_summary_text: 'Grinder 1 running strong this morning. Espresso grind consistency excellent after yesterday\'s new burrs.'
    },
    // Grinder 2 — stopped due to safety event
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(0),
      oee_percentage: 45.20,
      actual_output: 588,
      target_output: 1950,
      downtime_minutes: 105,
      waste_count: 8,
      financial_loss_dollars: 420.00,
      downtime_reasons: { "Safety Stop": 90, "Inspection": 15 },
      smart_summary_text: 'Grinder 2 offline since vibration alarm at 9:51 AM. Awaiting maintenance assessment — machine locked out per SOP.'
    },
    // Roaster 1 — good morning
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(0),
      oee_percentage: 91.80,
      actual_output: 87,
      target_output: 143,
      downtime_minutes: 15,
      waste_count: 1,
      financial_loss_dollars: 62.50,
      downtime_reasons: { "Changeover": 15 },
      smart_summary_text: 'Roaster 1 on track. Running Colombian medium roast — first crack timing consistent at 9:42.'
    },
    // Roaster 2 — excellent
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(0),
      oee_percentage: 95.40,
      actual_output: 91,
      target_output: 143,
      downtime_minutes: 8,
      waste_count: 0,
      financial_loss_dollars: 33.33,
      downtime_reasons: { "Cleanup": 8 },
      smart_summary_text: 'Roaster 2 leading the floor. Dark roast Italian blend batch completing ahead of schedule.'
    },
    // Filler Line A — held due to nitrogen pressure issue
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(0),
      oee_percentage: 52.10,
      actual_output: 1598,
      target_output: 4600,
      downtime_minutes: 135,
      waste_count: 85,
      financial_loss_dollars: 562.50,
      downtime_reasons: { "Pressure Issue": 95, "QA Hold": 40 },
      smart_summary_text: 'Filler Line A held since nitrogen flush pressure dropped below spec. 42 bags quarantined. Line restarted at 10:30 AM after regulator replacement.'
    },
    // Grinder 3 — normal morning
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(0),
      oee_percentage: 88.70,
      actual_output: 1155,
      target_output: 1950,
      downtime_minutes: 22,
      waste_count: 20,
      financial_loss_dollars: 78.00,
      downtime_reasons: { "Changeover": 15, "Cleanup": 7 },
      smart_summary_text: 'Grinder 3 operating normally. Switched from French press to drip grind at 8:15 AM.'
    },
    // Packaging Line 1 — running well
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(0),
      oee_percentage: 92.30,
      actual_output: 3822,
      target_output: 6200,
      downtime_minutes: 18,
      waste_count: 35,
      financial_loss_dollars: 28.50,
      downtime_reasons: { "Label Changeover": 18 },
      smart_summary_text: 'Packaging Line 1 on pace. Running 12oz bags for the Costco order — label changeover at 7:45 AM went smoothly.'
    },
  ];

  // Strip downtime_reasons if column doesn't exist yet
  // The column can be added via: ALTER TABLE daily_summaries ADD COLUMN IF NOT EXISTS downtime_reasons JSONB DEFAULT NULL;
  const summariesWithoutReasons = dailySummaries.map(({ downtime_reasons, ...rest }) => rest);

  const { error: summariesErr } = await supabase.from('daily_summaries').upsert(summariesWithoutReasons, { onConflict: 'asset_id,report_date' });
  if (summariesErr) console.error('  Daily summaries error:', summariesErr.message);
  else console.log('  ✓ Daily summaries inserted (note: downtime_reasons requires manual migration)');

  // 4. Live Snapshots (Epic 5 UAT: Fresh snapshots for all key assets including Grinder 5)
  console.log('⚡ Inserting live snapshots...');
  const liveSnapshots = [
    // Roasters
    { asset_id: 'a0000001-0000-0000-0000-000000000001', snapshot_timestamp: minutesAgo(5), current_output: 6, target_output: 6, status: 'on_target', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', snapshot_timestamp: minutesAgo(5), current_output: 7, target_output: 6, status: 'ahead', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000003', snapshot_timestamp: minutesAgo(5), current_output: 5, target_output: 6, status: 'behind', financial_loss_dollars: 41.67 },
    // Grinders (including Grinder 5)
    { asset_id: 'a0000001-0000-0000-0000-000000000004', snapshot_timestamp: minutesAgo(5), current_output: 245, target_output: 250, status: 'behind', financial_loss_dollars: 14.58 },
    { asset_id: 'a0000001-0000-0000-0000-000000000005', snapshot_timestamp: minutesAgo(5), current_output: 252, target_output: 250, status: 'ahead', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000006', snapshot_timestamp: minutesAgo(5), current_output: 240, target_output: 250, status: 'behind', financial_loss_dollars: 29.17 },
    { asset_id: 'a0000001-0000-0000-0000-000000000007', snapshot_timestamp: minutesAgo(5), current_output: 255, target_output: 250, status: 'ahead', financial_loss_dollars: 0 },
    // Grinder 5 - Key UAT asset, currently running slightly behind
    { asset_id: 'a0000001-0000-0000-0000-000000000014', snapshot_timestamp: minutesAgo(5), current_output: 235, target_output: 250, status: 'behind', financial_loss_dollars: 43.75 },
    // Fillers
    { asset_id: 'a0000001-0000-0000-0000-000000000008', snapshot_timestamp: minutesAgo(5), current_output: 285, target_output: 300, status: 'behind', financial_loss_dollars: 31.25 },
    { asset_id: 'a0000001-0000-0000-0000-000000000009', snapshot_timestamp: minutesAgo(5), current_output: 305, target_output: 300, status: 'ahead', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000010', snapshot_timestamp: minutesAgo(5), current_output: 300, target_output: 300, status: 'on_target', financial_loss_dollars: 0 },
    // Packaging
    { asset_id: 'a0000001-0000-0000-0000-000000000011', snapshot_timestamp: minutesAgo(5), current_output: 380, target_output: 400, status: 'behind', financial_loss_dollars: 31.67 },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', snapshot_timestamp: minutesAgo(5), current_output: 400, target_output: 400, status: 'on_target', financial_loss_dollars: 0 },
    { asset_id: 'a0000001-0000-0000-0000-000000000013', snapshot_timestamp: minutesAgo(5), current_output: 410, target_output: 400, status: 'ahead', financial_loss_dollars: 0 },
  ];

  const { error: snapshotsErr } = await supabase.from('live_snapshots').insert(liveSnapshots);
  if (snapshotsErr) console.error('  Live snapshots error:', snapshotsErr.message);
  else console.log('  ✓ Live snapshots inserted');

  // 5. Safety Events
  // Epic 5 UAT: Safety events for Grinder 5 and other assets
  console.log('🚨 Inserting safety events...');
  const safetyEvents = [
    { asset_id: 'a0000001-0000-0000-0000-000000000001', event_timestamp: hoursAgo(72), reason_code: 'Chaff Fire', severity: 'high', description: 'Chaff fire detected in cooling tray during dark roast batch. Suppression system activated automatically. No injuries. Root cause: chaff buildup exceeded cleaning interval threshold.', is_resolved: true, resolved_at: hoursAgo(71) },
    // Grinder 5 safety event (key UAT asset)
    { asset_id: 'a0000001-0000-0000-0000-000000000014', event_timestamp: hoursAgo(48), reason_code: 'Vibration Alarm', severity: 'medium', description: 'Grinder 5 vibration exceeded 8.2mm/s threshold — potential bearing imbalance. Machine auto-stopped per SOP. Bearing inspection completed, cleared for operation.', is_resolved: true, resolved_at: hoursAgo(46) },
    // Grinder 2 unresolved safety event
    { asset_id: 'a0000001-0000-0000-0000-000000000005', event_timestamp: hoursAgo(2), reason_code: 'Vibration Alarm', severity: 'medium', description: 'Grinder 2 vibration at 7.9mm/s — approaching critical threshold. Burr assembly may be worn unevenly. Machine stopped, awaiting maintenance assessment before restart.', is_resolved: false },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', event_timestamp: hoursAgo(24), reason_code: 'Light Curtain Trip', severity: 'low', description: 'Light curtain triggered on Packaging Line 1 case erector during box jam clearance. Safety interlock engaged correctly. Operator retrained on proper jam clearing procedure.', is_resolved: true, resolved_at: hoursAgo(23.5) },
    // Filler Line A — nitrogen flush pressure drop
    { asset_id: 'a0000001-0000-0000-0000-000000000008', event_timestamp: hoursAgo(4), reason_code: 'Pressure Anomaly', severity: 'high', description: 'Nitrogen flush pressure dropped below 12 PSI minimum on Filler Line A. Product integrity risk — 42 bags quarantined for QA inspection. Line held pending pressure regulator check.', is_resolved: false },
  ];

  const { error: safetyErr } = await supabase.from('safety_events').insert(safetyEvents);
  if (safetyErr) console.error('  Safety events error:', safetyErr.message);
  else console.log('  ✓ Safety events inserted');

  // 6. Create test users if not exist
  console.log('👤 Creating test users...');
  const testUsers = [
    { email: 'heimdall@test.com', role: 'admin' },
    { email: 'maria.garcia@test.com', role: 'plant_manager' },
    { email: 'james.chen@test.com', role: 'supervisor' },
    { email: 'sarah.johnson@test.com', role: 'supervisor' },
    { email: 'mike.torres@test.com', role: 'supervisor' },
  ];

  const { data: existingUser } = await supabase.auth.admin.listUsers();
  const existingEmails = new Set(existingUser?.users?.map(u => u.email) || []);

  for (const user of testUsers) {
    if (existingEmails.has(user.email)) {
      console.log(`  ✓ ${user.email} already exists`);
      // Ensure role is set
      const existing = existingUser?.users?.find(u => u.email === user.email);
      if (existing) {
        await supabase.from('user_roles').upsert(
          { user_id: existing.id, role: user.role },
          { onConflict: 'user_id' }
        );
      }
      continue;
    }

    const { data: newUser, error: userErr } = await supabase.auth.admin.createUser({
      email: user.email,
      password: 'Test1234!@#$',
      email_confirm: true,
    });
    if (userErr) {
      console.error(`  ${user.email} error:`, userErr.message);
    } else {
      console.log(`  ✓ Created ${user.email} (${user.role})`);
      // Set role
      if (newUser?.user) {
        await supabase.from('user_roles').upsert(
          { user_id: newUser.user.id, role: user.role },
          { onConflict: 'user_id' }
        );
      }
    }
  }

  console.log('\n✅ Seed complete!');
  console.log('\nYou can log in with any of these (password: Test1234!@#$):');
  for (const user of testUsers) {
    console.log(`  ${user.email} (${user.role})`);
  }
}

seed().catch(console.error);
