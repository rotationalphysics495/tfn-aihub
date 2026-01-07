"""
Memory Service Module (Story 4.1)

Provides Mem0 vector memory integration for:
- User session memory storage and retrieval
- Asset history memory with Plant Object Model integration
- LangChain-compatible context retrieval

AC#1: Mem0 Python SDK Integration
AC#6: Memory Service API
"""

from app.services.memory.mem0_service import (
    MemoryService,
    MemoryServiceError,
    memory_service,
    get_memory_service,
)
from app.services.memory.asset_detector import (
    extract_asset_from_message,
    AssetDetector,
)

__all__ = [
    "MemoryService",
    "MemoryServiceError",
    "memory_service",
    "get_memory_service",
    "extract_asset_from_message",
    "AssetDetector",
]
