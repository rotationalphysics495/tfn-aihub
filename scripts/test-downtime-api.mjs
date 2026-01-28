#!/usr/bin/env node
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://gfmalixorurasjrlgicq.supabase.co',
  'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA'
);

const { data: authData, error: authErr } = await supabase.auth.signInWithPassword({
  email: 'heimdall@test.com',
  password: 'Test1234!@#$'
});

if (authErr) {
  console.log('Auth error:', authErr.message);
  process.exit(1);
}

const API_URL = 'http://localhost:8000';
const token = authData.session.access_token;

// Test downtime pareto
console.log('Testing /api/v1/downtime/pareto...');
try {
  const paretoRes = await fetch(`${API_URL}/api/v1/downtime/pareto?source=yesterday`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log('Status:', paretoRes.status);
  const pareto = await paretoRes.json();
  console.log('Pareto data:', JSON.stringify(pareto, null, 2));
} catch (e) {
  console.log('Error:', e.message);
}

// Test downtime events
console.log('\nTesting /api/v1/downtime/events...');
try {
  const eventsRes = await fetch(`${API_URL}/api/v1/downtime/events?source=yesterday`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log('Status:', eventsRes.status);
  const events = await eventsRes.json();
  console.log('Events data:', JSON.stringify(events, null, 2));
} catch (e) {
  console.log('Error:', e.message);
}
