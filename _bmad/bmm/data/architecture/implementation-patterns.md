# Implementation Patterns & Consistency Rules

> **Parent Document:** [architecture.md](../architecture.md)
> **Purpose:** Code patterns and consistency rules for AI agent implementation
> **Applies To:** Core Platform + Voice Briefing Extension

---

## 1. Established Patterns (Inherited from Existing Codebase)

### Backend Tool Pattern

```python
# File: app/services/agent/tools/{tool_name}.py
# Pattern: snake_case filename, docstring with story/AC refs

"""
{Tool Name} Tool (Story X.Y)

{Description}

AC#1: {Acceptance Criteria}
AC#2: {Acceptance Criteria}
"""

class {ToolName}Tool(ManufacturingTool):
    name = "{tool_name}"
    description = "..."
    args_schema: Type[BaseModel] = {ToolName}Input

    async def _arun(self, **kwargs) -> ToolResult:
        # Implementation
        return self._create_success_result(data, citations)
```

### Frontend Component Pattern

```typescript
// File: components/{domain}/{ComponentName}.tsx
// Pattern: PascalCase filename, feature-organized

interface {ComponentName}Props {
  // Props with JSDoc comments
}

export function {ComponentName}({ ... }: {ComponentName}Props) {
  // Implementation
}
```

### Test Location Pattern

```
components/{domain}/
├── {ComponentName}.tsx
└── __tests__/
    └── {ComponentName}.test.tsx
```

---

## 2. Voice Briefing Patterns

### BriefingService Pattern

```python
# File: app/services/briefing/service.py
# NOT a ManufacturingTool - dedicated orchestration service

class BriefingService:
    """Orchestrates briefing generation by composing existing tools."""

    async def generate_morning_briefing(
        self,
        user_id: str,
        role: UserRole
    ) -> BriefingResponse:
        # 1. Load user preferences
        # 2. Get scoped data based on role
        # 3. Compose sections from existing tools
        # 4. Format narrative via LLM
        # 5. Request ElevenLabs stream URL
        return BriefingResponse(sections=..., audio_stream_url=...)
```

### Voice Component Naming

```
components/voice/
├── VoiceControls.tsx        # Play/pause, volume
├── PushToTalkButton.tsx     # STT trigger
├── TranscriptPanel.tsx      # Always-visible transcript
├── BriefingPlayer.tsx       # Orchestrates playback + transcript
└── __tests__/
```

### Handoff Component Naming

```
components/handoff/
├── HandoffCreator.tsx       # Outgoing supervisor UI
├── HandoffViewer.tsx        # Incoming supervisor UI
├── HandoffAcknowledge.tsx   # Acknowledge action
├── HandoffList.tsx          # List of pending/completed
├── VoiceNoteRecorder.tsx    # Voice note attachment
└── __tests__/
```

### New Supabase Tables (snake_case)

```sql
-- Pattern: {domain}_{entity} for new tables
shift_handoffs
handoff_acknowledgments
handoff_voice_notes
user_preferences
user_roles
supervisor_assignments
audit_logs
push_subscriptions
```

### Admin Route Pattern

```
app/(admin)/
├── layout.tsx               # Admin layout with sidebar nav
├── page.tsx                 # Dashboard redirect
├── users/
│   ├── page.tsx            # User list
│   └── [id]/page.tsx       # User detail/edit
└── assignments/
    └── page.tsx            # Asset assignment grid
```

### API Endpoint Pattern for Voice

```
POST /api/v1/briefing/morning      # Generate morning briefing
POST /api/v1/briefing/handoff      # Create shift handoff
GET  /api/v1/briefing/handoff/{id} # Get handoff details
POST /api/v1/briefing/handoff/{id}/acknowledge
POST /api/v1/briefing/eod          # Generate EOD summary

# Voice-specific
POST /api/v1/voice/tts-url         # Get ElevenLabs stream URL
WS   /api/v1/voice/stt             # WebSocket for push-to-talk
```

### Service Worker Organization

```
apps/web/
├── public/
│   └── sw.js                      # Service Worker entry
├── src/
│   └── lib/
│       └── offline/
│           ├── handoff-cache.ts   # IndexedDB operations
│           ├── sync-queue.ts      # Offline action queue
│           └── sw-registration.ts # SW lifecycle
```

---

## 3. Consistency Rules for AI Agents

### All AI Agents MUST:

1. Follow existing `ManufacturingTool` pattern for any new AI tools
2. Use `ToolResult` with `Citation` for all data-returning operations
3. Use `snake_case` for Python files, `PascalCase` for TypeScript components
4. Co-locate tests in `__tests__/` folders
5. Reference Story/AC numbers in docstrings
6. Use existing Pydantic models where applicable, extend don't duplicate

### BriefingService Specific Rules:

1. BriefingService is NOT a ManufacturingTool - it orchestrates tools
2. All briefing data must include citations from underlying tools
3. `audio_stream_url` must be nullable for graceful degradation
4. Section-based output required for pause-point Q&A

### Voice Integration Rules:

1. Text transcript must always be generated, even if voice fails
2. ElevenLabs errors must never surface to user - fallback to text
3. Push-to-talk must show clear visual feedback during recording
4. All voice components must have text-only fallback variants

### Offline Rules:

1. Only cache handoff records, never briefings
2. Acknowledgments queued offline must sync on reconnect
3. IndexedDB operations must handle quota exceeded errors
4. Service Worker must not cache API responses except handoffs

---

## 4. Naming Conventions Summary

| Domain | Python Files | TypeScript Files | Database Tables |
|--------|-------------|------------------|-----------------|
| General | `snake_case.py` | `PascalCase.tsx` | `snake_case` |
| Tools | `{tool_name}.py` | - | - |
| Components | - | `{ComponentName}.tsx` | - |
| Services | `{service_name}/service.py` | - | - |
| API Routes | `{domain}.py` | `app/(group)/{route}/page.tsx` | - |
| Tables | - | - | `{domain}_{entity}` |

---

## Related Documents

- **Parent:** [architecture.md](../architecture.md) - Core platform architecture
- **Voice Extension:** [voice-briefing.md](./voice-briefing.md) - Voice feature decisions
- **Validation:** [validation-results.md](./validation-results.md) - Architecture validation & readiness
