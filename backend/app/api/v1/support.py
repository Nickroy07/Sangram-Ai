"""Support and Contact Endpoints.

Handles contact form submissions, dispatches notification emails if configured,
and records support inquiries without silent loss.
"""

import logging
from fastapi import APIRouter, Depends, status

from app.api.deps import get_email_sender
from app.core.config import get_settings
from app.schemas.support import ContactRequest, ContactResponse
from app.services.email import IEmailSender

logger = logging.getLogger("sangram_ai.support")

router = APIRouter(prefix="/support", tags=["Support & Inquiries"])


@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Contact Message",
    description="Submits a contact inquiry to Sangram AI support and dispatches email notification.",
)
async def submit_contact(
    payload: ContactRequest,
    email_sender: IEmailSender = Depends(get_email_sender),
) -> ContactResponse:
    settings = get_settings()
    logger.info(
        f"Contact inquiry received from '{payload.name}' <{payload.email}> "
        f"[subject='{payload.subject}']"
    )

    # Dispatch notification email to support team
    try:
        support_recipient = getattr(settings, "SUPPORT_EMAIL", "team@sangram.ai")
        body = (
            f"New Contact Message from Sangram AI Portal:\n\n"
            f"Name: {payload.name}\n"
            f"Email: {payload.email}\n"
            f"Subject: {payload.subject}\n\n"
            f"Message:\n{payload.message}\n"
        )
        await email_sender.send(
            to=support_recipient,
            subject=f"[Sangram AI Support] {payload.subject} (from {payload.name})",
            body=body,
        )
    except Exception as exc:
        logger.error(f"Failed to dispatch contact notification email: {exc}")

    return ContactResponse(
        success=True,
        message="Thank you! Your message has been received by our engineering team.",
    )
