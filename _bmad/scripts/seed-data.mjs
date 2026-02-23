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
  // Use local date to match the browser's "yesterday" calculation
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
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

// Deterministic seeded PRNG (linear congruential generator)
// Ensures reproducible but varied data across runs
function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

function seededRandom(seed) {
  let state = hashString(String(seed));
  return function next() {
    state = (state * 1664525 + 1013904223) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

/**
 * Generate shift_summaries records from dailySummaries array.
 * For each daily record, creates 3 shift records (morning, afternoon, night).
 *
 * Ensures:
 * - Sum of shift units_produced exactly matches daily actual_output
 * - Weighted-average shift OEE approximately matches daily oee_percentage
 * - Realistic variance: afternoon occasionally lower, night more downtime
 * - Deterministic output via seeded PRNG
 */
function generateShiftSummaries(dailySummaries) {
  const shifts = ['morning', 'afternoon', 'night'];
  const shiftSummaries = [];

  for (const daily of dailySummaries) {
    const rng = seededRandom(`${daily.asset_id}-${daily.report_date}`);

    // Base allocation percentages for units_produced
    const baseAllocations = [0.37, 0.33, 0.30]; // morning, afternoon, night

    // Apply variance: ±5-15% of base allocation
    const variance = baseAllocations.map((base) => {
      const variancePct = 0.05 + rng() * 0.10; // 5-15% variance
      const direction = rng() > 0.5 ? 1 : -1;
      return base * (1 + direction * variancePct);
    });

    // Normalize so allocations sum to 1.0
    const totalAlloc = variance.reduce((sum, v) => sum + v, 0);
    const normalizedAlloc = variance.map(v => v / totalAlloc);

    // Distribute units_produced — ensure exact sum match
    const totalUnits = daily.actual_output || 0;
    const shiftUnits = normalizedAlloc.map(alloc => Math.round(alloc * totalUnits));
    // Adjust last shift to ensure exact sum
    const unitsDiff = totalUnits - shiftUnits.reduce((sum, u) => sum + u, 0);
    shiftUnits[2] += unitsDiff;

    // Distribute downtime_minutes — weight toward night and lower-performing shifts
    const totalDowntime = daily.downtime_minutes || 0;
    const downtimeWeights = [0.25, 0.30, 0.45]; // night gets more downtime
    // Apply some variance to downtime distribution
    const downtimeVariance = downtimeWeights.map((w) => {
      return w * (0.85 + rng() * 0.30);
    });
    const totalDtWeight = downtimeVariance.reduce((sum, w) => sum + w, 0);
    const shiftDowntime = downtimeVariance.map(w => Math.round((w / totalDtWeight) * totalDowntime));
    // Adjust last shift to ensure exact sum
    const dtDiff = totalDowntime - shiftDowntime.reduce((sum, d) => sum + d, 0);
    shiftDowntime[2] += dtDiff;

    // Generate OEE and sub-components per shift
    const dailyOee = daily.oee_percentage || 80;

    for (let i = 0; i < 3; i++) {
      const shiftName = shifts[i];

      // Base shift OEE varies around daily OEE
      let shiftOeeOffset;
      if (shiftName === 'morning') {
        // Morning tends to be slightly above daily average
        shiftOeeOffset = 1 + rng() * 4; // +1 to +5
      } else if (shiftName === 'afternoon') {
        // Afternoon: 30% chance of distinctly lower performance
        const isLowPerformance = rng() < 0.30;
        if (isLowPerformance) {
          shiftOeeOffset = -(5 + rng() * 10); // -5 to -15
        } else {
          shiftOeeOffset = -2 + rng() * 4; // -2 to +2
        }
      } else {
        // Night: slightly lower on average
        shiftOeeOffset = -(1 + rng() * 5); // -1 to -6
      }

      let shiftOee = Math.max(20, Math.min(100, dailyOee + shiftOeeOffset));
      shiftOee = Math.round(shiftOee * 100) / 100;

      // Generate OEE sub-components such that availability * performance * quality / 10000 ≈ shiftOee
      // Availability: 85-98% range
      const availability = Math.round((85 + rng() * 13) * 100) / 100;
      // Quality: 95-100% range
      const quality = Math.round((95 + rng() * 5) * 100) / 100;
      // Back-calculate performance from target OEE
      let performance = (shiftOee * 10000) / (availability * quality);
      performance = Math.max(50, Math.min(100, performance));
      performance = Math.round(performance * 100) / 100;

      // Recalculate actual OEE from components (may differ slightly due to clamping)
      const actualOee = Math.round((availability * performance * quality) / 10000 * 100) / 100;

      shiftSummaries.push({
        asset_id: daily.asset_id,
        date: daily.report_date,
        shift: shiftName,
        oee: actualOee,
        availability,
        performance,
        quality,
        downtime_minutes: shiftDowntime[i],
        units_produced: Math.max(0, shiftUnits[i]),
      });
    }
  }

  return shiftSummaries;
}

async function seed() {
  console.log('🌱 Starting seed...\n');

  // 0. Clear existing data that needs to be refreshed
  console.log('🧹 Clearing existing data...');
  await supabase.from('production_actuals').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('production_schedule').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('products').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('safety_events').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('live_snapshots').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('shift_targets').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('downtime_events').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('shift_summaries').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  await supabase.from('daily_summaries').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  console.log('  ✓ Cleared production_actuals, production_schedule, products, safety_events, live_snapshots, shift_targets, downtime_events, shift_summaries, and daily_summaries');

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
      oee_percentage: 83.50,
      actual_output: 1628,
      target_output: 1950,
      downtime_minutes: 62,
      waste_count: 38,
      financial_loss_dollars: 180.83,
      downtime_reasons: { "Mechanical Failure": 35, "Material Shortage": 17, "Operator Break": 10 },
      smart_summary_text: 'Grinder 5 still struggling. Burr assembly vibration worsening, material shortages adding to downtime.'
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
      oee_percentage: 81.20,
      actual_output: 1583,
      target_output: 1950,
      downtime_minutes: 68,
      waste_count: 42,
      financial_loss_dollars: 198.33,
      downtime_reasons: { "Mechanical Failure": 40, "Changeover": 18, "Operator Break": 10 },
      smart_summary_text: 'Grinder 5 mechanical issues continuing. Burr housing inspection ordered.'
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
      actual_output: 1960,
      target_output: 1950,
      downtime_minutes: 0,
      waste_count: 15,
      financial_loss_dollars: 0,
      downtime_reasons: {},
      smart_summary_text: 'Perfect uptime day! Grinder 2 running flawlessly on French press coarse grind. Exceeded daily target.'
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
      actual_output: 145,
      target_output: 143,
      downtime_minutes: 10,
      waste_count: 1,
      financial_loss_dollars: 41.67,
      downtime_reasons: { "Changeover": 10 },
      smart_summary_text: 'Best performing roaster yesterday. Dark roast blend running flawlessly. Exceeded daily target.'
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

    // ============ FILLER LINE B - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(1),
      oee_percentage: 89.20,
      actual_output: 4650,
      target_output: 4600,
      downtime_minutes: 42,
      waste_count: 65,
      financial_loss_dollars: 87.50,
      downtime_reasons: { "Changeover": 25, "Cleanup": 17 },
      smart_summary_text: 'Outstanding day on 2lb bag line. Exceeded daily target. Weight variance within spec.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(2),
      oee_percentage: 91.80,
      actual_output: 4223,
      target_output: 4600,
      downtime_minutes: 30,
      waste_count: 50,
      financial_loss_dollars: 62.50,
      downtime_reasons: { "Changeover": 20, "Cleanup": 10 },
      smart_summary_text: 'Steady filling. Degassing valve placement accuracy improved.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(3),
      oee_percentage: 94.30,
      actual_output: 4338,
      target_output: 4600,
      downtime_minutes: 18,
      waste_count: 35,
      financial_loss_dollars: 37.50,
      downtime_reasons: { "Changeover": 18 },
      smart_summary_text: 'Outstanding day. Bag sealing quality excellent throughout.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(4),
      oee_percentage: 87.50,
      actual_output: 4025,
      target_output: 4600,
      downtime_minutes: 48,
      waste_count: 72,
      financial_loss_dollars: 100.00,
      downtime_reasons: { "Film Tension": 30, "Changeover": 18 },
      smart_summary_text: 'Film tension issues caused periodic stops.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(5),
      oee_percentage: 90.60,
      actual_output: 4168,
      target_output: 4600,
      downtime_minutes: 35,
      waste_count: 55,
      financial_loss_dollars: 72.92,
      downtime_reasons: { "Changeover": 22, "Cleanup": 13 },
      smart_summary_text: 'Consistent filling with minor adjustments.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(6),
      oee_percentage: 93.10,
      actual_output: 4283,
      target_output: 4600,
      downtime_minutes: 22,
      waste_count: 40,
      financial_loss_dollars: 45.83,
      downtime_reasons: { "Cleanup": 22 },
      smart_summary_text: 'Excellent bag weight consistency.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(7),
      oee_percentage: 88.90,
      actual_output: 4089,
      target_output: 4600,
      downtime_minutes: 40,
      waste_count: 60,
      financial_loss_dollars: 83.33,
      downtime_reasons: { "Changeover": 25, "Operator Break": 15 },
      smart_summary_text: 'Good start to the week on 1lb bag line.'
    },

    // ============ FILLER LINE C - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(1),
      oee_percentage: 80.00,
      actual_output: 3200,
      target_output: 4000,
      downtime_minutes: 62,
      waste_count: 75,
      financial_loss_dollars: 129.17,
      downtime_reasons: { "Bag Feed Issue": 40, "Changeover": 22 },
      smart_summary_text: 'Filler C had bag feed issues on specialty blend line. Throughput reduced.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(2),
      oee_percentage: 88.50,
      actual_output: 3540,
      target_output: 4000,
      downtime_minutes: 38,
      waste_count: 55,
      financial_loss_dollars: 79.17,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Good output with minor feed adjustments.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(3),
      oee_percentage: 93.20,
      actual_output: 3728,
      target_output: 4000,
      downtime_minutes: 20,
      waste_count: 35,
      financial_loss_dollars: 41.67,
      downtime_reasons: { "Changeover": 20 },
      smart_summary_text: 'Outstanding day. New nozzle configuration working well.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(4),
      oee_percentage: 86.80,
      actual_output: 3472,
      target_output: 4000,
      downtime_minutes: 45,
      waste_count: 62,
      financial_loss_dollars: 93.75,
      downtime_reasons: { "Bag Feed Issue": 30, "Changeover": 15 },
      smart_summary_text: 'Bag feed alignment needed adjustment mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(5),
      oee_percentage: 90.50,
      actual_output: 3620,
      target_output: 4000,
      downtime_minutes: 32,
      waste_count: 48,
      financial_loss_dollars: 66.67,
      downtime_reasons: { "Changeover": 22, "Cleanup": 10 },
      smart_summary_text: 'Steady performance on single-serve pods.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(6),
      oee_percentage: 94.00,
      actual_output: 3760,
      target_output: 4000,
      downtime_minutes: 15,
      waste_count: 30,
      financial_loss_dollars: 31.25,
      downtime_reasons: { "Cleanup": 15 },
      smart_summary_text: 'Excellent run. Minimal downtime.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(7),
      oee_percentage: 87.30,
      actual_output: 3492,
      target_output: 4000,
      downtime_minutes: 42,
      waste_count: 58,
      financial_loss_dollars: 87.50,
      downtime_reasons: { "Bag Feed Issue": 27, "Changeover": 15 },
      smart_summary_text: 'Some initial startup delays but recovered well.'
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

    // ============ ROASTER 3 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(1),
      oee_percentage: 89.00,
      actual_output: 127,
      target_output: 143,
      downtime_minutes: 35,
      waste_count: 4,
      financial_loss_dollars: 145.83,
      downtime_reasons: { "Cooling Cycle": 22, "Changeover": 13 },
      smart_summary_text: 'Roaster 3 performing well on medium roast batch. Minor cooling cycle adjustment.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(2),
      oee_percentage: 91.50,
      actual_output: 131,
      target_output: 143,
      downtime_minutes: 25,
      waste_count: 3,
      financial_loss_dollars: 104.17,
      downtime_reasons: { "Changeover": 25 },
      smart_summary_text: 'Consistent performance. Light roast Ethiopian beans processed smoothly.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(3),
      oee_percentage: 86.20,
      actual_output: 123,
      target_output: 143,
      downtime_minutes: 48,
      waste_count: 5,
      financial_loss_dollars: 200.00,
      downtime_reasons: { "Changeover": 30, "Cleanup": 18 },
      smart_summary_text: 'Extended changeover for specialty blend caused throughput reduction.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(4),
      oee_percentage: 93.80,
      actual_output: 134,
      target_output: 143,
      downtime_minutes: 18,
      waste_count: 2,
      financial_loss_dollars: 75.00,
      downtime_reasons: { "Changeover": 18 },
      smart_summary_text: 'Excellent batch consistency. Dark roast profile running optimally.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(5),
      oee_percentage: 88.10,
      actual_output: 126,
      target_output: 143,
      downtime_minutes: 40,
      waste_count: 4,
      financial_loss_dollars: 166.67,
      downtime_reasons: { "Material Issue": 25, "Changeover": 15 },
      smart_summary_text: 'Some first-crack timing variance on new bean lot.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(6),
      oee_percentage: 90.90,
      actual_output: 130,
      target_output: 143,
      downtime_minutes: 28,
      waste_count: 3,
      financial_loss_dollars: 116.67,
      downtime_reasons: { "Changeover": 18, "Cleanup": 10 },
      smart_summary_text: 'Steady roasting day. Chaff system operating normally.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(7),
      oee_percentage: 87.40,
      actual_output: 125,
      target_output: 143,
      downtime_minutes: 42,
      waste_count: 5,
      financial_loss_dollars: 175.00,
      downtime_reasons: { "Cooling System": 30, "Changeover": 12 },
      smart_summary_text: 'Minor cooling delays on larger batch sizes.'
    },

    // ============ GRINDER 4 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(1),
      oee_percentage: 87.18,
      actual_output: 1700,
      target_output: 1950,
      downtime_minutes: 50,
      waste_count: 35,
      financial_loss_dollars: 145.83,
      downtime_reasons: { "Feed Rate Issue": 32, "Changeover": 18 },
      smart_summary_text: 'Grinder 4 running at moderate pace. Feed rate adjustment needed mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(2),
      oee_percentage: 91.30,
      actual_output: 1780,
      target_output: 1950,
      downtime_minutes: 30,
      waste_count: 22,
      financial_loss_dollars: 87.50,
      downtime_reasons: { "Changeover": 20, "Cleanup": 10 },
      smart_summary_text: 'Good performance on medium grind setting.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(3),
      oee_percentage: 85.40,
      actual_output: 1665,
      target_output: 1950,
      downtime_minutes: 58,
      waste_count: 40,
      financial_loss_dollars: 169.17,
      downtime_reasons: { "Hopper Feed Issue": 38, "Changeover": 20 },
      smart_summary_text: 'Hopper feed issues caused intermittent slowdowns.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(4),
      oee_percentage: 89.70,
      actual_output: 1749,
      target_output: 1950,
      downtime_minutes: 38,
      waste_count: 28,
      financial_loss_dollars: 110.83,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Steady grinding with minor adjustments.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(5),
      oee_percentage: 93.20,
      actual_output: 1817,
      target_output: 1950,
      downtime_minutes: 22,
      waste_count: 18,
      financial_loss_dollars: 64.17,
      downtime_reasons: { "Changeover": 22 },
      smart_summary_text: 'Excellent day. Consistent particle size throughout.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(6),
      oee_percentage: 86.50,
      actual_output: 1687,
      target_output: 1950,
      downtime_minutes: 52,
      waste_count: 35,
      financial_loss_dollars: 151.67,
      downtime_reasons: { "Material Issue": 35, "Changeover": 17 },
      smart_summary_text: 'Bean moisture caused grind inconsistency.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(7),
      oee_percentage: 90.80,
      actual_output: 1771,
      target_output: 1950,
      downtime_minutes: 32,
      waste_count: 24,
      financial_loss_dollars: 93.33,
      downtime_reasons: { "Changeover": 22, "Cleanup": 10 },
      smart_summary_text: 'Solid start to the week.'
    },

    // ============ PACKAGING LINE 2 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(1),
      oee_percentage: 88.90,
      actual_output: 6300,
      target_output: 6200,
      downtime_minutes: 45,
      waste_count: 78,
      financial_loss_dollars: 71.25,
      downtime_reasons: { "Label Changeover": 30, "Jam": 15 },
      smart_summary_text: 'Excellent day on wholesale pack line. Exceeded daily target. Case sealing quality excellent.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(2),
      oee_percentage: 91.20,
      actual_output: 5654,
      target_output: 6200,
      downtime_minutes: 32,
      waste_count: 60,
      financial_loss_dollars: 50.67,
      downtime_reasons: { "Changeover": 22, "Cleanup": 10 },
      smart_summary_text: 'Consistent throughput. Shrink wrap tension optimized.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(3),
      oee_percentage: 93.50,
      actual_output: 5797,
      target_output: 6200,
      downtime_minutes: 20,
      waste_count: 45,
      financial_loss_dollars: 31.67,
      downtime_reasons: { "Changeover": 20 },
      smart_summary_text: 'Excellent run on bulk case packing.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(4),
      oee_percentage: 86.80,
      actual_output: 5382,
      target_output: 6200,
      downtime_minutes: 55,
      waste_count: 85,
      financial_loss_dollars: 87.08,
      downtime_reasons: { "Labeler Jam": 35, "Changeover": 20 },
      smart_summary_text: 'Labeler jam caused extended changeover.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(5),
      oee_percentage: 90.50,
      actual_output: 5611,
      target_output: 6200,
      downtime_minutes: 35,
      waste_count: 62,
      financial_loss_dollars: 55.42,
      downtime_reasons: { "Changeover": 25, "Cleanup": 10 },
      smart_summary_text: 'Good recovery from yesterday issues.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(6),
      oee_percentage: 94.20,
      actual_output: 5840,
      target_output: 6200,
      downtime_minutes: 15,
      waste_count: 38,
      financial_loss_dollars: 23.75,
      downtime_reasons: { "Cleanup": 15 },
      smart_summary_text: 'Outstanding day. Minimal changeovers needed.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(7),
      oee_percentage: 87.50,
      actual_output: 5425,
      target_output: 6200,
      downtime_minutes: 48,
      waste_count: 72,
      financial_loss_dollars: 76.00,
      downtime_reasons: { "Changeover": 30, "Label Issue": 18 },
      smart_summary_text: 'Moderate start to the week.'
    },

    // ============ PACKAGING LINE 3 - 7 days ============
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(1),
      oee_percentage: 87.50,
      actual_output: 4900,
      target_output: 5600,
      downtime_minutes: 55,
      waste_count: 80,
      financial_loss_dollars: 87.08,
      downtime_reasons: { "Film Feed": 35, "Changeover": 20 },
      smart_summary_text: 'Packaging Line 3 running slightly below target. Film feed alignment.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(2),
      oee_percentage: 90.20,
      actual_output: 5051,
      target_output: 5600,
      downtime_minutes: 38,
      waste_count: 62,
      financial_loss_dollars: 60.17,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Good performance. Carton sealing quality improved.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(3),
      oee_percentage: 85.80,
      actual_output: 4805,
      target_output: 5600,
      downtime_minutes: 62,
      waste_count: 95,
      financial_loss_dollars: 98.17,
      downtime_reasons: { "Label Applicator": 40, "Changeover": 22 },
      smart_summary_text: 'Label applicator needed recalibration mid-shift.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(4),
      oee_percentage: 91.40,
      actual_output: 5118,
      target_output: 5600,
      downtime_minutes: 30,
      waste_count: 50,
      financial_loss_dollars: 47.50,
      downtime_reasons: { "Changeover": 20, "Cleanup": 10 },
      smart_summary_text: 'Strong day. Case erector running smoothly.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(5),
      oee_percentage: 88.60,
      actual_output: 4962,
      target_output: 5600,
      downtime_minutes: 45,
      waste_count: 70,
      financial_loss_dollars: 71.25,
      downtime_reasons: { "Changeover": 28, "Jam": 17 },
      smart_summary_text: 'Moderate output with some changeover delays.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(6),
      oee_percentage: 92.80,
      actual_output: 5197,
      target_output: 5600,
      downtime_minutes: 22,
      waste_count: 42,
      financial_loss_dollars: 34.83,
      downtime_reasons: { "Changeover": 22 },
      smart_summary_text: 'Excellent performance on retail pack line.'
    },
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(7),
      oee_percentage: 86.40,
      actual_output: 4838,
      target_output: 5600,
      downtime_minutes: 55,
      waste_count: 78,
      financial_loss_dollars: 87.08,
      downtime_reasons: { "Case Erector": 35, "Changeover": 20 },
      smart_summary_text: 'Some case erector issues at start of shift.'
    },

    // ============ WEEK AGO (daysAgo(8)) - Required for week-over-week trend arrows (Epic 14) ============
    // These values are compared against daysAgo(1) to compute weekOverWeekChange.
    // Grinder 5: 87.1% → daysAgo(1) 82.5% = -5.3% (worsening, red arrow)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000014',
      report_date: daysAgo(8),
      oee_percentage: 87.10,
      actual_output: 1698,
      target_output: 1950,
      downtime_minutes: 52,
      waste_count: 28,
      financial_loss_dollars: 151.67,
      downtime_reasons: { "Mechanical Failure": 32, "Operator Break": 20 },
      smart_summary_text: 'Steady performance with minor mechanical hiccups.'
    },
    // Grinder 1: 86.5% → daysAgo(1) 91.2% = +5.4% (improving, green arrow)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000004',
      report_date: daysAgo(8),
      oee_percentage: 86.50,
      actual_output: 1687,
      target_output: 1950,
      downtime_minutes: 55,
      waste_count: 30,
      financial_loss_dollars: 160.42,
      downtime_reasons: { "Material Issue": 35, "Changeover": 20 },
      smart_summary_text: 'Grinder 1 with some material flow issues last week.'
    },
    // Grinder 2: 93.5% → daysAgo(1) high, good baseline
    {
      asset_id: 'a0000001-0000-0000-0000-000000000005',
      report_date: daysAgo(8),
      oee_percentage: 93.50,
      actual_output: 1823,
      target_output: 1950,
      downtime_minutes: 20,
      waste_count: 12,
      financial_loss_dollars: 58.33,
      downtime_reasons: { "Changeover": 20 },
      smart_summary_text: 'Grinder 2 strong performance last week.'
    },
    // Roaster 1: 90.5% → daysAgo(1) 87.5% = -3.3% (worsening)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000001',
      report_date: daysAgo(8),
      oee_percentage: 90.50,
      actual_output: 129,
      target_output: 143,
      downtime_minutes: 18,
      waste_count: 2,
      financial_loss_dollars: 95.83,
      downtime_reasons: { "Changeover": 12, "Cleanup": 6 },
      smart_summary_text: 'Roaster 1 running well with clean drum profile.'
    },
    // Roaster 2: 95.1% → daysAgo(1) 96.1% = +1.0% (stable, gray arrow)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000002',
      report_date: daysAgo(8),
      oee_percentage: 95.10,
      actual_output: 136,
      target_output: 143,
      downtime_minutes: 10,
      waste_count: 0,
      financial_loss_dollars: 41.67,
      downtime_reasons: { "Cleanup": 10 },
      smart_summary_text: 'Roaster 2 consistent performance.'
    },
    // Roaster 3: 90.8% → daysAgo(1) 87.18% = -3.9% (worsening)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000007',
      report_date: daysAgo(8),
      oee_percentage: 90.80,
      actual_output: 1771,
      target_output: 1950,
      downtime_minutes: 38,
      waste_count: 22,
      financial_loss_dollars: 93.33,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Roaster 3 solid run last week.'
    },
    // Filler Line A: 89.8% → daysAgo(1) 72.5% = -19.2% (strongly worsening)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000008',
      report_date: daysAgo(8),
      oee_percentage: 89.80,
      actual_output: 4131,
      target_output: 4600,
      downtime_minutes: 35,
      waste_count: 18,
      financial_loss_dollars: 79.17,
      downtime_reasons: { "Changeover": 22, "Cleanup": 13 },
      smart_summary_text: 'Filler Line A running cleanly last week.'
    },
    // Filler Line B: 88.9% → daysAgo(1) 89.2% = +0.3% (stable)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000009',
      report_date: daysAgo(8),
      oee_percentage: 88.90,
      actual_output: 4089,
      target_output: 4600,
      downtime_minutes: 38,
      waste_count: 22,
      financial_loss_dollars: 83.33,
      downtime_reasons: { "Changeover": 25, "Cleanup": 13 },
      smart_summary_text: 'Filler Line B consistent performance.'
    },
    // Filler Line C: 83.5% → daysAgo(1) 80.0% = -4.2% (worsening)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000010',
      report_date: daysAgo(8),
      oee_percentage: 83.50,
      actual_output: 3340,
      target_output: 4000,
      downtime_minutes: 55,
      waste_count: 32,
      financial_loss_dollars: 130.00,
      downtime_reasons: { "Material Shortage": 30, "Changeover": 25 },
      smart_summary_text: 'Filler Line C material issues persisting.'
    },
    // Pack Line A: 88.9% → daysAgo(1) 89.5% = +0.7% (stable)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000011',
      report_date: daysAgo(8),
      oee_percentage: 88.90,
      actual_output: 5512,
      target_output: 6200,
      downtime_minutes: 40,
      waste_count: 55,
      financial_loss_dollars: 71.25,
      downtime_reasons: { "Changeover": 25, "Label Issue": 15 },
      smart_summary_text: 'Pack Line A consistent throughout shift.'
    },
    // Pack Line B: 87.5% → daysAgo(1) 88.9% = +1.6% (stable)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000012',
      report_date: daysAgo(8),
      oee_percentage: 87.50,
      actual_output: 5425,
      target_output: 6200,
      downtime_minutes: 48,
      waste_count: 62,
      financial_loss_dollars: 76.00,
      downtime_reasons: { "Changeover": 30, "Label Issue": 18 },
      smart_summary_text: 'Pack Line B good run with standard changeovers.'
    },
    // Pack Line C: 86.4% → daysAgo(1) 87.5% = +1.3% (stable)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000013',
      report_date: daysAgo(8),
      oee_percentage: 86.40,
      actual_output: 4838,
      target_output: 5600,
      downtime_minutes: 55,
      waste_count: 78,
      financial_loss_dollars: 87.08,
      downtime_reasons: { "Case Erector": 35, "Changeover": 20 },
      smart_summary_text: 'Pack Line C modest performance last week.'
    },
    // Filler Line D (asset 6): 88.4% → daysAgo(1) 84.2% = -4.7% (worsening)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000006',
      report_date: daysAgo(8),
      oee_percentage: 88.40,
      actual_output: 1724,
      target_output: 1950,
      downtime_minutes: 42,
      waste_count: 28,
      financial_loss_dollars: 131.25,
      downtime_reasons: { "Changeover": 28, "Cleanup": 14 },
      smart_summary_text: 'Filler Line D good performance last week.'
    },
    // Roaster 4 (asset 3): 87.4% → daysAgo(1) 89.0% = +1.8% (stable)
    {
      asset_id: 'a0000001-0000-0000-0000-000000000003',
      report_date: daysAgo(8),
      oee_percentage: 87.40,
      actual_output: 125,
      target_output: 143,
      downtime_minutes: 22,
      waste_count: 3,
      financial_loss_dollars: 175.00,
      downtime_reasons: { "Changeover": 15, "Cleanup": 7 },
      smart_summary_text: 'Roaster 4 steady performance last week.'
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

  // 3b. Shift Summaries (Story 17.3: Per-shift performance breakdowns)
  console.log('📊 Inserting shift summaries...');
  const shiftSummaries = generateShiftSummaries(dailySummaries);
  const { error: shiftErr } = await supabase.from('shift_summaries').upsert(shiftSummaries, { onConflict: 'asset_id,date,shift' });
  if (shiftErr) console.error('  Shift summaries error:', shiftErr.message);
  else console.log(`  ✓ Shift summaries inserted (${shiftSummaries.length} records for ${dailySummaries.length} daily records)`);

  // 3a. Downtime Events (Story 14.1: Individual downtime event records for Pareto analysis)
  console.log('🔧 Inserting downtime events...');

  // Reason code mapping: freeform daily_summaries keys → standard reason codes
  const REASON_CODE_MAP = {
    'Mechanical Failure': { reason_code: 'Mechanical', is_planned: false },
    'Changeover': { reason_code: 'Changeover', is_planned: true },
    'Material Shortage': { reason_code: 'Material Shortage', is_planned: false },
    'Material Issue': { reason_code: 'Material Shortage', is_planned: false },
    'Quality Hold': { reason_code: 'Quality Hold', is_planned: false },
    'QA Hold': { reason_code: 'Quality Hold', is_planned: false },
    'Operator Unavailable': { reason_code: 'Operator Unavailable', is_planned: false },
    'Operator Break': { reason_code: 'Operator Unavailable', is_planned: false },
    'Planned Maintenance': { reason_code: 'Planned Maintenance', is_planned: true },
    'Cleanup': { reason_code: 'Planned Maintenance', is_planned: true },
    'Safety Stop': { reason_code: 'Mechanical', is_planned: false },
    'Inspection': { reason_code: 'Mechanical', is_planned: false },
    'Cooling System': { reason_code: 'Mechanical', is_planned: false },
    'Sensor Malfunction': { reason_code: 'Mechanical', is_planned: false },
    'Burner Issue': { reason_code: 'Mechanical', is_planned: false },
    'Valve Issue': { reason_code: 'Mechanical', is_planned: false },
    'Jam': { reason_code: 'Mechanical', is_planned: false },
    'Pressure Issue': { reason_code: 'Mechanical', is_planned: false },
    'Label Changeover': { reason_code: 'Mechanical', is_planned: false },
    'Startup Delay': { reason_code: 'Mechanical', is_planned: false },
    'Case Erector Jam': { reason_code: 'Mechanical', is_planned: false },
    'Carton Issue': { reason_code: 'Mechanical', is_planned: false },
    'Chaff Collection': { reason_code: 'Planned Maintenance', is_planned: true },
    'Calibration': { reason_code: 'Planned Maintenance', is_planned: true },
    'Cooling Cycle': { reason_code: 'Mechanical', is_planned: false },
    'Feed Rate Issue': { reason_code: 'Mechanical', is_planned: false },
    'Hopper Feed Issue': { reason_code: 'Mechanical', is_planned: false },
    'Film Tension': { reason_code: 'Mechanical', is_planned: false },
    'Bag Feed Issue': { reason_code: 'Mechanical', is_planned: false },
    'Film Feed': { reason_code: 'Mechanical', is_planned: false },
    'Label Applicator': { reason_code: 'Mechanical', is_planned: false },
    'Labeler Jam': { reason_code: 'Mechanical', is_planned: false },
    'Case Erector': { reason_code: 'Mechanical', is_planned: false },
    'Label Issue': { reason_code: 'Mechanical', is_planned: false },
  };

  // Reason detail templates for realistic descriptions
  const REASON_DETAILS = {
    'Mechanical': [
      'Bearing noise detected, required adjustment.',
      'Vibration exceeded threshold, auto-stop triggered.',
      'Component wear detected during inspection.',
      'Alignment check required mid-shift.',
      'Assembly vibration causing operational issues.',
      'Intermittent sensor malfunction addressed.',
      'Jam cleared from feed mechanism.',
      'Pressure regulator replacement needed.',
      'Motor current spike investigated.',
      'Belt tension adjustment performed.',
    ],
    'Changeover': [
      'Switched to new product profile.',
      'SKU changeover between batches.',
      'Grind size adjustment for new blend.',
      'Label format change for retail line.',
      'Packaging format switch completed.',
      'Product line changeover performed.',
      'Configuration change for new batch.',
      'Tooling swap for different product.',
    ],
    'Material Shortage': [
      'Hopper ran empty waiting on upstream supply.',
      'Raw material delivery delayed.',
      'Input material quality variance caused pause.',
      'Upstream feed interrupted supply.',
      'Bean moisture variance required adjustment.',
      'Material feed interruption from supplier.',
    ],
    'Quality Hold': [
      'Product sample failed QA check.',
      'Line held for quality inspection.',
      'Product quarantined pending review.',
      'Weight variance exceeded specification.',
      'Quality parameter out of tolerance.',
    ],
    'Operator Unavailable': [
      'Scheduled operator break.',
      'Shift handover pause.',
      'Operator reassigned temporarily.',
      'Break during shift change.',
      'Brief pause for crew rotation.',
    ],
    'Planned Maintenance': [
      'Routine cleaning cycle completed.',
      'Scheduled maintenance window.',
      'Preventive maintenance performed.',
      'Equipment calibration completed.',
      'System cleanup between batches.',
      'Chaff collection system cleaned.',
    ],
  };

  // Shift assignment logic: distribute events across shifts
  const SHIFTS = ['morning', 'afternoon', 'night'];
  let detailCounters = {};

  const getReasonDetail = (reasonCode) => {
    const details = REASON_DETAILS[reasonCode];
    if (!detailCounters[reasonCode]) detailCounters[reasonCode] = 0;
    const detail = details[detailCounters[reasonCode] % details.length];
    detailCounters[reasonCode]++;
    return detail;
  };

  const downtimeEvents = [];

  for (const summary of dailySummaries) {
    // Skip if no downtime or empty reasons
    if (!summary.downtime_minutes || summary.downtime_minutes === 0) continue;
    if (!summary.downtime_reasons || Object.keys(summary.downtime_reasons).length === 0) continue;

    const reasons = Object.entries(summary.downtime_reasons);
    let eventIdx = 0;

    // Distribute events across shifts, splitting large-duration events to increase event count
    reasons.forEach((entry) => {
      const [rawReason, totalMinutes] = entry;
      const mapping = REASON_CODE_MAP[rawReason];
      if (!mapping) {
        console.warn(`  ⚠ Unknown reason key: "${rawReason}" — skipping`);
        return;
      }

      // Split events to increase granularity:
      // - Mechanical events > 12 min split into 2 (reflects multiple incident types)
      // - Changeover events never split (single changeover operations)
      // - Other events > 25 min split into 2
      const isRoaster = summary.asset_id.endsWith('000000000001') || summary.asset_id.endsWith('000000000002') || summary.asset_id.endsWith('000000000003');
      let splitThreshold;
      if (mapping.reason_code === 'Mechanical') {
        splitThreshold = 10;
      } else if (mapping.reason_code === 'Changeover') {
        splitThreshold = 999; // Never split changeover events
      } else {
        splitThreshold = 25;
      }
      const eventParts = totalMinutes > splitThreshold ? [Math.ceil(totalMinutes / 2), Math.floor(totalMinutes / 2)] : [totalMinutes];

      eventParts.forEach((minutes, partIdx) => {
        // Shift distribution: cycle through morning, afternoon, night
        // Split parts get different shifts to avoid duplicates
        let shift;
        if (eventIdx === 0 && partIdx === 0) {
          shift = 'morning';
        } else if (eventIdx === 0 && partIdx === 1) {
          shift = 'afternoon';
        } else if (eventIdx === 1 && partIdx === 0) {
          shift = 'afternoon';
        } else {
          shift = isRoaster ? 'night' : SHIFTS[(eventIdx + partIdx) % 3];
        }
        if (partIdx === 0) eventIdx++;

        downtimeEvents.push({
          asset_id: summary.asset_id,
          event_date: summary.report_date,
          shift: shift,
          reason_code: mapping.reason_code,
          reason_detail: getReasonDetail(mapping.reason_code),
          duration_minutes: minutes,
          is_planned: mapping.is_planned,
          source_system: 'manual',
        });
      });
    });
  }

  const { error: downtimeErr } = await supabase.from('downtime_events').insert(downtimeEvents);
  if (downtimeErr) console.error('  Downtime events error:', downtimeErr.message);
  else console.log(`  ✓ ${downtimeEvents.length} downtime events inserted`);

  // 3b. Shift Targets (Story 11.3: Production targets per shift for all 14 assets)
  console.log('🎯 Inserting shift targets...');
  const shiftTargets = [
    // Roasters: each sums to 143 (morning=50, afternoon=48, night=45)
    { asset_id: 'a0000001-0000-0000-0000-000000000001', target_output: 50, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000001', target_output: 48, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000001', target_output: 45, shift: 'night', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', target_output: 50, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', target_output: 48, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000002', target_output: 45, shift: 'night', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000003', target_output: 50, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000003', target_output: 48, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000003', target_output: 45, shift: 'night', effective_date: '2026-01-01' },
    // Grinders: each sums to 1950
    { asset_id: 'a0000001-0000-0000-0000-000000000004', target_output: 1000, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000004', target_output: 950, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000005', target_output: 1000, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000005', target_output: 950, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000006', target_output: 900, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000006', target_output: 1050, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000007', target_output: 850, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000007', target_output: 1100, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000014', target_output: 1000, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000014', target_output: 950, shift: 'afternoon', effective_date: '2026-01-01' },
    // Fillers: A/B sum to 4600, C sums to 4000
    { asset_id: 'a0000001-0000-0000-0000-000000000008', target_output: 2400, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000008', target_output: 2200, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000009', target_output: 2400, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000009', target_output: 2200, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000010', target_output: 2000, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000010', target_output: 2000, shift: 'afternoon', effective_date: '2026-01-01' },
    // Packaging: 1/2 sum to 6200, 3 sums to 5600
    { asset_id: 'a0000001-0000-0000-0000-000000000011', target_output: 3200, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000011', target_output: 3000, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', target_output: 3200, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000012', target_output: 3000, shift: 'afternoon', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000013', target_output: 2800, shift: 'morning', effective_date: '2026-01-01' },
    { asset_id: 'a0000001-0000-0000-0000-000000000013', target_output: 2800, shift: 'afternoon', effective_date: '2026-01-01' },
  ];

  const { error: shiftTargetsErr } = await supabase.from('shift_targets').insert(shiftTargets);
  if (shiftTargetsErr) console.error('  Shift targets error:', shiftTargetsErr.message);
  else console.log('  ✓ Shift targets inserted for all 14 assets');

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

  // 5.5. Products, Schedule & Actuals (Epic 12)
  console.log('📦 Inserting products...');
  const products = [
    { id: 'b0000001-0000-0000-0000-000000000001', name: 'Colombian Single Origin', sku: 'RST-COL-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000002', name: 'Brazilian Santos', sku: 'RST-BRZ-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000003', name: 'Ethiopian Yirgacheffe', sku: 'RST-ETH-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000004', name: 'House Blend', sku: 'RST-HBL-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000005', name: 'Dark Roast Blend', sku: 'RST-DRK-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000006', name: 'Espresso Grind', sku: 'GRN-ESP-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000007', name: 'Medium Grind', sku: 'GRN-MED-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000008', name: 'Coarse Grind', sku: 'GRN-CRS-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
    { id: 'b0000001-0000-0000-0000-000000000009', name: 'K-Cup', sku: 'FIL-KCP-001', product_family: 'Filling', unit_of_measure: 'units' },
    { id: 'b0000001-0000-0000-0000-000000000010', name: '12oz Bag', sku: 'FIL-12B-001', product_family: 'Filling', unit_of_measure: 'units' },
    { id: 'b0000001-0000-0000-0000-000000000011', name: '5lb Bag', sku: 'FIL-5LB-001', product_family: 'Filling', unit_of_measure: 'units' },
  ];

  const { error: productsErr } = await supabase.from('products').upsert(products, { onConflict: 'id' });
  if (productsErr) console.error('  Products error:', productsErr.message);
  else console.log('  ✓ 11 products inserted');

  // 5.6. Production Schedule (Epic 12)
  // Product-to-asset mapping and daily_summaries actual_output reference:
  //   Roaster 1 (001): d1=125, d2=135, d3=108, d4=131, d5=125, d6=133, d7=126  target=143
  //   Roaster 2 (002): d1=145, d2=122, d3=133, d4=129, d5=135, d6=128, d7=130  target=143
  //   Roaster 3 (003): d1=127, d2=131, d3=123, d4=134, d5=126, d6=130, d7=125  target=143
  //   Grinder 1 (004): d1=1780, d2=1725, d3=1848, d4=1409, d5=1817, d6=1756, d7=1687  target=1950
  //   Grinder 2 (005): d1=1960, d2=1862, d3=1760, d4=1802, d5=1835, d6=1790, d7=1823  target=1950
  //   Grinder 3 (006): d1=1642, d2=1749, d3=1702, d4=1784, d5=1693, d6=1759, d7=1724  target=1950
  //   Grinder 4 (007): d1=1700, d2=1780, d3=1665, d4=1749, d5=1817, d6=1687, d7=1771  target=1950
  //   Grinder 5 (014): d1=1608, d2=1722, d3=1498, d4=1778, d5=1669, d6=1743, d7=1698  target=1950
  //   Filler A (008):  d1=3335, d2=4246, d3=3616, d4=4374, d5=4066, d6=4195, d7=4131  target=4600
  //   Filler B (009):  d1=4650, d2=4223, d3=4338, d4=4025, d5=4168, d6=4283, d7=4089  target=4600
  //   Filler C (010):  d1=3200, d2=3540, d3=3728, d4=3472, d5=3620, d6=3760, d7=3492  target=4000
  console.log('📅 Inserting production schedule...');

  // Asset ID shortcuts
  const R1 = 'a0000001-0000-0000-0000-000000000001';
  const R2 = 'a0000001-0000-0000-0000-000000000002';
  const R3 = 'a0000001-0000-0000-0000-000000000003';
  const G1 = 'a0000001-0000-0000-0000-000000000004';
  const G2 = 'a0000001-0000-0000-0000-000000000005';
  const G3 = 'a0000001-0000-0000-0000-000000000006';
  const G4 = 'a0000001-0000-0000-0000-000000000007';
  const G5 = 'a0000001-0000-0000-0000-000000000014';
  const FA = 'a0000001-0000-0000-0000-000000000008';
  const FB = 'a0000001-0000-0000-0000-000000000009';
  const FC = 'a0000001-0000-0000-0000-000000000010';

  // Product ID shortcuts
  const COL = 'b0000001-0000-0000-0000-000000000001'; // Colombian Single Origin
  const BRZ = 'b0000001-0000-0000-0000-000000000002'; // Brazilian Santos
  const ETH = 'b0000001-0000-0000-0000-000000000003'; // Ethiopian Yirgacheffe
  const HBL = 'b0000001-0000-0000-0000-000000000004'; // House Blend
  const DRK = 'b0000001-0000-0000-0000-000000000005'; // Dark Roast Blend
  const ESP = 'b0000001-0000-0000-0000-000000000006'; // Espresso Grind
  const MED = 'b0000001-0000-0000-0000-000000000007'; // Medium Grind
  const CRS = 'b0000001-0000-0000-0000-000000000008'; // Coarse Grind
  const KCP = 'b0000001-0000-0000-0000-000000000009'; // K-Cup
  const B12 = 'b0000001-0000-0000-0000-000000000010'; // 12oz Bag
  const B5L = 'b0000001-0000-0000-0000-000000000011'; // 5lb Bag

  // Helper: generate schedule UUID — c{assetIdx 2 digit}{day 1 digit}{shift: 1=Day 2=Night}
  const schedId = (assetIdx, day, shift) =>
    `c0000001-0000-0000-0000-${String(assetIdx).padStart(3, '0')}${day}${shift === 'Day' ? '1' : '2'}0000000`;

  // Helper: generate actuals UUID — d{assetIdx 2 digit}{day 1 digit}{shift: 1=Day 2=Night}
  const actualId = (assetIdx, day, shift) =>
    `d0000001-0000-0000-0000-${String(assetIdx).padStart(3, '0')}${day}${shift === 'Day' ? '1' : '2'}0000000`;

  // Weekly product rotation per asset (indexed by day 1-7)
  // Roaster 1: Colombian Mon-Wed, Brazilian Thu-Fri, Colombian Sat-Sun
  // Roaster 2: Dark Roast Mon-Thu, House Blend Fri-Sun
  // Roaster 3: Ethiopian Mon-Wed, House Blend Thu-Fri, Ethiopian Sat-Sun
  // Grinder 1: Espresso Grind all week
  // Grinder 2: Coarse Grind all week
  // Grinder 3: Medium Grind Mon-Wed, Espresso Grind Thu-Fri, Medium Grind Sat-Sun
  // Grinder 4: Medium Grind all week
  // Grinder 5: Espresso Grind Mon-Wed, Medium Grind Thu-Fri, Espresso Grind Sat-Sun
  // Filler A: K-Cup Mon-Wed, 12oz Bag Thu-Fri, K-Cup Sat-Sun
  // Filler B: 12oz Bag all week
  // Filler C: 5lb Bag Mon-Wed, K-Cup Thu-Fri, 5lb Bag Sat-Sun

  // Asset config: [assetId, assetIdx, target, productFn]
  // target = daily scheduled total, split ~55%/45% Day/Night
  const assetConfigs = [
    { id: R1, idx: 1,  target: 143, productFn: (d) => [1,2,3].includes(d) ? COL : [4,5].includes(d) ? BRZ : COL, prefix: 'RST1' },
    { id: R2, idx: 2,  target: 143, productFn: (d) => [1,2,3,4].includes(d) ? DRK : HBL, prefix: 'RST2' },
    { id: R3, idx: 3,  target: 143, productFn: (d) => [1,2,3].includes(d) ? ETH : [4,5].includes(d) ? HBL : ETH, prefix: 'RST3' },
    { id: G1, idx: 4,  target: 1950, productFn: () => ESP, prefix: 'GRN1' },
    { id: G2, idx: 5,  target: 1950, productFn: () => CRS, prefix: 'GRN2' },
    { id: G3, idx: 6,  target: 1950, productFn: (d) => [1,2,3].includes(d) ? MED : [4,5].includes(d) ? ESP : MED, prefix: 'GRN3' },
    { id: G4, idx: 7,  target: 1950, productFn: () => MED, prefix: 'GRN4' },
    { id: G5, idx: 14, target: 1950, productFn: (d) => [1,2,3].includes(d) ? ESP : [4,5].includes(d) ? MED : ESP, prefix: 'GRN5' },
    { id: FA, idx: 8,  target: 4600, productFn: (d) => [1,2,3].includes(d) ? KCP : [4,5].includes(d) ? B12 : KCP, prefix: 'FILA' },
    { id: FB, idx: 9,  target: 4600, productFn: () => B12, prefix: 'FILB' },
    { id: FC, idx: 10, target: 4000, productFn: (d) => [1,2,3].includes(d) ? B5L : [4,5].includes(d) ? KCP : B5L, prefix: 'FILC' },
  ];

  const productionSchedule = [];
  for (const asset of assetConfigs) {
    for (let day = 1; day <= 7; day++) {
      const dayQty = Math.round(asset.target * 0.55);
      const nightQty = asset.target - dayQty;
      const product = asset.productFn(day);
      const dateStr = daysAgo(day);
      productionSchedule.push({
        id: schedId(asset.idx, day, 'Day'),
        asset_id: asset.id,
        product_id: product,
        scheduled_quantity: dayQty,
        scheduled_date: dateStr,
        shift: 'Day',
        production_order_ref: `PO-${asset.prefix}-${dateStr}-D`,
      });
      productionSchedule.push({
        id: schedId(asset.idx, day, 'Night'),
        asset_id: asset.id,
        product_id: product,
        scheduled_quantity: nightQty,
        scheduled_date: dateStr,
        shift: 'Night',
        production_order_ref: `PO-${asset.prefix}-${dateStr}-N`,
      });
    }
  }

  const { error: scheduleErr } = await supabase.from('production_schedule').upsert(productionSchedule, { onConflict: 'id' });
  if (scheduleErr) console.error('  Production schedule error:', scheduleErr.message);
  else console.log(`  ✓ ${productionSchedule.length} production schedule entries inserted`);

  // 5.7. Production Actuals with Variance Patterns (Epic 12)
  // Actual_output from daily_summaries per asset/day (must match sums)
  console.log('📊 Inserting production actuals...');
  const dailyActuals = {
    // asset_id -> { day -> actual_output }
    [R1]: { 1: 125, 2: 135, 3: 108, 4: 131, 5: 125, 6: 133, 7: 126 },
    [R2]: { 1: 145, 2: 122, 3: 133, 4: 129, 5: 135, 6: 128, 7: 130 },
    [R3]: { 1: 127, 2: 131, 3: 123, 4: 134, 5: 126, 6: 130, 7: 125 },
    [G1]: { 1: 1780, 2: 1725, 3: 1848, 4: 1409, 5: 1817, 6: 1756, 7: 1687 },
    [G2]: { 1: 1960, 2: 1862, 3: 1760, 4: 1802, 5: 1835, 6: 1790, 7: 1823 },
    [G3]: { 1: 1642, 2: 1749, 3: 1702, 4: 1784, 5: 1693, 6: 1759, 7: 1724 },
    [G4]: { 1: 1700, 2: 1780, 3: 1665, 4: 1749, 5: 1817, 6: 1687, 7: 1771 },
    [G5]: { 1: 1608, 2: 1722, 3: 1498, 4: 1778, 5: 1669, 6: 1743, 7: 1698 },
    [FA]: { 1: 3335, 2: 4246, 3: 3616, 4: 4374, 5: 4066, 6: 4195, 7: 4131 },
    [FB]: { 1: 4650, 2: 4223, 3: 4338, 4: 4025, 5: 4168, 6: 4283, 7: 4089 },
    [FC]: { 1: 3200, 2: 3540, 3: 3728, 4: 3472, 5: 3620, 6: 3760, 7: 3492 },
  };

  // Swap product lookup within same family
  const roastingProducts = [COL, BRZ, ETH, HBL, DRK];
  const grindingProducts = [ESP, MED, CRS];
  const fillingProducts = [KCP, B12, B5L];
  const swapProduct = (productId) => {
    let family;
    if (roastingProducts.includes(productId)) family = roastingProducts;
    else if (grindingProducts.includes(productId)) family = grindingProducts;
    else family = fillingProducts;
    const others = family.filter(p => p !== productId);
    return others[0]; // deterministic: pick first alternative
  };

  // Variance scenario definitions — keyed by "assetId:day:shift"
  // Types: 'on_schedule' (default), 'swap', 'under', 'over'
  const varianceOverrides = {
    // AC3: daysAgo(1) Roaster 1 swap — Brazilian instead of Colombian
    [`${R1}:1:Day`]: 'swap',
    [`${R1}:1:Night`]: 'swap',
    // AC3: daysAgo(1) Grinder 5 underproduction (total=1608)
    [`${G5}:1:Day`]: 'under',
    [`${G5}:1:Night`]: 'under',
    // AC3: daysAgo(2) Filler A exceeds K-Cup target
    [`${FA}:2:Day`]: 'over',
    [`${FA}:2:Night`]: 'over',
    // AC3: daysAgo(3) multiple grinder swaps
    [`${G1}:3:Day`]: 'swap',
    [`${G1}:3:Night`]: 'swap',
    [`${G3}:3:Day`]: 'swap',
    [`${G3}:3:Night`]: 'swap',
    [`${G5}:3:Day`]: 'swap',
    [`${G5}:3:Night`]: 'swap',
    // AC3: shift-level variance — Grinder 4 daysAgo(2): Day on-target, Night underproduced
    [`${G4}:2:Night`]: 'under',
    // More underproduction to hit ~25% overall
    [`${R3}:3:Day`]: 'under',
    [`${R3}:3:Night`]: 'under',
    [`${G4}:3:Day`]: 'under',
    [`${G4}:3:Night`]: 'under',
    [`${FC}:1:Day`]: 'under',
    [`${FC}:1:Night`]: 'under',
    [`${FA}:1:Day`]: 'under',
    [`${FA}:1:Night`]: 'under',
    [`${G3}:1:Day`]: 'under',
    [`${G3}:1:Night`]: 'under',
    [`${R2}:2:Day`]: 'under',
    [`${R2}:2:Night`]: 'under',
    [`${G1}:4:Day`]: 'under',
    [`${G1}:4:Night`]: 'under',
    [`${FB}:4:Day`]: 'under',
    [`${FB}:4:Night`]: 'under',
    [`${FC}:4:Day`]: 'under',
    [`${FC}:4:Night`]: 'under',
    // More swaps to hit ~15%
    [`${R2}:5:Day`]: 'swap',
    [`${R2}:5:Night`]: 'swap',
    [`${R3}:6:Day`]: 'swap',
    [`${R3}:6:Night`]: 'swap',
    [`${G2}:7:Day`]: 'swap',
    [`${G2}:7:Night`]: 'swap',
    [`${FB}:6:Day`]: 'swap',
    [`${FB}:6:Night`]: 'swap',
    [`${FC}:5:Day`]: 'swap',
    [`${FC}:5:Night`]: 'swap',
    // Additional underproduction for ~25% coverage
    [`${R1}:5:Day`]: 'under',
    [`${R1}:5:Night`]: 'under',
    [`${R3}:7:Day`]: 'under',
    [`${R3}:7:Night`]: 'under',
    [`${G2}:4:Day`]: 'under',
    [`${G2}:4:Night`]: 'under',
    [`${G3}:5:Day`]: 'under',
    [`${G3}:5:Night`]: 'under',
    [`${G5}:5:Day`]: 'under',
    [`${G5}:5:Night`]: 'under',
    [`${FA}:3:Day`]: 'under',
    [`${FA}:3:Night`]: 'under',
    [`${FB}:7:Day`]: 'under',
    [`${FB}:7:Night`]: 'under',
    [`${R1}:7:Day`]: 'under',
    [`${R1}:7:Night`]: 'under',
    [`${G4}:6:Day`]: 'under',
    [`${G4}:6:Night`]: 'under',
  };

  const productionActuals = [];
  for (const asset of assetConfigs) {
    for (let day = 1; day <= 7; day++) {
      const totalActual = dailyActuals[asset.id][day];
      const scheduledProduct = asset.productFn(day);

      // Split total actual between Day (55%) and Night (45%) by default
      let dayActual = Math.round(totalActual * 0.55);
      let nightActual = totalActual - dayActual;

      const dayKey = `${asset.id}:${day}:Day`;
      const nightKey = `${asset.id}:${day}:Night`;
      const dayVariance = varianceOverrides[dayKey] || 'on_schedule';
      const nightVariance = varianceOverrides[nightKey] || 'on_schedule';

      // Shift-level variance: Grinder 4 daysAgo(2) — Day on-target, Night underproduced
      if (asset.id === G4 && day === 2) {
        // Total actual = 1780, Day gets ~1020 (on-target), Night gets 760 (under)
        dayActual = 1020;
        nightActual = 760;
      }

      const dayProduct = dayVariance === 'swap' ? swapProduct(scheduledProduct) : scheduledProduct;
      const nightProduct = nightVariance === 'swap' ? swapProduct(scheduledProduct) : scheduledProduct;

      productionActuals.push({
        id: actualId(asset.idx, day, 'Day'),
        asset_id: asset.id,
        product_id: dayProduct,
        actual_quantity: dayActual,
        production_date: daysAgo(day),
        shift: 'Day',
      });
      productionActuals.push({
        id: actualId(asset.idx, day, 'Night'),
        asset_id: asset.id,
        product_id: nightProduct,
        actual_quantity: nightActual,
        production_date: daysAgo(day),
        shift: 'Night',
      });
    }
  }

  const { error: actualsErr } = await supabase.from('production_actuals').upsert(productionActuals, { onConflict: 'id' });
  if (actualsErr) console.error('  Production actuals error:', actualsErr.message);
  else console.log(`  ✓ ${productionActuals.length} production actuals with variance patterns inserted`);

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
