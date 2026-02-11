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
    -- Grinding (5 grinders - high throughput, Grinder 5 added for Epic 5 UAT)
    ('a0000001-0000-0000-0000-000000000004', 'Grinder 1', 'GRND-001', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000005', 'Grinder 2', 'GRND-002', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000006', 'Grinder 3', 'GRND-003', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000007', 'Grinder 4', 'GRND-004', 'Grinding'),
    ('a0000001-0000-0000-0000-000000000014', 'Grinder 5', 'GRND-005', 'Grinding'),
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
    ('a0000001-0000-0000-0000-000000000014', 175.00),
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
    -- Roaster targets (batches) - each sums to 143
    ('a0000001-0000-0000-0000-000000000001', 50, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000001', 48, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000001', 45, 'night', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000002', 50, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000002', 48, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000002', 45, 'night', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000003', 50, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000003', 48, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000003', 45, 'night', '2026-01-01'),
    -- Grinder targets (lbs processed) - each sums to 1950
    ('a0000001-0000-0000-0000-000000000004', 1000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000004', 950, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000005', 1000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000005', 950, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000006', 900, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000006', 1050, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000007', 850, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000007', 1100, 'afternoon', '2026-01-01'),
    -- Grinder 5 targets (Epic 5 UAT key asset) - sums to 1950
    ('a0000001-0000-0000-0000-000000000014', 1000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000014', 950, 'afternoon', '2026-01-01'),
    -- Filler targets (bags filled) - A/B sum to 4600, C sums to 4000
    ('a0000001-0000-0000-0000-000000000008', 2400, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000008', 2200, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000009', 2400, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000009', 2200, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000010', 2000, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000010', 2000, 'afternoon', '2026-01-01'),
    -- Packaging targets (cases packed) - 1/2 sum to 6200, 3 sums to 5600
    ('a0000001-0000-0000-0000-000000000011', 3200, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000011', 3000, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000012', 3200, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000012', 3000, 'afternoon', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000013', 2800, 'morning', '2026-01-01'),
    ('a0000001-0000-0000-0000-000000000013', 2800, 'afternoon', '2026-01-01')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DAILY SUMMARIES: Historical Production Data (Last 7 days)
-- ============================================================================

INSERT INTO daily_summaries (asset_id, report_date, oee_percentage, actual_output, target_output, downtime_minutes, waste_count, financial_loss_dollars, smart_summary_text) VALUES
    -- ============ ROASTER 1 - 7 days (target_output=143) ============
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 1, 87.50, 125, 143, 45, 8, 187.50, 'Roaster 1 experienced cooling system issues causing extended batch cycle times.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 2, 94.20, 135, 143, 18, 1, 75.00, 'Outstanding roasting day. Colombian single-origin profile nailed consistently.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 3, 75.80, 108, 143, 95, 8, 395.83, 'Drum temperature sensor malfunction caused extended downtime.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 4, 91.50, 131, 143, 25, 2, 104.17, 'Strong recovery post-maintenance. Ethiopian Yirgacheffe roast profile optimized.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 5, 87.20, 125, 143, 42, 4, 175.00, 'Green bean moisture variance caused adjustments mid-shift.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 6, 92.80, 133, 143, 22, 2, 91.67, 'Smooth operation. New Brazilian beans roasting beautifully.'),
    ('a0000001-0000-0000-0000-000000000001', CURRENT_DATE - 7, 88.40, 126, 143, 38, 5, 158.33, 'Chaff collection system cleaned during shift.'),

    -- ============ ROASTER 2 - 7 days (target_output=143) ============
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 1, 96.10, 145, 143, 10, 1, 41.67, 'Best performing roaster yesterday. Dark roast blend running flawlessly.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 2, 85.30, 122, 143, 55, 6, 229.17, 'Burner ignition issue caused startup delays.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 3, 93.00, 133, 143, 20, 2, 83.33, 'Consistent performance. Decaf Swiss Water batch processed successfully.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 4, 90.50, 129, 143, 30, 3, 125.00, 'Steady roasting with routine maintenance.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 5, 94.40, 135, 143, 15, 1, 62.50, 'Outstanding performance on medium roast blend.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 6, 89.50, 128, 143, 35, 4, 145.83, 'Good day with extended changeover for new blend.'),
    ('a0000001-0000-0000-0000-000000000002', CURRENT_DATE - 7, 91.20, 130, 143, 28, 3, 116.67, 'Reliable start to the week.'),

    -- ============ ROASTER 3 - 7 days (target_output=143, new asset) ============
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 1, 89.00, 127, 143, 35, 4, 145.83, 'Roaster 3 performing well on medium roast batch. Minor cooling cycle adjustment.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 2, 91.50, 131, 143, 25, 3, 104.17, 'Consistent performance. Light roast Ethiopian beans processed smoothly.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 3, 86.20, 123, 143, 48, 5, 200.00, 'Extended changeover for specialty blend caused throughput reduction.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 4, 93.80, 134, 143, 18, 2, 75.00, 'Excellent batch consistency. Dark roast profile running optimally.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 5, 88.10, 126, 143, 40, 4, 166.67, 'Some first-crack timing variance on new bean lot.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 6, 90.90, 130, 143, 28, 3, 116.67, 'Steady roasting day. Chaff system operating normally.'),
    ('a0000001-0000-0000-0000-000000000003', CURRENT_DATE - 7, 87.40, 125, 143, 42, 5, 175.00, 'Minor cooling delays on larger batch sizes.'),

    -- ============ GRINDER 1 - 7 days (target_output=1950) ============
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 1, 91.20, 1780, 1950, 30, 25, 87.50, 'Grinder 1 running well. Espresso grind consistency excellent.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 2, 88.50, 1725, 1950, 48, 35, 140.00, 'Slight throughput dip due to harder bean batch.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 3, 94.80, 1848, 1950, 15, 18, 43.75, 'Outstanding grinding day. Medium roast flowing at optimal rate.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 4, 72.30, 1409, 1950, 125, 65, 364.58, 'Burr replacement required. Extended downtime for maintenance.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 5, 93.20, 1817, 1950, 20, 22, 58.33, 'Post-maintenance performance excellent. New burrs producing consistent grind.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 6, 90.10, 1756, 1950, 35, 27, 102.08, 'Consistent grinding. Brief pause for shift handover.'),
    ('a0000001-0000-0000-0000-000000000004', CURRENT_DATE - 7, 86.50, 1687, 1950, 55, 32, 160.42, 'Some issues with bean moisture affecting grind quality.'),

    -- ============ GRINDER 2 - 7 days (target_output=1950) ============
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 1, 95.80, 1960, 1950, 0, 15, 0.00, 'Perfect uptime day! Grinder 2 running flawlessly on French press coarse grind.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 2, 95.50, 1862, 1950, 12, 15, 35.00, 'Top performance. Coarse grind for French press line running smoothly.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 3, 90.30, 1760, 1950, 35, 28, 102.08, 'Steady performance. Bean hopper sensor calibrated during shift change.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 4, 92.40, 1802, 1950, 25, 20, 72.92, 'Smooth operation with single changeover.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 5, 94.10, 1835, 1950, 18, 18, 52.50, 'Excellent grinding consistency throughout the shift.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 6, 91.80, 1790, 1950, 28, 22, 81.67, 'Reliable performance on dark roast batch.'),
    ('a0000001-0000-0000-0000-000000000005', CURRENT_DATE - 7, 93.50, 1823, 1950, 20, 19, 58.33, 'Consistent week-opener with quick changeover.'),

    -- ============ GRINDER 3 - 7 days (target_output=1950) ============
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 1, 84.20, 1642, 1950, 62, 38, 180.83, 'Grinder 3 had bearing noise issues requiring adjustment.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 2, 89.70, 1749, 1950, 38, 25, 110.83, 'Better day with routine changeovers.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 3, 87.30, 1702, 1950, 48, 30, 140.00, 'Bean quality variance caused some adjustments.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 4, 91.50, 1784, 1950, 28, 20, 81.67, 'Good throughput on espresso grind setting.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 5, 86.80, 1693, 1950, 52, 33, 151.67, 'Burr alignment check required mid-shift.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 6, 90.20, 1759, 1950, 35, 24, 102.08, 'Standard operation day.'),
    ('a0000001-0000-0000-0000-000000000006', CURRENT_DATE - 7, 88.40, 1724, 1950, 45, 28, 131.25, 'Some bean inconsistency from upstream roasting.'),

    -- ============ GRINDER 4 - 7 days (target_output=1950, new asset) ============
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 1, 87.18, 1700, 1950, 50, 35, 145.83, 'Grinder 4 running at moderate pace. Feed rate adjustment needed mid-shift.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 2, 91.30, 1780, 1950, 30, 22, 87.50, 'Good performance on medium grind setting.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 3, 85.40, 1665, 1950, 58, 40, 169.17, 'Hopper feed issues caused intermittent slowdowns.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 4, 89.70, 1749, 1950, 38, 28, 110.83, 'Steady grinding with minor adjustments.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 5, 93.20, 1817, 1950, 22, 18, 64.17, 'Excellent day. Consistent particle size throughout.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 6, 86.50, 1687, 1950, 52, 35, 151.67, 'Bean moisture caused grind inconsistency.'),
    ('a0000001-0000-0000-0000-000000000007', CURRENT_DATE - 7, 90.80, 1771, 1950, 32, 24, 93.33, 'Solid start to the week.'),

    -- ============ GRINDER 5 - 7 days (target_output=1950) ============
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 1, 82.50, 1608, 1950, 72, 35, 210.00, 'Grinder 5 had mechanical issues with burr assembly.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 2, 88.30, 1722, 1950, 45, 28, 131.25, 'Running better. Minor mechanical adjustment needed mid-shift.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 3, 76.80, 1498, 1950, 98, 45, 285.83, 'Rough day. Burr replacement required after vibration alarm.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 4, 91.20, 1778, 1950, 32, 22, 93.33, 'Solid performance. Standard changeover for medium roast batch.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 5, 85.60, 1669, 1950, 58, 30, 169.17, 'Bean hopper ran empty twice waiting on roaster output.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 6, 89.40, 1743, 1950, 40, 25, 116.67, 'Good day. Multiple changeovers for different grind sizes.'),
    ('a0000001-0000-0000-0000-000000000014', CURRENT_DATE - 7, 87.10, 1698, 1950, 52, 28, 151.67, 'Steady performance with minor mechanical hiccups.'),

    -- ============ FILLER LINE A - 7 days (target_output=4600) ============
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 1, 72.50, 3335, 4600, 95, 120, 197.92, 'Filler A experiencing valve sticking issues. Multiple stoppages.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 2, 92.30, 4246, 4600, 28, 45, 58.33, 'Strong filling performance. New bag stock feeding well.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 3, 78.60, 3616, 4600, 82, 95, 170.83, 'Valve sticking issue continued. Cleaned and reseated during break.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 4, 95.10, 4374, 4600, 15, 35, 31.25, 'Excellent recovery. K-Cup filling mode achieving target weights.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 5, 88.40, 4066, 4600, 42, 58, 87.50, 'Some jamming issues with new bag material.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 6, 91.20, 4195, 4600, 32, 48, 66.67, 'Solid performance on 2lb bag line.'),
    ('a0000001-0000-0000-0000-000000000008', CURRENT_DATE - 7, 89.80, 4131, 4600, 38, 52, 79.17, 'Good week opener for filling operations.'),

    -- ============ FILLER LINE B - 7 days (target_output=4600) ============
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 1, 89.20, 4650, 4600, 42, 65, 87.50, 'Outstanding day on 2lb bag line. Weight variance within spec. Exceeded daily target.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 2, 91.80, 4223, 4600, 30, 50, 62.50, 'Steady filling. Degassing valve placement accuracy improved.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 3, 94.30, 4338, 4600, 18, 35, 37.50, 'Outstanding day. Bag sealing quality excellent throughout.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 4, 87.50, 4025, 4600, 48, 72, 100.00, 'Film tension issues caused periodic stops.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 5, 90.60, 4168, 4600, 35, 55, 72.92, 'Consistent filling with minor adjustments.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 6, 93.10, 4283, 4600, 22, 40, 45.83, 'Excellent bag weight consistency.'),
    ('a0000001-0000-0000-0000-000000000009', CURRENT_DATE - 7, 88.90, 4089, 4600, 40, 60, 83.33, 'Good start to the week on 1lb bag line.'),

    -- ============ FILLER LINE C - 7 days (target_output=4000, new asset) ============
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 1, 80.00, 3200, 4000, 62, 75, 129.17, 'Filler C had bag feed issues on specialty blend line. Throughput reduced.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 2, 88.50, 3540, 4000, 38, 55, 79.17, 'Good output with minor feed adjustments.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 3, 93.20, 3728, 4000, 20, 35, 41.67, 'Outstanding day. New nozzle configuration working well.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 4, 86.80, 3472, 4000, 45, 62, 93.75, 'Bag feed alignment needed adjustment mid-shift.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 5, 90.50, 3620, 4000, 32, 48, 66.67, 'Steady performance on single-serve pods.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 6, 94.00, 3760, 4000, 15, 30, 31.25, 'Excellent run. Minimal downtime.'),
    ('a0000001-0000-0000-0000-000000000010', CURRENT_DATE - 7, 87.30, 3492, 4000, 42, 58, 87.50, 'Some initial startup delays but recovered well.'),

    -- ============ PACKAGING LINE 1 - 7 days (target_output=6200) ============
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 1, 89.50, 5549, 6200, 42, 65, 66.50, 'Good day on Packaging Line 1. Minor label changeover delays.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 2, 94.80, 5878, 6200, 18, 42, 28.50, 'Outstanding day. Holiday blend cases flowing smoothly.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 3, 79.30, 4917, 6200, 88, 145, 139.33, 'Case erector jam caused significant downtime.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 4, 92.50, 5735, 6200, 25, 55, 39.58, 'Strong recovery. Automated case packing running efficiently.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 5, 87.20, 5406, 6200, 52, 78, 82.33, 'Multiple SKU changeovers slowed throughput.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 6, 91.80, 5692, 6200, 30, 52, 47.50, 'Consistent packaging output.'),
    ('a0000001-0000-0000-0000-000000000011', CURRENT_DATE - 7, 88.90, 5512, 6200, 45, 68, 71.25, 'Solid week start with routine changeovers.'),

    -- ============ PACKAGING LINE 2 - 7 days (target_output=6200) ============
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 1, 88.90, 6300, 6200, 45, 78, 71.25, 'Excellent day on wholesale pack line. Exceeded daily target. Case sealing quality excellent.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 2, 91.20, 5654, 6200, 32, 60, 50.67, 'Consistent throughput. Shrink wrap tension optimized.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 3, 93.50, 5797, 6200, 20, 45, 31.67, 'Excellent run on bulk case packing.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 4, 86.80, 5382, 6200, 55, 85, 87.08, 'Labeler jam caused extended changeover.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 5, 90.50, 5611, 6200, 35, 62, 55.42, 'Good recovery from yesterday issues.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 6, 94.20, 5840, 6200, 15, 38, 23.75, 'Outstanding day. Minimal changeovers needed.'),
    ('a0000001-0000-0000-0000-000000000012', CURRENT_DATE - 7, 87.50, 5425, 6200, 48, 72, 76.00, 'Moderate start to the week.'),

    -- ============ PACKAGING LINE 3 - 7 days (target_output=5600, new asset) ============
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 1, 87.50, 4900, 5600, 55, 80, 87.08, 'Packaging Line 3 running slightly below target. Film feed alignment.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 2, 90.20, 5051, 5600, 38, 62, 60.17, 'Good performance. Carton sealing quality improved.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 3, 85.80, 4805, 5600, 62, 95, 98.17, 'Label applicator needed recalibration mid-shift.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 4, 91.40, 5118, 5600, 30, 50, 47.50, 'Strong day. Case erector running smoothly.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 5, 88.60, 4962, 5600, 45, 70, 71.25, 'Moderate output with some changeover delays.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 6, 92.80, 5197, 5600, 22, 42, 34.83, 'Excellent performance on retail pack line.'),
    ('a0000001-0000-0000-0000-000000000013', CURRENT_DATE - 7, 86.40, 4838, 5600, 55, 78, 87.08, 'Some case erector issues at start of shift.')
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
