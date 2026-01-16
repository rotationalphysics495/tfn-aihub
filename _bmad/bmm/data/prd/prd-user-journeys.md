# PRD: User Journeys

**Parent Document:** [prd.md](../prd.md)

---

## Journey 1: David Chen - The Prepared Plant Manager

David is a Plant Manager who's been running this facility for 8 years. He takes pride in knowing his plant inside and out, but mornings have become a grind. He arrives at 6:15 AM, and the next 45 minutes are spent opening dashboards, cross-referencing yesterday's numbers, and building a mental picture of what happened overnight.

One morning, David tries the new Morning Briefing feature. He taps "Start Briefing" on his phone as he walks from the parking lot. By the time he's poured his coffee, the system has told him: plant-wide output hit 87% of target, three wins worth celebrating, and three concerns needing attention. When Grinder 5 comes up as a concern, he asks "What caused the Grinder 5 downtime?" and gets a cited breakdown of blade changes and material jams.

David walks into his 7 AM meeting already knowing the three things he needs to address.

**Capabilities Required:**
- Voice TTS, text display
- Area-by-area delivery
- Q&A with citations
- Mem0 preferences
- Plant-wide data aggregation

---

## Journey 2: Maria Santos - The Exhausted Night Supervisor Handing Off

Maria has been running the night shift for 3 years. She's meticulous and catches problems others miss, but handoffs have always been her frustration. After a 12-hour shift, she's exhausted, and the incoming supervisor is just waking up.

Tonight was rough—Grinder 5 went down twice, there's a quality hold on Line 3. At 5:45 AM, Maria triggers a Shift Handoff from her tablet. The system synthesizes her shift data automatically. Maria reviews it, adds a voice note: "Carlos, keep an eye on the new guy on 800-1, he's good but nervous." She hits send and heads home, confident that everything important is captured.

**Capabilities Required:**
- Shift data synthesis via LangChain tools
- Voice note attachment
- Persistent record creation
- Send notification

---

## Journey 3: Carlos Rivera - The Incoming Supervisor Getting Up to Speed

Carlos arrives at 5:55 AM. He sees a notification: "Shift Handoff from Maria Santos." He opens it on his tablet while grabbing coffee. The system walks him through the key issues—Grinder 5 stoppages, Line 3 quality hold, the new operator situation.

He has a question: "What caused the second Grinder 5 stoppage?" The system responds with citations: "Material jam detected at 3:15 AM. Sensor logs show moisture variance in incoming material. Maintenance cleared jam at 3:56 AM."

Carlos taps "Acknowledge" and adds a note: "Will check moisture levels on incoming material first thing." Maria gets a notification that her handoff was received and acknowledged. Carlos walks onto the floor already knowing exactly where to focus.

**Capabilities Required:**
- Handoff review UI
- Follow-up Q&A with citations
- Acknowledge action
- Audit trail

---

## Journey 4: Rachel Kim - The Admin Configuring the System

Rachel is the Operations Coordinator who manages system access. She opens the Admin UI and assigns supervisors to their assets. She selects Maria Santos and assigns her to Grinding (Grinders 1-5) and Packing (CAMA lines, Pack Cells). The system shows a preview: "Maria will receive briefings for 12 assets across 2 areas."

When a new supervisor joins next month, Rachel adds them in 2 minutes—assign role, assign assets, done. When coverage changes due to vacation, she can temporarily reassign assets without IT involvement. The system keeps an audit log of all assignment changes for compliance.

**Capabilities Required:**
- Supervisor-asset assignment UI
- Role management
- Assignment preview
- Audit logging

---

## Journey 5: David Chen - First-Time Onboarding

Before David can use his first Morning Briefing, the system needs to understand his preferences. When he first opens the briefing feature, the system greets him:

"Welcome, David! Let's set up your briefing preferences—this will take about 2 minutes."

The system asks:
1. "What's your role?" David selects "Plant Manager."
2. "Which areas do you want to hear about first?" David drags Grinding and Packing to the top—those are his problem children.
3. "How much detail do you prefer?" David chooses "Summary" for mornings.
4. "Voice or text?" David enables voice—he wants hands-free briefings.

The system confirms: "Got it! Your briefings will cover all plant areas, starting with Grinding and Packing, at summary level, delivered by voice. You can change these anytime in Settings."

David's preferences are stored in Mem0, and every future briefing is personalized to how he works.

**Capabilities Required:**
- Role selection
- Area ordering
- Detail level preference
- Voice toggle
- Mem0 storage

---

## Journey Requirements Summary

| Journey | Primary Persona | Key Capabilities |
|---------|-----------------|------------------|
| Morning Briefing | Plant Manager (David) | Voice TTS, area-by-area delivery, Q&A with citations, plant-wide aggregation |
| Shift Handoff - Outgoing | Supervisor (Maria) | Shift synthesis, voice notes, persistent records, notifications |
| Shift Handoff - Incoming | Supervisor (Carlos) | Handoff review, follow-up Q&A, acknowledgment, audit trail |
| Admin Configuration | Admin (Rachel) | Asset assignment, role management, preview, audit logging |
| First-Time Onboarding | Any User (David) | Role selection, preferences, Mem0 storage |
