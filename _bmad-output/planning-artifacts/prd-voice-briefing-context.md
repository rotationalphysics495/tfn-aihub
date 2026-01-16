# PRD Context: Voice-Enabled Manufacturing Assistant

**Purpose:** Context preservation file for resuming PRD creation workflow
**Created:** 2026-01-15
**Workflow:** `bmad:bmm:workflows:create-prd` - paused at Step 2 (Discovery)

---

## 1. Project Background

**Project:** TFN AI Hub - Manufacturing Performance Assistant
**Type:** Brownfield - extending existing fully-implemented system
**Current State:** 7 epics complete (43 stories, 100% success rate)

### Existing PRDs
1. **Original PRD** (`_bmad/bmm/data/prd.md`) - FR1-FR6, Epics 1-5
2. **PRD Addendum v1.1** (`_bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md`) - FR7 (13 AI tools), NFR4-NFR7, Epics 5-7

### Key Existing Documents
- `_bmad/bmm/data/project-brief.md` - Executive summary, problem statement, target users
- `_bmad/bmm/data/architecture.md` - TurboRepo, Next.js, FastAPI, Supabase, Railway
- `_bmad/bmm/data/ux-design.md` - Personas, design principles, information architecture
- `docs/` - 9 generated documentation files

---

## 2. New Feature Set to Document

### Overview
Extend TFN AI Hub with voice interaction capabilities and structured workflow patterns.

### Feature 1: ElevenLabs Voice Integration
- **Push-to-talk** voice input (control room environment, low noise)
- Text-to-speech responses via ElevenLabs Conversational AI
- **Silence detection** (3-4 seconds) = continue to next section
- Voice + text transcript displayed simultaneously
- Environment: Office/control room (not plant floor)

### Feature 2: Morning Briefing Workflow
- Structured **by-area sequential briefing**
- Areas: Rychiger, CAMA, Packing, Powder, Grinding, Roasting, Green Bean/Flavor
- **Pause after each area** for Q&A before continuing
- Data sourced from **Supabase** (existing pipelines)
- Voice-optimized formatting ("2.1 million" not "2,130,500")

### Feature 3: User Preferences System (Mem0)
- **Role:** Plant Manager vs Supervisor
- **Area order:** User-controlled sequence preference
- **Detail level:** Summary vs Detailed
- **Voice enabled:** On/Off
- **Excluded areas:** Skip certain areas entirely
- **First-time onboarding flow** triggered on ANY first interaction

### Feature 4: Role-Based Personalization
**Plant Manager:**
- Scope: Entire plant, all areas
- Focus: High-level performance, cross-area comparison
- Detail Level: Summary metrics, top wins/concerns only
- Includes plant-wide headline

**Supervisor:**
- Scope: Assigned assets only (1-3 areas typically)
- Focus: Line-by-line detail, actionable issues
- Detail Level: Full downtime breakdown, specific assets
- No plant-wide headline - straight to their areas

### Feature 5: Admin-Configured Asset Assignments
- New DB table: `supervisor_assignments`
- Supervisors see only their assigned lines
- **Admin configures assignments** (not self-service)
- Users can only control **order** of their assigned areas

---

## 3. Key Design Decisions Made

| Decision | Choice |
|----------|--------|
| Voice activation | Push-to-talk (not continuous listening) |
| Pause behavior | Silence detection (3-4 sec) = continue |
| Area order | User-controlled via Mem0 |
| Supervisor assignments | Admin-configured in Supabase |
| Onboarding trigger | First interaction with system |
| Delivery mode | Interactive only (no scheduled push) |
| Historical comparison | Deferred to future phase |

---

## 4. Data Context

### Source Dashboard
`Trilliant_Daily_Dashboard.pdf` - 12-page Power BI report containing:

**7 Production Areas:**
1. Packing (CAMA lines, Pack Cells, Variety Pack, Bag Lines, Nuspark)
2. Rychigers (101-109, 1009)
3. Grinding (Grinders 1-5)
4. Powder (1002-1004 Fill & Pack, Manual Bulk)
5. Roasting (Roasters 1-4)
6. Green Bean (Manual, Silo Transfer)
7. Flavor Room (Coffee Flavor Room - Manual)

**Metrics per Asset:**
- Actual Output (units)
- Target Output (units)
- Schedule Adherence (%)
- OEE (%)
- T-max Output (theoretical max)
- Man Hours (labor allocated)

**Downtime Data:**
- Minutes Lost by Asset
- Minutes Lost by Reason Code
- Problem Type Categories

---

## 5. Technical Architecture Sketched

### Morning Briefing Workflow Stages
1. **Data Aggregation** - Pull from all areas, calculate totals
2. **Analysis & Ranking** - Identify wins (>100% adherence), concerns (gaps), anomalies
3. **Narrative Generation** - Voice-optimized script with structure
4. **Delivery** - Voice (ElevenLabs TTS) or text with pause points

### New Components Needed
1. `MorningBriefingWorkflow` - Orchestrates briefing generation
2. `morning_briefing` tool - Agent-callable workflow trigger
3. Voice response formatter - Transforms data → spoken narrative
4. `BriefingPreferencesService` - Mem0 preference management
5. `supervisor_assignments` table - Admin asset assignments

### Mem0 Schema
```python
UserBriefingPreferences = {
    "user_id": "uuid",
    "role": "plant_manager" | "supervisor",
    "area_order": ["cama", "rychiger", ...],  # User-controlled
    "excluded_areas": [],
    "asset_order": [...],  # Supervisor only
    "detail_level": "summary" | "detailed",
    "voice_enabled": True,
    "onboarding_complete": True
}
```

### Database Schema Addition
```sql
CREATE TABLE supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    asset_name TEXT NOT NULL,
    area TEXT NOT NULL,
    assigned_by UUID REFERENCES auth.users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, asset_name)
);
```

---

## 6. Example Voice Scripts

### Plant Manager Morning Briefing (~75 seconds)
> Good morning. Yesterday across all production areas you moved about 6.7 million units, hitting 87% of your combined target.
>
> No safety incidents were reported.
>
> Three highlights worth celebrating: Pack Cell 2 ran hot at 159% schedule adherence with 334,000 units. CAMA 2400 was your volume leader at 2.1 million units and 97% adherence. And on the fill side, 105 Rychiger led at 112% with 580,000 units.
>
> Three areas that need attention: First, 109 Fill & Pack produced zero units despite 84 man-hours allocated - that's worth a look. Second, 1009 Rychiger Fill only hit 9% adherence - the downtime pareto shows cleaning and lid feeder issues consuming over 4,000 minutes. And third, the Grinders ran at just 30% OEE, with red zone sensor issues being the top loss.
>
> Any questions on [Area] before I continue?

### Pause Handling
- "No" / "Nope" / "Continue" / "Next" → Continue
- Silence (3-4 seconds) → Continue
- Question detected → Answer, then "Anything else on [Area]?"

---

## 7. Onboarding Flow Summary

**Trigger:** ANY first interaction with the system

**Steps:**
1. Welcome + explain quick setup
2. Role identification (Plant Manager vs Supervisor)
3. For Supervisor: Check `supervisor_assignments` table
4. Area order preference (PM) or asset order (Supervisor)
5. Detail level preference (Summary vs Detailed)
6. Voice preference (On/Off)
7. Confirmation + handoff to original request

---

## 8. Classification for PRD

- **Project Type:** web_app (extending existing)
- **Domain:** Manufacturing/Industrial (maps closest to "energy" in complexity)
- **Complexity:** Medium-High (voice integration, multi-role personalization)
- **Context:** Brownfield - extending existing system

---

## 9. Workflow State

**PRD file created:** `_bmad-output/planning-artifacts/prd.md`
**Steps completed:** [1] (Initialization)
**Next step:** Step 2 (Discovery) - needs to complete discovery conversation

**To resume:**
1. Run `/bmad:bmm:workflows:create-prd`
2. Reference this context file for feature details
3. Continue from Step 2 discovery conversation

---

## 10. User Personas (Existing)

From `_bmad/bmm/data/ux-design.md`:

**Plant Manager (Strategic)**
- Reviewer of "Morning Report"
- Needs Daily Action List immediately
- Values Financial impact and Plant-wide OEE

**Line Supervisor (Tactical)**
- Floor-walker with tablet
- Needs "Live Pulse" for specific machine status
- Values Asset details and specific Downtime Codes

---

## 11. Open Questions for PRD Discovery

1. Should voice be MVP or Phase 2? (Text briefings could ship first)
2. Admin UI for supervisor assignments, or just DB + manual config?
3. Should briefing support "compare to last week" in MVP?
4. Any other workflows beyond Morning Briefing to scope now?
