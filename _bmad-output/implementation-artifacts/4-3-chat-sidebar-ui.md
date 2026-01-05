# Story 4.3: Chat Sidebar UI

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager or Line Supervisor**,
I want **an overlay/sidebar chat interface following the Industrial Clarity design system**,
so that **I can query complex factory data using natural language without leaving my current view**.

## Acceptance Criteria

1. **Chat Sidebar Component**: A collapsible sidebar/overlay component exists that can be triggered from anywhere in the application
2. **Industrial Clarity Compliance**: The chat interface follows the established Industrial Clarity design system (high-contrast, factory-floor readable, proper color semantics)
3. **Message Display**: Chat messages display in a scrollable conversation view with clear visual distinction between user messages and AI responses
4. **Input Interface**: A text input field with send button allows users to type and submit natural language queries
5. **Loading States**: Visual feedback (loading indicators) displays while AI responses are being generated
6. **Citation Display**: AI responses include a structured area for displaying data citations/evidence (NFR1 compliance preparation)
7. **Responsive Design**: Sidebar functions correctly on tablet (primary) and desktop viewports
8. **Keyboard Accessibility**: Chat interface is fully keyboard navigable (Tab, Enter to send, Escape to close)

## Tasks / Subtasks

- [ ] Task 1: Create ChatSidebar Container Component (AC: #1, #2)
  - [ ] 1.1 Create `ChatSidebar.tsx` component in `apps/web/src/components/chat/`
  - [ ] 1.2 Implement slide-in/out animation for sidebar (right-side overlay)
  - [ ] 1.3 Add backdrop overlay with proper opacity for focus
  - [ ] 1.4 Implement open/close state management with React useState or context
  - [ ] 1.5 Add close button and Escape key handler

- [ ] Task 2: Create Chat Trigger Component (AC: #1, #8)
  - [ ] 2.1 Create `ChatTrigger.tsx` floating action button component
  - [ ] 2.2 Position fixed at bottom-right corner of viewport
  - [ ] 2.3 Use appropriate icon (MessageSquare or similar from lucide-react)
  - [ ] 2.4 Apply Industrial Clarity styling with high-contrast visibility
  - [ ] 2.5 Add keyboard focus states

- [ ] Task 3: Build Message List Component (AC: #3, #6)
  - [ ] 3.1 Create `MessageList.tsx` for conversation display
  - [ ] 3.2 Implement scrollable container with auto-scroll to latest message
  - [ ] 3.3 Create `ChatMessage.tsx` for individual message rendering
  - [ ] 3.4 Style user messages (right-aligned, distinct background)
  - [ ] 3.5 Style AI messages (left-aligned, different background)
  - [ ] 3.6 Add citation display area within AI messages (collapsible section for evidence)

- [ ] Task 4: Build Chat Input Component (AC: #4, #8)
  - [ ] 4.1 Create `ChatInput.tsx` with textarea and send button
  - [ ] 4.2 Implement auto-expanding textarea (up to max height)
  - [ ] 4.3 Add Enter key submission (Shift+Enter for newline)
  - [ ] 4.4 Disable send button when input is empty
  - [ ] 4.5 Focus input automatically when sidebar opens

- [ ] Task 5: Implement Loading States (AC: #5)
  - [ ] 5.1 Create loading indicator component (animated dots or spinner)
  - [ ] 5.2 Show loading state after message submission
  - [ ] 5.3 Add "thinking" placeholder message while AI processes

- [ ] Task 6: Responsive Design Implementation (AC: #7)
  - [ ] 6.1 Set sidebar width: 400px desktop, 100% width on tablet/mobile
  - [ ] 6.2 Test at tablet breakpoints (768px - 1024px)
  - [ ] 6.3 Ensure touch-friendly button sizes (min 44px touch targets)

- [ ] Task 7: Integrate with Layout and Global State (AC: #1)
  - [ ] 7.1 Create ChatContext or use existing state management for open/close state
  - [ ] 7.2 Add ChatSidebar to root layout (`apps/web/src/app/layout.tsx`)
  - [ ] 7.3 Add ChatTrigger to layout or Command Center page
  - [ ] 7.4 Create mock message state for development/demo purposes

## Dev Notes

### Architecture Patterns

Per Architecture document Section 4 (Repository Structure):
- Frontend components go in `apps/web/src/components/`
- Chat-specific components: `apps/web/src/components/chat/`
- This story is UI-only - actual AI integration happens in Stories 4.1 (Mem0), 4.2 (LangChain), 4.4 (Asset Memory), 4.5 (Citations)
- Use placeholder mock data for chat messages during development

### Technical Stack Requirements

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14+ (App Router) | UI Framework |
| Tailwind CSS | 3.4+ | Styling (from Story 1.6) |
| Shadcn/UI | Latest | Component library (from Story 1.6) |
| Radix UI Primitives | Latest | Dialog/Sheet primitives for sidebar |
| lucide-react | Latest | Icons (MessageSquare, Send, X) |

### Industrial Clarity Design Requirements

From Story 1.6 and UX Design document:

**Color Usage:**
- DO NOT use "Safety Red" (#DC2626) - reserved exclusively for safety incidents
- Use `info-blue` (#3B82F6) for user messages
- Use `industrial-gray` neutrals for AI messages
- Use high-contrast text colors for factory floor readability

**Typography:**
- Minimum 16px body text for chat messages
- Clear visual hierarchy between message sender and content
- Readable from 3 feet away on tablet

**Visual Context:**
- Chat sidebar should NOT use "Live" mode pulsing indicators (it's a tool, not a status display)
- Use subtle, professional styling appropriate for an AI assistant interface

### Component Architecture

```
apps/web/src/components/chat/
  ChatSidebar.tsx        # Main container with open/close logic
  ChatTrigger.tsx        # Floating action button to open chat
  ChatMessage.tsx        # Individual message bubble
  MessageList.tsx        # Scrollable message container
  ChatInput.tsx          # Text input with send button
  ChatLoadingIndicator.tsx  # Loading/thinking state
  index.ts               # Barrel exports
```

### Shadcn/UI Components to Use

- **Sheet** (from Radix UI Dialog) - For sidebar overlay behavior
- **Button** - For send button and close button
- **Input** or **Textarea** - For message input
- **ScrollArea** - For scrollable message list
- **Card** - For message bubbles (optional)

Install Sheet component if not already present:
```bash
npx shadcn@latest add sheet
npx shadcn@latest add scroll-area
npx shadcn@latest add textarea
```

### State Management Approach

For this UI-only story, use local React state:
```typescript
// ChatSidebar.tsx
const [isOpen, setIsOpen] = useState(false);
const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
const [inputValue, setInputValue] = useState('');
const [isLoading, setIsLoading] = useState(false);
```

When Stories 4.1-4.2 are implemented, this will be refactored to:
- Connect to API endpoints for real AI responses
- Integrate Mem0 memory context
- Use LangChain Text-to-SQL for data queries

### Mock Data for Development

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
}

interface Citation {
  source: string;      // e.g., "daily_summaries"
  dataPoint: string;   // e.g., "OEE: 78.3%"
  timestamp?: string;  // When the data was from
}

const MOCK_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'user',
    content: 'What was the OEE for Grinder 5 yesterday?',
    timestamp: new Date(),
  },
  {
    id: '2',
    role: 'assistant',
    content: 'Grinder 5 had an OEE of 78.3% yesterday, which is 6.7% below the target of 85%. The main contributing factor was a 45-minute unplanned stop due to bearing overheating.',
    timestamp: new Date(),
    citations: [
      { source: 'daily_summaries', dataPoint: 'OEE: 78.3%' },
      { source: 'downtime_events', dataPoint: 'Bearing overheat - 45min' },
    ],
  },
];
```

### Accessibility Requirements

- All interactive elements must be keyboard accessible
- ARIA labels for buttons and input fields
- Focus trap within sidebar when open
- Announce new messages to screen readers (aria-live region)
- Minimum touch target size of 44x44px

### Integration Points (Future Stories)

| Story | Integration |
|-------|-------------|
| 4.1 (Mem0) | Chat will use Mem0 for session memory and context |
| 4.2 (LangChain) | Text-to-SQL will power data queries |
| 4.4 (Asset History) | Asset-specific memory retrieval |
| 4.5 (Citations) | Citation display will link to raw data |

### Testing Requirements

- Visual inspection on tablet (768px) and desktop (1280px) viewports
- Keyboard navigation testing (Tab through all elements)
- Test sidebar open/close animations
- Verify responsive behavior at breakpoints
- No unit tests required for pure UI components (will be added with API integration)

### Project Structure Notes

Files to create:
- `apps/web/src/components/chat/ChatSidebar.tsx`
- `apps/web/src/components/chat/ChatTrigger.tsx`
- `apps/web/src/components/chat/ChatMessage.tsx`
- `apps/web/src/components/chat/MessageList.tsx`
- `apps/web/src/components/chat/ChatInput.tsx`
- `apps/web/src/components/chat/ChatLoadingIndicator.tsx`
- `apps/web/src/components/chat/index.ts`
- `apps/web/src/components/chat/types.ts` (Message, Citation interfaces)
- `apps/web/src/components/chat/mockData.ts` (MOCK_MESSAGES)

Files to modify:
- `apps/web/src/app/layout.tsx` - Add ChatSidebar and ChatTrigger

### Dependencies

**Requires (must be completed first):**
- Story 1.1: TurboRepo Monorepo Scaffold (apps/web structure)
- Story 1.6: Industrial Clarity Design System (Tailwind, Shadcn/UI)
- Story 1.7: Command Center UI Shell (layout structure)

**Enables (unblocks):**
- Story 4.5: Cited Response Generation (needs UI for displaying citations)
- Story 4.4: Asset History Memory (needs UI for contextual queries)

### References

- [Source: _bmad/bmm/data/architecture.md#3. Tech Stack] - Next.js, Tailwind CSS, Shadcn/UI
- [Source: _bmad/bmm/data/architecture.md#4. Repository Structure] - apps/web/src/components structure
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 integration context
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Zero-Training Interface, Trust & Transparency
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - AI Analyst Chat as Overlay/Sidebar
- [Source: _bmad/bmm/data/prd.md#2. Requirements FR6] - AI Chat with Memory requirement
- [Source: _bmad-output/planning-artifacts/epic-4.md] - Epic 4 context and story relationships
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Design system details
- [Source: _bmad-output/implementation-artifacts/1-7-command-center-ui-shell.md] - UI shell patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
