# Story 9.6: Handoff Q&A

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **incoming Supervisor**,
I want to **ask follow-up questions about the handoff content**,
So that **I can clarify anything unclear before taking over**.

## Acceptance Criteria

1. **Given** a Supervisor is viewing a handoff
   **When** they have a question (FR26)
   **Then** they can type or speak their question
   **And** the AI processes it with handoff context

2. **Given** a question is asked
   **When** the AI responds
   **Then** the response references specific handoff content where relevant
   **And** includes citations to source data (FR52)
   **And** response is added to a Q&A thread on the handoff

3. **Given** the outgoing Supervisor is still online
   **When** a question is asked
   **Then** they are notified of the question
   **And** can respond directly if desired

4. **Given** the Q&A thread grows
   **When** viewed later
   **Then** all questions and answers are preserved
   **And** visible to both supervisors

## Tasks / Subtasks

- [ ] Task 1: Create HandoffQA Component (AC: #1, #4)
  - [ ] 1.1 Create `apps/web/src/components/handoff/HandoffQA.tsx` component
  - [ ] 1.2 Implement text input field with send button
  - [ ] 1.3 Integrate push-to-talk button from Story 8.2 infrastructure
  - [ ] 1.4 Display Q&A thread with proper scrolling and timestamps
  - [ ] 1.5 Add loading states during AI processing
  - [ ] 1.6 Show question attribution (who asked)
  - [ ] 1.7 Create `apps/web/src/components/handoff/__tests__/HandoffQA.test.tsx`

- [ ] Task 2: Create Q&A Backend Service (AC: #1, #2)
  - [ ] 2.1 Create `apps/api/app/services/handoff/qa.py` service module
  - [ ] 2.2 Implement context injection pattern - inject handoff summary into LangChain prompt
  - [ ] 2.3 Implement `process_qa_question()` method that routes through ManufacturingAgent
  - [ ] 2.4 Add shift time range and assets scope to agent context for accurate data retrieval
  - [ ] 2.5 Ensure citations are generated from underlying tool responses (FR52)
  - [ ] 2.6 Handle partial failures gracefully (continue with available data)
  - [ ] 2.7 Create `apps/api/app/tests/services/test_handoff_qa.py`

- [ ] Task 3: Create Q&A API Endpoint (AC: #1, #2, #4)
  - [ ] 3.1 Add Q&A endpoint to `apps/api/app/api/handoff.py`: `POST /api/v1/handoff/{id}/qa`
  - [ ] 3.2 Accept request body: `{ "question": string, "voice_transcript"?: string }`
  - [ ] 3.3 Validate handoff exists and user has access (RLS check)
  - [ ] 3.4 Store Q&A entries in handoff record (append-only for immutability)
  - [ ] 3.5 Return response with citations and thread update
  - [ ] 3.6 Create `apps/api/app/tests/api/test_handoff_qa.py`

- [ ] Task 4: Database Schema for Q&A Thread (AC: #4)
  - [ ] 4.1 Create migration `supabase/migrations/20260116_001_handoff_qa_thread.sql`
  - [ ] 4.2 Create `handoff_qa_entries` table with columns: id, handoff_id (FK), user_id, role (questioner/responder), content_type (question/answer/human_response), content, citations (JSONB), created_at
  - [ ] 4.3 Add RLS policies: users can read/write Q&A for handoffs they have access to
  - [ ] 4.4 Add index on handoff_id for efficient thread retrieval

- [ ] Task 5: Real-time Q&A Updates (AC: #3)
  - [ ] 5.1 Configure Supabase Realtime for `handoff_qa_entries` table
  - [ ] 5.2 Create `apps/web/src/lib/hooks/useHandoffQA.ts` hook with Realtime subscription
  - [ ] 5.3 Display incoming question notification to outgoing supervisor (if online)
  - [ ] 5.4 Enable outgoing supervisor to respond directly via same Q&A interface
  - [ ] 5.5 Differentiate AI responses vs human responses in UI (icon/badge)

- [ ] Task 6: Handoff Model Updates (AC: #2, #4)
  - [ ] 6.1 Add Pydantic models: `HandoffQAEntry`, `HandoffQARequest`, `HandoffQAResponse` to `apps/api/app/models/handoff.py`
  - [ ] 6.2 Update `ShiftHandoff` model to include optional `qa_thread: List[HandoffQAEntry]`
  - [ ] 6.3 Add citation model for Q&A responses extending existing Citation pattern

## Dev Notes

### Architecture Patterns

This story follows the established patterns from Epic 7-8:

1. **Service Pattern**: Create dedicated `HandoffQAService` in `services/handoff/qa.py` - NOT a ManufacturingTool. This is an orchestration service similar to `BriefingService` pattern.

2. **Context Injection**: The Q&A service must inject handoff context into the LangChain agent:
```python
# Pattern from voice-briefing.md
async def process_question(
    self,
    handoff_id: str,
    question: str,
    user_id: str,
) -> HandoffQAResponse:
    # 1. Load handoff summary
    # 2. Inject into agent context
    # 3. Include shift time range for accurate tool queries
    # 4. Route to ManufacturingAgent
    # 5. Return response with citations
```

3. **Citation Pattern**: All responses MUST include citations using the established `Citation` model from `app/models/chat.py`. Transform agent citations using `_transform_agent_citations()` pattern from `chat.py`.

4. **Immutability**: Q&A entries are append-only (per NFR24). No UPDATE/DELETE allowed on Q&A records.

### Key Dependencies

- **Story 9.4 (Persistent Handoff Records)**: Handoffs must exist before Q&A can be added
- **Story 9.5 (Handoff Review UI)**: Q&A component integrates into the handoff viewer
- **Story 8.2 (Push-to-Talk STT)**: Reuse voice input infrastructure for spoken questions

### Technical Implementation Details

**Q&A Context Flow:**
```
1. User asks question (text or voice)
2. Frontend sends to POST /api/v1/handoff/{id}/qa
3. Backend loads handoff summary and metadata
4. Context injected into agent: {
     "handoff_summary": <shift summary text>,
     "shift_time_range": { "start": datetime, "end": datetime },
     "assets_covered": [asset_ids],
     "outgoing_supervisor": user_name
   }
5. Agent processes with existing tools (OEE, Downtime, etc.)
6. Response formatted with citations from tool outputs
7. Q&A entry stored with created_at timestamp
8. Real-time broadcast to connected users viewing this handoff
```

**Supabase Realtime Pattern:**
```typescript
// useHandoffQA.ts hook pattern
const channel = supabase
  .channel(`handoff-qa:${handoffId}`)
  .on(
    'postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'handoff_qa_entries', filter: `handoff_id=eq.${handoffId}` },
    (payload) => setQaEntries(prev => [...prev, payload.new])
  )
  .subscribe();
```

**Latency Target (from architecture):**
- Q&A round-trip: <2s (NFR performance budget)
- TTS latency if voice: ~300-500ms additional

### Testing Requirements

1. **Unit Tests**: Q&A service logic, context injection, citation generation
2. **Integration Tests**: Full flow from API to database
3. **E2E Considerations**: Test with mocked agent responses
4. **RLS Tests**: Verify users can only access Q&A for their handoffs

### Project Structure Notes

**New Files:**
- `apps/api/app/services/handoff/qa.py` - Q&A processing service
- `apps/web/src/components/handoff/HandoffQA.tsx` - Q&A UI component
- `apps/web/src/lib/hooks/useHandoffQA.ts` - Real-time Q&A hook
- `supabase/migrations/20260116_001_handoff_qa_thread.sql` - Q&A table

**Modified Files:**
- `apps/api/app/api/handoff.py` - Add Q&A endpoint
- `apps/api/app/models/handoff.py` - Add Q&A models
- `apps/web/src/components/handoff/HandoffViewer.tsx` - Integrate Q&A component

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based Access Control] - RLS patterns for handoff access
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#BriefingService Architecture] - Service orchestration pattern
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Voice Integration Rules] - Text fallback requirements
- [Source: apps/api/app/api/chat.py] - Agent routing and citation transformation patterns
- [Source: apps/api/app/services/agent/tools/recommendation_engine.py] - Tool pattern with citations
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.6] - Story requirements

### Error Handling

- **Agent Timeout**: If AI processing exceeds 15 seconds, return partial response with "AI response delayed"
- **Handoff Not Found**: Return 404 with clear error message
- **Access Denied**: Return 403 if user doesn't have RLS access to handoff
- **Voice Transcription Failure**: Fall back to text input with user notification

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

