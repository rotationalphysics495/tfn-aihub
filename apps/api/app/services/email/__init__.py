"""
Email Services Package (Story 15.2, 15.3)

Provides email notification services for follow-up assignments.

Components:
- SMTPEmailProvider: SMTP-based email sending via aiosmtplib
- FollowUpNotificationService: Orchestrates email sending and message logging
- TokenService: Token generation and validation for unauthenticated responses
"""

from app.services.email.provider import SMTPEmailProvider, SendResult, EmailProvider
from app.services.email.notification_service import FollowUpNotificationService
from app.services.email.tokens import TokenService

_email_service_instance = None
_notification_service_instance = None
_token_service_instance = None


def get_email_service() -> SMTPEmailProvider:
    """Get singleton SMTPEmailProvider instance."""
    global _email_service_instance
    if _email_service_instance is None:
        from app.core.config import get_settings
        settings = get_settings()
        _email_service_instance = SMTPEmailProvider(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            smtp_from=settings.smtp_from,
            smtp_use_tls=settings.smtp_use_tls,
        )
    return _email_service_instance


def get_notification_service() -> FollowUpNotificationService:
    """Get singleton FollowUpNotificationService instance."""
    global _notification_service_instance
    if _notification_service_instance is None:
        from app.core.config import get_settings
        from supabase import create_client
        settings = get_settings()
        supabase_client = None
        if settings.supabase_url and settings.supabase_key:
            supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        _notification_service_instance = FollowUpNotificationService(
            email_provider=get_email_service(),
            supabase_client=supabase_client,
        )
    return _notification_service_instance


def get_token_service() -> TokenService:
    """Get singleton TokenService instance using service_role client."""
    global _token_service_instance
    if _token_service_instance is None:
        from app.core.config import get_settings
        from supabase import create_client
        settings = get_settings()
        supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        _token_service_instance = TokenService(supabase_client=supabase_client)
    return _token_service_instance


__all__ = [
    "SMTPEmailProvider",
    "SendResult",
    "EmailProvider",
    "FollowUpNotificationService",
    "TokenService",
    "get_email_service",
    "get_notification_service",
    "get_token_service",
]
