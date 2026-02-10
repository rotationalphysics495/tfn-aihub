# TFN AI Hub — Improvements Tracker

Tracking planned and completed improvements to the Manufacturing Performance Assistant.

---

## Completed

### Root redirect for unauthenticated users
- **Files changed:** `apps/web/src/middleware.ts`
- **Description:** Previously, unauthenticated users hitting `/` saw a generic placeholder page. Now `/` redirects to `/login` for unauthenticated users and `/morning-report` for authenticated users.

### Coffee-manufacturing-specific action item descriptions
- **Files changed:** `apps/api/app/services/action_engine.py`, `scripts/seed-data.mjs`
- **Description:** Action item recommendation text was generic (e.g., "Review performance on Unknown"). Updated the action engine to produce descriptive, contextual text:
  - **Safety:** Includes the first sentence of the event description (e.g., "Investigate vibration alarm on Grinder 2 — vibration at 7.9mm/s approaching critical threshold")
  - **OEE:** Includes downtime and units-short context (e.g., "Review Grinder 5 — OEE 12.5% below target (72min downtime, 342 units short)")
  - **Financial:** Includes loss drivers (e.g., "Address $210 production loss on Grinder 5 driven by 72min downtime, 35 units waste")
- Seed data safety events updated with specific reason codes (`Vibration Alarm`, `Chaff Fire`, `Pressure Anomaly`, `Light Curtain Trip`) replacing generic `Safety Issue`.

### CORS support for alternate dev port
- **Files changed:** `apps/api/app/main.py`
- **Description:** Added `http://localhost:3001` to CORS allowed origins so the frontend works when port 3000 is occupied.

### Dashboard Daily Action List wired to live data
- **Files changed:** `apps/web/src/components/dashboard/ActionListSection.tsx`
- **Description:** The Command Center dashboard had a static placeholder ("Coming in Epic 3") for the Daily Action List. Replaced it with the `InsightEvidenceCardList` component that fetches real data from the Action Engine API.

### Fixed asset name resolution ("Unknown" bug)
- **Files changed:** `apps/api/app/services/action_engine.py`
- **Description:** All action items showed "Unknown" as the asset name. Root cause: the `_load_assets()` query selected `cost_center_id` which doesn't exist in the `assets` table, causing the entire query to fail silently. Also fixed `_load_shift_targets()` which queried a non-existent `target_oee` column.

### Adjusted action engine thresholds for realistic data
- **Files changed:** `apps/api/app/core/config.py`
- **Description:** Financial loss threshold was $1,000 (no items qualified with real data). Adjusted to $150. OEE gap thresholds also adjusted (high: 20% -> 15%, medium: 10% -> 5%) to surface more actionable items.

### Removed broken "View Details" link on evidence cards
- **Files changed:** `apps/web/src/components/action-engine/EvidenceSection.tsx`
- **Description:** The "View Details" link pointed to `/evidence/{recordId}` — a page that doesn't exist. Removed the dead link to prevent 404s. Evidence detail drill-down page is a planned feature.

### Added today's partial-day seed data
- **Files changed:** `scripts/seed-data.mjs`
- **Description:** Added `daysAgo(0)` entries for 8 key assets with realistic partial-day production data for the current shift, including safety-related downtime on Grinder 2 and Filler Line A.

---

## Planned

### Action item acknowledgment flow
- **Status:** Not started
- **Description:** Currently there is no way for users to mark action items as reviewed or completed. Actions are ephemeral — regenerated daily from raw data with no persistence of user interactions.
- **Proposed approach:**
  - **Database:** New `action_acknowledgments` table (following the existing `handoff_acknowledgments` pattern)
  - **API:** `POST /api/v1/actions/{action_id}/acknowledge` endpoint
  - **Frontend:** Checkbox or button on each action card with optimistic UI updates
- **Open questions:**
  - Full DB-backed persistence vs. lightweight localStorage for the day?
  - Should acknowledged items be hidden, grayed out, or moved to a separate section?
  - Should there be an audit trail of who acknowledged what and when?

### Follow-up status tracking & "My Assignments" view
- **Status:** Not started
- **Priority:** P1
- **Description:** The assign follow-up button currently writes to `action_followups` but there's no visibility into assignments afterward. The loop is open — the manager assigns, and then has no way to check status without asking in person.
- **Proposed approach:**
  - **"My Assignments" panel** on the morning report page showing all open follow-ups the manager has created, grouped by status (assigned / in-progress / resolved). Should be accessible without leaving the report.
  - **Assignee status updates** — engineers/supervisors can mark follow-ups as "in progress" or "resolved" with a short note explaining what they found or did.
  - **Assignment badge on action cards** — if an action item already has a follow-up assigned, show who it's assigned to directly on the card. During morning meetings the manager needs to see at a glance: "this one's already being looked at by Carlos."
  - **RLS update** — assignees need UPDATE permission on their own follow-ups (currently only the assigner can update).
- **Open questions:**
  - Should resolved follow-ups persist for an audit trail, or archive after N days?
  - Should the assignee see follow-ups on their own morning report view?

### Trend indicators on action items
- **Status:** Not started
- **Priority:** P1
- **Description:** The report shows T-1 data with zero historical context. A plant manager seeing "Grinder 5 OEE at 72.5%" immediately asks "is this new or has it been trending down?" — and the report can't answer that. This is the single biggest intelligence gap.
- **Proposed approach:**
  - **7-day sparkline or trend arrow** on each action item showing recent history for that asset+metric.
  - **Repeat offender badge** — "3rd consecutive day on the report" or "appeared 4 of last 7 days." This is the trigger that separates "operator can handle it" from "escalate to maintenance planning."
  - **Week-over-week comparison** in the AI summary header — "Overall plant OEE 81.2%, down 3.1 points from last week."
  - **Backend:** Query `daily_summaries` for the trailing 7 days per asset when building action items. Add `trend_data` field to the ActionItem response model.
- **Open questions:**
  - Sparkline vs. simple arrow indicator? Sparkline is richer but adds visual complexity.
  - Should repeat offender logic count consecutive days, or appearances in last N days?

### Teams push notifications
- **Status:** Not started
- **Priority:** P2
- **Description:** The report only exists when the manager opens the app. For adoption, the app needs to reach out to the manager, not wait to be found.
- **Proposed approach:**
  - **Morning summary card at 6:15 AM** — post to a configured Teams channel via webhook: "3 action items this morning: 1 safety event, 2 OEE misses. [Open Report]". This is the daily hook that builds the habit.
  - **Follow-up assignment notification** — when a task is assigned, DM or channel-mention the assignee in Teams so they know immediately without needing to check the app.
  - **Escalation nudges** — if a safety event goes unacknowledged for 2 hours, ping the manager again. If a follow-up sits in "assigned" for 24 hours with no update, nudge the assignee.
  - **Implementation:** Teams Incoming Webhooks for channel posts, Microsoft Graph API or Power Automate for DMs/mentions.
- **Open questions:**
  - Teams Incoming Webhooks (simple, channel-only) vs. Graph API (richer, supports DMs but requires app registration)?
  - Should escalation timing be configurable per-plant?

### Conversational follow-up on AI summary
- **Status:** Not started
- **Priority:** P3
- **Description:** The smart summary is a static markdown blob. A plant manager reading "Grinder 5 had 72 minutes of downtime" will immediately want to ask "what was the root cause?" or "how does this compare to last week?" — but there's no way to do that from the report.
- **Proposed approach:**
  - **"Ask about this" button** on the summary section that opens the existing AI chat with the morning report context pre-loaded (summary text, action items, evidence data).
  - **Drill-down links in summary text** — when the AI mentions an asset name, make it a clickable link to the asset detail page. Action cards already do this; the summary narrative should too.
  - **Context injection:** Pass the `SummaryContext` object into the chat session so the LLM can answer follow-up questions without the user re-explaining what they're looking at.

### Workcenter production summary (how much did we make?)
- **Status:** Not started
- **Priority:** P1
- **Description:** The plant manager's first question in the morning is "how much did we produce?" — broken down by workcenter (Roasting, Grinding, Filling, Packaging) and then by individual asset within each. The current report only surfaces assets that *missed* targets. It doesn't show the full picture: what ran well, what didn't, and how the plant performed as a whole.
- **What exists today:**
  - `assets` table has an `area` column (Roasting, Grinding, Filling, Packaging) — workcenter grouping is already in the data model.
  - `daily_summaries` has `actual_output`, `target_output`, `oee_percentage` per asset per day.
  - `shift_targets` has per-shift quantity targets per asset.
  - The morning report only shows assets that missed OEE or financial thresholds — good assets are invisible.
- **Proposed approach:**
  - **Workcenter scorecard section** at the top of the morning report, above the action items. One row per workcenter showing:
    - Total actual output vs. total target output (aggregated across assets in that area)
    - Workcenter-level attainment % (actual / target)
    - Number of assets that hit target vs. missed
  - **Expandable asset detail** — click a workcenter row to see per-asset breakdown: asset name, actual vs. target, OEE, downtime minutes. Color-coded green/red for hit/miss.
  - **Backend:** New API endpoint `GET /api/v1/production/workcenter-summary?date={date}` that groups `daily_summaries` by `assets.area`, aggregates output, and returns the scorecard data.
  - **Visual:** Horizontal stacked bar or simple table. Keep it scannable — the manager should absorb the whole plant in 5 seconds.
- **Key principle:** Show the full picture first (all workcenters, all assets), then let the action items below call out what needs attention. The report should answer "how did we do?" before "what went wrong?"

### Schedule attainment & product mix (did we make the RIGHT stuff?)
- **Status:** Not started
- **Priority:** P1
- **Description:** Producing 100% of target quantity means nothing if you ran the wrong product. The plant manager needs to know: did we produce what was scheduled? Did we hit the right blend of products? This is the gap between "we made enough" and "we made what the customer needs." Currently, the system has no concept of *what* was produced — only *how much*. Product/blend information exists only as unstructured text in AI-generated summaries, not as queryable data.
- **What exists today:**
  - `shift_targets` tracks quantity targets per asset per shift, but has no product/SKU reference.
  - `daily_summaries` tracks actual output counts, but no product breakdown.
  - No `products`, `production_orders`, or `schedule` tables exist.
  - Product names appear only in `smart_summary_text` narrative (e.g., "Colombian single-origin", "Dark roast blend") — not structured or queryable.
- **Proposed approach — Data model:**
  - **`products` table** — SKU/blend master data: `id`, `name`, `sku`, `product_family` (e.g., "Single Origin", "Blend", "Flavored"), `unit_of_measure`.
  - **`production_schedule` table** — what should have been produced: `id`, `asset_id`, `product_id`, `scheduled_quantity`, `scheduled_date`, `shift`, `production_order_ref` (optional link to AX/D365 PO number).
  - **`production_actuals` table** — what was actually produced by product: `id`, `asset_id`, `product_id`, `actual_quantity`, `production_date`, `shift`. This replaces the single `actual_output` number in `daily_summaries` with product-level detail.
- **Proposed approach — Frontend:**
  - **Schedule attainment section** on the morning report, between the workcenter scorecard and the action items:
    - Per-workcenter: scheduled vs. actual by product, with attainment %.
    - **Variance callouts:** "Roaster 1 ran Colombian instead of scheduled Brazilian" or "Filler Line A produced 80% K-Cup, 20% bag — schedule called for 100% K-Cup."
    - **Overall product mix chart** — planned vs. actual mix as a simple bar or pie comparison.
  - **Action item integration** — when schedule attainment misses (wrong product, underproduction of a specific SKU), the action engine should generate an action item: "Grinder 3 produced Medium Grind instead of scheduled Espresso Grind — 1,200 units of Espresso still needed for PO #4821."
- **Data integration dependency:** This feature requires structured production schedule data. Two paths:
  1. **Manual/seed approach** (MVP) — populate `production_schedule` from a CSV upload or seed script based on the weekly plan. Good enough to prove the concept.
  2. **AX/D365 integration** (production) — pull production orders and scheduled quantities from Dynamics via API. This is the Phase 1 data integration work already on the roadmap.
- **Open questions:**
  - Should `production_actuals` replace `daily_summaries.actual_output` or supplement it? Keeping both means reconciliation logic; replacing it is cleaner but a bigger migration.
  - How granular should product tracking be? SKU-level (Colombian 12oz bag) vs. product-family-level (Single Origin)?
  - Does Redzone already capture what product was running on each line, or is that only in AX?

### Schedule upload (CSV/Excel) + seed data
- **Status:** Not started
- **Priority:** P1
- **Description:** The schedule attainment feature requires production schedule data, but no integration with AX/D365 exists yet. To unblock the feature, the plant manager or planner needs a way to upload the weekly production schedule directly — a CSV or Excel file mapping assets to products and quantities by date/shift. The system should also ship with realistic seed data so the feature is demonstrable out of the box.
- **Proposed approach — Upload:**
  - **Upload page** at `/settings/schedule-upload` (or inline on the morning report as a setup prompt when no schedule exists for the current week).
  - **Accepted formats:** CSV and Excel (.xlsx). Drag-and-drop or file picker.
  - **Expected columns:** `date`, `shift` (morning/afternoon/night), `asset_name` (matched against `assets` table), `product_name` or `sku` (matched against `products` table), `scheduled_quantity`, `production_order_ref` (optional).
  - **Validation on upload:**
    - Asset names must match existing assets (fuzzy match with suggestions for near-misses).
    - Product names auto-create if not found in `products` table (with a confirmation prompt showing what will be created).
    - Dates must be valid, quantities must be positive numbers.
    - Show a preview table of parsed rows before committing, with errors highlighted in red.
  - **Upsert behavior:** Re-uploading for the same date range replaces existing schedule rows (with confirmation). This lets planners update mid-week.
  - **Backend:** `POST /api/v1/schedule/upload` — accepts multipart form data, parses CSV/XLSX (using `openpyxl` or `pandas`), validates, and inserts into `production_schedule` table.
- **Proposed approach — Seed data:**
  - **`products` seed:** ~10 products representing a realistic coffee plant mix:
    - Roasting: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend
    - Grinding: Espresso Grind, Medium Grind, Coarse Grind, French Press
    - Filling: K-Cup, 12oz Bag, 5lb Bag
  - **`production_schedule` seed:** 7 days of schedule data across all assets, with realistic product assignments (e.g., Roaster 1 runs Colombian Monday-Wednesday, Brazilian Thursday-Friday).
  - **`production_actuals` seed:** Matching actuals with realistic variances — some on-schedule, some product swaps, some underproduction — so the schedule attainment view has interesting data to display.
- **Open questions:**
  - Should we support Google Sheets import as well, or is CSV/Excel sufficient?
  - Should the upload be per-week or per-day? Weekly is more natural for planning, but daily allows corrections.

### Email notifications with response tracking
- **Status:** Not started
- **Priority:** P1
- **Description:** When a plant manager assigns a follow-up task, the assignee needs to know about it immediately — and the manager needs to see the response without chasing people down. Email is the universal fallback: everyone has it, it works on every device, and it doesn't require the assignee to log into the app. Critically, the full conversation (what was sent, what was replied, and when) must be logged in the database to build an audit trail and feed the action plan feature.
- **Proposed approach — Outbound email:**
  - **Trigger:** When a follow-up is assigned via `AssignFollowUpDialog`, send an email to the assignee.
  - **Email content:**
    - Subject: `[Action Required] {category} — {asset_name}: {action_summary}`
    - Body: The action item details (recommendation, evidence summary, financial impact), who assigned it, the optional note, and a "Respond" link/button.
    - Reply-to address: A unique inbound address per follow-up (see below) OR a link to the app's response form.
  - **Email provider:** SendGrid, AWS SES, or Microsoft 365 SMTP (likely M365 since the org already uses it). Configure via environment variables.
- **Proposed approach — Response capture:**
  - **Option A: Email reply parsing (richer UX, more complex)**
    - Generate a unique reply-to address per follow-up: `followup+{followup_id}@{domain}` or use a catch-all address with the ID in the subject line.
    - Inbound email webhook (SendGrid Inbound Parse or similar) receives replies, extracts the body text, and logs it as a response.
    - Assignees just hit "reply" in their email client — zero friction.
  - **Option B: In-app response via email link (simpler)**
    - Email contains a link: `{app_url}/followups/{id}/respond?token={one_time_token}`
    - Link opens a simple form: text field + submit button. No login required (token-authenticated).
    - Response is saved to the database.
  - **Recommendation:** Start with Option B (link-based response) for MVP. Add email reply parsing later if adoption proves the workflow.
- **Proposed approach — Data model:**
  - **`followup_messages` table:**
    - `id` UUID primary key
    - `followup_id` UUID references `action_followups(id)`
    - `sender_id` UUID references `auth.users(id)` (nullable for email replies from non-app-users)
    - `sender_email` TEXT
    - `direction` TEXT CHECK ('outbound', 'inbound') — outbound = notification sent, inbound = response received
    - `message_type` TEXT CHECK ('assignment', 'response', 'escalation', 'status_update')
    - `subject` TEXT
    - `body` TEXT
    - `sent_at` TIMESTAMP — when the email was sent or received
    - `created_at` TIMESTAMP
  - **Indexes:** `followup_id`, `direction`, `sent_at`
  - **RLS:** Same pattern as `action_followups` — visible to assigner and assignee.
- **Proposed approach — Frontend:**
  - **Message thread on follow-up detail:** When viewing a follow-up (from "My Assignments" panel or action card), show the full conversation thread: assignment notification sent at 6:15 AM, response received at 8:42 AM with the engineer's findings, status update at 2:00 PM.
  - **Unread indicator:** If a response has come in that the manager hasn't viewed, show a badge on the action card / assignments panel.
- **Open questions:**
  - M365 SMTP vs. SendGrid vs. AWS SES? M365 aligns with existing org infrastructure but may have IT approval hurdles.
  - Should escalation reminders also go via email, or just Teams?
  - Do we need to handle the case where the assignee doesn't have an email in the `auth.users` table?

### Action plans (continuous improvement from investigations)
- **Status:** Not started
- **Priority:** P1
- **Description:** The end goal of the assign→investigate→respond loop isn't just to fix today's problem — it's to prevent it from happening again. When an engineer investigates a vibration alarm and discovers the bearing is worn, that finding should feed into a structured action plan: "Replace bearing on Grinder 5, schedule PM every 90 days." Over time, these action plans become the plant's continuous improvement record — connecting shopfloor issues to root causes to corrective actions to results.
- **How it connects to the workflow:**
  1. Morning report surfaces the issue (action item: "Grinder 5 OEE below target")
  2. Manager assigns investigation to an engineer (follow-up)
  3. Engineer investigates and responds via email: "Bearing worn, causing excessive vibration and unplanned stops"
  4. Manager (or engineer) creates an action plan from the investigation findings
  5. Action plan tracks corrective action to completion
  6. Next time Grinder 5 appears on the report, the system shows: "Active action plan exists — bearing replacement scheduled for Friday"
- **Proposed approach — Data model:**
  - **`action_plans` table:**
    - `id` UUID primary key
    - `title` TEXT — short description (e.g., "Replace worn bearing on Grinder 5")
    - `description` TEXT — full context, root cause analysis
    - `asset_id` UUID references `assets(id)` (nullable — some plans are plant-wide)
    - `category` TEXT CHECK ('corrective', 'preventive', 'improvement') — corrective = fix the issue, preventive = stop it from recurring, improvement = general optimization
    - `root_cause` TEXT — what was found during investigation
    - `corrective_action` TEXT — what needs to be done
    - `preventive_action` TEXT — what changes to prevent recurrence (e.g., "add to PM schedule")
    - `source_followup_id` UUID references `action_followups(id)` (nullable — links back to the investigation that spawned this plan)
    - `owner_id` UUID references `auth.users(id)` — who's responsible for driving the plan
    - `status` TEXT CHECK ('draft', 'open', 'in_progress', 'completed', 'verified')
    - `priority` TEXT CHECK ('low', 'medium', 'high', 'critical')
    - `due_date` DATE
    - `completed_at` TIMESTAMP
    - `verified_by` UUID references `auth.users(id)` — who confirmed the fix worked
    - `verified_at` TIMESTAMP
    - `created_at`, `updated_at` TIMESTAMP
  - **`action_plan_updates` table** — log of progress updates:
    - `id` UUID primary key
    - `action_plan_id` UUID references `action_plans(id)`
    - `author_id` UUID references `auth.users(id)`
    - `update_text` TEXT
    - `status_change` TEXT (nullable — e.g., "open → in_progress")
    - `created_at` TIMESTAMP
- **Proposed approach — Integration with morning report:**
  - **"Create Action Plan" button** on follow-up responses — when an engineer's investigation reveals a root cause, the manager can one-click create an action plan pre-populated with the asset, the issue, and the engineer's findings.
  - **Active plans badge on action items** — if Grinder 5 has an open action plan, the morning report action card shows: "Action plan: bearing replacement (due Friday, in progress)." This prevents redundant assignments and shows the team is already working on it.
  - **Action plan dashboard** — a separate view (`/action-plans`) showing all open plans grouped by status, with overdue items highlighted. This becomes the plant's continuous improvement tracker.
- **Proposed approach — AI integration:**
  - When generating the smart summary, include active action plans in the context. The AI can then say: "Grinder 5 OEE is still below target — note that a corrective action plan is in progress (bearing replacement, due Friday)."
  - Over time, with enough action plan data, the AI can start suggesting patterns: "3 of the last 5 action plans for Grinder 5 are bearing-related — consider a capital replacement review."
- **Open questions:**
  - Should action plans have sub-tasks, or keep it flat with updates?
  - How does this relate to existing CMMS/maintenance systems? Should action plans push work orders to the maintenance system?
  - Should there be a "verification" step where someone confirms the fix actually improved performance (checking OEE after the corrective action)?

### Downtime Pareto (why did we lose time?)
- **Status:** Not started
- **Priority:** P1
- **Description:** The report shows *that* downtime happened and what it cost, but not *why*. "Grinder 5 had 72 minutes of downtime" immediately raises "what were the top reasons?" — mechanical failure? Changeover? Waiting on material? Redzone captures downtime reason codes at the event level, but the morning report rolls them up into a single number. Without a Pareto breakdown, the manager can't direct investigations effectively — they're assigning "go look at Grinder 5" instead of "go look at why Grinder 5 had 45 minutes of mechanical downtime."
- **What exists today:**
  - `daily_summaries` has `downtime_minutes` as a single aggregate number per asset per day. No reason code breakdown.
  - Redzone (source system) captures individual downtime events with reason codes, duration, and timestamps. This data isn't currently pulled into the app.
  - The `safety_events` table captures safety-specific events but not general downtime reasons.
- **Proposed approach — Data model:**
  - **`downtime_events` table:**
    - `id` UUID primary key
    - `asset_id` UUID references `assets(id)`
    - `event_date` DATE
    - `shift` TEXT CHECK ('morning', 'afternoon', 'night')
    - `reason_code` TEXT (e.g., "Mechanical", "Changeover", "Material Shortage", "Quality Hold", "Operator Unavailable", "Planned Maintenance")
    - `reason_detail` TEXT (freeform — e.g., "Bearing failure on main drive")
    - `duration_minutes` INTEGER
    - `is_planned` BOOLEAN — distinguishes planned downtime (changeovers, PM) from unplanned
    - `source_system` TEXT DEFAULT 'manual' — 'redzone', 'manual', 'ignition'
    - `source_event_id` TEXT (nullable — reference back to Redzone event ID)
    - `created_at` TIMESTAMP
  - **Indexes:** `asset_id`, `event_date`, `reason_code`
- **Proposed approach — Frontend:**
  - **Pareto chart on each action item** with downtime — horizontal bar chart showing top 3-5 reason codes sorted by duration. Example: Mechanical (45 min) | Changeover (18 min) | Material Wait (9 min).
  - **Workcenter-level Pareto** in the workcenter scorecard section — aggregate downtime reasons across all assets in that area. "Grinding area: 142 total downtime minutes — 68% mechanical, 22% changeover, 10% other."
  - **Plant-level Pareto** in the AI summary or header metrics — "Top downtime driver yesterday: Mechanical (187 min across 4 assets)."
- **Proposed approach — AI integration:**
  - Feed downtime reason breakdown into the smart summary context so the AI can say: "Grinder 5 lost 72 minutes — primarily mechanical (bearing-related, 45 min). This is consistent with the vibration alarms logged this week."
  - Connect to action plans: if a downtime reason keeps showing up in the Pareto, the AI should flag it as a candidate for a preventive action plan.
- **Data integration dependency:** Requires downtime event data. Two paths:
  1. **Seed/manual approach** (MVP) — populate `downtime_events` via seed data and allow manual entry through the app. Good enough to prove the visualization.
  2. **Redzone integration** (production) — pull downtime events with reason codes from Redzone API. This is the richest path since Redzone is where operators log downtime in real time.
- **Open questions:**
  - Should the Pareto show on every action card, or only on OEE-miss cards?
  - Standard reason code taxonomy or configurable per-plant?
  - Should planned vs. unplanned downtime be shown separately or combined with a visual distinction?

### Report history (date picker)
- **Status:** Not started
- **Priority:** P2
- **Description:** The morning report always shows T-1 (yesterday). But managers need to look back — "what did last Tuesday look like?" for a weekly review meeting, or "show me the day we had that fire alarm" to compare against today. There's no way to navigate to a different date.
- **What exists today:**
  - The backend already supports date parameters — `GET /api/actions/daily?date={date}` and `GET /api/summaries/smart/{date}` both accept arbitrary dates.
  - `daily_summaries` and `safety_events` store historical data by date.
  - The frontend hardcodes T-1 (`yesterday()`) in the hooks and page components.
- **Proposed approach:**
  - **Date picker** in the morning report header, next to the "T-1 Data" badge. Defaults to yesterday, allows selecting any past date that has data.
  - **Navigation arrows** — prev/next day buttons for quick browsing without opening the calendar.
  - **"No data" state** — if the selected date has no `daily_summaries` records, show a clear empty state: "No production data available for this date."
  - **URL-driven** — selected date reflected in the URL (`/morning-report?date=2026-02-05`) so links to specific reports can be shared (e.g., pasted into Teams).
  - **Smart summary generation** — if a smart summary doesn't exist for the selected historical date, offer to generate one on demand (the backend already supports this).
- **Implementation notes:**
  - Minimal backend work — the APIs already support date parameters.
  - Frontend-only changes: update `useDailyActions`, `useSmartSummary`, and the page component to accept a date prop from a picker instead of hardcoded yesterday.
- **Open questions:**
  - Should there be a "this week" or "last week" quick-select, or is day-by-day sufficient?
  - Should historical reports be read-only (no assign button), or can you still create follow-ups from old reports?

### Shift-level granularity
- **Status:** Not started
- **Priority:** P2
- **Description:** The report aggregates to daily totals, but a plant running 3 shifts needs to know *which shift* had the problems. "72 minutes downtime" is very different if it was spread across 3 shifts (systemic issue) vs. concentrated in one shift (shift-specific issue — staffing, training, or a single incident). The data model already supports shifts (`shift_targets` has a `shift` column), but the report doesn't use it.
- **What exists today:**
  - `shift_targets` stores targets per asset per shift (morning/afternoon/night).
  - `daily_summaries` aggregates to daily totals — no shift breakdown in actuals.
  - The action engine generates one action item per asset per day, regardless of which shift caused the miss.
- **Proposed approach — Data model:**
  - **Option A: Add shift column to `daily_summaries`** — change the grain from (asset, date) to (asset, date, shift). Each row represents one shift's performance. Daily aggregates are computed by summing.
  - **Option B: New `shift_summaries` table** — keep `daily_summaries` as-is for backward compatibility, add a new table at shift grain. Daily view aggregates from shift data.
  - **Recommendation:** Option A is cleaner long-term but requires migrating existing data. Option B is safer for incremental rollout.
- **Proposed approach — Frontend:**
  - **Shift tabs or breakdown** on the workcenter scorecard — "Morning: 92% attainment | Afternoon: 78% | Night: 85%". Click a shift to filter the entire report to that shift's data.
  - **Shift context on action items** — instead of "Grinder 5: 72 min downtime" show "Grinder 5: 72 min downtime (afternoon shift — 58 min mechanical)". The action engine should identify which shift drove the miss.
  - **Shift-over-shift comparison** — "Afternoon shift has missed OEE target 4 of last 5 days on Grinder 5" is far more actionable than a daily aggregate trend.
- **Proposed approach — Action engine update:**
  - When shift data is available, the action engine should attribute misses to the responsible shift. This changes the recommendation from "Review Grinder 5" to "Review Grinder 5 afternoon shift — 58 min mechanical downtime, 15 min changeover."
  - If all three shifts missed, keep it as a daily-level item (systemic issue).
- **Open questions:**
  - How many shifts does the plant actually run? Is it always 3, or does it vary by workcenter?
  - Should the default view be daily (current behavior) with shift as a drill-down, or shift-first?
  - Does `production_actuals` (from the schedule attainment feature) also need shift granularity?

### Morning meeting mode (talking points view)
- **Status:** Not started
- **Priority:** P2
- **Description:** Plant managers don't just read the report — they run a 15-minute standup with it. The current report shows everything at equal weight, which is too much detail for a meeting format.
- **Proposed approach:**
  - **Condensed "meeting mode" toggle** — shows only the top 3-5 items as large, scannable talking points. Strip evidence detail, keep just the headline + who's assigned.
  - **Clear section headers matching meeting agenda** — "Safety" / "Yesterday's Performance" / "Today's Priorities" with strong visual separation. The current priority ordering is implicit; make it explicit.
  - **Assignment column visible by default** — during the meeting, the manager is doing "Grinder 5 was down — Carlos, can you look at that?" The assign button should be prominent, not discovered.
- **Open questions:**
  - Separate route (`/morning-report/meeting`) or a toggle on the existing page?
  - Should meeting mode auto-activate during typical standup hours (6:00-7:00 AM)?

### Safety alerts auth fix
- **Status:** Not started
- **Description:** `useSafetyAlerts.ts` sends `credentials: 'include'` (cookies) instead of a `Bearer` token in the `Authorization` header. The API expects Bearer auth, so safety alert requests return `403 Forbidden`. Other hooks (`useDailyActions`, `useLivePulse`, `useCostOfLoss`) already follow the correct pattern.
- **Files to change:** `apps/web/src/hooks/useSafetyAlerts.ts`

### Live Pulse schema fix
- **Status:** Not started
- **Description:** `/api/live-pulse` returns `500` because it queries `live_snapshots.oee_percentage`, a column that doesn't exist in the table.

### Cost of Loss schema fix
- **Status:** Not started
- **Description:** `/api/financial/cost-of-loss` returns `500` because it queries `daily_summaries.waste`, a column that doesn't exist (the actual column is `waste_count`).

---

## Product Roadmap — Becoming the First Tab of the Day

### Context

The org currently runs on **Redzone** (real-time production/OEE), **Ignition** (SCADA/alarms), **AX/Dynamics** (ERP/financials), and **Microsoft Teams** (communication). This app won't replace any of them — they're systems of record and data entry points. Instead, this app becomes the **intelligence layer on top of all four**, the one place where data converges into decisions.

**Target value proposition:** "Open this before your morning meeting and you won't need to open anything else for the first 30 minutes of your day."

### What Each Tool Owns Today

| Tool | Why they go there | Stickiness factor |
|------|-------------------|-------------------|
| Redzone | Real-time production counts, OEE, downtime logging, shift handoffs, team chat | Where operators live — data entry happens here |
| Ignition | SCADA dashboards, alarm history, process variables (temps, pressures, speeds) | Source of truth for machine state |
| AX (Dynamics) | Production orders, costing, inventory, purchase orders, financials | System of record for the business |
| Teams | Morning meetings, escalation threads, file sharing, ad-hoc decisions | Where conversations happen |

### Phase 1 — Data Integration (Foundation)

| Integration | What it provides | Method |
|-------------|------------------|--------|
| Redzone API | OEE, downtime events, production counts, shift notes | REST API polling |
| Ignition | Alarms, process historian data | Tag Historian / MQTT |
| AX / D365 | Production orders, planned vs actual, cost variances, inventory | D365 API / data pipeline |
| Teams (outbound) | Push action items and alerts into Teams channels | Webhooks / Power Automate |

### Phase 2 — Cross-System Intelligence (The Differentiator)

No single tool can do this today — a plant manager mentally stitches together "Grinder 5 OEE dropped" (Redzone) + "vibration alarm fired at 2pm" (Ignition) + "that batch was the premium blend order due Friday" (AX). This app should automate that correlation:

- **Cross-system action items** — "Grinder 5 OEE dropped 12% — vibration alarm history shows 3 events this week — this impacts PO #4821 (premium blend, ships Friday)"
- **Financial context on every operational issue** — Redzone tells you what happened, this app tells you what it costs
- **Trend intelligence** — "This is the 3rd mechanical failure on Grinder 5 in 10 days — recommend PM review"

### Phase 3 — Must-Have Features to Drive Adoption

| Feature | Replaces going to... | Current status |
|---------|---------------------|----------------|
| Morning briefing with prioritized actions | Redzone dashboards + AX reports + Teams catch-up | Built (enhancing) |
| Workcenter production summary | Redzone per-line dashboards + mental math | Planned (P1) |
| Schedule attainment & product mix | AX production orders + Redzone + spreadsheet comparison | Planned (P1) |
| Schedule upload (CSV/Excel) | Manual data entry or waiting for AX integration | Planned (P1) |
| Email notifications + response tracking | Verbal follow-ups, Teams DMs, "did you get my email?" | Planned (P1) |
| Action plans (continuous improvement) | Spreadsheets, whiteboards, tribal knowledge | Planned (P1) |
| Downtime Pareto (reason code breakdown) | Redzone downtime Pareto + manual investigation | Planned (P1) |
| Report history (date picker) | Asking someone "what happened last Tuesday?" | Planned (P2) |
| Shift-level granularity | Redzone shift reports + comparing manually | Planned (P2) |
| Live production pulse | Redzone real-time view | Partially built (schema fix needed) |
| Action acknowledgment + audit trail | Teams threads ("did anyone look at this?") | Planned (P1) |
| Follow-up tracking + "My Assignments" view | Verbal follow-ups in standups + Teams DMs | Planned (P1) |
| Trend indicators + repeat offender flagging | Manually checking last week's Redzone data | Planned (P1) |
| Morning meeting mode (talking points) | Mentally filtering the report during standup | Planned (P2) |
| Teams notifications (push) | Nothing — alerts go to their existing flow | Planned (P2) |
| Conversational follow-up on AI summary | Switching to chat and re-explaining context | Planned (P3) |
| Alarm correlation | Ignition alarm journal + manual investigation | Not started |
| Cost-of-loss with root cause | AX cost reports + Redzone downtime Pareto | Partially built |
| Shift handoff with context | Redzone shift notes + Teams messages | Exists |
| Natural language Q&A | Digging through 4 different tools | Chat/AI agent exists |

### Adoption Strategy

The wedge is the morning report. If it answers "what happened, what does it cost, and what do I do about it" — all in one place — people will open it first. Then expand from there:

1. **Morning report** pulls them in daily (already built, needs polish)
2. **Workcenter scorecard + schedule attainment** answers "how did we do?" and "did we make the right stuff?" (planned)
3. **Action acknowledgment + follow-up tracking + email** keeps them engaged through the day (planned)
4. **Action plans** close the loop from issue to resolution to prevention — the app becomes the plant's improvement system (planned)
5. **Trend intelligence** becomes the thing they can't get from any single tool (planned)
6. **Teams notifications** meet them where they already are (not started)
7. **Cross-system correlation** makes it irreplaceable (Phase 2)

### The Indispensable Litmus Test

The morning report is indispensable when a plant manager can walk into their morning standup having only looked at this app and confidently:

- **"Here's how the plant performed — Roasting hit 95%, Grinding missed at 78%, Filling and Packing were on target"** — workcenter production summary (planned: P1)
- **"We ran Colombian on Roaster 1 instead of the scheduled Brazilian — we're short 2,400 lbs on PO #4821"** — schedule attainment & product mix (planned: P1)
- **"Here are the 3 things we need to talk about"** — prioritized action items (works today)
- **"Carlos, I assigned you that vibration issue yesterday — what's the status?"** — follow-up tracking (planned: P1)
- **"Carlos replied at 8:42 — he found the bearing is worn. Let's create an action plan for replacement."** — email response tracking + action plans (planned: P1)
- **"Grinder 5 has been on this report 3 days in a row — we need to escalate to maintenance planning"** — trend intelligence (planned: P1)
- **"Note that Grinder 5 already has an active action plan — bearing replacement is scheduled for Friday"** — continuous improvement loop (planned: P1)
- **"Overall we're tracking 2 points below last week's OEE — here's where the gap is"** — week-over-week context (planned: P1)

Right now they can do the third one. The rest require opening Redzone, AX, Teams, or relying on memory. That's the gap to close.

### Implementation Priority

| Priority | Feature | Why first |
|----------|---------|-----------|
| P1 | Workcenter production summary | The first question every morning: "how much did we make?" The report can't answer it today. |
| P1 | Schedule attainment & product mix | "Did we make the right stuff?" is the second question. Requires new data model (products, schedule, actuals). |
| P1 | Schedule upload (CSV/Excel) | Unblocks schedule attainment without waiting for AX integration. Low-friction data entry for planners. |
| P1 | Action acknowledgment + follow-up status visibility | Without this, the report is a newspaper — you read it and throw it away. No accountability loop. |
| P1 | Email notifications + response tracking | Meets assignees where they are (inbox). Creates the audit trail that feeds action plans. |
| P1 | Action plans (continuous improvement) | Closes the full loop: issue → investigation → root cause → corrective action → verification. This is what turns a daily report into an operational improvement system. |
| P1 | Downtime Pareto | "Why did we lose time?" turns a vague investigation into a targeted one. Enables smarter action assignments. |
| P1 | Trend indicators on action items | "Is this new or recurring?" changes the response entirely. Biggest intelligence gap. |
| P2 | Report history (date picker) | Look back at any past day for weekly reviews or comparisons. Backend already supports it — mostly frontend work. |
| P2 | Shift-level granularity | "Which shift had the problem?" changes who you assign the investigation to. |
| P2 | Teams push notifications | Gets the manager to open the app every day without thinking about it. Adoption driver. |
| P2 | Morning meeting mode | Structures the report around the actual workflow — running a standup. |
| P3 | Conversational follow-up on summary | Deepens engagement once they're already in the app daily. |
