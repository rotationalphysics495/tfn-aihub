#!/usr/bin/env node
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://gfmalixorurasjrlgicq.supabase.co',
  'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA'
);

// Check all daily_summaries
const { data: allSummaries } = await supabase
  .from('daily_summaries')
  .select('asset_id, report_date, oee_percentage, financial_loss_dollars')
  .order('report_date', { ascending: false });

console.log('📊 All Daily Summaries in DB:');
allSummaries?.forEach(s => {
  const flags = [];
  if (s.oee_percentage < 85) flags.push('OEE<85%');
  if (s.financial_loss_dollars > 1000) flags.push('Loss>$1000');
  console.log(`  ${s.report_date} | ${s.asset_id.slice(-4)}: OEE=${s.oee_percentage}%, Loss=$${s.financial_loss_dollars} ${flags.length ? '⚠️ ' + flags.join(', ') : '✓'}`);
});

// Check all safety events with full details
const { data: allSafety } = await supabase
  .from('safety_events')
  .select('*');

console.log('\n🚨 All Safety Events:');
allSafety?.forEach(s => {
  console.log(`  ${s.asset_id.slice(-4)}: severity=${s.severity}, resolved=${s.is_resolved}, timestamp=${s.event_timestamp}`);
});

// Check assets
const { data: assets } = await supabase.from('assets').select('id, name');
console.log('\n📦 Assets:');
assets?.forEach(a => {
  console.log(`  ${a.id}: ${a.name}`);
});
