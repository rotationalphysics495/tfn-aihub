"""
User models for authentication
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CurrentUser(BaseModel):
    """
    Represents the currently authenticated user extracted from JWT token.
    Used as the return type for the get_current_user dependency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "authenticated",
            }
        }
    )

    id: str
    email: Optional[str] = None
    role: str = "authenticated"
