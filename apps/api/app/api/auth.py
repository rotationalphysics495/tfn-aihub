"""
Authentication API endpoints.

Provides endpoints for:
- Getting current user info
- Testing protected endpoint access
"""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import CurrentUser

router = APIRouter()


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get the current authenticated user's information.

    Returns user data extracted from the JWT token:
    - id: Supabase user ID (UUID)
    - email: User's email address
    - role: User's role (default: authenticated)
    """
    return current_user


@router.get("/verify")
async def verify_authentication(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Verify that the user is authenticated.

    Returns a simple success response if the JWT token is valid.
    Used for testing authentication from the frontend.
    """
    return {
        "authenticated": True,
        "user_id": current_user.id,
    }
