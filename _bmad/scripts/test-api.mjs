#!/usr/bin/env node
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://gfmalixorurasjrlgicq.supabase.co',
  'sb_secret__ArYAEUx6MrYebGDu6MaOA_rkEzOsEA'
);

// Get a session token for the test user
const { data: authData, error: authErr } = await supabase.auth.signInWithPassword({
  email: 'heimdall@test.com',
  password: 'Test1234!@#$'
});

if (authErr) {
  console.log('Auth error:', authErr.message);
  process.exit(1);
}

console.log('✓ Authenticated as heimdall@test.com');
console.log('Token preview:', authData.session.access_token.slice(0, 30) + '...');

// Test the actions API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log('\nCalling API:', API_URL + '/api/v1/actions/daily');

try {
  const response = await fetch(`${API_URL}/api/v1/actions/daily`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${authData.session.access_token}`,
      'Content-Type': 'application/json',
    },
  });
  
  console.log('Response status:', response.status);
  
  if (response.ok) {
    const data = await response.json();
    console.log('\n📋 Action List Response:');
    console.log('Total count:', data.total_count);
    console.log('Counts by category:', JSON.stringify(data.counts_by_category));
    console.log('Report date:', data.report_date);
    console.log('\nActions:');
    data.actions?.forEach(a => {
      console.log(`  - [${a.category}] ${a.asset_name}: ${a.primary_metric_value}`);
    });
  } else {
    const text = await response.text();
    console.log('Error response:', text);
  }
} catch (e) {
  console.log('Fetch error:', e.message);
  console.log('\nIs the API server running? Check with: cd apps/api && poetry run uvicorn app.main:app --reload');
}
