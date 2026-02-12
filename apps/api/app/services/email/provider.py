"""
Email Provider - SMTP implementation for sending emails.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment
AC#3: Graceful failure on send error
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional, Protocol, runtime_checkable

import aiosmtplib
from aiosmtplib import SMTPException as _SMTPException

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    """Result of an email send attempt."""
    success: bool
    error: Optional[str]
    sent_at: Optional[datetime]


@runtime_checkable
class EmailProvider(Protocol):
    """Protocol for email sending providers."""

    async def send(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> SendResult:
        ...


class SMTPEmailProvider:
    """SMTP-based email provider using aiosmtplib."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from: str,
        smtp_use_tls: bool = True,
        timeout: int = 10,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.smtp_use_tls = smtp_use_tls
        self.timeout = timeout

    async def send(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> SendResult:
        """Send an email via SMTP.

        Returns SendResult with success/failure status. Never raises exceptions.
        """
        try:
            msg = EmailMessage()
            msg["From"] = self.smtp_from
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype="html")

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.smtp_use_tls,
                use_tls=False,
                timeout=self.timeout,
            )

            sent_at = datetime.now(timezone.utc)
            logger.info(f"Email sent to {recipient}: {subject}")
            return SendResult(success=True, error=None, sent_at=sent_at)

        except (TimeoutError, asyncio.TimeoutError):
            logger.error(f"SMTP timeout sending to {recipient}")
            return SendResult(success=False, error="SMTP connection timeout", sent_at=None)
        except _SMTPException as e:
            logger.error(f"SMTP error sending to {recipient}: {e}")
            return SendResult(success=False, error=str(e), sent_at=None)
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient}: {e}")
            return SendResult(success=False, error=str(e), sent_at=None)
