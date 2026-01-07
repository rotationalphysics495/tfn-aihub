"""
Asset Detection Utility (Story 4.1)

Extracts asset references from user messages and maps them to
asset_id from the Plant Object Model.

AC#4: Asset History Memory Storage
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from supabase import create_client, Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AssetDetector:
    """
    Detects and resolves asset references from user messages.

    Maps natural language references like "Grinder 5" or "Machine 7"
    to the corresponding asset_id from the Plant Object Model.

    AC#4: Enables asset linking for memory storage.
    """

    # Common asset type patterns
    ASSET_PATTERNS = [
        # Pattern: "Grinder 5", "Machine 7", "Press 3", "Mixer 2"
        r"\b(grinder|machine|asset|line|press|mixer|lathe|mill|saw|drill|cnc|robot)\s*[#]?\s*(\d+)\b",
        # Pattern: "Asset #123", "asset-123"
        r"\basset[_\-\s]?[#]?(\w+[-_]?\d+)\b",
        # Pattern: "Line A", "Line B" (for production lines)
        r"\bline\s+([A-Za-z])\b",
    ]

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the AssetDetector.

        Args:
            supabase_client: Optional Supabase client (created if not provided)
        """
        self._client = supabase_client
        self._assets_cache: Dict[str, Dict] = {}
        self._source_id_map: Dict[str, str] = {}  # source_id -> asset_id
        self._name_map: Dict[str, str] = {}  # lowercased name -> asset_id

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    async def load_assets(self, force: bool = False) -> None:
        """
        Load assets from Supabase for matching.

        Args:
            force: Force reload even if cached
        """
        if not force and self._assets_cache:
            return

        try:
            client = self._get_client()
            response = client.table("assets").select(
                "id, name, source_id, area"
            ).execute()

            self._assets_cache = {}
            self._source_id_map = {}
            self._name_map = {}

            for asset in response.data or []:
                asset_id = asset.get("id")
                if asset_id:
                    self._assets_cache[asset_id] = asset

                    # Map source_id to asset_id
                    source_id = asset.get("source_id")
                    if source_id:
                        self._source_id_map[source_id.lower()] = asset_id

                    # Map name to asset_id
                    name = asset.get("name")
                    if name:
                        self._name_map[name.lower()] = asset_id

            logger.debug(f"Loaded {len(self._assets_cache)} assets for detection")

        except Exception as e:
            logger.error(f"Failed to load assets: {e}")

    def _extract_references(self, message: str) -> List[Tuple[str, str]]:
        """
        Extract potential asset references from message.

        Args:
            message: User message text

        Returns:
            List of tuples (match_type, match_value)
        """
        references = []

        for pattern in self.ASSET_PATTERNS:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                # Get the full match
                full_match = match.group(0).strip()
                references.append(("pattern", full_match))

        return references

    async def detect_asset(self, message: str) -> Optional[str]:
        """
        Detect and resolve asset reference from message.

        AC#4: Extract asset reference and map to assets.source_id.

        Args:
            message: User message text

        Returns:
            asset_id if found, None otherwise
        """
        # Ensure assets are loaded
        await self.load_assets()

        if not self._assets_cache:
            logger.debug("No assets available for detection")
            return None

        references = self._extract_references(message)

        for match_type, match_value in references:
            # Try to find matching asset
            asset_id = self._resolve_reference(match_value)
            if asset_id:
                logger.info(f"Detected asset: {match_value} -> {asset_id}")
                return asset_id

        return None

    def _resolve_reference(self, reference: str) -> Optional[str]:
        """
        Resolve a reference string to an asset_id.

        Args:
            reference: Extracted reference string

        Returns:
            asset_id if found, None otherwise
        """
        reference_lower = reference.lower()

        # Direct name match
        if reference_lower in self._name_map:
            return self._name_map[reference_lower]

        # Source ID match
        if reference_lower in self._source_id_map:
            return self._source_id_map[reference_lower]

        # Partial name matching (e.g., "Grinder 5" matches "Grinder 5 - Main")
        for name, asset_id in self._name_map.items():
            if reference_lower in name or name in reference_lower:
                return asset_id

        # Partial source_id matching
        for source_id, asset_id in self._source_id_map.items():
            if reference_lower in source_id or source_id in reference_lower:
                return asset_id

        return None

    async def get_asset_info(self, asset_id: str) -> Optional[Dict]:
        """
        Get asset information by ID.

        Args:
            asset_id: Asset identifier

        Returns:
            Asset info dict or None
        """
        await self.load_assets()
        return self._assets_cache.get(asset_id)

    def clear_cache(self) -> None:
        """Clear the assets cache."""
        self._assets_cache.clear()
        self._source_id_map.clear()
        self._name_map.clear()
        logger.debug("Asset detector cache cleared")


# Module-level singleton
_asset_detector: Optional[AssetDetector] = None


def get_asset_detector() -> AssetDetector:
    """Get the singleton AssetDetector instance."""
    global _asset_detector
    if _asset_detector is None:
        _asset_detector = AssetDetector()
    return _asset_detector


async def extract_asset_from_message(message: str) -> Optional[str]:
    """
    Convenience function to extract asset_id from a message.

    AC#4: Extract asset reference and map to Plant Object Model asset_id.

    Args:
        message: User message text

    Returns:
        asset_id if detected, None otherwise
    """
    detector = get_asset_detector()
    return await detector.detect_asset(message)
