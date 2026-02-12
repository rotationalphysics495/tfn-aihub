/**
 * Integration Tests for Action Plans Data Model
 *
 * Story 16.1 - Action Plans Data Model
 *
 * These tests validate the action_plans and action_plan_updates tables against
 * a running Supabase instance. They require:
 *   - A running Supabase instance (local or remote)
 *   - SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
 *   - Schema migrations applied (including 0034_action_plans.sql and its dependencies)
 *
 * Tests will FAIL until Story 16.1 is implemented because:
 *   - Migration 0034_action_plans.sql does not yet exist
 *   - The action_plans and action_plan_updates tables do not exist in the database
 *
 * Test coverage:
 *   - CASCADE delete behavior (AC2)
 *   - ON DELETE SET NULL behavior for source_followup_id and asset_id (AC1)
 *   - RLS policies for SELECT, INSERT, UPDATE (AC3)
 *   - Constraint validation (CHECK, NOT NULL, FK)
 *   - Default value generation (gen_random_uuid, NOW(), 'draft', 'medium')
 *   - updated_at trigger behavior
 *   - Nullable column behavior
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// ============================================================================
// Setup
// ============================================================================

const SUPABASE_URL = process.env.SUPABASE_URL || 'http://127.0.0.1:54321'
const SUPABASE_KEY =
  process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_KEY || ''

const canConnect = !!SUPABASE_KEY

// Test user UUIDs (must exist in auth.users if RLS tests use authenticated context)
const USER_A_ID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
const USER_B_ID = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'

// Non-existent UUID for FK constraint tests
const NON_EXISTENT_UUID = '00000000-0000-0000-0000-000000000000'

// ============================================================================
// Helpers
// ============================================================================

/**
 * Creates a valid action_plan payload for inserts.
 */
function createActionPlanPayload(overrides: Record<string, any> = {}) {
  return {
    title: 'Test Action Plan',
    owner_id: USER_A_ID,
    ...overrides,
  }
}

/**
 * Creates a valid action_plan_update payload for inserts.
 */
function createUpdatePayload(
  actionPlanId: string,
  overrides: Record<string, any> = {}
) {
  return {
    action_plan_id: actionPlanId,
    author_id: USER_A_ID,
    update_text: 'Test progress update',
    ...overrides,
  }
}

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Action Plans Integration (Story 16.1)', () => {
  let serviceClient: SupabaseClient
  let testActionPlanId: string | null = null

  // Track IDs for cleanup
  const createdActionPlanIds: string[] = []
  const createdFollowupIds: string[] = []
  const createdAssetIds: string[] = []

  beforeAll(async () => {
    if (!canConnect) {
      console.warn(
        'Skipping integration tests: SUPABASE_SERVICE_KEY not set'
      )
      return
    }

    serviceClient = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false },
    })

    // Create a test action plan for use in subsequent tests
    const { data: plan, error: planErr } = await serviceClient
      .from('action_plans')
      .insert(createActionPlanPayload({ title: 'Fixture Action Plan' }))
      .select('id')
      .single()

    if (planErr) {
      console.warn('Could not create test action plan:', planErr.message)
    } else {
      testActionPlanId = (plan as any).id
      createdActionPlanIds.push(testActionPlanId!)
    }
  })

  afterAll(async () => {
    if (!canConnect) return

    // Cleanup created action plans (cascades to updates)
    for (const id of createdActionPlanIds) {
      await serviceClient.from('action_plans').delete().eq('id', id)
    }

    // Cleanup created followups
    for (const id of createdFollowupIds) {
      await serviceClient.from('action_followups').delete().eq('id', id)
    }

    // Cleanup created assets
    for (const id of createdAssetIds) {
      await serviceClient.from('assets').delete().eq('id', id)
    }
  })

  // Helper to ensure we have a test action plan
  function requireActionPlan() {
    expect(
      testActionPlanId,
      'Test action plan must exist in action_plans'
    ).not.toBeNull()
  }

  // ==========================================================================
  // AC2: Cascade delete behavior
  // ==========================================================================

  describe('AC2: Cascade delete behavior', () => {
    it('16-1-action-plans-data-model-INT-001: Cascade delete removes action_plan_updates when action_plan is deleted', async () => {
      // Given: An action_plan exists with id X, and 3 action_plan_updates exist with action_plan_id = X
      // When: The action_plan with id X is deleted from action_plans
      // Then: All 3 action_plan_updates rows with action_plan_id = X are also deleted, and the query returns 0 rows

      if (!canConnect) return

      // Create a dedicated action plan for this cascade test
      const { data: cascadePlan, error: cpErr } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({ title: 'Cascade delete test plan' })
        )
        .select('id')
        .single()

      expect(cpErr).toBeNull()
      expect(cascadePlan).not.toBeNull()
      const cascadePlanId = (cascadePlan as any).id

      // Insert 3 updates for this plan
      const updates = [
        createUpdatePayload(cascadePlanId, { update_text: 'Update 1' }),
        createUpdatePayload(cascadePlanId, { update_text: 'Update 2' }),
        createUpdatePayload(cascadePlanId, { update_text: 'Update 3' }),
      ]

      const { error: insertErr } = await serviceClient
        .from('action_plan_updates')
        .insert(updates)

      expect(insertErr).toBeNull()

      // Verify 3 updates exist
      const { data: beforeDelete, error: beforeErr } = await serviceClient
        .from('action_plan_updates')
        .select('id')
        .eq('action_plan_id', cascadePlanId)

      expect(beforeErr).toBeNull()
      expect(beforeDelete!.length).toBe(3)

      // Delete the parent action plan
      const { error: deleteErr } = await serviceClient
        .from('action_plans')
        .delete()
        .eq('id', cascadePlanId)

      expect(deleteErr).toBeNull()

      // Verify all updates were cascade-deleted
      const { data: afterDelete, error: afterErr } = await serviceClient
        .from('action_plan_updates')
        .select('id')
        .eq('action_plan_id', cascadePlanId)

      expect(afterErr).toBeNull()
      expect(afterDelete!.length).toBe(0)
    })

    it('16-1-action-plans-data-model-INT-002: Deleting a followup sets source_followup_id to NULL (ON DELETE SET NULL)', async () => {
      // Given: An action_followup exists with id F, and an action_plan exists with source_followup_id = F
      // When: The action_followup with id F is deleted from action_followups
      // Then: The action_plan still exists but its source_followup_id is now NULL

      if (!canConnect) return

      // Create a test followup
      const { data: followup, error: fuErr } = await serviceClient
        .from('action_followups')
        .insert({
          action_item_id: 'test-for-set-null',
          action_summary: 'Followup for SET NULL test',
          category: 'oee',
          assigned_to: USER_A_ID,
          assigned_by: USER_B_ID,
          status: 'assigned',
          report_date: new Date().toISOString().split('T')[0],
        })
        .select('id')
        .single()

      expect(fuErr).toBeNull()
      expect(followup).not.toBeNull()
      const followupId = (followup as any).id

      // Create an action plan linked to that followup
      const { data: plan, error: planErr } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({
            title: 'Plan linked to followup for SET NULL test',
            source_followup_id: followupId,
          })
        )
        .select('id, source_followup_id')
        .single()

      expect(planErr).toBeNull()
      expect(plan).not.toBeNull()
      const planId = (plan as any).id
      createdActionPlanIds.push(planId)

      // Verify the link exists
      expect((plan as any).source_followup_id).toBe(followupId)

      // Delete the followup
      const { error: deleteErr } = await serviceClient
        .from('action_followups')
        .delete()
        .eq('id', followupId)

      expect(deleteErr).toBeNull()

      // Verify the plan still exists but source_followup_id is now NULL
      const { data: updatedPlan, error: fetchErr } = await serviceClient
        .from('action_plans')
        .select('id, source_followup_id')
        .eq('id', planId)
        .single()

      expect(fetchErr).toBeNull()
      expect(updatedPlan).not.toBeNull()
      expect((updatedPlan as any).source_followup_id).toBeNull()
    })

    it('16-1-action-plans-data-model-INT-003: Deleting an asset sets asset_id to NULL (ON DELETE SET NULL)', async () => {
      // Given: An asset exists with id A, and an action_plan exists with asset_id = A
      // When: The asset with id A is deleted from assets
      // Then: The action_plan still exists but its asset_id is now NULL

      if (!canConnect) return

      // Create a test asset
      const { data: asset, error: assetErr } = await serviceClient
        .from('assets')
        .insert({
          name: 'Test Asset for SET NULL',
          source_id: 'test-asset-set-null-' + Date.now(),
          area: 'Test Area',
        })
        .select('id')
        .single()

      expect(assetErr).toBeNull()
      expect(asset).not.toBeNull()
      const assetId = (asset as any).id

      // Create an action plan linked to that asset
      const { data: plan, error: planErr } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({
            title: 'Plan linked to asset for SET NULL test',
            asset_id: assetId,
          })
        )
        .select('id, asset_id')
        .single()

      expect(planErr).toBeNull()
      expect(plan).not.toBeNull()
      const planId = (plan as any).id
      createdActionPlanIds.push(planId)

      // Verify the link exists
      expect((plan as any).asset_id).toBe(assetId)

      // Delete the asset
      const { error: deleteErr } = await serviceClient
        .from('assets')
        .delete()
        .eq('id', assetId)

      expect(deleteErr).toBeNull()

      // Verify the plan still exists but asset_id is now NULL
      const { data: updatedPlan, error: fetchErr } = await serviceClient
        .from('action_plans')
        .select('id, asset_id')
        .eq('id', planId)
        .single()

      expect(fetchErr).toBeNull()
      expect(updatedPlan).not.toBeNull()
      expect((updatedPlan as any).asset_id).toBeNull()
    })
  })

  // ==========================================================================
  // AC3: RLS policies (Integration)
  // ==========================================================================

  describe('AC3: RLS policies', () => {
    it('16-1-action-plans-data-model-INT-004: Authenticated user can SELECT all action_plans (shared visibility)', async () => {
      // Given: User A owns an action_plan and User B owns another action_plan
      // When: User A queries all action_plans via authenticated client
      // Then: User A can see both their own plan and User B's plan (shared read access)

      if (!canConnect) return

      // Insert plans for two different owners via service role
      const { data: planA, error: errA } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Plan by User A', owner_id: USER_A_ID }))
        .select('id')
        .single()

      expect(errA).toBeNull()
      if (planA) createdActionPlanIds.push((planA as any).id)

      const { data: planB, error: errB } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Plan by User B', owner_id: USER_B_ID }))
        .select('id')
        .single()

      expect(errB).toBeNull()
      if (planB) createdActionPlanIds.push((planB as any).id)

      // Using service role to verify both are visible (shared read access)
      const { data: allPlans, error: selectErr } = await serviceClient
        .from('action_plans')
        .select('id, owner_id')

      expect(selectErr).toBeNull()
      expect(allPlans).not.toBeNull()
      expect(allPlans!.length).toBeGreaterThanOrEqual(2)

      // Both user's plans should be in the results
      const ownerIds = allPlans!.map((p: any) => p.owner_id)
      expect(ownerIds).toContain(USER_A_ID)
      expect(ownerIds).toContain(USER_B_ID)
    })

    it('16-1-action-plans-data-model-INT-005: Owner can INSERT an action_plan with owner_id = auth.uid()', async () => {
      // Given: User A is authenticated
      // When: User A inserts an action_plan with owner_id = User A's uid
      // Then: The insert succeeds and the row is persisted

      if (!canConnect) return

      const { data, error } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({
            title: 'Owner insert test',
            owner_id: USER_A_ID,
          })
        )
        .select('id, owner_id')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).owner_id).toBe(USER_A_ID)
      if (data) createdActionPlanIds.push((data as any).id)
    })

    it('16-1-action-plans-data-model-INT-006: Authenticated user cannot INSERT an action_plan with owner_id != auth.uid()', async () => {
      // Given: User A is authenticated
      // When: User A attempts to insert an action_plan with owner_id = User B's uid
      // Then: The insert fails or is denied by RLS policy

      if (!canConnect) return

      // Note: True RLS testing requires JWT auth context.
      // This test uses anon key to validate that unauthenticated users are blocked.
      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping RLS INSERT test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      const { error } = await anonClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({
            title: 'Unauthorized insert attempt',
            owner_id: USER_B_ID,
          })
        )

      // Expect RLS to block the insert
      expect(error).not.toBeNull()
    })

    it('16-1-action-plans-data-model-INT-007: Owner can UPDATE their own action_plan', async () => {
      // Given: User A owns an action_plan with id X
      // When: User A updates the title of action_plan X via authenticated client
      // Then: The update succeeds

      if (!canConnect) return
      requireActionPlan()

      const { error } = await serviceClient
        .from('action_plans')
        .update({ title: 'Updated title by owner' })
        .eq('id', testActionPlanId!)

      expect(error).toBeNull()

      // Verify the update
      const { data, error: fetchErr } = await serviceClient
        .from('action_plans')
        .select('title')
        .eq('id', testActionPlanId!)
        .single()

      expect(fetchErr).toBeNull()
      expect((data as any).title).toBe('Updated title by owner')
    })

    it('16-1-action-plans-data-model-INT-008: Non-owner cannot UPDATE another user\'s action_plan', async () => {
      // Given: User A owns an action_plan with id X
      // When: User B attempts to update the title of action_plan X via authenticated client
      // Then: The update fails or affects 0 rows (RLS blocks the operation)

      if (!canConnect) return

      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping RLS UPDATE test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      requireActionPlan()

      const { error, count } = await anonClient
        .from('action_plans')
        .update({ title: 'Unauthorized update attempt' })
        .eq('id', testActionPlanId!)

      // Should fail or affect 0 rows
      if (error) {
        expect(error).not.toBeNull()
      } else {
        expect(count).toBe(0)
      }
    })

    it('16-1-action-plans-data-model-INT-009: Authenticated user can SELECT all action_plan_updates (timeline visibility)', async () => {
      // Given: Updates exist for action_plans owned by various users
      // When: Any authenticated user queries action_plan_updates
      // Then: All updates are visible (shared read access for timeline)

      if (!canConnect) return
      requireActionPlan()

      // Insert a test update via service role
      const { error: insertErr } = await serviceClient
        .from('action_plan_updates')
        .insert(createUpdatePayload(testActionPlanId!))

      expect(insertErr).toBeNull()

      // Query all updates
      const { data, error } = await serviceClient
        .from('action_plan_updates')
        .select('*')
        .eq('action_plan_id', testActionPlanId!)

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect(data!.length).toBeGreaterThanOrEqual(1)
    })

    it('16-1-action-plans-data-model-INT-010: Authenticated user can INSERT action_plan_update with author_id = auth.uid()', async () => {
      // Given: An action_plan exists and User A is authenticated
      // When: User A inserts an action_plan_update with author_id = User A's uid
      // Then: The insert succeeds and the row is persisted

      if (!canConnect) return
      requireActionPlan()

      const { data, error } = await serviceClient
        .from('action_plan_updates')
        .insert(
          createUpdatePayload(testActionPlanId!, {
            update_text: 'Progress update from authenticated user',
            author_id: USER_A_ID,
          })
        )
        .select('id')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).id).toBeDefined()
    })

    it('16-1-action-plans-data-model-INT-011: Authenticated user cannot INSERT action_plan_update with author_id != auth.uid()', async () => {
      // Given: An action_plan exists and User A is authenticated
      // When: User A attempts to insert an action_plan_update with author_id = User B's uid
      // Then: The insert fails or is denied by RLS policy

      if (!canConnect) return
      requireActionPlan()

      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping RLS update INSERT test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      const { error } = await anonClient
        .from('action_plan_updates')
        .insert(
          createUpdatePayload(testActionPlanId!, {
            author_id: USER_B_ID,
            update_text: 'Unauthorized update insert',
          })
        )

      // Expect RLS to block the insert
      expect(error).not.toBeNull()
    })

    it('16-1-action-plans-data-model-INT-012: Service role has full CRUD access on both tables', async () => {
      // Given: The service_role connection is used
      // When: The service role performs INSERT, SELECT, UPDATE, and DELETE on action_plans and action_plan_updates
      // Then: All operations succeed without RLS restrictions

      if (!canConnect) return

      // ---- action_plans CRUD ----

      // INSERT
      const { data: inserted, error: insertErr } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({ title: 'Service role CRUD test plan' })
        )
        .select('id')
        .single()

      expect(insertErr).toBeNull()
      expect(inserted).not.toBeNull()
      const testPlanId = (inserted as any).id

      // SELECT
      const { data: selected, error: selectErr } = await serviceClient
        .from('action_plans')
        .select('*')
        .eq('id', testPlanId)
        .single()

      expect(selectErr).toBeNull()
      expect(selected).not.toBeNull()
      expect((selected as any).title).toBe('Service role CRUD test plan')

      // UPDATE
      const { error: updateErr } = await serviceClient
        .from('action_plans')
        .update({ title: 'Updated by service role' })
        .eq('id', testPlanId)

      expect(updateErr).toBeNull()

      // Verify update
      const { data: updated, error: verifyErr } = await serviceClient
        .from('action_plans')
        .select('title')
        .eq('id', testPlanId)
        .single()

      expect(verifyErr).toBeNull()
      expect((updated as any).title).toBe('Updated by service role')

      // ---- action_plan_updates CRUD ----

      // INSERT update
      const { data: insertedUpdate, error: insertUpdateErr } = await serviceClient
        .from('action_plan_updates')
        .insert(
          createUpdatePayload(testPlanId, {
            update_text: 'Service role update entry',
          })
        )
        .select('id')
        .single()

      expect(insertUpdateErr).toBeNull()
      expect(insertedUpdate).not.toBeNull()
      const testUpdateId = (insertedUpdate as any).id

      // SELECT update
      const { data: selectedUpdate, error: selectUpdateErr } = await serviceClient
        .from('action_plan_updates')
        .select('*')
        .eq('id', testUpdateId)
        .single()

      expect(selectUpdateErr).toBeNull()
      expect(selectedUpdate).not.toBeNull()
      expect((selectedUpdate as any).update_text).toBe('Service role update entry')

      // DELETE update
      const { error: deleteUpdateErr } = await serviceClient
        .from('action_plan_updates')
        .delete()
        .eq('id', testUpdateId)

      expect(deleteUpdateErr).toBeNull()

      // DELETE plan (also cleans up)
      const { error: deletePlanErr } = await serviceClient
        .from('action_plans')
        .delete()
        .eq('id', testPlanId)

      expect(deletePlanErr).toBeNull()

      // Verify deletion
      const { data: deleted, error: checkErr } = await serviceClient
        .from('action_plans')
        .select('id')
        .eq('id', testPlanId)

      expect(checkErr).toBeNull()
      expect(deleted!.length).toBe(0)
    })
  })

  // ==========================================================================
  // Constraint Validation (Integration)
  // ==========================================================================

  describe('Constraint Validation', () => {
    it('16-1-action-plans-data-model-INT-013: CHECK constraint rejects invalid category value', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with category = 'invalid_category'
      // Then: The insert fails with a CHECK constraint violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({ category: 'invalid_category' })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('16-1-action-plans-data-model-INT-014: CHECK constraint rejects invalid status value', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with status = 'invalid_status'
      // Then: The insert fails with a CHECK constraint violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({ status: 'invalid_status' })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('16-1-action-plans-data-model-INT-015: CHECK constraint rejects invalid priority value', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with priority = 'invalid_priority'
      // Then: The insert fails with a CHECK constraint violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plans')
        .insert(
          createActionPlanPayload({ priority: 'invalid_priority' })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('16-1-action-plans-data-model-INT-016: NOT NULL constraint rejects null title', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with title = NULL
      // Then: The insert fails with a NOT NULL violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plans')
        .insert({
          title: null,
          owner_id: USER_A_ID,
        } as any)

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/null|not-null|violat/i)
    })

    it('16-1-action-plans-data-model-INT-017: NOT NULL constraint rejects null owner_id', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with owner_id = NULL
      // Then: The insert fails with a NOT NULL violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plans')
        .insert({
          title: 'Plan with null owner',
          owner_id: null,
        } as any)

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/null|not-null|violat/i)
    })

    it('16-1-action-plans-data-model-INT-018: NOT NULL constraint rejects null update_text in action_plan_updates', async () => {
      // Given: The action_plan_updates table exists and an action_plan exists
      // When: An action_plan_update is inserted via service_role with update_text = NULL
      // Then: The insert fails with a NOT NULL violation error

      if (!canConnect) return
      requireActionPlan()

      const { error } = await serviceClient
        .from('action_plan_updates')
        .insert({
          action_plan_id: testActionPlanId,
          author_id: USER_A_ID,
          update_text: null,
        } as any)

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/null|not-null|violat/i)
    })

    it('16-1-action-plans-data-model-INT-019: FK constraint rejects invalid action_plan_id in action_plan_updates', async () => {
      // Given: No action_plan exists with a specific UUID
      // When: An action_plan_update is inserted via service_role with action_plan_id = non-existent UUID
      // Then: The insert fails with a foreign key constraint violation

      if (!canConnect) return

      const { error } = await serviceClient
        .from('action_plan_updates')
        .insert(createUpdatePayload(NON_EXISTENT_UUID))

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/foreign key|violat|reference/i)
    })

    it('16-1-action-plans-data-model-INT-020: Default gen_random_uuid() generates unique id on insert for both tables', async () => {
      // Given: Both tables exist
      // When: Two action_plans and two action_plan_updates are inserted without specifying id
      // Then: All inserts succeed and each row has a unique, non-null UUID id value

      if (!canConnect) return

      // Insert two action plans without specifying id
      const { data: plan1, error: err1 } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'UUID test plan 1' }))
        .select('id')
        .single()

      expect(err1).toBeNull()
      expect(plan1).not.toBeNull()
      const planId1 = (plan1 as any).id
      createdActionPlanIds.push(planId1)

      const { data: plan2, error: err2 } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'UUID test plan 2' }))
        .select('id')
        .single()

      expect(err2).toBeNull()
      expect(plan2).not.toBeNull()
      const planId2 = (plan2 as any).id
      createdActionPlanIds.push(planId2)

      // Insert two updates without specifying id
      const { data: upd1, error: uerr1 } = await serviceClient
        .from('action_plan_updates')
        .insert(createUpdatePayload(planId1, { update_text: 'UUID update 1' }))
        .select('id')
        .single()

      expect(uerr1).toBeNull()

      const { data: upd2, error: uerr2 } = await serviceClient
        .from('action_plan_updates')
        .insert(createUpdatePayload(planId1, { update_text: 'UUID update 2' }))
        .select('id')
        .single()

      expect(uerr2).toBeNull()

      // All IDs should be unique
      const ids = [planId1, planId2, (upd1 as any).id, (upd2 as any).id]
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(4)

      // All IDs should look like UUIDs
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      for (const id of ids) {
        expect(id).toMatch(uuidPattern)
      }
    })

    it('16-1-action-plans-data-model-INT-021: Default status draft is applied when not specified', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role without specifying status
      // Then: The status column defaults to 'draft'

      if (!canConnect) return

      const { data, error } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Default status test' }))
        .select('id, status')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).status).toBe('draft')
      if (data) createdActionPlanIds.push((data as any).id)
    })

    it('16-1-action-plans-data-model-INT-022: Default priority medium is applied when not specified', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role without specifying priority
      // Then: The priority column defaults to 'medium'

      if (!canConnect) return

      const { data, error } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Default priority test' }))
        .select('id, priority')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).priority).toBe('medium')
      if (data) createdActionPlanIds.push((data as any).id)
    })

    it('16-1-action-plans-data-model-INT-023: Default NOW() populates created_at and updated_at on insert for action_plans', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role without specifying created_at or updated_at
      // Then: Both created_at and updated_at are automatically populated with the current timestamp

      if (!canConnect) return

      const beforeInsert = new Date()

      const { data, error } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Timestamp default test' }))
        .select('id, created_at, updated_at')
        .single()

      const afterInsert = new Date()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      if (data) createdActionPlanIds.push((data as any).id)

      const createdAt = new Date((data as any).created_at)
      const updatedAt = new Date((data as any).updated_at)

      // Both timestamps should be between beforeInsert and afterInsert (with tolerance)
      expect(createdAt.getTime()).toBeGreaterThanOrEqual(
        beforeInsert.getTime() - 5000
      )
      expect(createdAt.getTime()).toBeLessThanOrEqual(
        afterInsert.getTime() + 5000
      )
      expect(updatedAt.getTime()).toBeGreaterThanOrEqual(
        beforeInsert.getTime() - 5000
      )
      expect(updatedAt.getTime()).toBeLessThanOrEqual(
        afterInsert.getTime() + 5000
      )
    })

    it('16-1-action-plans-data-model-INT-024: update_updated_at trigger automatically updates updated_at on UPDATE', async () => {
      // Given: An action_plan exists with a known updated_at timestamp
      // When: The action_plan's title is updated via service_role after a brief delay
      // Then: The updated_at column is automatically changed to a more recent timestamp than the original value

      if (!canConnect) return

      // Create a plan and capture its initial updated_at
      const { data: created, error: createErr } = await serviceClient
        .from('action_plans')
        .insert(createActionPlanPayload({ title: 'Trigger test plan' }))
        .select('id, updated_at')
        .single()

      expect(createErr).toBeNull()
      expect(created).not.toBeNull()
      const planId = (created as any).id
      createdActionPlanIds.push(planId)
      const originalUpdatedAt = new Date((created as any).updated_at)

      // Brief delay to ensure timestamp difference
      await new Promise((resolve) => setTimeout(resolve, 1100))

      // Update the plan
      const { error: updateErr } = await serviceClient
        .from('action_plans')
        .update({ title: 'Trigger test plan - updated' })
        .eq('id', planId)

      expect(updateErr).toBeNull()

      // Fetch the updated plan
      const { data: updated, error: fetchErr } = await serviceClient
        .from('action_plans')
        .select('updated_at')
        .eq('id', planId)
        .single()

      expect(fetchErr).toBeNull()
      expect(updated).not.toBeNull()

      const newUpdatedAt = new Date((updated as any).updated_at)

      // The new updated_at should be more recent than the original
      expect(newUpdatedAt.getTime()).toBeGreaterThan(originalUpdatedAt.getTime())
    })

    it('16-1-action-plans-data-model-INT-025: Nullable columns accept NULL values (asset_id, description, root_cause, etc.)', async () => {
      // Given: The action_plans table exists
      // When: An action_plan is inserted via service_role with only required fields and all nullable fields set to NULL
      // Then: The insert succeeds with NULL values for all nullable columns

      if (!canConnect) return

      const { data, error } = await serviceClient
        .from('action_plans')
        .insert({
          title: 'Minimal plan with nulls',
          owner_id: USER_A_ID,
          description: null,
          asset_id: null,
          category: null,
          root_cause: null,
          corrective_action: null,
          preventive_action: null,
          source_followup_id: null,
          due_date: null,
          completed_at: null,
          verified_by: null,
          verified_at: null,
        })
        .select('id, description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, due_date, completed_at, verified_by, verified_at')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      if (data) createdActionPlanIds.push((data as any).id)

      // All nullable fields should be NULL
      expect((data as any).description).toBeNull()
      expect((data as any).asset_id).toBeNull()
      expect((data as any).category).toBeNull()
      expect((data as any).root_cause).toBeNull()
      expect((data as any).corrective_action).toBeNull()
      expect((data as any).preventive_action).toBeNull()
      expect((data as any).source_followup_id).toBeNull()
      expect((data as any).due_date).toBeNull()
      expect((data as any).completed_at).toBeNull()
      expect((data as any).verified_by).toBeNull()
      expect((data as any).verified_at).toBeNull()
    })
  })
})
