# Story 5.7: Agent Chat Integration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to use the existing chat sidebar to interact with the new AI agent**,
so that **I don't need to learn a new interface**.

## Acceptance Criteria

1. **Chat Routing to Agent**
   - GIVEN a user opens the chat sidebar
   - WHEN they send a message
   - THEN the message is routed to the new agent endpoint (/api/agent/chat)
   - AND the response is displayed in the existing chat UI
   - AND the existing chat history is preserved

2. **Citation Rendering**
   - GIVEN the agent returns a response with citations
   - WHEN the response is displayed
   - THEN citations are rendered as clickable links/badges
   - AND clicking a citation shows source details (table, timestamp)
   - AND citations are visually distinct but not distracting

3. **Follow-Up Question Chips**
   - GIVEN the agent returns suggested follow-up questions
   - WHEN the response is displayed
   - THEN follow-ups appear as clickable chips below the response
   - AND clicking a chip sends that question as the next message
   - AND chips match the existing chat UI styling

4. **Loading Indicator**
   - GIVEN the agent is processing a request
   - WHEN the user is waiting
   - THEN a loading indicator is shown
   - AND the indicator matches the existing chat UI pattern
   - AND the send button is disabled during processing

5. **Error Handling in UI**
   - GIVEN an error occurs during agent processing
   - WHEN the error response is received
   - THEN a user-friendly error message is displayed
   - AND the user can retry the message
   - AND the chat remains functional

6. **Memory Preservation**
   - GIVEN the user interacts with the new agent
   - WHEN messages are sent and received
   - THEN conversations are still stored in Mem0
   - AND the memory API from Story 4.1 continues to work
   - AND asset-related memories are linked correctly

7. **Response Formatting**
   - GIVEN the agent returns structured data (tables, lists)
   - WHEN the response is displayed
   - THEN the data is formatted appropriately for the chat UI
   - AND tables are rendered as clean markdown or HTML tables
   - AND status indicators show appropriate colors

8. **Mobile Responsiveness**
   - GIVEN the chat sidebar is used on mobile/tablet
   - WHEN the agent returns responses
   - THEN all elements (citations, chips, tables) render correctly
   - AND touch interactions work properly
   - AND the UI remains usable on smaller screens

## Tasks / Subtasks

- [ ] Task 1: Update Chat API Route (AC: #1, #6)
  - [ ] 1.1 Modify `apps/api/app/api/chat.py` to route to agent endpoint
  - [ ] 1.2 Update request schema to match agent input format
  - [ ] 1.3 Preserve Mem0 memory storage for conversations
  - [ ] 1.4 Handle response transformation for frontend
  - [ ] 1.5 Add error handling for agent failures
  - [ ] 1.6 Create tests for routing logic

- [ ] Task 2: Enhance ChatMessage Component for Citations (AC: #2)
  - [ ] 2.1 Modify `apps/web/src/components/chat/ChatMessage.tsx`
  - [ ] 2.2 Integrate existing CitationLink and CitationPanel components
  - [ ] 2.3 Parse agent citations format to CitationData
  - [ ] 2.4 Style citation badges for Industrial Clarity design
  - [ ] 2.5 Create unit tests for citation rendering

- [ ] Task 3: Create FollowUpChips Component (AC: #3)
  - [ ] 3.1 Create `apps/web/src/components/chat/FollowUpChips.tsx`
  - [ ] 3.2 Design chip styling (clickable, light background)
  - [ ] 3.3 Implement click handler to send question
  - [ ] 3.4 Handle max 3 chips with overflow
  - [ ] 3.5 Add animation on appear (fade-in, slide-up)
  - [ ] 3.6 Create unit tests

- [ ] Task 4: Update ChatSidebar for Agent Integration (AC: #1, #4)
  - [ ] 4.1 Replace mock message handler with agent API call
  - [ ] 4.2 Update state management for follow-up questions
  - [ ] 4.3 Pass follow-up handler to ChatMessage
  - [ ] 4.4 Verify loading indicator works with agent latency
  - [ ] 4.5 Create integration tests

- [ ] Task 5: Implement Error Handling UI (AC: #5)
  - [ ] 5.1 Create error message component for chat
  - [ ] 5.2 Add retry button functionality
  - [ ] 5.3 Handle different error types (network, timeout, server)
  - [ ] 5.4 Log errors for debugging
  - [ ] 5.5 Create tests for error scenarios

- [ ] Task 6: Response Formatting (AC: #7)
  - [ ] 6.1 Add ReactMarkdown for structured content
  - [ ] 6.2 Create table rendering with horizontal scroll
  - [ ] 6.3 Apply status colors (green/red) for production data
  - [ ] 6.4 Test with various response formats
  - [ ] 6.5 Create unit tests

- [ ] Task 7: Test Mobile Responsiveness (AC: #8)
  - [ ] 7.1 Test citations on mobile (tap targets)
  - [ ] 7.2 Test follow-up chips on mobile
  - [ ] 7.3 Test table scrolling on mobile
  - [ ] 7.4 Verify sidebar width adjustments
  - [ ] 7.5 Create responsive design tests

- [ ] Task 8: Integration Testing (AC: All)
  - [ ] 8.1 Test full chat flow with agent
  - [ ] 8.2 Test memory storage with new agent
  - [ ] 8.3 Test citation display and interaction
  - [ ] 8.4 Test follow-up chip flow
  - [ ] 8.5 Test error recovery

## Dev Notes

### Architecture Compliance

This story bridges the Epic 4 chat UI with the Epic 5 agent framework. It modifies existing components rather than creating new ones where possible.

**Existing Components to Modify:**
- `apps/web/src/components/chat/ChatMessage.tsx` - Already has citation support from Story 4.5
- `apps/web/src/components/chat/ChatSidebar.tsx` - Currently uses mock responses
- `apps/api/app/api/chat.py` - Currently uses Text-to-SQL, needs agent routing

**New Component to Create:**
- `apps/web/src/components/chat/FollowUpChips.tsx` - New component for suggested questions

### Technical Requirements

#### Integration Flow
```
User types message
    |
    v
+-------------------+
| ChatSidebar.tsx   |
| (handleSubmit)    |
+-------------------+
    |
    v POST /api/chat/query
+-------------------+
| chat.py (API)     |
| - Call agent      |
| - Store in Mem0   |
| - Format response |
+-------------------+
    |
    v Internal call to /api/agent/chat
+-------------------+
| ManufacturingAgent|
| (executor.py)     |
+-------------------+
    |
    v AgentResponse with citations & follow-ups
+-------------------+
| ChatMessage.tsx   |
| - Render content  |
| - Show citations  |
+-------------------+
    |
    v
+-------------------+
| FollowUpChips.tsx |
| - Render chips    |
| - Handle clicks   |
+-------------------+
```

### Backend: Chat API Modification

**Update chat.py to route to agent:**
```python
from app.services.agent.executor import get_agent
from app.services.memory.mem0_service import memory_service

@router.post("/query", response_model=QueryResponse)
async def query_data(
    query_input: QueryInput,
    current_user: CurrentUser = Depends(get_current_user),
    agent: ManufacturingAgent = Depends(get_agent),
):
    """Process chat message through manufacturing agent."""
    user_id = current_user.id

    try:
        # Get memory context for the query
        memory_context = await memory_service.get_context_for_query(
            query_input.question, user_id
        )

        # Process through agent instead of Text-to-SQL
        agent_response = await agent.process_message(
            message=query_input.question,
            user_id=user_id,
            chat_history=memory_context
        )

        # Store conversation in Mem0
        await memory_service.add_memory(
            messages=[
                {"role": "user", "content": query_input.question},
                {"role": "assistant", "content": agent_response.content}
            ],
            user_id=user_id
        )

        # Transform to QueryResponse format
        return QueryResponse(
            answer=agent_response.content,
            citations=[...],  # Transform agent citations
            follow_up_questions=agent_response.follow_ups
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")
```

### Frontend: FollowUpChips Component

**FollowUpChips.tsx:**
```tsx
'use client'

import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FollowUpChipsProps {
  questions: string[]
  onSelect: (question: string) => void
  className?: string
}

export function FollowUpChips({ questions, onSelect, className }: FollowUpChipsProps) {
  if (!questions || questions.length === 0) return null

  return (
    <div
      className={cn(
        "flex flex-wrap gap-2 mt-3",
        "animate-in fade-in slide-in-from-bottom-2 duration-300",
        className
      )}
    >
      {questions.slice(0, 3).map((question, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          className={cn(
            "text-xs h-auto py-1.5 px-3",
            "border-industrial-300 dark:border-industrial-600",
            "hover:bg-info-blue/10 hover:border-info-blue",
            "transition-colors"
          )}
          onClick={() => onSelect(question)}
        >
          {question}
          <ChevronRight className="ml-1 h-3 w-3" />
        </Button>
      ))}
    </div>
  )
}
```

### Frontend: ChatMessage Updates

**Add follow-up chips to ChatMessage.tsx:**
```tsx
import { FollowUpChips } from './FollowUpChips'

interface ChatMessageProps {
  message: Message
  followUpQuestions?: string[]
  onFollowUpSelect?: (question: string) => void
  className?: string
}

export function ChatMessage({
  message,
  followUpQuestions = [],
  onFollowUpSelect,
  className
}: ChatMessageProps) {
  // ... existing code ...

  return (
    <div className={...}>
      {/* ... existing message content ... */}

      {/* Follow-up chips for assistant messages */}
      {!isUser && followUpQuestions.length > 0 && onFollowUpSelect && (
        <FollowUpChips
          questions={followUpQuestions}
          onSelect={onFollowUpSelect}
        />
      )}
    </div>
  )
}
```

### Frontend: ChatSidebar Updates

**Update handleSubmit in ChatSidebar.tsx:**
```tsx
const handleSubmit = useCallback(async () => {
  if (!inputValue.trim() || isLoading) return

  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: inputValue.trim(),
    timestamp: new Date(),
  }

  setMessages((prev) => [...prev, userMessage])
  setInputValue('')
  setIsLoading(true)

  try {
    // Call the chat API (which routes to agent)
    const response = await fetch('/api/chat/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userMessage.content }),
    })

    if (!response.ok) throw new Error('Failed to get response')

    const data = await response.json()

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: data.answer,
      timestamp: new Date(),
      citations: data.citations,
      groundingScore: data.meta?.grounding_score,
    }

    setMessages((prev) => [...prev, assistantMessage])
    setFollowUpQuestions(data.follow_up_questions || [])
  } catch (error) {
    // Handle error - show error message to user
    const errorMessage: Message = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: 'I encountered an error processing your request. Please try again.',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, errorMessage])
  } finally {
    setIsLoading(false)
  }
}, [inputValue, isLoading])
```

### Project Structure Notes

**Files to modify:**
```
apps/
├── api/
│   └── app/
│       └── api/
│           └── chat.py              # Route to agent endpoint
├── web/
│   └── src/
│       └── components/
│           └── chat/
│               ├── ChatMessage.tsx  # Add follow-up rendering
│               ├── ChatSidebar.tsx  # Replace mock with API call
│               ├── FollowUpChips.tsx # NEW component
│               ├── types.ts         # Add follow_up_questions type
│               └── index.ts         # Export new component
```

### Dependencies

**Story Dependencies:**
- Story 4.1 (Mem0 Memory) - Memory service for context retrieval
- Story 4.3 (Chat Sidebar UI) - Base UI components
- Story 4.5 (Cited Responses) - Citation components already exist
- Story 5.1 (Agent Framework) - ManufacturingAgent class
- Stories 5.3-5.6 (Core Tools) - Tools for agent to use

**Blocked By:** Stories 4.1, 4.3, 5.1, 5.2, 5.3-5.6

**Enables:**
- Epic 6 & 7 - All future tools accessible through chat
- Full plant manager workflow via natural language

### Existing Components to Reuse

**From Story 4.5 (already implemented):**
- `CitationLink.tsx` - Clickable citation badge
- `CitationPanel.tsx` - Citation detail popover
- `CitationData` type - Citation data structure

**From Story 4.3 (already implemented):**
- `ChatInput.tsx` - Already has loading state
- `ChatLoadingIndicator.tsx` - Typing indicator
- `MessageList.tsx` - Message scrolling container

### Testing Strategy

1. **Unit Tests:**
   - FollowUpChips component rendering
   - FollowUpChips click handling
   - ChatMessage with follow-up props
   - Chat API response transformation

2. **Integration Tests:**
   - Full chat flow with agent response
   - Memory storage verification
   - Citation display from agent response
   - Follow-up chip to new message flow

3. **E2E Tests:**
   - Send message, verify agent response
   - Click citation, verify popover
   - Click follow-up chip, verify new message sent
   - Test error recovery

4. **Manual Testing:**
   - Test on desktop and mobile
   - Verify citation readability
   - Test chip touch targets (min 44px)
   - Verify memory recall works

### NFR Compliance

- **NFR1 (Accuracy):** Citations displayed for all factual claims (existing from 4.5)
- **NFR2 (Latency):** Loading indicator shown during agent processing
- **NFR4 (Agent Honesty):** Agent "I don't know" responses render correctly
- **NFR6 (Response Structure):** Structured data renders cleanly in chat
- **Industrial Clarity:** All new components use design system tokens

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#6. User Experience] - UX patterns and example interactions
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.7] - Story requirements
- [Source: apps/web/src/components/chat/ChatMessage.tsx] - Existing citation support
- [Source: apps/web/src/components/chat/ChatSidebar.tsx] - Existing chat container
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - AI Analyst Chat IA

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
