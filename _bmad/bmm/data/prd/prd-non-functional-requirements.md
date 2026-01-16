# PRD: Non-Functional Requirements

**Parent Document:** [prd.md](../prd.md)

---

## Accuracy & Honesty (NFR1-NFR4)

| ID | Requirement |
|----|-------------|
| NFR1 | AI must cite specific data points for every recommendation to prevent hallucination |
| NFR2 | AI Agent shall never fabricate data or statistics |
| NFR3 | AI Agent shall clearly state when information is unavailable |
| NFR4 | AI Agent shall distinguish between "no data" and "zero value" in responses |

---

## Latency & Performance (NFR5-NFR10)

| ID | Requirement |
|----|-------------|
| NFR5 | "Live" views must reflect SQL data within 60 seconds of ingestion |
| NFR6 | Tool Response Time < 2 seconds (p95) |
| NFR7 | Q&A interactions complete within 2 seconds (voice input → response delivered) |
| NFR8 | Full briefing generation completes within 30 seconds |
| NFR9 | ElevenLabs TTS begins audio playback within 2 seconds of text generation |
| NFR10 | Push-to-talk transcription completes within 2 seconds of button release |

---

## Security & Access (NFR11)

| ID | Requirement |
|----|-------------|
| NFR11 | System must strictly observe Read-Only permissions on source manufacturing databases |

---

## Tool Architecture (NFR12-NFR14)

| ID | Requirement |
|----|-------------|
| NFR12 | Tool architecture shall support adding new data sources (MSSQL) without modifying existing tools |
| NFR13 | Tools shall use a data access abstraction layer that can route queries to appropriate sources |
| NFR14 | New tools can be registered without modifying the agent core |

---

## Response Structure (NFR15-NFR17)

| ID | Requirement |
|----|-------------|
| NFR15 | All tool responses shall include a citations array with source table, query, and timestamp |
| NFR16 | Tool responses shall return structured data (JSON) that the agent formats for display |
| NFR17 | Tool responses shall include suggested follow-up questions when relevant |

---

## Caching (NFR18)

Tool responses SHALL be cached with tiered TTLs:

| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| Live Data (Production Status, Alert Check) | 60 seconds | Time-based only |
| Daily Data (OEE, Downtime, Financial) | 15 minutes | Time-based; invalidate on new pipeline run |
| Static Data (Asset Lookup metadata) | 1 hour | Time-based; invalidate on asset table change |
| Memory Recall | No cache | Always fetch fresh |
| Action List | 5 minutes | Time-based; invalidate on safety event |

---

## Reliability (NFR19-NFR22)

| ID | Requirement |
|----|-------------|
| NFR19 | System maintains 99.9% uptime during shift change windows (5-7 AM, 5-7 PM) |
| NFR20 | Shift handoff records are cached locally and survive connectivity loss |
| NFR21 | Acknowledgment syncs automatically when connectivity is restored |
| NFR22 | Voice fallback to text-only if ElevenLabs API is unavailable |

---

## Data Integrity (NFR23-NFR26)

| ID | Requirement |
|----|-------------|
| NFR23 | All briefing data reflects production data no older than 15 minutes |
| NFR24 | Shift handoff records are immutable once created (append-only notes) |
| NFR25 | Audit logs are tamper-evident and retained for 90 days minimum |
| NFR26 | User preference changes are versioned in Mem0 for rollback capability |
