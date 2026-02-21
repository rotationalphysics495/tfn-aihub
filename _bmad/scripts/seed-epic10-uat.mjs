#!/usr/bin/env node
/**
 * Epic 10 UAT Seed Script
 *
 * Ensures the test environment has the data required for Epic 10 UAT:
 *   - live_snapshots: at least 2 assets with recent 15-min interval snapshots
 *     (needed for Scenarios 3 & 4: Live Pulse view)
 *   - safety_events: at least 1 open (unacknowledged) event
 *     (needed for Scenario 2: Acknowledge a Safety Alert)
 *   - daily_summaries: recent data with waste_count > 0
 *     (needed for Scenarios 5 & 6: Cost of Loss / Financial Summary)
 *
 * Usage: node _bmad/scripts/seed-epic10-uat.mjs
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://gfmalixorurasjrlgicq.supabase.co';
const SUPABASE_KEY = 'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const ASSETS = {
  ROASTER_1:   'a0000001-0000-0000-0000-000000000001',
  ROASTER_2:   'a0000001-0000-0000-0000-000000000002',
  ROASTER_3:   'a0000001-0000-0000-0000-000000000003',
  GRINDER_1:   'a0000001-0000-0000-0000-000000000004',
  GRINDER_2:   'a0000001-0000-0000-0000-000000000005',
  GRINDER_3:   'a0000001-0000-0000-0000-000000000006',
  GRINDER_4:   'a0000001-0000-0000-0000-000000000007',
  GRINDER_5:   'a0000001-0000-0000-0000-000000000014',
  FILLER_A:    'a0000001-0000-0000-0000-000000000008',
  FILLER_B:    'a0000001-0000-0000-0000-000000000009',
  FILLER_C:    'a0000001-0000-0000-0000-000000000010',
  PACKAGING_1: 'a0000001-0000-0000-0000-000000000011',
  PACKAGING_2: 'a0000001-0000-0000-0000-000000000012',
  PACKAGING_3: 'a0000001-0000-0000-0000-000000000013',
};

// Returns a Date offset by N minutes from now
function minutesAgo(n) {
  return new Date(Date.now() - n * 60 * 1000).toISOString();
}

// Returns a date string N days ago (YYYY-MM-DD)
function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

// ============================================================================
// SEED: live_snapshots
// ============================================================================
// Inserts recent 15-min interval snapshots for all 14 assets.
// Each asset gets 6 snapshots covering the last 90 minutes.
// financial_loss_dollars is non-zero for "behind" entries so the
// Cost of Loss widget shows real values.

async function seedLiveSnapshots() {
  console.log('📸 Seeding live_snapshots...');

  // Delete stale snapshots older than 2 hours so the table doesn't grow unbounded
  const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
  await supabase.from('live_snapshots').delete().lt('snapshot_timestamp', twoHoursAgo);

  // Asset configs: [target per 15-min window, hourly rate $/hr]
  const assetConfigs = [
    // Roasters (batches)
    { id: ASSETS.ROASTER_1,   target: 6,    rate: 250, label: 'Roaster 1'      },
    { id: ASSETS.ROASTER_2,   target: 6,    rate: 250, label: 'Roaster 2'      },
    { id: ASSETS.ROASTER_3,   target: 5,    rate: 250, label: 'Roaster 3'      },
    // Grinders (lbs)
    { id: ASSETS.GRINDER_1,   target: 250,  rate: 175, label: 'Grinder 1'      },
    { id: ASSETS.GRINDER_2,   target: 250,  rate: 175, label: 'Grinder 2'      },
    { id: ASSETS.GRINDER_3,   target: 225,  rate: 175, label: 'Grinder 3'      },
    { id: ASSETS.GRINDER_4,   target: 212,  rate: 175, label: 'Grinder 4'      },
    { id: ASSETS.GRINDER_5,   target: 250,  rate: 175, label: 'Grinder 5'      },
    // Fillers (bags)
    { id: ASSETS.FILLER_A,    target: 300,  rate: 125, label: 'Filler Line A'  },
    { id: ASSETS.FILLER_B,    target: 300,  rate: 125, label: 'Filler Line B'  },
    { id: ASSETS.FILLER_C,    target: 250,  rate: 125, label: 'Filler Line C'  },
    // Packaging (cases)
    { id: ASSETS.PACKAGING_1, target: 400,  rate: 95,  label: 'Packaging Line 1' },
    { id: ASSETS.PACKAGING_2, target: 400,  rate: 95,  label: 'Packaging Line 2' },
    { id: ASSETS.PACKAGING_3, target: 350,  rate: 95,  label: 'Packaging Line 3' },
  ];

  // Snapshot patterns per asset (multiplier applied to target each period)
  // Gives each asset a distinct story: ahead, behind, recovering, etc.
  const patterns = [
    [1.00, 0.92, 1.00, 1.00, 0.98, 1.00], // Roaster 1: mostly on-target, one behind
    [1.17, 1.08, 1.00, 1.08, 1.00, 1.00], // Roaster 2: running ahead
    [1.00, 1.00, 1.07, 1.00, 1.00, 1.00], // Roaster 3: slight ahead
    [0.98, 1.01, 0.97, 1.00, 0.99, 1.00], // Grinder 1: slightly behind, recovering
    [1.01, 1.00, 1.02, 1.00, 1.00, 1.00], // Grinder 2: consistently on/ahead
    [0.98, 0.99, 1.00, 1.00, 0.98, 1.00], // Grinder 3: slightly behind
    [1.01, 1.00, 1.01, 1.00, 1.00, 1.00], // Grinder 4: slight ahead
    [0.93, 0.97, 1.00, 0.95, 1.00, 0.98], // Grinder 5: behind (mechanical issues)
    [0.95, 0.98, 1.00, 0.97, 1.00, 1.00], // Filler A: behind, recovering
    [1.01, 1.00, 1.02, 1.00, 1.00, 1.00], // Filler B: on/ahead
    [1.00, 1.00, 1.00, 1.00, 1.00, 1.00], // Filler C: perfectly on target
    [0.95, 0.99, 0.98, 1.00, 1.00, 1.00], // Packaging 1: behind, catching up
    [1.00, 1.01, 1.00, 1.00, 1.00, 1.00], // Packaging 2: consistent
    [0.99, 1.00, 1.00, 0.99, 1.00, 1.00], // Packaging 3: slight variance
  ];

  const rows = [];

  assetConfigs.forEach((asset, idx) => {
    const pattern = patterns[idx];
    // 6 snapshots: 15, 30, 45, 60, 75, 90 minutes ago
    // cumulative output = sum of each period's output up to that point
    let cumOutput = 0;
    let cumTarget = 0;

    for (let p = 0; p < 6; p++) {
      const periodOutput = Math.round(asset.target * pattern[p]);
      const periodTarget = asset.target;
      cumOutput += periodOutput;
      cumTarget += periodTarget;

      const status = periodOutput > periodTarget
        ? 'ahead'
        : periodOutput < periodTarget
          ? 'behind'
          : 'on_target';

      // Financial loss: shortfall * (rate / target per 15-min window)
      // i.e. rate per unit * units missed
      const shortfall = Math.max(0, periodTarget - periodOutput);
      const lossPerUnit = asset.rate / asset.target; // $/unit in this period
      const financialLoss = Math.round(shortfall * lossPerUnit * 100) / 100;

      rows.push({
        asset_id: asset.id,
        snapshot_timestamp: minutesAgo((p + 1) * 15),
        current_output: cumOutput,
        target_output: cumTarget,
        status,
        financial_loss_dollars: financialLoss,
      });
    }
  });

  const { error } = await supabase.from('live_snapshots').insert(rows);
  if (error) {
    console.error('  Error inserting live_snapshots:', error.message);
    return false;
  }

  console.log(`  ✓ Inserted ${rows.length} snapshots across ${assetConfigs.length} assets`);
  console.log('    - 6 snapshots per asset (15-min intervals, last 90 min)');
  console.log('    - Mix of on_target, ahead, and behind statuses');
  console.log('    - financial_loss_dollars populated for behind entries');
  return true;
}

// ============================================================================
// SEED: safety_events (open/unacknowledged)
// ============================================================================
// Only inserts if fewer than 1 open event exists.

async function seedOpenSafetyEvent() {
  console.log('🚨 Checking safety_events...');

  const { data: open } = await supabase
    .from('safety_events')
    .select('id, severity')
    .eq('is_resolved', false);

  if (open && open.length >= 1) {
    console.log(`  ✓ ${open.length} open safety event(s) already exist — no insert needed`);
    console.log(`    Open: ${open.map(e => e.severity).join(', ')}`);
    return true;
  }

  console.log('  No open events found — inserting two open events...');

  const events = [
    {
      asset_id: ASSETS.GRINDER_2,
      event_timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hrs ago
      reason_code: 'Safety Issue',
      severity: 'medium',
      description: 'Grinder 2 vibration alarm — potential bearing imbalance detected. Machine stopped for inspection. Awaiting maintenance assessment. Operator reported unusual noise before alarm triggered.',
      is_resolved: false,
      resolved_at: null,
    },
    {
      asset_id: ASSETS.FILLER_A,
      event_timestamp: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(), // 18 hrs ago
      reason_code: 'Safety Issue',
      severity: 'high',
      description: 'Nitrogen line pressure spike to 180 PSI detected (normal: 120 PSI). Pressure relief valve activated. Line isolated pending full inspection by maintenance team.',
      is_resolved: false,
      resolved_at: null,
    },
  ];

  const { error } = await supabase.from('safety_events').insert(events);
  if (error) {
    console.error('  Error inserting safety events:', error.message);
    return false;
  }

  console.log('  ✓ Inserted 2 open safety events (medium + high severity)');
  return true;
}

// ============================================================================
// SEED: daily_summaries (today + recent days)
// ============================================================================
// The daily summaries table already has 98 rows but we ensure today's date
// is covered so the morning report and cost-of-loss views have current data.

async function seedTodayDailySummaries() {
  console.log('📊 Checking daily_summaries for today and yesterday...');

  // Asset profiles: [targetOutput, hourlyRate, baseOee]
  const profiles = [
    { id: ASSETS.ROASTER_1,   target: 143,  rate: 250, oee: 87.5  },
    { id: ASSETS.ROASTER_2,   target: 143,  rate: 250, oee: 96.1  },
    { id: ASSETS.ROASTER_3,   target: 143,  rate: 250, oee: 89.0  },
    { id: ASSETS.GRINDER_1,   target: 1950, rate: 175, oee: 91.2  },
    { id: ASSETS.GRINDER_2,   target: 1950, rate: 175, oee: 95.8  },
    { id: ASSETS.GRINDER_3,   target: 1950, rate: 175, oee: 84.2  },
    { id: ASSETS.GRINDER_4,   target: 1950, rate: 175, oee: 87.2  },
    { id: ASSETS.GRINDER_5,   target: 1950, rate: 175, oee: 82.5  },
    { id: ASSETS.FILLER_A,    target: 4600, rate: 125, oee: 72.5  },
    { id: ASSETS.FILLER_B,    target: 4600, rate: 125, oee: 89.2  },
    { id: ASSETS.FILLER_C,    target: 4000, rate: 125, oee: 80.0  },
    { id: ASSETS.PACKAGING_1, target: 6200, rate: 95,  oee: 89.5  },
    { id: ASSETS.PACKAGING_2, target: 6200, rate: 95,  oee: 88.9  },
    { id: ASSETS.PACKAGING_3, target: 5600, rate: 95,  oee: 87.5  },
  ];

  // Seed both today (morning report) and yesterday (cost-of-loss widget queries T-1)
  const datesToSeed = [daysAgo(0), daysAgo(1)];
  const rows = [];

  for (const reportDate of datesToSeed) {
    for (const p of profiles) {
      // Slightly vary OEE for yesterday vs today
      const oee = reportDate === daysAgo(1) ? Math.max(70, p.oee - 3 + Math.random() * 6) : p.oee;
      const actualOutput = Math.round(p.target * (oee / 100));
      const downtimeMinutes = Math.round((100 - oee) * 1.5);
      const wasteCount = Math.max(1, Math.round(actualOutput * 0.015));
      const financialLoss = Math.round((downtimeMinutes / 60) * p.rate * 100) / 100;
      rows.push({
        asset_id: p.id,
        report_date: reportDate,
        oee_percentage: Math.round(oee * 10) / 10,
        actual_output: actualOutput,
        target_output: p.target,
        downtime_minutes: downtimeMinutes,
        waste_count: wasteCount,
        financial_loss_dollars: financialLoss,
        smart_summary_text: `OEE at ${oee.toFixed(1)}% on ${reportDate}. ${downtimeMinutes} min downtime, ${wasteCount} units waste.`,
      });
    }
  }

  const { error } = await supabase.from('daily_summaries').upsert(rows, {
    onConflict: 'asset_id,report_date',
  });

  if (error) {
    console.error('  Error inserting daily_summaries:', error.message);
    return false;
  }

  console.log(`  ✓ Upserted ${rows.length} daily summary rows (today + yesterday)`);
  console.log(`    - Today (${daysAgo(0)}): ${profiles.length} rows`);
  console.log(`    - Yesterday (${daysAgo(1)}): ${profiles.length} rows (for cost-of-loss T-1 query)`);
  console.log('    - All rows have waste_count > 0 and financial_loss_dollars > 0');
  return true;
}

// ============================================================================
// VERIFY
// ============================================================================

async function verify() {
  console.log('\n📋 Verification\n');

  const [snapshots, openSafety, summariesWithWaste] = await Promise.all([
    supabase.from('live_snapshots').select('id', { count: 'exact', head: true }),
    supabase.from('safety_events').select('severity').eq('is_resolved', false),
    supabase.from('daily_summaries').select('id', { count: 'exact', head: true }).gt('waste_count', 0),
  ]);

  const ok = (v) => v ? '✓' : '✗';

  const hasSnapshots = (snapshots.count || 0) >= 2;
  const hasOpenAlert = (openSafety.data || []).length >= 1;
  const hasWasteData = (summariesWithWaste.count || 0) >= 1;

  console.log(`  [${ok(hasSnapshots)}] live_snapshots: ${snapshots.count} rows (need ≥2)`);
  console.log(`  [${ok(hasOpenAlert)}] safety_events open: ${(openSafety.data || []).length} (need ≥1) — ${(openSafety.data || []).map(e => e.severity).join(', ')}`);
  console.log(`  [${ok(hasWasteData)}] daily_summaries with waste_count > 0: ${summariesWithWaste.count} rows`);

  const allGood = hasSnapshots && hasOpenAlert && hasWasteData;
  console.log(`\n${allGood ? '✅ All Epic 10 UAT data requirements met.' : '❌ Some requirements not met — check errors above.'}`);
}

// ============================================================================
// MAIN
// ============================================================================

console.log('🚀 Epic 10 UAT Data Seeding\n' + '='.repeat(50));
await seedLiveSnapshots();
console.log('');
await seedOpenSafetyEvent();
console.log('');
await seedTodayDailySummaries();
await verify();
console.log('='.repeat(50));
