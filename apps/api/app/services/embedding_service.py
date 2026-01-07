"""
Embedding Service (Story 4.4)

Service for generating text embeddings using OpenAI's text-embedding-3-small model.
Embeddings are used for semantic search of asset history entries.

AC#1: Vector embeddings generated for semantic search
AC#7: Integrate OpenAI text-embedding-3-small
"""

import logging
from typing import List, Optional

from openai import OpenAI, OpenAIError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingServiceError(Exception):
    """Base exception for Embedding Service errors."""
    pass


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI.

    Story 4.4 Implementation:
    - AC#1: Generates vector embeddings for asset history entries
    - AC#7: Uses OpenAI text-embedding-3-small (1536 dimensions)
    """

    def __init__(self):
        """Initialize the Embedding Service (lazy initialization)."""
        self._client: Optional[OpenAI] = None
        self._settings = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def _ensure_client(self) -> OpenAI:
        """Ensure OpenAI client is initialized."""
        if self._client is None:
            settings = self._get_settings()
            if not settings.openai_api_key:
                raise EmbeddingServiceError(
                    "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
                )
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        AC#7: Uses text-embedding-3-small model (1536 dimensions).

        Args:
            text: Text to generate embedding for

        Returns:
            List of 1536 floats representing the embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingServiceError("Cannot generate embedding for empty text")

        try:
            client = self._ensure_client()

            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text.strip(),
                encoding_format="float"
            )

            embedding = response.data[0].embedding

            logger.debug(
                f"Generated embedding for text ({len(text)} chars): "
                f"vector of {len(embedding)} dimensions"
            )

            return embedding

        except OpenAIError as e:
            logger.error(f"OpenAI API error generating embedding: {e}")
            raise EmbeddingServiceError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}")

    def generate_history_embedding(
        self,
        title: str,
        description: Optional[str] = None,
        resolution: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for an asset history entry.

        AC#7: Combines title + description + resolution for embedding input.

        Args:
            title: History entry title (required)
            description: Optional description
            resolution: Optional resolution text
            event_type: Optional event type for context

        Returns:
            List of 1536 floats representing the embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        # Combine fields into a single text for embedding
        parts = []

        if event_type:
            parts.append(f"[{event_type.upper()}]")

        parts.append(title)

        if description:
            parts.append(description)

        if resolution:
            parts.append(f"Resolution: {resolution}")

        combined_text = " ".join(parts)

        return self.generate_embedding(combined_text)

    def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Handles batching for large lists to avoid API limits.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 2048)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingServiceError: If any embedding generation fails
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            raise EmbeddingServiceError("No valid texts to embed")

        try:
            client = self._ensure_client()
            all_embeddings = []

            # Process in batches
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]

                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch,
                    encoding_format="float"
                )

                # Embeddings are returned in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(
                    f"Generated embeddings for batch {i // batch_size + 1}: "
                    f"{len(batch)} texts"
                )

            return all_embeddings

        except OpenAIError as e:
            logger.error(f"OpenAI API error in batch embedding: {e}")
            raise EmbeddingServiceError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in batch embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate batch embeddings: {e}")

    def is_configured(self) -> bool:
        """Check if the embedding service is properly configured."""
        settings = self._get_settings()
        return bool(settings.openai_api_key)

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._settings = None
        self._client = None
        logger.debug("Embedding service cache cleared")


# Module-level singleton instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """
    Get the singleton EmbeddingService instance.

    Returns:
        EmbeddingService singleton instance
    """
    return embedding_service
