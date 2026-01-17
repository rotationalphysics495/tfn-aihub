/**
 * Handoff Types (Story 9.5, Task 7.1)
 *
 * TypeScript interfaces for shift handoff data structures.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 * @see AC#2 - Handoff Detail View
 * @see AC#3 - Voice Note Playback
 */

// ============================================================================
// Voice Note Types
// ============================================================================

/**
 * Voice note attached to a handoff
 */
export interface HandoffVoiceNote {
  id: string;
  handoff_id: string;
  user_id: string;
  storage_path: string;
  storage_url: string | null;
  transcript: string | null;
  duration_seconds: number;
  sequence_order: number;
  created_at: string;
}

// ============================================================================
// Handoff Types
// ============================================================================

/**
 * Handoff status values
 */
export type HandoffStatus =
  | 'draft'
  | 'pending_acknowledgment'
  | 'acknowledged'
  | 'superseded';

/**
 * Shift type values
 */
export type ShiftType = 'morning' | 'afternoon' | 'night';

/**
 * Full handoff record with related data
 */
export interface Handoff {
  id: string;
  created_by: string;
  creator_name: string;
  creator_email: string;
  shift_date: string;
  shift_type: ShiftType;
  shift_start_time: string;
  shift_end_time: string;
  assets_covered: string[];
  summary_text: string | null;
  text_notes: string | null;
  status: HandoffStatus;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  voice_notes: HandoffVoiceNote[];
}

/**
 * Handoff list item (summary for list view)
 */
export interface HandoffListItem {
  id: string;
  created_by: string;
  creator_name: string;
  shift_date: string;
  shift_type: ShiftType;
  status: HandoffStatus;
  assets_covered: string[];
  summary_preview: string | null;
  voice_note_count: number;
  created_at: string;
  submitted_at: string | null;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Response from handoff list endpoint
 */
export interface HandoffListResponse {
  handoffs: HandoffListItem[];
  pending_count: number;
  acknowledged_count: number;
}

/**
 * Response from single handoff endpoint
 */
export interface HandoffDetailResponse {
  handoff: Handoff;
  can_acknowledge: boolean;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Filter options for handoff list
 */
export interface HandoffListFilters {
  status?: HandoffStatus;
  shift_date?: string;
}

/**
 * State for handoff hooks
 */
export interface HandoffState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}
