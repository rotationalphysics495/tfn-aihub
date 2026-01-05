# Story 4.4: Asset History Memory

Status: ready-for-dev

## Story

As a **Plant Manager or Line Supervisor**,
I want **past resolutions, maintenance actions, and operational context to be stored and linked to specific assets**,
so that **when I ask the AI "Why does Grinder 5 keep failing?", it can retrieve and synthesize historical context to provide actionable, evidence-based answers**.

## Acceptance Criteria

1. **Asset History Data Model**
   - Asset history records are stored in Supabase with proper schema
   - Each history entry links to a specific asset via `asset_id` (FK to `assets.id`)
   - History entries include: event_type, description, resolution, outcome, timestamp, source
   - Vector embeddings generated for semantic search of history entries
   - Support for multiple event types: downtime, maintenance, resolution, note, incident

2. **Mem0 Asset Memory Integration**
   - Mem0 stores and indexes asset history entries as memories
   - Each memory is tagged with asset identifiers (asset_id, asset_name, area)
   - Memories are retrievable by asset context (e.g., "Grinder 5" retrieves all Grinder 5 history)
   - Support for temporal queries (e.g., "recent issues with Grinder 5")
   - Integration with Mem0 vector storage in Supabase pgvector

3. **History Storage API**
   - POST `/api/assets/{asset_id}/history` - Create new history entry
   - GET `/api/assets/{asset_id}/history` - Retrieve asset history (paginated)
   - GET `/api/assets/{asset_id}/history/search` - Semantic search within asset history
   - History entries automatically generate Mem0 memories on creation
   - Protected by Supabase Auth JWT validation

4. **History Retrieval for AI Context**
   - Service function retrieves relevant asset history for AI prompts
   - Returns top-k most relevant history entries based on semantic similarity
   - Includes temporal weighting (recent events ranked higher)
   - Formatted output suitable for LLM context injection
   - Supports multi-asset queries (e.g., "all grinding area machines")

5. **Data Citation and Provenance**
   - Each history entry includes source field (manual, system, ai-generated)
   - Timestamps for creation and last modification
   - Support for linking to original data sources (downtime events, safety incidents)
   - History entries can reference related records (e.g., `related_downtime_id`)

6. **Performance Requirements**
   - History retrieval completes within 500ms for typical queries
   - Semantic search returns results within 1 second
   - Support for assets with 1000+ history entries
   - Efficient pagination for large result sets

## Tasks / Subtasks

- [ ] Task 1: Create asset_history database schema (AC: #1, #5)
  - [ ] 1.1 Create Supabase migration for `asset_history` table
  - [ ] 1.2 Add columns: id (UUID), asset_id (FK), event_type, title, description, resolution, outcome, created_at, updated_at, source, related_record_type, related_record_id
  - [ ] 1.3 Create index on asset_id for efficient lookups
  - [ ] 1.4 Create index on event_type for filtering
  - [ ] 1.5 Add row-level security policies for authenticated users

- [ ] Task 2: Create asset_history_embeddings for vector search (AC: #1, #2)
  - [ ] 2.1 Create Supabase migration for `asset_history_embeddings` table
  - [ ] 2.2 Add columns: id (UUID), history_id (FK), embedding (vector(1536)), created_at
  - [ ] 2.3 Enable pgvector extension if not already enabled
  - [ ] 2.4 Create HNSW index for efficient similarity search
  - [ ] 2.5 Add foreign key constraint to asset_history

- [ ] Task 3: Create AssetHistory Pydantic models (AC: #1, #3)
  - [ ] 3.1 Create `apps/api/app/models/asset_history.py`
  - [ ] 3.2 Define AssetHistoryBase, AssetHistoryCreate, AssetHistoryRead models
  - [ ] 3.3 Define AssetHistorySearchQuery model for search parameters
  - [ ] 3.4 Define AssetHistoryForAI model (optimized for LLM context)
  - [ ] 3.5 Add event_type enum: DOWNTIME, MAINTENANCE, RESOLUTION, NOTE, INCIDENT

- [ ] Task 4: Implement asset history service (AC: #2, #4, #6)
  - [ ] 4.1 Create `apps/api/app/services/asset_history_service.py`
  - [ ] 4.2 Implement create_history_entry() with embedding generation
  - [ ] 4.3 Implement get_asset_history() with pagination
  - [ ] 4.4 Implement search_asset_history() with vector similarity
  - [ ] 4.5 Implement get_history_for_ai_context() with temporal weighting
  - [ ] 4.6 Implement multi-asset query support (by area or asset group)

- [ ] Task 5: Integrate with Mem0 memory system (AC: #2)
  - [ ] 5.1 Create `apps/api/app/services/mem0_asset_service.py`
  - [ ] 5.2 Implement add_asset_memory() to store history as Mem0 memory
  - [ ] 5.3 Tag memories with asset metadata (asset_id, asset_name, area)
  - [ ] 5.4 Implement retrieve_asset_memories() for context retrieval
  - [ ] 5.5 Handle Mem0 API integration (or local Supabase pgvector if self-hosted)

- [ ] Task 6: Create asset history API endpoints (AC: #3)
  - [ ] 6.1 Create `apps/api/app/api/asset_history.py` router
  - [ ] 6.2 Implement POST `/api/assets/{asset_id}/history` endpoint
  - [ ] 6.3 Implement GET `/api/assets/{asset_id}/history` with pagination
  - [ ] 6.4 Implement GET `/api/assets/{asset_id}/history/search` with query param
  - [ ] 6.5 Add JWT authentication dependency
  - [ ] 6.6 Register router in `apps/api/app/main.py`

- [ ] Task 7: Implement embedding generation (AC: #1, #2)
  - [ ] 7.1 Create `apps/api/app/services/embedding_service.py`
  - [ ] 7.2 Integrate OpenAI text-embedding-3-small (or alternative)
  - [ ] 7.3 Implement generate_embedding() for history text
  - [ ] 7.4 Combine title + description + resolution for embedding input
  - [ ] 7.5 Handle API errors and retries gracefully

- [ ] Task 8: Create AI context formatter (AC: #4, #5)
  - [ ] 8.1 Create `apps/api/app/services/ai_context_service.py`
  - [ ] 8.2 Implement format_history_for_prompt() to create LLM-ready context
  - [ ] 8.3 Include citation markers for NFR1 compliance
  - [ ] 8.4 Implement temporal weighting algorithm (decay function)
  - [ ] 8.5 Limit context size to avoid token overflow

- [ ] Task 9: Integration testing (AC: #6)
  - [ ] 9.1 Test history creation with embedding generation
  - [ ] 9.2 Test semantic search returns relevant results
  - [ ] 9.3 Test pagination for large history sets
  - [ ] 9.4 Test AI context retrieval performance
  - [ ] 9.5 Test multi-asset queries

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **Database:** Supabase PostgreSQL with pgvector extension
- **AI Memory:** Mem0 for context storage OR direct pgvector usage
- **Embeddings:** OpenAI text-embedding-3-small (1536 dimensions)
- **API Pattern:** REST endpoints under `/api/assets/{asset_id}/history`

### Technical Requirements

**Database Schema (Supabase):**
```sql
-- Enable pgvector if not already enabled (from Story 4.1)
CREATE EXTENSION IF NOT EXISTS vector;

-- Asset History Table
CREATE TABLE asset_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,  -- 'downtime', 'maintenance', 'resolution', 'note', 'incident'
  title VARCHAR(255) NOT NULL,
  description TEXT,
  resolution TEXT,
  outcome VARCHAR(100),  -- 'resolved', 'ongoing', 'escalated', 'deferred'
  source VARCHAR(50) NOT NULL DEFAULT 'manual',  -- 'manual', 'system', 'ai-generated'
  related_record_type VARCHAR(50),  -- 'downtime_event', 'safety_event', etc.
  related_record_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id)
);

-- Indexes for performance
CREATE INDEX idx_asset_history_asset_id ON asset_history(asset_id);
CREATE INDEX idx_asset_history_event_type ON asset_history(event_type);
CREATE INDEX idx_asset_history_created_at ON asset_history(created_at DESC);

-- Vector embeddings for semantic search
CREATE TABLE asset_history_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  history_id UUID NOT NULL REFERENCES asset_history(id) ON DELETE CASCADE,
  embedding vector(1536) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX idx_asset_history_embeddings_vector
ON asset_history_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Row Level Security
ALTER TABLE asset_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_history_embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read all history
CREATE POLICY "Authenticated users can view asset history"
ON asset_history FOR SELECT
TO authenticated
USING (true);

-- Policy: Authenticated users can insert history
CREATE POLICY "Authenticated users can create asset history"
ON asset_history FOR INSERT
TO authenticated
WITH CHECK (true);
```

**Embedding Generation Pattern:**
```python
from openai import OpenAI
from typing import List

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for history entry text."""
    client = OpenAI()  # Uses OPENAI_API_KEY from environment

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )

    return response.data[0].embedding  # 1536-dimensional vector
```

**Semantic Search Pattern:**
```python
async def search_asset_history(
    asset_id: UUID,
    query: str,
    limit: int = 5
) -> List[AssetHistoryRead]:
    """Search asset history using vector similarity."""

    # Generate query embedding
    query_embedding = generate_embedding(query)

    # Similarity search with pgvector
    results = await db.execute(
        """
        SELECT ah.*, 1 - (ahe.embedding <=> :query_embedding) as similarity
        FROM asset_history ah
        JOIN asset_history_embeddings ahe ON ah.id = ahe.history_id
        WHERE ah.asset_id = :asset_id
        ORDER BY ahe.embedding <=> :query_embedding
        LIMIT :limit
        """,
        {
            "asset_id": asset_id,
            "query_embedding": query_embedding,
            "limit": limit
        }
    )

    return results
```

**AI Context Formatting:**
```python
def format_history_for_prompt(
    history_entries: List[AssetHistoryRead],
    max_tokens: int = 2000
) -> str:
    """Format history entries for LLM context injection."""

    context_parts = []
    for entry in history_entries:
        # Include citation marker for NFR1 compliance
        citation = f"[History:{entry.id[:8]}]"

        context_parts.append(
            f"{citation} {entry.created_at.strftime('%Y-%m-%d')}: "
            f"{entry.title}. {entry.description or ''} "
            f"Resolution: {entry.resolution or 'N/A'}"
        )

    return "\n".join(context_parts)
```

**Mem0 Integration Pattern (if using Mem0):**
```python
from mem0 import Memory

# Initialize Mem0 with Supabase pgvector backend
memory = Memory.from_config({
    "vector_store": {
        "provider": "supabase",
        "config": {
            "url": os.getenv("SUPABASE_URL"),
            "key": os.getenv("SUPABASE_KEY"),
            "table": "mem0_memories"
        }
    }
})

async def add_asset_memory(asset_id: str, content: str, metadata: dict):
    """Add asset history to Mem0 memory."""
    memory.add(
        content,
        user_id=f"asset:{asset_id}",
        metadata={
            "asset_id": asset_id,
            "asset_name": metadata.get("asset_name"),
            "area": metadata.get("area"),
            "event_type": metadata.get("event_type"),
            "timestamp": metadata.get("timestamp")
        }
    )

async def retrieve_asset_memories(asset_id: str, query: str, limit: int = 5):
    """Retrieve relevant memories for an asset."""
    return memory.search(
        query,
        user_id=f"asset:{asset_id}",
        limit=limit
    )
```

### Temporal Weighting Algorithm

Apply decay to prioritize recent history entries:

```python
import math
from datetime import datetime, timedelta

def calculate_temporal_weight(created_at: datetime, half_life_days: int = 30) -> float:
    """
    Calculate temporal weight using exponential decay.
    Recent entries get higher weight.

    half_life_days: Time for weight to decay to 50%
    """
    age_days = (datetime.now() - created_at).days
    decay_constant = math.log(2) / half_life_days
    weight = math.exp(-decay_constant * age_days)
    return weight

def rank_history_with_temporal_weight(
    entries: List[AssetHistoryRead],
    similarity_scores: List[float]
) -> List[AssetHistoryRead]:
    """Combine similarity and temporal weight for final ranking."""
    ranked = []
    for entry, similarity in zip(entries, similarity_scores):
        temporal_weight = calculate_temporal_weight(entry.created_at)
        # Combined score: 70% similarity, 30% recency
        combined_score = 0.7 * similarity + 0.3 * temporal_weight
        ranked.append((entry, combined_score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return [entry for entry, score in ranked]
```

### Project Structure Notes

```
apps/api/app/
  models/
    asset_history.py          # Pydantic models (NEW)
  api/
    asset_history.py          # API endpoints (NEW)
  services/
    asset_history_service.py  # Business logic (NEW)
    embedding_service.py      # Embedding generation (NEW)
    mem0_asset_service.py     # Mem0 integration (NEW)
    ai_context_service.py     # AI context formatting (NEW)

supabase/migrations/
  YYYYMMDDHHMMSS_create_asset_history.sql     # Schema migration (NEW)
  YYYYMMDDHHMMSS_create_asset_history_embeddings.sql  # Embeddings table (NEW)
```

### Dependencies

**Python Dependencies (apps/api/requirements.txt):**
```
openai>=1.0.0         # For text-embedding-3-small
mem0ai>=0.0.5         # Optional: If using Mem0 SDK
pgvector>=0.2.0       # For vector operations with SQLAlchemy
```

**Requires (must be completed):**
- Story 1.2: Supabase Auth Integration (JWT validation)
- Story 1.3: Plant Object Model Schema (provides `assets` table)
- Story 4.1: Mem0 Vector Memory Integration (sets up Mem0/pgvector infrastructure)

**Enables:**
- Story 4.5: Cited Response Generation (uses history for citations)
- AI Chat can answer "Why does X keep failing?" with historical context

### NFR Compliance

- **NFR1 (Accuracy):** History entries include source provenance and citation markers; AI responses can reference specific history entries with [History:ID] format
- **NFR3 (Read-Only):** Asset history is separate from source MSSQL - only reads from Supabase PostgreSQL

### Example Use Case Flow

When user asks: "Why does Grinder 5 keep failing?"

1. **Asset Resolution:** Parse "Grinder 5" to find matching asset_id from `assets` table
2. **History Retrieval:** Query `asset_history` for all entries where asset_id matches Grinder 5
3. **Semantic Search:** Use embedding similarity to find entries most relevant to "failing"
4. **Temporal Ranking:** Apply temporal weighting to prioritize recent issues
5. **Context Formatting:** Format top 5 entries into LLM-ready context with citations
6. **AI Response:** LLM synthesizes answer with citations like "[History:a1b2c3d4] On 2025-12-15, bearing replacement resolved intermittent failures"

### API Response Schemas

```typescript
// POST /api/assets/{asset_id}/history
interface CreateAssetHistoryRequest {
  event_type: 'downtime' | 'maintenance' | 'resolution' | 'note' | 'incident';
  title: string;
  description?: string;
  resolution?: string;
  outcome?: 'resolved' | 'ongoing' | 'escalated' | 'deferred';
  source?: 'manual' | 'system' | 'ai-generated';
  related_record_type?: string;
  related_record_id?: string;
}

// GET /api/assets/{asset_id}/history
interface AssetHistoryResponse {
  items: Array<{
    id: string;
    asset_id: string;
    event_type: string;
    title: string;
    description: string | null;
    resolution: string | null;
    outcome: string | null;
    source: string;
    created_at: string;  // ISO 8601
    updated_at: string;
  }>;
  pagination: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

// GET /api/assets/{asset_id}/history/search?q=...
interface AssetHistorySearchResponse {
  query: string;
  results: Array<{
    id: string;
    title: string;
    description: string | null;
    resolution: string | null;
    similarity_score: number;  // 0.0 - 1.0
    created_at: string;
  }>;
}
```

### Testing Guidance

**Unit Tests:**
- Test embedding generation with mock OpenAI responses
- Test temporal weighting algorithm with various date ranges
- Test AI context formatting produces valid LLM input
- Test Pydantic model validation for all event types

**Integration Tests:**
- Test full flow: create history -> generate embedding -> search
- Test pagination returns correct subsets
- Test semantic search finds relevant entries
- Test multi-asset area queries

**Performance Tests:**
- Verify search completes within 1 second for 1000+ entries
- Verify retrieval completes within 500ms for typical queries
- Test embedding generation handles rate limiting gracefully

### References

- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 integration for "Asset Histories"
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - assets table structure
- [Source: _bmad/bmm/data/prd.md#2. Requirements] - FR6 AI Chat with Memory, NFR1 Accuracy
- [Source: _bmad-output/planning-artifacts/epic-4.md] - Epic 4 scope, Story 4.4 definition
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] - "Why does Grinder 5 keep failing?" use case

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
