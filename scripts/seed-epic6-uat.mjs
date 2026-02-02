#!/usr/bin/env node
/**
 * Epic 6 UAT Seed Script
 *
 * This script ensures the test environment has all required data for Epic 6 UAT:
 * - Safety events with various severity levels (critical, high, medium, low)
 * - Safety events with different resolution statuses (open, under_investigation, resolved)
 * - 30 days of historical data for trend analysis
 * - Downtime reasons for root cause analysis (requires migration 0024 to be run first)
 *
 * Usage: node scripts/seed-epic6-uat.mjs
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://gfmalixorurasjrlgicq.supabase.co';
const SUPABASE_KEY = 'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false }
});

// Helper functions
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

// Asset IDs
const ASSETS = {
  ROASTER_1: 'a0000001-0000-0000-0000-000000000001',
  ROASTER_2: 'a0000001-0000-0000-0000-000000000002',
  ROASTER_3: 'a0000001-0000-0000-0000-000000000003',
  GRINDER_1: 'a0000001-0000-0000-0000-000000000004',
  GRINDER_2: 'a0000001-0000-0000-0000-000000000005',
  GRINDER_3: 'a0000001-0000-0000-0000-000000000006',
  GRINDER_4: 'a0000001-0000-0000-0000-000000000007',
  GRINDER_5: 'a0000001-0000-0000-0000-000000000014',
  FILLER_A: 'a0000001-0000-0000-0000-000000000008',
  FILLER_B: 'a0000001-0000-0000-0000-000000000009',
  FILLER_C: 'a0000001-0000-0000-0000-000000000010',
  PACKAGING_1: 'a0000001-0000-0000-0000-000000000011',
  PACKAGING_2: 'a0000001-0000-0000-0000-000000000012',
  PACKAGING_3: 'a0000001-0000-0000-0000-000000000013',
};

async function seedSafetyEvents() {
  console.log('🚨 Seeding safety events with all severity levels...');

  // Clear existing safety events
  await supabase.from('safety_events').delete().neq('id', '00000000-0000-0000-0000-000000000000');

  const safetyEvents = [
    // CRITICAL severity (1 event)
    {
      asset_id: ASSETS.PACKAGING_2,
      event_timestamp: hoursAgo(240), // 10 days ago
      reason_code: 'Safety Issue',
      severity: 'critical',
      description: 'Palletizer arm collision detected during operation. E-stop activated immediately. Full safety inspection required. Sensor realignment and software update completed.',
      is_resolved: true,
      resolved_at: hoursAgo(216) // resolved 24 hours later
    },

    // HIGH severity (2 events - 1 resolved, 1 under investigation)
    {
      asset_id: ASSETS.ROASTER_2,
      event_timestamp: hoursAgo(192), // 8 days ago
      reason_code: 'Safety Issue',
      severity: 'high',
      description: 'Drum bearing overheat alarm triggered at 285°F. Emergency shutdown initiated. Thermal imaging confirmed bearing failure. Replaced bearing assembly and tested.',
      is_resolved: true,
      resolved_at: hoursAgo(168) // resolved 24 hours later
    },
    {
      asset_id: ASSETS.FILLER_A,
      event_timestamp: hoursAgo(18), // 18 hours ago
      reason_code: 'Safety Issue',
      severity: 'high',
      description: 'Nitrogen line pressure spike to 180 PSI detected (normal: 120 PSI). Pressure relief valve activated. Line isolated pending full inspection by maintenance team.',
      is_resolved: false,
      resolved_at: null
      // This one is "under investigation" - is_resolved: false without resolved_at
    },

    // MEDIUM severity (3 events - mixed statuses)
    {
      asset_id: ASSETS.ROASTER_1,
      event_timestamp: hoursAgo(72), // 3 days ago
      reason_code: 'Safety Issue',
      severity: 'medium',
      description: 'Chaff fire detected in cooling tray. Automatic suppression system activated correctly. Fire extinguished in 30 seconds. No injuries. Area cleared and inspected.',
      is_resolved: true,
      resolved_at: hoursAgo(71)
    },
    {
      asset_id: ASSETS.GRINDER_5,
      event_timestamp: hoursAgo(48), // 2 days ago
      reason_code: 'Safety Issue',
      severity: 'medium',
      description: 'Grinder 5 vibration alarm triggered - potential bearing imbalance detected. Machine stopped for inspection. Maintenance assessment ongoing.',
      is_resolved: true,
      resolved_at: hoursAgo(46)
    },
    {
      asset_id: ASSETS.GRINDER_2,
      event_timestamp: hoursAgo(2), // 2 hours ago - recent open issue
      reason_code: 'Safety Issue',
      severity: 'medium',
      description: 'Grinder 2 vibration alarm - potential imbalance detected. Machine stopped for inspection. Awaiting maintenance assessment. Operator reported unusual noise before alarm.',
      is_resolved: false,
      resolved_at: null
    },

    // LOW severity (2 events)
    {
      asset_id: ASSETS.PACKAGING_1,
      event_timestamp: hoursAgo(24), // 1 day ago
      reason_code: 'Safety Issue',
      severity: 'low',
      description: 'Light curtain triggered on case erector - operator reached into guarded zone. Safety system worked correctly. No injury. Operator retraining scheduled.',
      is_resolved: true,
      resolved_at: hoursAgo(23.5)
    },
    {
      asset_id: ASSETS.GRINDER_4,
      event_timestamp: hoursAgo(120), // 5 days ago
      reason_code: 'Safety Issue',
      severity: 'low',
      description: 'Coffee dust accumulation exceeded threshold near Grinder 4. Deep cleaning performed. Dust collection filter replaced. Air quality within normal range.',
      is_resolved: true,
      resolved_at: hoursAgo(117)
    }
  ];

  const { error } = await supabase.from('safety_events').insert(safetyEvents);
  if (error) {
    console.error('  Error inserting safety events:', error.message);
    return false;
  }

  console.log('  ✓ Inserted 8 safety events:');
  console.log('    - 1 critical (resolved)');
  console.log('    - 2 high (1 resolved, 1 under investigation)');
  console.log('    - 3 medium (2 resolved, 1 open)');
  console.log('    - 2 low (resolved)');
  return true;
}

async function seedHistoricalDailySummaries() {
  console.log('📊 Seeding recent and historical daily summaries...');

  // Generate data for days 0-2 (today and recent) AND days 8-30 (extended history)
  // Note: OEE page needs today's data (day 0) to display
  const allAssets = Object.values(ASSETS);
  const summaries = [];

  // Base OEE and variance by asset type
  const assetProfiles = {
    [ASSETS.ROASTER_1]: { baseOee: 88, variance: 8, baseOutput: 130, targetOutput: 143 },
    [ASSETS.ROASTER_2]: { baseOee: 91, variance: 6, baseOutput: 132, targetOutput: 143 },
    [ASSETS.ROASTER_3]: { baseOee: 86, variance: 9, baseOutput: 125, targetOutput: 143 },
    [ASSETS.GRINDER_1]: { baseOee: 89, variance: 7, baseOutput: 1750, targetOutput: 1950 },
    [ASSETS.GRINDER_2]: { baseOee: 93, variance: 4, baseOutput: 1820, targetOutput: 1950 },
    [ASSETS.GRINDER_3]: { baseOee: 87, variance: 8, baseOutput: 1700, targetOutput: 1950 },
    [ASSETS.GRINDER_4]: { baseOee: 90, variance: 6, baseOutput: 1780, targetOutput: 1950 },
    [ASSETS.GRINDER_5]: { baseOee: 85, variance: 10, baseOutput: 1660, targetOutput: 1950 },
    [ASSETS.FILLER_A]: { baseOee: 86, variance: 12, baseOutput: 3960, targetOutput: 4600 },
    [ASSETS.FILLER_B]: { baseOee: 91, variance: 5, baseOutput: 4190, targetOutput: 4600 },
    [ASSETS.FILLER_C]: { baseOee: 89, variance: 6, baseOutput: 4100, targetOutput: 4600 },
    [ASSETS.PACKAGING_1]: { baseOee: 88, variance: 9, baseOutput: 5460, targetOutput: 6200 },
    [ASSETS.PACKAGING_2]: { baseOee: 91, variance: 5, baseOutput: 5640, targetOutput: 6200 },
    [ASSETS.PACKAGING_3]: { baseOee: 87, variance: 8, baseOutput: 5400, targetOutput: 6200 },
  };

  // Downtime reason categories with weights
  const downtimeReasons = [
    { reason: 'Mechanical Failure', weight: 25 },
    { reason: 'Changeover', weight: 20 },
    { reason: 'Material Issue', weight: 15 },
    { reason: 'Cleanup', weight: 15 },
    { reason: 'Operator Break', weight: 10 },
    { reason: 'Calibration', weight: 5 },
    { reason: 'Safety Stop', weight: 5 },
    { reason: 'Quality Check', weight: 5 },
  ];

  // Generate summaries for days 0-2 (recent) AND days 3-30 (extended history)
  // This ensures today (day 0) has data for the OEE page
  const daysToSeed = [0, 1, 2, ...Array.from({length: 28}, (_, i) => i + 3)];

  for (const day of daysToSeed) {
    const reportDate = daysAgo(day);

    for (const assetId of allAssets) {
      const profile = assetProfiles[assetId];

      // Random variation
      const oeeVariance = (Math.random() - 0.5) * 2 * profile.variance;
      const oee = Math.max(65, Math.min(98, profile.baseOee + oeeVariance));

      // Calculate other metrics based on OEE
      const outputRatio = oee / 100;
      const actualOutput = Math.round(profile.targetOutput * outputRatio * (0.95 + Math.random() * 0.1));

      // Downtime minutes inversely related to OEE
      const downtimeMinutes = Math.round((100 - oee) * (0.8 + Math.random() * 0.4) * 1.5);

      // Waste count somewhat random but related to output
      const wasteCount = Math.round(actualOutput * (0.01 + Math.random() * 0.02));

      // Financial loss based on downtime and asset hourly rate
      const hourlyRates = {
        [ASSETS.ROASTER_1]: 250, [ASSETS.ROASTER_2]: 250, [ASSETS.ROASTER_3]: 250,
        [ASSETS.GRINDER_1]: 175, [ASSETS.GRINDER_2]: 175, [ASSETS.GRINDER_3]: 175,
        [ASSETS.GRINDER_4]: 175, [ASSETS.GRINDER_5]: 175,
        [ASSETS.FILLER_A]: 125, [ASSETS.FILLER_B]: 125, [ASSETS.FILLER_C]: 125,
        [ASSETS.PACKAGING_1]: 95, [ASSETS.PACKAGING_2]: 95, [ASSETS.PACKAGING_3]: 95,
      };
      const financialLoss = Math.round((downtimeMinutes / 60) * hourlyRates[assetId] * 100) / 100;

      // Generate downtime reasons breakdown (if we have downtime)
      let downtimeReasonsObj = {};
      if (downtimeMinutes > 0) {
        let remainingMinutes = downtimeMinutes;
        // Pick 1-3 random reasons
        const numReasons = Math.min(3, Math.ceil(Math.random() * 3));
        const shuffledReasons = [...downtimeReasons].sort(() => Math.random() - 0.5).slice(0, numReasons);

        for (let i = 0; i < shuffledReasons.length; i++) {
          if (i === shuffledReasons.length - 1) {
            downtimeReasonsObj[shuffledReasons[i].reason] = remainingMinutes;
          } else {
            const minutes = Math.round(remainingMinutes * (0.3 + Math.random() * 0.4));
            downtimeReasonsObj[shuffledReasons[i].reason] = minutes;
            remainingMinutes -= minutes;
          }
        }
      }

      // Smart summary text
      const summaryTexts = [
        `${oee > 90 ? 'Excellent' : oee > 80 ? 'Good' : 'Challenging'} performance day. OEE at ${oee.toFixed(1)}%.`,
        `Production ${oee > 90 ? 'exceeded expectations' : oee > 80 ? 'met targets' : 'below target'}. ${downtimeMinutes} minutes downtime.`,
        `${downtimeMinutes > 60 ? 'Extended downtime affected output.' : 'Minimal disruptions.'} Output: ${actualOutput} units.`,
      ];
      const smartSummary = summaryTexts[Math.floor(Math.random() * summaryTexts.length)];

      summaries.push({
        asset_id: assetId,
        report_date: reportDate,
        oee_percentage: Math.round(oee * 100) / 100,
        actual_output: actualOutput,
        target_output: profile.targetOutput,
        downtime_minutes: downtimeMinutes,
        waste_count: wasteCount,
        financial_loss_dollars: financialLoss,
        smart_summary_text: smartSummary,
        // Note: downtime_reasons will be added separately if column exists
      });
    }
  }

  // Insert in batches to avoid timeout
  const batchSize = 50;
  let inserted = 0;

  for (let i = 0; i < summaries.length; i += batchSize) {
    const batch = summaries.slice(i, i + batchSize);
    const { error } = await supabase.from('daily_summaries').upsert(batch, {
      onConflict: 'asset_id,report_date'
    });

    if (error) {
      console.error(`  Error inserting batch ${i / batchSize + 1}:`, error.message);
    } else {
      inserted += batch.length;
    }
  }

  console.log(`  ✓ Inserted/updated ${inserted} daily summary records`);
  console.log(`    - Days 0-30 added (today through 30 days ago)`);
  console.log(`    - 14 assets x 31 days = ${14 * 31} records`);
  return true;
}

async function checkAndSeedDowntimeReasons() {
  console.log('🔧 Checking for downtime_reasons column...');

  // Check if column exists
  const { data, error } = await supabase.from('daily_summaries')
    .select('downtime_reasons')
    .limit(1);

  if (error && error.message.includes('does not exist')) {
    console.log('  ⚠️  Column downtime_reasons does NOT exist');
    console.log('  Please run this SQL in Supabase dashboard first:');
    console.log('  --------------------------------------------------');
    console.log('  ALTER TABLE daily_summaries ADD COLUMN IF NOT EXISTS downtime_reasons JSONB DEFAULT NULL;');
    console.log('  --------------------------------------------------');
    console.log('  Then re-run this script to populate the data.');
    return false;
  }

  console.log('  ✓ Column exists, populating downtime_reasons data...');

  // Get all summaries that need downtime_reasons
  const { data: summaries } = await supabase.from('daily_summaries')
    .select('id, asset_id, downtime_minutes, downtime_reasons')
    .is('downtime_reasons', null)
    .gt('downtime_minutes', 0);

  if (!summaries || summaries.length === 0) {
    console.log('  ✓ All summaries already have downtime_reasons');
    return true;
  }

  // Downtime reason categories
  const downtimeReasons = [
    'Mechanical Failure', 'Changeover', 'Material Issue', 'Cleanup',
    'Operator Break', 'Calibration', 'Safety Stop', 'Quality Check',
    'Valve Issue', 'Jam', 'Sensor Malfunction', 'Cooling System'
  ];

  // Update each summary with downtime reasons
  let updated = 0;
  for (const summary of summaries) {
    let remainingMinutes = summary.downtime_minutes;
    const reasons = {};

    // Pick 1-3 random reasons
    const numReasons = Math.min(3, Math.ceil(Math.random() * 3));
    const shuffledReasons = [...downtimeReasons].sort(() => Math.random() - 0.5).slice(0, numReasons);

    for (let i = 0; i < shuffledReasons.length; i++) {
      if (i === shuffledReasons.length - 1) {
        reasons[shuffledReasons[i]] = remainingMinutes;
      } else {
        const minutes = Math.round(remainingMinutes * (0.3 + Math.random() * 0.4));
        reasons[shuffledReasons[i]] = minutes;
        remainingMinutes -= minutes;
      }
    }

    const { error: updateError } = await supabase.from('daily_summaries')
      .update({ downtime_reasons: reasons })
      .eq('id', summary.id);

    if (!updateError) updated++;
  }

  console.log(`  ✓ Updated ${updated} records with downtime_reasons`);
  return true;
}

async function verifySeedData() {
  console.log('\n📋 Verifying seed data...\n');

  // Check assets
  const { data: assets } = await supabase.from('assets').select('area');
  const byArea = {};
  assets?.forEach(a => { byArea[a.area] = (byArea[a.area] || 0) + 1; });
  console.log('Assets:', assets?.length, '- By Area:', byArea);

  // Check safety events
  const { data: safety } = await supabase.from('safety_events').select('severity, is_resolved');
  const bySeverity = {};
  const byResolved = { resolved: 0, open: 0 };
  safety?.forEach(s => {
    bySeverity[s.severity] = (bySeverity[s.severity] || 0) + 1;
    if (s.is_resolved) byResolved.resolved++;
    else byResolved.open++;
  });
  console.log('Safety Events:', safety?.length, '- By Severity:', bySeverity, '- By Status:', byResolved);

  // Check cost centers
  const { count: costCount } = await supabase.from('cost_centers').select('*', { count: 'exact', head: true });
  console.log('Cost Centers:', costCount);

  // Check daily summaries
  const { data: dates } = await supabase.from('daily_summaries').select('report_date');
  const uniqueDates = [...new Set(dates?.map(d => d.report_date))].sort();
  console.log('Daily Summaries: Date Range:', uniqueDates[0], 'to', uniqueDates[uniqueDates.length - 1], `(${uniqueDates.length} days)`);

  // Check downtime_reasons
  const { data: withReasons, error: reasonsErr } = await supabase.from('daily_summaries')
    .select('downtime_reasons')
    .not('downtime_reasons', 'is', null)
    .limit(1);

  if (reasonsErr && reasonsErr.message.includes('does not exist')) {
    console.log('Downtime Reasons: ❌ Column does not exist yet');
  } else {
    const { count } = await supabase.from('daily_summaries')
      .select('*', { count: 'exact', head: true })
      .not('downtime_reasons', 'is', null);
    console.log('Downtime Reasons: ✓', count, 'records have downtime_reasons data');
  }

  console.log('\n✅ Epic 6 UAT Requirements Status:');
  console.log('  [' + (assets?.length >= 5 ? '✓' : '✗') + '] 5-8 assets across multiple areas');
  console.log('  [' + (bySeverity.critical > 0 && bySeverity.high > 0 ? '✓' : '✗') + '] Safety events with critical/high severity');
  console.log('  [' + (byResolved.open > 0 && byResolved.resolved > 0 ? '✓' : '✗') + '] Safety events with open/resolved statuses');
  console.log('  [' + (costCount > 0 ? '✓' : '✗') + '] Cost center data configured');
  console.log('  [' + (uniqueDates.length >= 7 ? '✓' : '✗') + '] 7-30 days of historical data');
}

async function main() {
  console.log('🚀 Epic 6 UAT Data Seeding\n');
  console.log('='.repeat(50));

  await seedSafetyEvents();
  console.log('');

  await seedHistoricalDailySummaries();
  console.log('');

  await checkAndSeedDowntimeReasons();

  await verifySeedData();

  console.log('\n' + '='.repeat(50));
  console.log('🎉 Seeding complete!\n');
}

main().catch(console.error);
