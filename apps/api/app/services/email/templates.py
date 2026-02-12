"""
Email Templates for follow-up notifications.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment

Uses inline styles for email client compatibility.
Industrial Clarity design: dark header (#1a1a2e), white content (#ffffff), blue CTA (#3b82f6).
"""

from html import escape as html_escape
from typing import Optional


def render_assignment_email(
    category: str,
    asset_name: str,
    action_summary: str,
    recommendation: str,
    evidence_summary: str,
    assigner_name: str,
    followup_id: str,
    app_base_url: str,
    financial_impact: Optional[str] = None,
    note: Optional[str] = None,
    response_token: Optional[str] = None,
) -> dict:
    """Render an assignment notification email.

    Returns a dict with 'subject', 'html_body', and 'text_body' keys.

    Args:
        response_token: Optional token to append to the respond URL (Story 15.3).
    """
    subject = f"[Action Required] {category} - {asset_name}: {action_summary}"

    respond_url = f"{app_base_url.rstrip('/')}/followups/{followup_id}/respond"
    if response_token:
        respond_url = f"{respond_url}?token={response_token}"

    # HTML-escape user-supplied values to prevent XSS in email clients
    esc_category = html_escape(category)
    esc_asset_name = html_escape(asset_name)
    esc_action_summary = html_escape(action_summary)
    esc_recommendation = html_escape(recommendation)
    esc_evidence_summary = html_escape(evidence_summary)
    esc_assigner_name = html_escape(assigner_name)

    # Build optional sections
    financial_section_html = ""
    if financial_impact:
        esc_financial_impact = html_escape(financial_impact)
        financial_section_html = f"""
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; font-size: 14px; vertical-align: top; width: 140px;">Financial Impact</td>
                    <td style="padding: 8px 0; color: #111827; font-size: 14px;">{esc_financial_impact}</td>
                </tr>"""

    note_section_html = ""
    if note:
        esc_note = html_escape(note)
        note_section_html = f"""
            <div style="margin-top: 20px; padding: 12px 16px; background-color: #f9fafb; border-left: 3px solid #3b82f6; border-radius: 4px;">
                <p style="margin: 0 0 4px 0; font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Note from {esc_assigner_name}</p>
                <p style="margin: 0; font-size: 14px; color: #111827;">{esc_note}</p>
            </div>"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 24px 32px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 18px; font-weight: 600;">Action Required</h1>
                            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">{esc_category} &middot; {esc_asset_name}</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 32px;">
                            <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 16px; font-weight: 600;">{esc_action_summary}</h2>

                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; font-size: 14px; vertical-align: top; width: 140px;">Recommendation</td>
                    <td style="padding: 8px 0; color: #111827; font-size: 14px;">{esc_recommendation}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; font-size: 14px; vertical-align: top; width: 140px;">Evidence</td>
                    <td style="padding: 8px 0; color: #111827; font-size: 14px;">{esc_evidence_summary}</td>
                </tr>{financial_section_html}
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; font-size: 14px; vertical-align: top; width: 140px;">Assigned by</td>
                    <td style="padding: 8px 0; color: #111827; font-size: 14px;">{esc_assigner_name}</td>
                </tr>
                            </table>
{note_section_html}

                            <!-- CTA Button -->
                            <div style="margin-top: 24px; text-align: center;">
                                <a href="{respond_url}" style="display: inline-block; padding: 12px 32px; background-color: #3b82f6; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600;">Respond</a>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 16px 32px; text-align: center; border-radius: 0 0 8px 8px; background-color: #f9fafb;">
                            <p style="margin: 0; font-size: 12px; color: #9ca3af;">Manufacturing Performance Assistant</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    # Plain text fallback
    text_parts = [
        f"[Action Required] {category} - {asset_name}: {action_summary}",
        "",
        f"Recommendation: {recommendation}",
        f"Evidence: {evidence_summary}",
    ]
    if financial_impact:
        text_parts.append(f"Financial Impact: {financial_impact}")
    text_parts.append(f"Assigned by: {assigner_name}")
    if note:
        text_parts.extend(["", f"Note: {note}"])
    text_parts.extend([
        "",
        f"Respond: {respond_url}",
    ])
    text_body = "\n".join(text_parts)

    return {
        "subject": subject,
        "html_body": html_body,
        "text_body": text_body,
    }
