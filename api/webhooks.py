# api/webhooks.py
"""
Webhook Endpoints for TaskVault CRM

Handles incoming webhooks from:
- Gmail (via Google Pub/Sub)
- WhatsApp (via Twilio)
- Web Support Form
"""

import os
import sys
import json
import base64
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channels.gmail_handler import get_gmail_handler
from database.queries import (
    get_or_create_customer,
    start_conversation,
    log_message,
    create_ticket
)
from agent.customer_success_agent import process_customer_message

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Pydantic Models ---

class PubSubMessage(BaseModel):
    """Google Pub/Sub push message format."""
    message: dict
    subscription: str


class WebFormSubmission(BaseModel):
    """Web support form submission."""
    name: str
    email: EmailStr
    subject: str
    message: str
    phone: Optional[str] = None


# --- Gmail Webhook ---

@router.get("/gmail/ping")
async def gmail_ping():
    """Quick connectivity test — open this in browser to verify routing works."""
    logger.info("✅ Gmail ping received!")
    return {"status": "ok", "message": "Gmail webhook endpoint is reachable!"}


@router.post("/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Gmail Pub/Sub webhook endpoint.

    Receives push notifications when new emails arrive.
    Processes emails in the background to respond quickly.
    """
    try:
        # Log EVERYTHING about the raw request first
        raw_body = await request.body()
        logger.info(f"📬 ===== Gmail webhook HIT =====")
        logger.info(f"   Method: {request.method}")
        logger.info(f"   URL: {request.url}")
        logger.info(f"   Headers: {dict(request.headers)}")
        logger.info(f"   Raw body ({len(raw_body)} bytes): {raw_body[:500]}")

        # Parse body
        if not raw_body:
            logger.warning("   ⚠️ Empty body received!")
            return {"status": "acknowledged"}

        body = json.loads(raw_body)
        logger.info(f"   Parsed body keys: {list(body.keys())}")

        # Decode Pub/Sub data
        if 'message' in body and 'data' in body['message']:
            data = base64.b64decode(body['message']['data']).decode('utf-8')
            pubsub_data = json.loads(data)
            logger.info(f"   📧 Email address: {pubsub_data.get('emailAddress')}")
            logger.info(f"   📧 History ID: {pubsub_data.get('historyId')}")

            # Process in background
            background_tasks.add_task(process_gmail_notification, pubsub_data)
        else:
            logger.warning(f"   ⚠️ No 'message.data' found in body: {body}")

        # Must return 200 quickly to acknowledge
        return {"status": "acknowledged"}

    except Exception as e:
        logger.error(f"❌ Gmail webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Still return 200 to prevent Pub/Sub retries
        return {"status": "error", "message": str(e)}


async def process_gmail_notification(pubsub_data: dict):
    """
    Background task to process Gmail notification.

    1. Fetch new emails via Gmail API
    2. Create/find customer in CRM
    3. Create conversation and ticket
    4. Process through agent
    5. Send reply via Gmail
    """
    try:
        handler = get_gmail_handler()

        # Get new messages
        messages = await handler.process_pubsub_notification(pubsub_data)

        for email_msg in messages:
            logger.info(f"📧 Processing email from: {email_msg['customer_email']}")
            logger.info(f"   Subject: {email_msg['subject']}")

            # 1. Get or create customer
            customer_id = await get_or_create_customer(
                name=email_msg.get('customer_name'),
                email=email_msg['customer_email']
            )
            logger.info(f"   Customer ID: {customer_id}")

            # 2. Start conversation
            conversation_id = await start_conversation(customer_id, "email")
            logger.info(f"   Conversation ID: {conversation_id}")

            # 3. Log inbound message
            await log_message(
                conversation_id=conversation_id,
                channel="email",
                direction="inbound",
                role="customer",
                content=email_msg['content']
            )

            # 4. Process through agent
            # Combine subject and content for context
            full_message = f"Subject: {email_msg['subject']}\n\n{email_msg['content']}"

            agent_response = await process_customer_message(
                customer_id=customer_id,
                conversation_id=conversation_id,
                channel="email",
                message=full_message
            )
            logger.info(f"   Agent response generated ({len(agent_response)} chars)")

            # 5. Log outbound message
            await log_message(
                conversation_id=conversation_id,
                channel="email",
                direction="outbound",
                role="agent",
                content=agent_response
            )

            # 6. Send reply via Gmail
            reply_result = await handler.send_reply(
                to_email=email_msg['customer_email'],
                subject=email_msg['subject'],
                body=agent_response,
                thread_id=email_msg.get('thread_id'),
                in_reply_to=email_msg.get('metadata', {}).get('headers', {}).get('message-id')
            )
            logger.info(f"   Reply sent: {reply_result['delivery_status']}")

            # 7. Mark original as read and add label
            await handler.mark_as_read(email_msg['channel_message_id'])
            await handler.add_label(email_msg['channel_message_id'], "TaskVault/Processed")

    except Exception as e:
        logger.error(f"❌ Error processing Gmail notification: {e}")
        import traceback
        logger.error(traceback.format_exc())


# --- Web Form Webhook ---

@router.post("/web-form")
async def web_form_webhook(submission: WebFormSubmission, background_tasks: BackgroundTasks):
    """
    Web support form submission endpoint.

    Processes form submissions and triggers agent response.
    Response is sent via email to the customer.
    """
    try:
        logger.info(f"🌐 Web form submission received")
        logger.info(f"   From: {submission.name} <{submission.email}>")
        logger.info(f"   Subject: {submission.subject}")

        # Process in background, return ticket ID immediately
        # Generate a temporary ticket reference
        ticket_ref = f"WEB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        background_tasks.add_task(process_web_form, submission, ticket_ref)

        return {
            "status": "received",
            "ticket_reference": ticket_ref,
            "message": f"Thank you, {submission.name}! We've received your request and will respond to {submission.email} shortly."
        }

    except Exception as e:
        logger.error(f"❌ Web form error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_web_form(submission: WebFormSubmission, ticket_ref: str):
    """
    Background task to process web form submission.
    """
    try:
        # 1. Get or create customer
        customer_id = await get_or_create_customer(
            name=submission.name,
            email=submission.email,
            phone=submission.phone
        )
        logger.info(f"   Customer ID: {customer_id}")

        # 2. Start conversation
        conversation_id = await start_conversation(customer_id, "web_form")
        logger.info(f"   Conversation ID: {conversation_id}")

        # 3. Log inbound message
        full_message = f"Subject: {submission.subject}\n\n{submission.message}"
        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="inbound",
            role="customer",
            content=full_message
        )

        # 4. Process through agent
        agent_response = await process_customer_message(
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel="web_form",
            message=full_message
        )
        logger.info(f"   Agent response generated ({len(agent_response)} chars)")

        # 5. Log outbound message
        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="outbound",
            role="agent",
            content=agent_response
        )

        # 6. Send response via Gmail
        try:
            handler = get_gmail_handler()
            await handler.send_reply(
                to_email=submission.email,
                subject=f"Re: {submission.subject} [{ticket_ref}]",
                body=agent_response
            )
            logger.info(f"   Email response sent to {submission.email}")
        except Exception as email_error:
            logger.error(f"   Failed to send email response: {email_error}")
            # TODO: Queue for retry or notify team

    except Exception as e:
        logger.error(f"❌ Error processing web form: {e}")
        import traceback
        logger.error(traceback.format_exc())


# --- WhatsApp Webhook (Placeholder) ---

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp webhook endpoint (via Twilio).

    TODO: Implement Twilio WhatsApp integration.
    """
    logger.info("📱 WhatsApp webhook received (not yet implemented)")
    return {"status": "acknowledged"}


@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """
    WhatsApp webhook verification (for Twilio setup).
    """
    # Twilio doesn't require verification like Meta
    return {"status": "ok"}
