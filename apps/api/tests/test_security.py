"""
Tests for the security module (JWT validation logic).

Test Coverage for Story 1.2 Acceptance Criteria:
- AC#3: JWT tokens are validated in FastAPI backend
- AC#4: Unauthenticated requests are rejected with appropriate 401 response
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

from app.core.security import (
    verify_supabase_jwt,
    get_current_user,
    get_optional_user,
    _fetch_jwks,
    _get_signing_key,
    _jwks_cache,
)
from app.models.user import CurrentUser


class TestVerifySupabaseJWT:
    """Tests for JWT verification logic."""

    @pytest.mark.asyncio
    async def test_verify_jwt_no_supabase_url(self):
        """Should raise 500 if Supabase URL not configured."""
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value.supabase_url = ""
            with pytest.raises(HTTPException) as exc_info:
                await verify_supabase_jwt("some-token")
            assert exc_info.value.status_code == 500
            assert "not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_jwt_invalid_key_not_found(self):
        """Should raise 401 if signing key not found."""
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value.supabase_url = "https://test.supabase.co"
            with patch(
                "app.core.security._get_signing_key", new_callable=AsyncMock
            ) as mock_get_key:
                mock_get_key.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await verify_supabase_jwt("some-token")
                assert exc_info.value.status_code == 401
                assert "Invalid authentication credentials" in exc_info.value.detail


class TestFetchJWKS:
    """Tests for JWKS fetching."""

    @pytest.mark.asyncio
    async def test_fetch_jwks_timeout(self):
        """Should raise 503 on timeout."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await _fetch_jwks("https://test.supabase.co")
            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_fetch_jwks_http_error(self):
        """Should raise 503 on HTTP error."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPError("HTTP Error")
            mock_client_class.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await _fetch_jwks("https://test.supabase.co")
            assert exc_info.value.status_code == 503
            assert "Failed to fetch" in exc_info.value.detail


class TestGetSigningKey:
    """Tests for signing key retrieval."""

    @pytest.mark.asyncio
    async def test_get_signing_key_invalid_token(self):
        """Should return None for invalid token that can't be parsed."""
        # Clear cache first
        _jwks_cache.clear()

        with patch(
            "app.core.security._fetch_jwks", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = {"keys": []}

            result = await _get_signing_key("not-a-valid-jwt", "https://test.supabase.co")
            assert result is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Should return CurrentUser for valid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        with patch(
            "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.return_value = {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
            }

            user = await get_current_user(mock_credentials)
            assert isinstance(user, CurrentUser)
            assert user.id == "user-123"
            assert user.email == "test@example.com"
            assert user.role == "authenticated"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_email(self):
        """Should handle missing email in token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        with patch(
            "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.return_value = {
                "sub": "user-123",
                "role": "authenticated",
            }

            user = await get_current_user(mock_credentials)
            assert user.id == "user-123"
            assert user.email is None
            assert user.role == "authenticated"


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_get_optional_user_no_credentials(self):
        """Should return None when no credentials provided."""
        user = await get_optional_user(None)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_user_invalid_token(self):
        """Should return None for invalid token (not raise)."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        with patch(
            "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid")

            user = await get_optional_user(mock_credentials)
            assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_user_valid_token(self):
        """Should return user for valid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        with patch(
            "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.return_value = {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
            }

            user = await get_optional_user(mock_credentials)
            assert user is not None
            assert user.id == "user-123"


class TestCurrentUserModel:
    """Tests for CurrentUser Pydantic model."""

    def test_current_user_with_all_fields(self):
        """Should create user with all fields."""
        user = CurrentUser(id="123", email="test@example.com", role="admin")
        assert user.id == "123"
        assert user.email == "test@example.com"
        assert user.role == "admin"

    def test_current_user_with_defaults(self):
        """Should use default role when not provided."""
        user = CurrentUser(id="123")
        assert user.id == "123"
        assert user.email is None
        assert user.role == "authenticated"

    def test_current_user_json_serialization(self):
        """Should serialize to JSON correctly."""
        user = CurrentUser(id="123", email="test@example.com", role="admin")
        json_data = user.model_dump()
        assert json_data["id"] == "123"
        assert json_data["email"] == "test@example.com"
        assert json_data["role"] == "admin"
