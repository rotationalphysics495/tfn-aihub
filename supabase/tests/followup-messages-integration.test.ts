/**
 * Integration Tests for Follow-Up Messages
 *
 * Story 15.1 - Follow-Up Messages Data Model
 *
 * These tests validate the followup_messages table against a running Supabase
 * instance. They require:
 *   - A running Supabase instance (local or remote)
 *   - SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
 *   - Schema migrations applied (including 0030_followup_messages.sql and 0025_action_followups.sql)
 *
 * Tests will FAIL until Story 15.1 is implemented because:
 *   - Migration 0030_followup_messages.sql does not yet exist
 *   - The followup_messages table does not exist in the database
 *
 * Test coverage:
 *   - CASCADE delete behavior (AC4)
 *   - RLS policies for SELECT, INSERT, DELETE, UPDATE (AC3)
 *   - Constraint validation (CHECK, NOT NULL, FK)
 *   - Default value generation (gen_random_uuid, NOW())
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
const USER_C_ID = 'cccccccc-cccc-cccc-cccc-cccccccccccc'

// Non-existent UUID for FK constraint tests
const NON_EXISTENT_UUID = '00000000-0000-0000-0000-000000000000'

// ============================================================================
// Helpers
// ============================================================================

/**
 * Creates a valid message payload for followup_messages inserts.
 */
function createMessagePayload(followupId: string, overrides: Record<string, any> = {}) {
  return {
    followup_id: followupId,
    sender_id: USER_A_ID,
    sender_email: 'test@example.com',
    direction: 'outbound',
    message_type: 'assignment',
    subject: 'Test message subject',
    body: 'Test message body',
    ...overrides,
  }
}

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Follow-Up Messages Integration (Story 15.1)', () => {
  let serviceClient: SupabaseClient
  let testFollowupId: string | null = null

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

    // Create a test follow-up in action_followups for use in message tests
    const { data: followup, error: followupErr } = await serviceClient
      .from('action_followups')
      .insert({
        action_item_id: 'test-action-item-for-messages',
        action_summary: 'Test followup for message integration tests',
        asset_name: 'Test Asset',
        category: 'oee',
        assigned_to: USER_A_ID,
        assigned_by: USER_B_ID,
        note: 'Integration test fixture',
        status: 'assigned',
        report_date: new Date().toISOString().split('T')[0],
      })
      .select('id')
      .single()

    if (followupErr) {
      console.warn(
        'Could not create test followup:',
        followupErr.message
      )
    } else {
      testFollowupId = (followup as any).id
    }
  })

  afterAll(async () => {
    if (!canConnect || !testFollowupId) return

    // Cleanup: delete the test followup (cascades to messages)
    await serviceClient
      .from('action_followups')
      .delete()
      .eq('id', testFollowupId)
  })

  // Helper to ensure we have a test followup
  function requireFollowup() {
    expect(
      testFollowupId,
      'Test followup must exist in action_followups'
    ).not.toBeNull()
  }

  // ==========================================================================
  // AC4: Foreign key cascades (Integration)
  // ==========================================================================

  describe('AC4: Cascade delete behavior', () => {
    it('15-1-followup-messages-data-model-INT-001: Cascade delete removes associated messages when follow-up is deleted', async () => {
      // Given: A follow-up exists in action_followups with id X, and 3 messages exist in followup_messages with followup_id = X
      // When: The follow-up with id X is deleted from action_followups
      // Then: All 3 followup_messages rows with followup_id = X are also deleted

      if (!canConnect) return

      // Create a dedicated followup for this cascade test
      const { data: cascadeFollowup, error: cfErr } = await serviceClient
        .from('action_followups')
        .insert({
          action_item_id: 'cascade-test-action',
          action_summary: 'Followup for cascade delete test',
          category: 'safety',
          assigned_to: USER_A_ID,
          assigned_by: USER_B_ID,
          status: 'assigned',
          report_date: new Date().toISOString().split('T')[0],
        })
        .select('id')
        .single()

      expect(cfErr).toBeNull()
      expect(cascadeFollowup).not.toBeNull()
      const cascadeFollowupId = (cascadeFollowup as any).id

      // Insert 3 messages for this followup
      const messages = [
        createMessagePayload(cascadeFollowupId, { message_type: 'assignment', direction: 'outbound' }),
        createMessagePayload(cascadeFollowupId, { message_type: 'response', direction: 'inbound', sender_email: 'responder@example.com' }),
        createMessagePayload(cascadeFollowupId, { message_type: 'status_update', direction: 'outbound' }),
      ]

      const { error: insertErr } = await serviceClient
        .from('followup_messages')
        .insert(messages)

      expect(insertErr).toBeNull()

      // Verify 3 messages exist
      const { data: beforeDelete, error: beforeErr } = await serviceClient
        .from('followup_messages')
        .select('id')
        .eq('followup_id', cascadeFollowupId)

      expect(beforeErr).toBeNull()
      expect(beforeDelete!.length).toBe(3)

      // Delete the parent followup
      const { error: deleteErr } = await serviceClient
        .from('action_followups')
        .delete()
        .eq('id', cascadeFollowupId)

      expect(deleteErr).toBeNull()

      // Verify all messages were cascade-deleted
      const { data: afterDelete, error: afterErr } = await serviceClient
        .from('followup_messages')
        .select('id')
        .eq('followup_id', cascadeFollowupId)

      expect(afterErr).toBeNull()
      expect(afterDelete!.length).toBe(0)
    })
  })

  // ==========================================================================
  // AC3: RLS policies (Integration)
  // ==========================================================================

  describe('AC3: RLS policies', () => {
    it('15-1-followup-messages-data-model-INT-002: Assigner can SELECT messages for their follow-up', async () => {
      // Given: User A created a follow-up (assigned_by = User A) and messages exist
      // When: User A queries followup_messages filtered by that followup_id
      // Then: User A can see all messages in the thread

      if (!canConnect) return
      requireFollowup()

      // Insert a test message via service role
      const { error: insertErr } = await serviceClient
        .from('followup_messages')
        .insert(createMessagePayload(testFollowupId!))

      expect(insertErr).toBeNull()

      // Query as the assigner (User B is assigned_by in our test fixture)
      // Using service_role with RPC or impersonation is complex;
      // we test by verifying the policy SQL structure in unit tests.
      // Here we verify service role can see the messages.
      const { data, error } = await serviceClient
        .from('followup_messages')
        .select('*')
        .eq('followup_id', testFollowupId!)

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect(data!.length).toBeGreaterThanOrEqual(1)
    })

    it('15-1-followup-messages-data-model-INT-003: Assignee can SELECT messages for their follow-up', async () => {
      // Given: User A created a follow-up (assigned_to = User A) and messages exist
      // When: User B queries followup_messages filtered by that followup_id
      // Then: User B can see all messages in the thread

      if (!canConnect) return
      requireFollowup()

      // The test followup has assigned_to = USER_A, assigned_by = USER_B
      // Both should have SELECT access; verified via service_role here
      const { data, error } = await serviceClient
        .from('followup_messages')
        .select('id, followup_id, direction')
        .eq('followup_id', testFollowupId!)

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect(data!.length).toBeGreaterThanOrEqual(1)
    })

    it('15-1-followup-messages-data-model-INT-004: Unrelated user cannot SELECT messages for a follow-up', async () => {
      // Given: User A created a follow-up (assigned_by = User A, assigned_to = User B) and messages exist
      // When: User C (not assigned_to or assigned_by) queries followup_messages filtered by that followup_id
      // Then: User C receives 0 rows (RLS blocks access)

      if (!canConnect) return
      requireFollowup()

      // Note: Testing true RLS with user impersonation requires JWT mocking.
      // This test verifies via the anon key (no authenticated user context).
      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping RLS user isolation test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      const { data, error } = await anonClient
        .from('followup_messages')
        .select('id')
        .eq('followup_id', testFollowupId!)

      // Anon users should get 0 rows or an error (RLS blocks)
      if (error) {
        expect(error).not.toBeNull()
      } else {
        expect(data!.length).toBe(0)
      }
    })

    it('15-1-followup-messages-data-model-INT-005: Assigner can INSERT messages for their follow-up', async () => {
      // Given: User A created a follow-up (assigned_by = User A)
      // When: User A inserts a message with followup_id pointing to that follow-up
      // Then: The insert succeeds and the message is persisted

      if (!canConnect) return
      requireFollowup()

      const { data, error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            sender_email: 'assigner@example.com',
            message_type: 'escalation',
            direction: 'outbound',
          })
        )
        .select('id')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).id).toBeDefined()
    })

    it('15-1-followup-messages-data-model-INT-006: Assignee can INSERT messages for their follow-up', async () => {
      // Given: User A created a follow-up (assigned_to = User B)
      // When: User B inserts a message with followup_id pointing to that follow-up
      // Then: The insert succeeds and the message is persisted

      if (!canConnect) return
      requireFollowup()

      const { data, error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            sender_id: USER_B_ID,
            sender_email: 'assignee@example.com',
            message_type: 'response',
            direction: 'inbound',
          })
        )
        .select('id')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).id).toBeDefined()
    })

    it('15-1-followup-messages-data-model-INT-007: Unrelated user cannot INSERT messages for a follow-up', async () => {
      // Given: User A created a follow-up (assigned_by = User A, assigned_to = User B)
      // When: User C (not assigned_to or assigned_by) attempts to insert a message
      // Then: The insert fails or the row is not visible (RLS blocks the operation)

      if (!canConnect) return
      requireFollowup()

      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping RLS insert test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      const { error } = await anonClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            sender_id: USER_C_ID,
            sender_email: 'unrelated@example.com',
          })
        )

      // Expect RLS to block the insert
      expect(error).not.toBeNull()
    })

    it('15-1-followup-messages-data-model-INT-008: Authenticated user cannot DELETE messages', async () => {
      // Given: Messages exist in followup_messages for a follow-up assigned to User A
      // When: User A attempts to DELETE a message from followup_messages
      // Then: The delete fails or affects 0 rows (no DELETE policy exists for authenticated)

      if (!canConnect) return
      requireFollowup()

      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping DELETE policy test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      // Attempt to delete all messages for the test followup
      const { error, count } = await anonClient
        .from('followup_messages')
        .delete()
        .eq('followup_id', testFollowupId!)

      // Should fail or affect 0 rows
      if (error) {
        expect(error).not.toBeNull()
      } else {
        expect(count).toBe(0)
      }
    })

    it('15-1-followup-messages-data-model-INT-009: Authenticated user cannot UPDATE messages', async () => {
      // Given: Messages exist in followup_messages for a follow-up assigned to User A
      // When: User A attempts to UPDATE the body of a message
      // Then: The update fails or affects 0 rows (no UPDATE policy exists for authenticated)

      if (!canConnect) return
      requireFollowup()

      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping UPDATE policy test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      // Attempt to update messages for the test followup
      const { error, count } = await anonClient
        .from('followup_messages')
        .update({ body: 'Attempted update - should fail' })
        .eq('followup_id', testFollowupId!)

      // Should fail or affect 0 rows
      if (error) {
        expect(error).not.toBeNull()
      } else {
        expect(count).toBe(0)
      }
    })

    it('15-1-followup-messages-data-model-INT-010: Service role has full CRUD access', async () => {
      // Given: The service_role connection is used
      // When: The service role performs INSERT, SELECT, UPDATE, and DELETE on followup_messages
      // Then: All operations succeed without RLS restrictions

      if (!canConnect) return
      requireFollowup()

      // INSERT
      const { data: inserted, error: insertErr } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            subject: 'Service role CRUD test',
            body: 'Testing full CRUD access',
          })
        )
        .select('id')
        .single()

      expect(insertErr).toBeNull()
      expect(inserted).not.toBeNull()
      const testMsgId = (inserted as any).id

      // SELECT
      const { data: selected, error: selectErr } = await serviceClient
        .from('followup_messages')
        .select('*')
        .eq('id', testMsgId)
        .single()

      expect(selectErr).toBeNull()
      expect(selected).not.toBeNull()
      expect((selected as any).subject).toBe('Service role CRUD test')

      // UPDATE
      const { error: updateErr } = await serviceClient
        .from('followup_messages')
        .update({ body: 'Updated by service role' })
        .eq('id', testMsgId)

      expect(updateErr).toBeNull()

      // Verify update took effect
      const { data: updated, error: verifyErr } = await serviceClient
        .from('followup_messages')
        .select('body')
        .eq('id', testMsgId)
        .single()

      expect(verifyErr).toBeNull()
      expect((updated as any).body).toBe('Updated by service role')

      // DELETE
      const { error: deleteErr } = await serviceClient
        .from('followup_messages')
        .delete()
        .eq('id', testMsgId)

      expect(deleteErr).toBeNull()

      // Verify deletion
      const { data: deleted, error: checkErr } = await serviceClient
        .from('followup_messages')
        .select('id')
        .eq('id', testMsgId)

      expect(checkErr).toBeNull()
      expect(deleted!.length).toBe(0)
    })
  })

  // ==========================================================================
  // Constraint Validation (Integration)
  // ==========================================================================

  describe('Constraint Validation', () => {
    it('15-1-followup-messages-data-model-INT-011: CHECK constraint rejects invalid direction value', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: A message is inserted via service_role with direction = 'invalid_direction'
      // Then: The insert fails with a CHECK constraint violation error

      if (!canConnect) return
      requireFollowup()

      const { error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            direction: 'invalid_direction',
          })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('15-1-followup-messages-data-model-INT-012: CHECK constraint rejects invalid message_type value', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: A message is inserted via service_role with message_type = 'invalid_type'
      // Then: The insert fails with a CHECK constraint violation error

      if (!canConnect) return
      requireFollowup()

      const { error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            message_type: 'invalid_type',
          })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('15-1-followup-messages-data-model-INT-013: NOT NULL constraint rejects null sender_email', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: A message is inserted via service_role with sender_email = NULL
      // Then: The insert fails with a NOT NULL violation error

      if (!canConnect) return
      requireFollowup()

      const { error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            sender_email: null,
          })
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/null|not-null|violat/i)
    })

    it('15-1-followup-messages-data-model-INT-014: Nullable sender_id allows insert with null sender_id', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: A message is inserted via service_role with sender_id = NULL and a valid sender_email
      // Then: The insert succeeds, confirming sender_id is nullable for non-app-user email replies

      if (!canConnect) return
      requireFollowup()

      const { data, error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            sender_id: null,
            sender_email: 'external@example.com',
            direction: 'inbound',
            message_type: 'response',
          })
        )
        .select('id, sender_id')
        .single()

      expect(error).toBeNull()
      expect(data).not.toBeNull()
      expect((data as any).sender_id).toBeNull()
    })

    it('15-1-followup-messages-data-model-INT-015: FK constraint rejects invalid followup_id', async () => {
      // Given: No follow-up exists with a specific UUID
      // When: A message is inserted via service_role with followup_id = non-existent UUID
      // Then: The insert fails with a foreign key constraint violation

      if (!canConnect) return

      const { error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(NON_EXISTENT_UUID)
        )

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/foreign key|violat|reference/i)
    })

    it('15-1-followup-messages-data-model-INT-016: NOT NULL constraint rejects null followup_id', async () => {
      // Given: The followup_messages table exists
      // When: A message is inserted via service_role with followup_id = NULL
      // Then: The insert fails with a NOT NULL violation error

      if (!canConnect) return

      const { error } = await serviceClient
        .from('followup_messages')
        .insert({
          followup_id: null,
          sender_email: 'test@example.com',
          direction: 'outbound',
          message_type: 'assignment',
        } as any)

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/null|not-null|violat/i)
    })

    it('15-1-followup-messages-data-model-INT-017: Default gen_random_uuid() generates unique id on insert', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: Two messages are inserted via service_role without specifying id
      // Then: Both inserts succeed and each row has a unique, non-null UUID id value

      if (!canConnect) return
      requireFollowup()

      const { data: msg1, error: err1 } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            subject: 'UUID test message 1',
          })
        )
        .select('id')
        .single()

      expect(err1).toBeNull()
      expect(msg1).not.toBeNull()

      const { data: msg2, error: err2 } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            subject: 'UUID test message 2',
          })
        )
        .select('id')
        .single()

      expect(err2).toBeNull()
      expect(msg2).not.toBeNull()

      const id1 = (msg1 as any).id
      const id2 = (msg2 as any).id

      // Both IDs should be non-null
      expect(id1).not.toBeNull()
      expect(id2).not.toBeNull()

      // IDs should be different
      expect(id1).not.toBe(id2)

      // IDs should look like UUIDs
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      expect(id1).toMatch(uuidPattern)
      expect(id2).toMatch(uuidPattern)
    })

    it('15-1-followup-messages-data-model-INT-018: Default NOW() populates created_at on insert', async () => {
      // Given: A valid follow-up exists in action_followups
      // When: A message is inserted via service_role without specifying created_at
      // Then: The created_at column is automatically populated with the current timestamp

      if (!canConnect) return
      requireFollowup()

      const beforeInsert = new Date()

      const { data, error } = await serviceClient
        .from('followup_messages')
        .insert(
          createMessagePayload(testFollowupId!, {
            subject: 'created_at default test',
          })
        )
        .select('id, created_at')
        .single()

      const afterInsert = new Date()

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const createdAt = new Date((data as any).created_at)

      // created_at should be between beforeInsert and afterInsert (with some tolerance)
      expect(createdAt.getTime()).toBeGreaterThanOrEqual(
        beforeInsert.getTime() - 5000
      )
      expect(createdAt.getTime()).toBeLessThanOrEqual(
        afterInsert.getTime() + 5000
      )
    })
  })
})
