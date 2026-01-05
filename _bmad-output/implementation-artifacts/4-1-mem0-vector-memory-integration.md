# Story 4.1: Mem0 Vector Memory Integration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager or Line Supervisor**,
I want **the AI system to remember my past questions, preferences, and asset-specific context using Mem0 vector memory stored in Supabase pgvector**,
so that **when I ask follow-up questions or return later, the AI can provide personalized, context-aware responses without me having to repeat information**.

## Acceptance Criteria

1. **Mem0 Python SDK Integration**
   - GIVEN the FastAPI backend is running
   - WHEN Mem0 is initialized with Supabase pgvector configuration
   - THEN it successfully connects and can store/retrieve vector memories
   - AND the connection uses environment variables for credentials (no hardcoded secrets)

2. **Supabase Vector Database Schema**
   - GIVEN the Supabase database is available
   - WHEN the vector storage SQL migrations are executed
   - THEN the `memories` table exists with vector(1536) embedding column
   - AND the `match_vectors` function is available for similarity search
   - AND the pgvector extension is enabled
   - AND HNSW index is created for optimal search performance

3. **User Session Memory Storage**
   - GIVEN a user has an authenticated session
   - WHEN the user asks a question or provides context
   - THEN the interaction is stored in Mem0 with user_id from JWT claims
   - AND the memory includes both user message and AI response
   - AND metadata captures timestamp and session context

4. **Asset History Memory Storage**
   - GIVEN a user asks about a specific asset (e.g., "Grinder 5")
   - WHEN the question and response are processed
   - THEN the memory is stored with asset_id linked in metadata
   - AND future queries about the same asset can retrieve this history
   - AND asset mapping uses Plant Object Model `assets.source_id`

5. **Memory Retrieval for Context**
   - GIVEN a user asks a question
   - WHEN the AI processes the query
   - THEN Mem0 searches for relevant memories using semantic similarity
   - AND top-k relevant memories (configurable, default 5) are retrieved
   - AND memories are filtered by user_id for personalization

6. **Memory Service API**
   - GIVEN the FastAPI backend is running
   - WHEN the memory service is called
   - THEN it provides `add_memory()`, `search_memory()`, and `get_all_memories()` methods
   - AND methods are async for non-blocking operation
   - AND proper error handling returns meaningful error responses

7. **OpenAI Embeddings Configuration**
   - GIVEN Mem0 needs to generate embeddings
   - WHEN processing text for storage or search
   - THEN OpenAI text-embedding-ada-002 (or configured model) generates 1536-dim vectors
   - AND API key is loaded from environment variables
   - AND embedding generation errors are handled gracefully

8. **LangChain Integration Preparation**
   - GIVEN Mem0 is configured for this project
   - WHEN the memory service is implemented
   - THEN it follows patterns compatible with LangChain memory interface
   - AND context retrieval returns messages in LangChain-compatible format
   - AND the service can be easily integrated with LangChain agents in Story 4.2

## Tasks / Subtasks

- [ ] Task 1: Create Supabase Vector Database Schema (AC: #2)
  - [ ] 1.1 Create SQL migration file: `apps/api/migrations/001_mem0_vector_schema.sql`
  - [ ] 1.2 Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
  - [ ] 1.3 Create `memories` table with vector(1536) column
  - [ ] 1.4 Create `match_vectors` RPC function for similarity search
  - [ ] 1.5 Create HNSW index on embedding column for performance
  - [ ] 1.6 Execute migration via Supabase SQL Editor or CLI
  - [ ] 1.7 Verify schema in Supabase dashboard

- [ ] Task 2: Install and Configure Mem0 Dependencies (AC: #1, #7)
  - [ ] 2.1 Add `mem0ai` to `apps/api/requirements.txt`
  - [ ] 2.2 Add `openai` to requirements if not present (for embeddings)
  - [ ] 2.3 Update `apps/api/app/core/config.py` with Mem0 configuration settings
  - [ ] 2.4 Add environment variables to `.env` and Railway secrets
  - [ ] 2.5 Create configuration validation on startup

- [ ] Task 3: Create Memory Service Core (AC: #1, #6)
  - [ ] 3.1 Create `apps/api/app/services/memory/__init__.py`
  - [ ] 3.2 Create `apps/api/app/services/memory/mem0_service.py` - main service class
  - [ ] 3.3 Implement `initialize()` method with Supabase pgvector config
  - [ ] 3.4 Implement `add_memory()` async method for storing interactions
  - [ ] 3.5 Implement `search_memory()` async method for semantic retrieval
  - [ ] 3.6 Implement `get_all_memories()` async method for user history
  - [ ] 3.7 Add proper error handling and logging throughout

- [ ] Task 4: Implement User Session Memory (AC: #3)
  - [ ] 4.1 Create Pydantic models in `apps/api/app/models/memory.py`
  - [ ] 4.2 Define `MemoryInput` schema (user_id, messages, metadata)
  - [ ] 4.3 Define `MemoryOutput` schema (id, content, similarity, metadata)
  - [ ] 4.4 Implement user_id extraction from JWT claims via auth dependency
  - [ ] 4.5 Add session tracking metadata (timestamp, session_id)

- [ ] Task 5: Implement Asset History Memory (AC: #4)
  - [ ] 5.1 Create asset detection utility to extract asset references from messages
  - [ ] 5.2 Map detected asset names to `assets.source_id` from Plant Object Model
  - [ ] 5.3 Include `asset_id` in memory metadata when asset is referenced
  - [ ] 5.4 Add asset-filtered search capability to `search_memory()`
  - [ ] 5.5 Create `get_asset_history()` method for asset-specific retrieval

- [ ] Task 6: Implement Context Retrieval for AI (AC: #5, #8)
  - [ ] 6.1 Create `get_context_for_query()` method combining user + asset memories
  - [ ] 6.2 Implement top-k retrieval with configurable limit (default: 5)
  - [ ] 6.3 Format retrieved memories for LangChain compatibility
  - [ ] 6.4 Return as list of message dicts with role/content structure
  - [ ] 6.5 Add similarity threshold filtering (configurable, default: 0.7)

- [ ] Task 7: Create Memory API Endpoints (AC: #6)
  - [ ] 7.1 Create `apps/api/app/api/memory.py` router
  - [ ] 7.2 Implement `POST /api/memory` - store a memory
  - [ ] 7.3 Implement `GET /api/memory/search?query=...` - semantic search
  - [ ] 7.4 Implement `GET /api/memory` - get all user memories
  - [ ] 7.5 Implement `GET /api/memory/asset/{asset_id}` - get asset history
  - [ ] 7.6 Protect all endpoints with Supabase JWT authentication
  - [ ] 7.7 Add to main FastAPI router in `apps/api/app/main.py`

- [ ] Task 8: Write Tests (AC: All)
  - [ ] 8.1 Unit tests for memory service methods
  - [ ] 8.2 Unit tests for asset detection utility
  - [ ] 8.3 Integration tests with mock Supabase/Mem0
  - [ ] 8.4 Test memory storage and retrieval flow
  - [ ] 8.5 Test asset history linking
  - [ ] 8.6 Test LangChain-compatible output format

- [ ] Task 9: Documentation and Verification (AC: All)
  - [ ] 9.1 Add memory service documentation to README
  - [ ] 9.2 Document environment variables
  - [ ] 9.3 Manual end-to-end verification
  - [ ] 9.4 Verify Railway deployment with production Supabase

## Dev Notes

### Architecture Compliance

This story implements the **Mem0 Integration** component from the Architecture document (Section 7: AI & Memory Architecture). It is the foundation story for Epic 4 (AI Chat & Memory) and enables all subsequent AI-related stories.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/memory/` for memory service logic
**Pattern:** Service-layer with dependency injection, async operations

### Technical Requirements

**Memory Architecture Diagram:**
```
User Query
    |
    v
+-------------------+
| Memory Service    |
| (mem0_service.py) |
+-------------------+
    |
    +---> search_memory(query, user_id)
    |         |
    |         v
    |     Mem0 SDK
    |         |
    |         v
    |     Supabase pgvector
    |         |
    |         v
    |     [Relevant Memories]
    |
    +---> add_memory(messages, user_id, metadata)
              |
              v
          Mem0 SDK
              |
              v
          OpenAI Embeddings
              |
              v
          Supabase pgvector
              |
              v
          [Stored Memory]
```

### Supabase Vector Database Schema

**CRITICAL:** Execute this migration in Supabase SQL Editor BEFORE running the application.

```sql
-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the memories table for Mem0
CREATE TABLE IF NOT EXISTS memories (
  id TEXT PRIMARY KEY,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create HNSW index for optimal similarity search performance
-- HNSW provides faster search at the cost of more memory
CREATE INDEX IF NOT EXISTS memories_embedding_idx
ON memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create the vector similarity search function
CREATE OR REPLACE FUNCTION match_vectors(
  query_embedding vector(1536),
  match_count INT,
  filter JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (
  id TEXT,
  similarity FLOAT,
  metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    t.id::TEXT,
    1 - (t.embedding <=> query_embedding) AS similarity,
    t.metadata
  FROM memories t
  WHERE CASE
    WHEN filter::TEXT = '{}'::TEXT THEN TRUE
    ELSE t.metadata @> filter
  END
  ORDER BY t.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create index on metadata for filtered queries
CREATE INDEX IF NOT EXISTS memories_metadata_idx ON memories USING gin (metadata);

-- Create index on user_id within metadata for user-specific queries
CREATE INDEX IF NOT EXISTS memories_user_id_idx ON memories ((metadata->>'user_id'));

-- Create index on asset_id within metadata for asset-specific queries
CREATE INDEX IF NOT EXISTS memories_asset_id_idx ON memories ((metadata->>'asset_id'));
```

### Mem0 Python Configuration

**mem0_service.py Core Structure:**
```python
import os
from typing import List, Dict, Optional
from mem0 import Memory
from app.core.config import settings

class MemoryService:
    def __init__(self):
        self.memory: Optional[Memory] = None

    def initialize(self):
        """Initialize Mem0 with Supabase pgvector configuration."""
        config = {
            "vector_store": {
                "provider": "supabase",
                "config": {
                    "connection_string": settings.SUPABASE_DB_URL,
                    "collection_name": "memories",
                    "index_method": "hnsw",
                    "index_measure": "cosine_distance"
                }
            }
        }
        self.memory = Memory.from_config(config)

    async def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Store user interaction in memory."""
        meta = metadata or {}
        meta["user_id"] = user_id
        meta["timestamp"] = datetime.utcnow().isoformat()

        result = self.memory.add(messages, user_id=user_id, metadata=meta)
        return result

    async def search_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """Semantic search for relevant memories."""
        results = self.memory.search(query, user_id=user_id, limit=limit)

        # Filter by similarity threshold
        filtered = [
            mem for mem in results.get("results", [])
            if mem.get("similarity", 0) >= threshold
        ]
        return filtered

# Singleton instance
memory_service = MemoryService()
```

### Environment Variables

**Add to `apps/api/.env` and Railway Secrets:**

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes | `sk-...` |
| `SUPABASE_DB_URL` | Supabase PostgreSQL connection string | Yes | `postgresql://postgres.[ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres` |
| `MEM0_COLLECTION_NAME` | Memory collection name | No | `memories` (default) |
| `MEM0_EMBEDDING_DIMS` | Embedding dimensions | No | `1536` (default) |
| `MEM0_TOP_K` | Default number of memories to retrieve | No | `5` (default) |
| `MEM0_SIMILARITY_THRESHOLD` | Minimum similarity for results | No | `0.7` (default) |

**CRITICAL:** The `SUPABASE_DB_URL` must be the **direct database connection string**, NOT the REST API URL. Get this from Supabase Dashboard > Project Settings > Database > Connection String (URI format).

**Port 6543 vs 5432:** Use port **6543** (connection pooler) for production, **5432** for direct connection. The pooler URL is recommended for better connection management.

### LangChain Compatibility Pattern

The memory service must return context in a format compatible with LangChain:

```python
async def get_context_for_query(
    self,
    query: str,
    user_id: str,
    asset_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """Get relevant context formatted for LangChain."""
    memories = await self.search_memory(query, user_id)

    if asset_id:
        asset_memories = await self.get_asset_history(asset_id, user_id)
        memories.extend(asset_memories)

    # Format for LangChain
    context = []
    for mem in memories:
        context.append({
            "role": "system",
            "content": f"Previous context: {mem['memory']}"
        })

    return context
```

### Asset Detection Utility

```python
import re
from typing import Optional
from app.core.database import supabase

async def extract_asset_from_message(message: str) -> Optional[str]:
    """Extract asset reference from user message and map to asset_id."""
    # Common patterns: "Grinder 5", "Asset #123", "Machine 7"
    patterns = [
        r"(grinder|machine|asset|line|press|mixer)\s*#?\s*(\d+)",
        r"asset[_\s]?id[:\s]+(\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            # Query Plant Object Model to get asset_id
            source_id = match.group(0)
            result = await supabase.table("assets").select("id").ilike(
                "source_id", f"%{source_id}%"
            ).limit(1).execute()

            if result.data:
                return result.data[0]["id"]

    return None
```

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── memory/
│   │       ├── __init__.py           # Exports memory_service
│   │       ├── mem0_service.py       # Core memory service
│   │       └── asset_detector.py     # Asset extraction utility
│   ├── api/
│   │   └── memory.py                 # Memory API endpoints
│   └── models/
│       └── memory.py                 # Pydantic models
├── migrations/
│   └── 001_mem0_vector_schema.sql    # Supabase migration
```

**Dependencies to add to requirements.txt:**
```
mem0ai>=0.1.0
openai>=1.0.0
```

### Dependencies

**Story Dependencies:**
- Story 1.1 (TurboRepo Monorepo Scaffold) - Must have FastAPI structure
- Story 1.2 (Supabase Auth Integration) - Must have JWT auth working
- Story 1.3 (Plant Object Model Schema) - Must have `assets` table for asset linking

**Blocked By:** Stories 1.1, 1.2, 1.3 must be complete

**Enables:**
- Story 4.2 (LangChain Text-to-SQL) - Uses memory for context-aware queries
- Story 4.3 (Chat Sidebar UI) - Frontend consumes memory API
- Story 4.4 (Asset History Memory) - Extends asset-specific memory features
- Story 4.5 (Cited Response Generation) - Memory provides context for citations

### Testing Strategy

1. **Unit Tests:**
   - Memory service initialization with mock config
   - `add_memory()` with various message formats
   - `search_memory()` with similarity filtering
   - Asset detection regex patterns
   - LangChain output formatting

2. **Integration Tests:**
   - Full memory storage and retrieval cycle
   - Asset linking with Plant Object Model
   - JWT user_id extraction and filtering
   - Supabase pgvector operations (use test database)

3. **Manual Testing:**
   - Store a memory via API
   - Search for it via API
   - Verify in Supabase dashboard
   - Test with real OpenAI embeddings

### Error Handling Patterns

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    async def add_memory(self, messages, user_id, metadata=None):
        try:
            result = self.memory.add(messages, user_id=user_id, metadata=metadata)
            return result
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store memory. Please try again."
            )

    async def search_memory(self, query, user_id, limit=5):
        try:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            return results.get("results", [])
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            # Return empty results on search failure (graceful degradation)
            return []
```

### NFR Compliance

- **NFR1 (Accuracy):** Memory storage preserves exact user queries and AI responses for citation
- **NFR2 (Latency):** HNSW index ensures sub-100ms vector search performance
- **NFR3 (Read-Only):** Memory operations only touch Supabase (app database), not MSSQL source

### Known Issues and Workarounds

**Issue:** Supabase free tier blocks port 5432 for direct connections.
**Workaround:** Use the connection pooler URL on port 6543 instead.

**Issue:** Mem0 requires direct database connection (not HTTP API).
**Workaround:** Use the PostgreSQL connection string from Supabase settings, not the REST API URL.

**Issue:** Large embedding dimensions (1536) increase storage costs.
**Workaround:** Consider OpenAI text-embedding-3-small (512 dims) for cost optimization in future.

### References

- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 integration specification
- [Source: _bmad/bmm/data/architecture.md#3. Tech Stack] - Mem0 and LangChain versions
- [Source: _bmad/bmm/data/prd.md#Functional] - FR6 AI Chat with Memory requirement
- [Source: _bmad-output/planning-artifacts/epic-4.md] - Epic 4 context
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] - Story scope
- [Mem0 Supabase Docs](https://docs.mem0.ai/components/vectordbs/dbs/supabase) - Official Mem0 Supabase configuration
- [Mem0 LangChain Integration](https://docs.mem0.ai/integrations/langchain) - LangChain compatibility patterns
- [Supabase pgvector Docs](https://supabase.com/docs/guides/database/extensions/pgvector) - Vector storage reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
