-- Migration: Seed Data for Coffee Manufacturing
-- Purpose: Populate database with realistic coffee manufacturing test data
-- Date: 2026-01-24
--
-- This migration creates seed data for a coffee manufacturing operation:
--   - Roasting: Green bean roasters that roast raw coffee beans
--   - Grinding: Industrial grinders that grind roasted beans
--   - Filling: Machines that fill bags/cans with ground coffee
--   - Packaging: Lines that seal, label, and package finished products
--
-- Tables seeded:
--   - assets: Coffee manufacturing equipment
--   - cost_centers: Financial tracking for each asset
--   - shift_targets: Production targets per shift
--   - daily_summaries: Historical OEE and production data
--   - live_snapshots: Recent production snapshots with financial data
--   - safety_events: Sample safety incidents
--   - user_roles: Admin role for test user
--   - supervisor_assignments: Asset assignments for supervisors

-- ============================================================================
-- ASSETS: Coffee Manufacturing Equipment
-- ============================================================================

INSERT INTO assets (id, name, source_id, area) VALUES
    -- Roasting (3 roasters - high value, lower volume)
    ('a0000001-0000-0000-0000-000000000001', 'Roaster 1', 'ROAST-001', 'Roasting'),
    ('a0000001-0000-0000-0000-000000000002', 'Roaster 2', 'ROAST-002', 'Roasting'),
    ('a0000001-0000-0000-0000-000000000003', 'Roaster 3', 'ROAST-003', 'Roasting'),
    -- Grinding (4 grinders - high throughput)
    ('a0000001-0000-0000-0000-000000000004', 'Grinder 1', 'GRND-001', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000005', 'Grinder 2', 'GRND-002', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000006', 'Grinder 3', 'GRND-003', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000007', 'Grinder 4', 'GRND-004', 'Grinding'),
    -- Filling (3 filling lines - medium volume)
    ('a0000001-0000-0000-0000-000000000008', 'Filler Line A', 'FILL-001', 'Filling'),
    ('a0000001-0000-0000-0000-000000000009', 'Filler Line B', 'FILL-002', 'Filling'),
    ('a0000001-0000-0000-0000-000000000010', 'Filler Line C', 'FILL-003', 'Filling'),
    -- Packaging (3 packaging lines - high volume, final stage)
    ('a0000001-0000-0000-0000-000000000011', 'Packaging Line 1', 'PACK-001', 'Packaging'),
    ('a0000001-0000-0000-0000-000000000012', 'Packaging Line 2', 'PACK-002', 'Packaging'),
    ('a0000001-0000-0000-0000-000000000013', 'Packaging Line 3', 'PACK-003', 'Packaging')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- COST CENTERS: Financial Tracking
-- ============================================================================
-- Roasters have highest hourly rate (specialized equipment, quality-critical)
-- Grinders have medium-high rate (high throughput impact)
-- Fillers have medium rate (volume processing)
-- Packaging has standard rate (final assembly)

INSERT INTO cost_centers (asset_id, standard_hourly_rate) VALUES
    -- Roasters: $250/hr (quality-critical, batch processing)
    ('a0000001-0000-0000-0000-000000000001', 250.00),
    ('a0000001-0000-0000-0000-000000000002', 250.00),
    ('a0000001-0000-0000-0000-000000000003', 250.00),
    -- Grinders: $175/hr (high throughput, continuous operation)
    ('a0000001-0000-0000-0000-000000000004', 175.00),
    ('a0000001-0000-0000-0000-000000000005', 175.00),
    ('a0000001-0000-0000-0000-000000000006', 175.00),
    ('a0000001-0000-0000-0000-000000000007', 175.00),
    -- Fillers: $125/hr (volumetric filling operations)
    ('a0000001-0000-0000-0000-000000000008', 125.00),
    ('a0000001-0000-0000-0000-000000000009', 125.00),
    ('a0000001-0000-0000-0000-000000000010', 125.00),
    -- Packaging: $95/hr (final packaging and labeling)
    ('a0000001-0000-0000-0000-000000000011', 95.00),
    ('a0000001-0000-0000-0000-000000000012', 95.00),
    ('a0000001-0000-0000-0000-000000000013', 95.00)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SHIFT TARGETS: Production Goals
-- ============================================================================
-- Targets in batches/units appropriate to each operation:
-- Roasters: ~40-50 batches per 8-hour shift (each batch = ~500 lbs)
-- Grinders: ~800-1000 units per shift (continuous grinding)
-- Fillers: ~2000-2500 bags per shift
-- Packaging: ~3000-3500 cases per shift

INSERT INTO shift_targets (asset_id, target_output, shift, effective_date) VALUES
    -- Roaster targets (batches)
    ('a0000001-0000-0000-0000-000000000001', 48, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000001', 45, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000001', 40, 'night', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000002', 48, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000002', 45, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000003', 42, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000003', 42, 'afternoon', '2026-01-01'),
    -- Grinder targets (lbs processed)
    ('a0000001-0000-0000-0000-000000000004', 1000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000004', 950, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000005', 1000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000005', 950, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000006', 900, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000007', 850, 'morning', '2026-01-01'),
    -- Filler targets (bags filled)
    ('a0000001-0000-0000-0000-000000000008', 2400, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000008', 2200, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000009', 2400, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000010', 2000, 'morning', '2026-01-01'),
    -- Packaging targets (cases packed)
    ('a0000001-0000-0000-0000-000000000011', 3200, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000011', 3000, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000012', 3200, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000013', 2800, 'morning', '2026-01-01')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DAILY SUMMARIES: Historical Production Data (Last 7 days)
-- ============================================================================

INSERT INTO daily_summaries (asset_id, report_date, oee_percentage, actual_output, target_output, downtime_minutes, waste_count, financial_loss_dollars, smart_summary_text) VALUES
    -- Roaster 1 - Last 7 days (quality-focused narratives)
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 1, 89.50, 128, 143, 35, 3, 145.83, 'Roaster 1 performed well yesterday with 89.5% OEE. Batch quality excellent - all passed cupping tests. Brief cooling system delay resolved.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 2, 94.20, 135, 143, 18, 1, 75.00, 'Outstanding roasting day. Colombian single-origin profile nailed consistently. Minimal waste from one overroasted batch.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 3, 75.80, 108, 143, 95, 8, 395.83, 'Drum temperature sensor malfunction caused extended downtime. Calibration team called in. 8 batches below spec discarded.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 4, 91.50, 131, 143, 25, 2, 104.17, 'Strong recovery post-maintenance. Ethiopian Yirgacheffe roast profile optimized.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 5, 87.20, 125, 143, 42, 4, 175.00, 'Green bean moisture variance caused adjustments mid-shift. QC approved all batches after profile tweaks.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 6, 92.80, 133, 143, 22, 2, 91.67, 'Smooth operation. New Brazilian beans roasting beautifully at current profile settings.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 7, 88.40, 126, 143, 38, 5, 158.33, 'Chaff collection system cleaned during shift. Brief stoppage but prevented longer issue.'),

    -- Roaster 2 - Last 7 days
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 1, 96.10, 137, 143, 10, 1, 41.67, 'Best performing roaster yesterday. Dark roast blend production running flawlessly.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 2, 85.30, 122, 143, 55, 6, 229.17, 'Burner ignition issue caused startup delays. Maintenance addressed - monitoring closely.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 3, 93.00, 133, 143, 20, 2, 83.33, 'Consistent performance. Decaf Swiss Water batch processed successfully.'),

    -- Grinder 1 - Last 7 days (throughput-focused)
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 1, 91.20, 1780, 1950, 30, 25, 87.50, 'Grinder 1 running well. Espresso grind consistency excellent per QC samples. Minor burr adjustment completed.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 2, 88.50, 1725, 1950, 48, 35, 140.00, 'Slight throughput dip due to harder bean batch from Roaster 3. Adjusted feed rate.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 3, 94.80, 1848, 1950, 15, 18, 43.75, 'Outstanding grinding day. Medium roast flowing through at optimal rate.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 4, 82.50, 1608, 1950, 75, 45, 218.75, 'Burr replacement scheduled after detecting uneven particle distribution. Preventive maintenance performed.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 5, 93.20, 1817, 1950, 20, 22, 58.33, 'Post-maintenance performance excellent. New burrs producing consistent grind.'),

    -- Grinder 2 - Last 7 days
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 1, 87.80, 1712, 1950, 52, 38, 151.67, 'Medium grind production. Some clumping detected - humidity control adjusted.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 2, 95.50, 1862, 1950, 12, 15, 35.00, 'Top performance. Coarse grind for French press line running smoothly.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 3, 90.30, 1760, 1950, 35, 28, 102.08, 'Steady performance. Bean hopper sensor calibrated during shift change.'),

    -- Filler Line A - Last 7 days (volume-focused)
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 1, 84.50, 3886, 4600, 68, 85, 141.67, 'Filler A running 12oz bags. Nitrogen flush timing optimized for freshness seal. Some bag rejects from seal quality.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 2, 92.30, 4246, 4600, 28, 45, 58.33, 'Strong filling performance. New bag stock feeding well through magazine.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 3, 78.60, 3616, 4600, 95, 120, 197.92, 'Valve sticking issue caused multiple stoppages. Cleaned and reseated during break.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 4, 95.10, 4374, 4600, 15, 35, 31.25, 'Excellent recovery. K-Cup filling mode achieving target weights consistently.'),

    -- Filler Line B - Last 7 days
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 1, 89.20, 4103, 4600, 42, 65, 87.50, 'Good performance on 2lb bag line. Weight variance within spec.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 2, 91.80, 4223, 4600, 30, 50, 62.50, 'Steady filling. Degassing valve placement accuracy improved.'),

    -- Packaging Line 1 - Last 7 days (final output-focused)
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 1, 86.50, 5362, 6200, 58, 95, 91.83, 'Packaging Line 1 handled mixed SKU run. Label changeover time improved by 15%. Some carton rejects.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 2, 94.80, 5878, 6200, 18, 42, 28.50, 'Outstanding day. Holiday blend cases flowing smoothly to palletizer.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 3, 79.30, 4917, 6200, 88, 145, 139.17, 'Case erector jam caused significant downtime. Maintenance cleared cardboard buildup.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 4, 92.50, 5735, 6200, 25, 55, 39.58, 'Strong recovery. Automated case packing running efficiently.'),

    -- Packaging Line 2 - Last 7 days
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 1, 88.90, 5512, 6200, 45, 78, 71.25, 'Good performance on wholesale pack line. Case sealing quality excellent.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 2, 91.20, 5654, 6200, 32, 60, 50.67, 'Consistent throughput. Shrink wrap tension optimized.')
ON CONFLICT (asset_id, report_date) DO NOTHING;

-- ============================================================================
-- LIVE SNAPSHOTS: Recent Production Data (Last 4 hours, 15-min intervals)
-- Now includes financial_loss_dollars for Cost of Loss widget
-- ============================================================================

INSERT INTO live_snapshots (asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars) VALUES
    -- Roaster 1 - Recent snapshots (batches)
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '15 minutes', 6, 6, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '30 minutes', 11, 12, 'behind', 62.50),
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '45 minutes', 18, 18, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '1 hour', 24, 24, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '1 hour 15 minutes', 29, 30, 'behind', 62.50),
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '1 hour 30 minutes', 36, 36, 'on_target', 0.00),

    -- Roaster 2 - Recent snapshots (running ahead - dark roast batch)
    ('a0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '15 minutes', 7, 6, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '30 minutes', 13, 12, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '45 minutes', 19, 18, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '1 hour', 24, 24, 'on_target', 0.00),

    -- Grinder 1 - Recent snapshots (lbs)
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '15 minutes', 245, 250, 'behind', 14.58),
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '30 minutes', 502, 500, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '45 minutes', 748, 750, 'behind', 5.83),
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '1 hour', 1000, 1000, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '1 hour 15 minutes', 1240, 1250, 'behind', 29.17),
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '1 hour 30 minutes', 1498, 1500, 'behind', 5.83),

    -- Grinder 2 - Recent snapshots (running smoothly)
    ('a0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '15 minutes', 252, 250, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '30 minutes', 500, 500, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '45 minutes', 755, 750, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '1 hour', 1000, 1000, 'on_target', 0.00),

    -- Filler Line A - Recent snapshots (bags - some issues)
    ('a0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '15 minutes', 285, 300, 'behind', 31.25),
    ('a0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '30 minutes', 590, 600, 'behind', 20.83),
    ('a0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '45 minutes', 895, 900, 'behind', 10.42),
    ('a0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '1 hour', 1200, 1200, 'on_target', 0.00),

    -- Filler Line B - Recent snapshots (running well)
    ('a0000001-0000-0000-0000-000000000009', NOW() - INTERVAL '15 minutes', 302, 300, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000009', NOW() - INTERVAL '30 minutes', 600, 600, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000009', NOW() - INTERVAL '45 minutes', 905, 900, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000009', NOW() - INTERVAL '1 hour', 1200, 1200, 'on_target', 0.00),

    -- Packaging Line 1 - Recent snapshots (cases - recovering from earlier issue)
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '15 minutes', 380, 400, 'behind', 31.67),
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '30 minutes', 795, 800, 'behind', 7.92),
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '45 minutes', 1185, 1200, 'behind', 23.75),
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '1 hour', 1600, 1600, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '1 hour 15 minutes', 1980, 2000, 'behind', 31.67),
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '1 hour 30 minutes', 2400, 2400, 'on_target', 0.00),

    -- Packaging Line 2 - Recent snapshots (consistent)
    ('a0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '15 minutes', 400, 400, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '30 minutes', 805, 800, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '45 minutes', 1200, 1200, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '1 hour', 1600, 1600, 'on_target', 0.00),

    -- Roaster 3 - Recent snapshots (steady performance)
    ('a0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '15 minutes', 5, 5, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '30 minutes', 10, 10, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '45 minutes', 16, 15, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '1 hour', 21, 21, 'on_target', 0.00),

    -- Grinder 3 - Recent snapshots (slightly behind)
    ('a0000001-0000-0000-0000-000000000006', NOW() - INTERVAL '15 minutes', 220, 225, 'behind', 14.58),
    ('a0000001-0000-0000-0000-000000000006', NOW() - INTERVAL '30 minutes', 445, 450, 'behind', 14.58),
    ('a0000001-0000-0000-0000-000000000006', NOW() - INTERVAL '45 minutes', 675, 675, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000006', NOW() - INTERVAL '1 hour', 900, 900, 'on_target', 0.00),

    -- Grinder 4 - Recent snapshots (running well)
    ('a0000001-0000-0000-0000-000000000007', NOW() - INTERVAL '15 minutes', 215, 212, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000007', NOW() - INTERVAL '30 minutes', 425, 425, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000007', NOW() - INTERVAL '45 minutes', 638, 637, 'ahead', 0.00),
    ('a0000001-0000-0000-0000-000000000007', NOW() - INTERVAL '1 hour', 850, 850, 'on_target', 0.00),

    -- Filler Line C - Recent snapshots (on target)
    ('a0000001-0000-0000-0000-000000000010', NOW() - INTERVAL '15 minutes', 250, 250, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000010', NOW() - INTERVAL '30 minutes', 500, 500, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000010', NOW() - INTERVAL '45 minutes', 750, 750, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000010', NOW() - INTERVAL '1 hour', 1000, 1000, 'on_target', 0.00),

    -- Packaging Line 3 - Recent snapshots (slight variance)
    ('a0000001-0000-0000-0000-000000000013', NOW() - INTERVAL '15 minutes', 345, 350, 'behind', 7.92),
    ('a0000001-0000-0000-0000-000000000013', NOW() - INTERVAL '30 minutes', 700, 700, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000013', NOW() - INTERVAL '45 minutes', 1050, 1050, 'on_target', 0.00),
    ('a0000001-0000-0000-0000-000000000013', NOW() - INTERVAL '1 hour', 1400, 1400, 'on_target', 0.00)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAFETY EVENTS: Coffee Manufacturing Incidents
-- ============================================================================

INSERT INTO safety_events (asset_id, event_timestamp, reason_code, severity, description, is_resolved, resolved_at) VALUES
    -- Roasting area - high temperature environment
    ('a0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '3 days', 'Safety Issue', 'medium', 'Chaff fire detected in cooling tray. Suppression system activated correctly. Area cleared, fire extinguished in 30 seconds. No injuries.', true, NOW() - INTERVAL '3 days' + INTERVAL '1 hour'),
    ('a0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '8 days', 'Safety Issue', 'high', 'Drum bearing overheat alarm triggered. Emergency shutdown initiated. Thermal imaging showed 285F bearing temp. Replaced bearing assembly.', true, NOW() - INTERVAL '7 days'),

    -- Grinding area - dust and mechanical hazards
    ('a0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '5 days', 'Safety Issue', 'low', 'Coffee dust accumulation exceeded threshold near Grinder 1. Deep cleaning performed. Dust collection filter replaced.', true, NOW() - INTERVAL '5 days' + INTERVAL '3 hours'),
    ('a0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '2 hours', 'Safety Issue', 'medium', 'Grinder 2 vibration alarm - potential imbalance detected. Machine stopped for inspection. Awaiting maintenance assessment.', false, NULL),

    -- Filling area - pneumatic and weight hazards
    ('a0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '6 days', 'Safety Issue', 'medium', 'Nitrogen line pressure spike detected on Filler A. Pressure relief valve activated. Line isolated and inspected.', true, NOW() - INTERVAL '6 days' + INTERVAL '2 hours'),

    -- Packaging area - mechanical and ergonomic
    ('a0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '1 day', 'Safety Issue', 'low', 'Light curtain triggered on case erector - operator reached into zone. Safety system worked correctly. Retraining scheduled.', true, NOW() - INTERVAL '1 day' + INTERVAL '30 minutes'),
    ('a0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '10 days', 'Safety Issue', 'critical', 'Palletizer arm collision detected. E-stop activated. Full safety inspection completed. Sensor realignment required.', true, NOW() - INTERVAL '9 days')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- USER ROLES: Assign admin role to test user
-- ============================================================================

INSERT INTO user_roles (user_id, role)
SELECT id, 'admin' FROM auth.users WHERE email = 'heimdall@test.com'
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';

-- ============================================================================
-- SUPERVISOR ASSIGNMENTS: Assign assets to test user
-- ============================================================================

-- Assign Roasting and Grinding areas to test user (upstream process owner)
INSERT INTO supervisor_assignments (user_id, asset_id, assigned_at)
SELECT
    u.id,
    a.id,
    NOW()
FROM auth.users u
CROSS JOIN assets a
WHERE u.email = 'heimdall@test.com'
AND a.area IN ('Roasting', 'Grinding')
ON CONFLICT (user_id, asset_id) DO NOTHING;

-- ============================================================================
-- USER PREFERENCES: Default preferences for test user
-- ============================================================================

INSERT INTO user_preferences (user_id, role, area_order, detail_level, voice_enabled, onboarding_complete)
SELECT
    id,
    'admin',
    ARRAY['Roasting', 'Grinding', 'Filling', 'Packaging'],
    'detailed',
    true,
    true
FROM auth.users
WHERE email = 'heimdall@test.com'
ON CONFLICT (user_id) DO UPDATE SET
    role = 'admin',
    area_order = ARRAY['Roasting', 'Grinding', 'Filling', 'Packaging'],
    detail_level = 'detailed',
    voice_enabled = true,
    onboarding_complete = true;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Run these queries to verify seed data:
--
-- SELECT area, COUNT(*) as asset_count FROM assets GROUP BY area ORDER BY area;
-- SELECT COUNT(*) as daily_summary_count FROM daily_summaries;
-- SELECT COUNT(*) as live_snapshot_count FROM live_snapshots;
-- SELECT COUNT(*) as safety_event_count FROM safety_events;
-- SELECT SUM(financial_loss_dollars) as total_live_loss FROM live_snapshots;
-- SELECT * FROM user_roles WHERE user_id IN (SELECT id FROM auth.users WHERE email = 'heimdall@test.com');
