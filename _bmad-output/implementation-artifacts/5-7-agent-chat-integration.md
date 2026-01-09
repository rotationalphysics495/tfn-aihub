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

- [ ] Task 2: Create Citation Component (AC: #2)
  - [ ] 2.1 Create `apps/web/src/components/chat/Citation.tsx`
  - [ ] 2.2 Design citation badge styling (subtle but clickable)
  - [ ] 2.3 Implement click handler to show source details
  - [ ] 2.4 Create modal or popover for citation details
  - [ ] 2.5 Style to match Industrial Clarity design system
  - [ ] 2.6 Create unit tests

- [ ] Task 3: Create FollowUpChips Component (AC: #3)
  - [ ] 3.1 Create `apps/web/src/components/chat/FollowUpChips.tsx`
  - [ ] 3.2 Design chip styling (clickable, light background)
  - [ ] 3.3 Implement click handler to send question
  - [ ] 3.4 Handle max 3 chips with overflow
  - [ ] 3.5 Add animation on appear
  - [ ] 3.6 Create unit tests

- [ ] Task 4: Update ChatMessage Component (AC: #2, #7)
  - [ ] 4.1 Modify `apps/web/src/components/chat/ChatMessage.tsx`
  - [ ] 4.2 Parse citations from agent response
  - [ ] 4.3 Render Citation components inline or at end
  - [ ] 4.4 Parse and render markdown tables
  - [ ] 4.5 Apply status colors for production data
  - [ ] 4.6 Create tests for message rendering

- [ ] Task 5: Update Chat Loading State (AC: #4)
  - [ ] 5.1 Modify chat input component for loading state
  - [ ] 5.2 Add thinking/typing indicator in message area
  - [ ] 5.3 Disable send button during processing
  - [ ] 5.4 Add timeout handling (30 seconds max)
  - [ ] 5.5 Create tests for loading states

- [ ] Task 6: Implement Error Handling (AC: #5)
  - [ ] 6.1 Create error message component for chat
  - [ ] 6.2 Add retry button functionality
  - [ ] 6.3 Handle different error types (network, timeout, server)
  - [ ] 6.4 Log errors for debugging
  - [ ] 6.5 Create tests for error scenarios

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

This story integrates the new agent (Stories 5.1-5.6) with the existing chat UI built in Epic 4. It bridges the frontend (Story 4.3) with the new backend agent endpoint.

**Location:**
- Backend: `apps/api/app/api/chat.py` (modify)
- Frontend: `apps/web/src/components/chat/` (modify/create)

**Pattern:** API route modification + new React components

### Technical Requirements

**Integration Flow Diagram:**
```
User types message
    |
    v
+-------------------+
| Chat Sidebar UI   |
| (ChatInput.tsx)   |
+-------------------+
    |
    v POST /api/chat
+-------------------+
| chat.py (API)     |
| - Transform request
| - Call /api/agent/chat
| - Store in Mem0
| - Transform response
+-------------------+
    |
    v
+-------------------+
| ManufacturingAgent|
| (executor.py)     |
+-------------------+
    |
    v
+-------------------+
| ChatMessage.tsx   |
| - Render response |
| - Show citations  |
| - Show follow-ups |
+-------------------+
```

### Backend: Chat API Modification

**chat.py Updates:**
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.agent.executor import ManufacturingAgent, get_agent
from app.services.memory.mem0_service import memory_service
from app.core.auth import get_current_user

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class CitationResponse(BaseModel):
    source: str
    timestamp: str
    table: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    citations: List[CitationResponse] = []
    follow_up_questions: List[str] = []
    metadata: dict = {}

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
    agent: ManufacturingAgent = Depends(get_agent)
):
    """Process chat message through the manufacturing agent."""
    user_id = user["id"]

    try:
        # Get relevant memory context
        memory_context = await memory_service.get_context_for_query(
            request.message, user_id
        )

        # Process through agent
        agent_response = await agent.process_message(
            message=request.message,
            user_id=user_id,
            chat_history=memory_context
        )

        # Store in Mem0 for future context
        await memory_service.add_memory(
            messages=[
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": agent_response.content}
            ],
            user_id=user_id,
            metadata={"conversation_id": request.conversation_id}
        )

        # Transform response for frontend
        return ChatResponse(
            message=agent_response.content,
            citations=[
                CitationResponse(
                    source=c.source,
                    timestamp=c.timestamp.isoformat(),
                    table=c.table
                )
                for c in agent_response.citations
            ],
            follow_up_questions=agent_response.metadata.get("follow_up_questions", []),
            metadata=agent_response.metadata
        )

    except Exception as e:
        logger.error(f"Chat error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")
```

### Frontend: Citation Component

**Citation.tsx:**
```tsx
import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface CitationProps {
  source: string;
  timestamp: string;
  table?: string;
  index: number;
}

export function Citation({ source, timestamp, table, index }: CitationProps) {
  const formattedTime = new Date(timestamp).toLocaleString();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Badge
          variant="outline"
          className="cursor-pointer hover:bg-muted text-xs ml-1"
        >
          [{index}]
        </Badge>
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <div className="space-y-2">
          <h4 className="font-medium text-sm">Source Details</h4>
          <div className="text-xs text-muted-foreground">
            <p><strong>Source:</strong> {source}</p>
            {table && <p><strong>Table:</strong> {table}</p>}
            <p><strong>Retrieved:</strong> {formattedTime}</p>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

### Frontend: FollowUpChips Component

**FollowUpChips.tsx:**
```tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';

interface FollowUpChipsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export function FollowUpChips({ questions, onSelect }: FollowUpChipsProps) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3 animate-in fade-in slide-in-from-bottom-2">
      {questions.slice(0, 3).map((question, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          className="text-xs h-auto py-1.5 px-3 hover:bg-primary/10"
          onClick={() => onSelect(question)}
        >
          {question}
          <ChevronRight className="ml-1 h-3 w-3" />
        </Button>
      ))}
    </div>
  );
}
```

### Frontend: ChatMessage Updates

**ChatMessage.tsx Updates:**
```tsx
import { Citation } from './Citation';
import { FollowUpChips } from './FollowUpChips';
import ReactMarkdown from 'react-markdown';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{ source: string; timestamp: string; table?: string }>;
  followUpQuestions?: string[];
  onFollowUpSelect?: (question: string) => void;
}

export function ChatMessage({
  role,
  content,
  citations = [],
  followUpQuestions = [],
  onFollowUpSelect,
}: ChatMessageProps) {
  return (
    <div className={cn(
      "flex gap-3 p-4",
      role === 'user' ? "bg-muted/50" : "bg-background"
    )}>
      <Avatar role={role} />
      <div className="flex-1 space-y-2">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            components={{
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto">
                  <table className="min-w-full border-collapse" {...props} />
                </div>
              ),
              // Add custom rendering for status colors
              strong: ({ children }) => {
                const text = String(children);
                if (text.includes('behind') || text.includes('down')) {
                  return <strong className="text-destructive">{children}</strong>;
                }
                if (text.includes('ahead') || text.includes('running')) {
                  return <strong className="text-green-600">{children}</strong>;
                }
                return <strong>{children}</strong>;
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Citations */}
        {citations.length > 0 && (
          <div className="flex items-center gap-1 pt-2 border-t border-border/50">
            <span className="text-xs text-muted-foreground">Sources:</span>
            {citations.map((citation, index) => (
              <Citation
                key={index}
                index={index + 1}
                source={citation.source}
                timestamp={citation.timestamp}
                table={citation.table}
              />
            ))}
          </div>
        )}

        {/* Follow-up questions */}
        {role === 'assistant' && onFollowUpSelect && (
          <FollowUpChips
            questions={followUpQuestions}
            onSelect={onFollowUpSelect}
          />
        )}
      </div>
    </div>
  );
}
```

### Loading State Pattern

**ChatInput.tsx Updates:**
```tsx
import { Loader2 } from 'lucide-react';

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  return (
    <div className="flex gap-2 p-4 border-t">
      <Input
        placeholder="Ask about your plant..."
        disabled={isLoading}
        onKeyDown={(e) => e.key === 'Enter' && !isLoading && onSend()}
      />
      <Button
        onClick={onSend}
        disabled={isLoading}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}
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
│               ├── ChatMessage.tsx  # Add citation/follow-up rendering
│               ├── ChatInput.tsx    # Add loading state
│               ├── Citation.tsx     # New component
│               └── FollowUpChips.tsx # New component
```

### Dependencies

**Story Dependencies:**
- Story 4.1 (Mem0 Memory) - Memory storage continues to work
- Story 4.3 (Chat Sidebar UI) - Base UI to modify
- Story 5.1 (Agent Framework) - Agent endpoint to call

**Blocked By:** Stories 4.1, 4.3, 5.1

**Enables:**
- Epic 6 & 7 - All future tools accessible through chat

### Testing Strategy

1. **Unit Tests:**
   - Citation component rendering
   - FollowUpChips component rendering
   - ChatMessage citation integration
   - Loading state behavior
   - Error message display

2. **Integration Tests:**
   - Full chat flow with agent
   - Memory storage verification
   - Response transformation

3. **E2E Tests:**
   - Send message, verify agent response
   - Click citation, verify popover
   - Click follow-up chip, verify new message
   - Test loading indicator

4. **Manual Testing:**
   - Test on desktop and mobile
   - Verify citation readability
   - Test chip touch targets
   - Verify memory recall works

### NFR Compliance

- **NFR1 (Accuracy):** Citations displayed clearly for every factual claim
- **NFR2 (Latency):** Loading indicator for requests taking >1 second
- **Industrial Clarity:** Matches existing design system

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#6. User Experience] - UX patterns
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.7] - Story requirements
- [Source: _bmad-output/implementation-artifacts/4-3-chat-sidebar-ui.md] - Existing chat UI
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Design system

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

