"""
JWT token validation for Supabase Auth.

This module handles:
- Fetching and caching JWKS (JSON Web Key Set) from Supabase
- Validating JWT tokens from the Authorization header
- Extracting user information from validated tokens
"""
import httpx
from cachetools import TTLCache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk, JWTError
from jose.exceptions import JWKError
from typing import Any, Optional

from app.core.config import get_settings
from app.models.user import CurrentUser

# Security scheme for OpenAPI docs
security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT token from Supabase Auth",
    auto_error=True,
)

# Cache JWKS for 1 hour to avoid repeated fetches
_jwks_cache: TTLCache = TTLCache(maxsize=1, ttl=3600)

# Supabase JWT algorithm - supports both RSA and ECDSA
ALGORITHMS = ["RS256", "ES256"]


async def _fetch_jwks(supabase_url: str) -> dict[str, Any]:
    """
    Fetch JWKS from Supabase auth endpoint.

    Args:
        supabase_url: The Supabase project URL

    Returns:
        The JWKS response containing public keys

    Raises:
        HTTPException: If JWKS cannot be fetched
    """
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch authentication keys: {str(e)}",
        )


async def _get_signing_key(token: str, supabase_url: str) -> Optional[dict[str, Any]]:
    """
    Get the signing key for a JWT token from cached JWKS.

    Args:
        token: The JWT token to find the key for
        supabase_url: The Supabase project URL

    Returns:
        The matching key from JWKS, or None if not found
    """
    cache_key = "jwks"

    # Try to get from cache first
    if cache_key not in _jwks_cache:
        jwks = await _fetch_jwks(supabase_url)
        _jwks_cache[cache_key] = jwks
    else:
        jwks = _jwks_cache[cache_key]

    # Extract the key ID from the token header
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = unverified_header.get("kid")
    if not kid:
        return None

    # Find the matching key in JWKS
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    # If key not found, refresh cache and try again
    _jwks_cache.pop(cache_key, None)
    jwks = await _fetch_jwks(supabase_url)
    _jwks_cache[cache_key] = jwks

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    return None


async def verify_supabase_jwt(token: str) -> dict[str, Any]:
    """
    Verify a Supabase JWT token and return the payload.

    Args:
        token: The JWT token to verify

    Returns:
        The decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL not configured",
        )

    # Get the signing key for this token
    key_data = await _get_signing_key(token, settings.supabase_url)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Construct the public key from JWKS data
        public_key = jwk.construct(key_data)

        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience="authenticated",
            options={
                "verify_exp": True,
                "verify_aud": True,
            },
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, JWKError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    FastAPI dependency that validates JWT and returns the current user.

    Use this dependency on protected routes to require authentication:

    ```python
    @router.get("/protected")
    async def protected_route(user: CurrentUser = Depends(get_current_user)):
        return {"user_id": user.id}
    ```

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header

    Returns:
        CurrentUser object with user info from the token

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    payload = await verify_supabase_jwt(token)

    return CurrentUser(
        id=payload.get("sub", ""),
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[CurrentUser]:
    """
    FastAPI dependency that optionally validates JWT.

    Returns None if no token is provided, otherwise validates and returns user.
    Useful for routes that behave differently for authenticated vs anonymous users.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        CurrentUser if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    FastAPI dependency that requires admin role.

    Story 5.8 AC#7: Cache stats endpoint is admin-only.

    Args:
        current_user: Authenticated user from get_current_user

    Returns:
        CurrentUser if user has admin or service_role

    Raises:
        HTTPException: If user is not an admin
    """
    admin_roles = {"service_role", "admin", "supabase_admin"}
    if current_user.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this endpoint",
        )
    return current_user
