# api/webhooks.py
"""
Webhook Endpoints for TaskVault CRM

Handles incoming webhooks from:
- Gmail (via Google Pub/Sub)
- WhatsApp (via Twilio)
"""

import os
import sys
import json
import base64
import logging
import threading
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channels.gmail_handler import get_gmail_handler
from channels.whatsapp_handler import WhatsAppHandler
from database.queries import (
    get_or_create_customer,
    start_conversation,
    log_message,
    create_ticket
)
from agent.customer_success_agent import process_customer_message

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# WhatsApp handler singleton
# ---------------------------------------------------------------------------
_whatsapp_handler: Optional[WhatsAppHandler] = None

def get_whatsapp_handler() -> WhatsAppHandler:
    global _whatsapp_handler
    if _whatsapp_handler is None:
        _whatsapp_handler = WhatsAppHandler()
    return _whatsapp_handler

# ---------------------------------------------------------------------------
# Idempotency cache
# ---------------------------------------------------------------------------
_seen_pubsub_ids: set[str] = set()
_seen_whatsapp_ids: set[str] = set()
_seen_lock = threading.Lock()

# Gmail address that belongs to the AI — skip emails we sent ourselves
OWN_EMAIL: str = os.getenv("GMAIL_ADDRESS", "ibad0352@gmail.com").lower()
# WhatsApp number that belongs to the AI
OWN_WHATSAPP: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "").lower().replace("whatsapp:", "").replace("+", "")
# Dev mode toggle
DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Gmail webhook
# ---------------------------------------------------------------------------

@router.get("/gmail/ping")
async def gmail_ping():
    """Connectivity test — open in browser to verify the endpoint is reachable."""
    logger.info("✅ Gmail ping received!")
    return {"status": "ok", "message": "Gmail webhook endpoint is reachable!"}


@router.post("/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Gmail Pub/Sub push endpoint.

    Google calls this within seconds of a new message arriving.
    We acknowledge immediately (return 200) and process in the background
    so Google never retries due to a slow response.
    """
    try:
        raw_body = await request.body()

        if not raw_body:
            logger.warning("⚠️ Gmail webhook: empty body — ignoring")
            return {"status": "acknowledged"}

        body = json.loads(raw_body)

        if "message" not in body or "data" not in body["message"]:
            logger.warning(f"⚠️ Gmail webhook: unexpected payload shape — {list(body.keys())}")
            return {"status": "acknowledged"}

        pubsub_msg   = body["message"]
        pubsub_id    = pubsub_msg.get("messageId") or pubsub_msg.get("message_id", "")
        pubsub_data  = json.loads(base64.b64decode(pubsub_msg["data"]).decode("utf-8"))

        email_address = pubsub_data.get("emailAddress", "?")
        history_id    = pubsub_data.get("historyId", "?")

        logger.info(f"📬 Gmail webhook | pubsubId={pubsub_id} | email={email_address} | historyId={history_id}")

        # --- Idempotency check ---
        with _seen_lock:
            if pubsub_id and pubsub_id in _seen_pubsub_ids:
                logger.info(f"   ⏭️  Duplicate pubsubId {pubsub_id} — skipping")
                return {"status": "acknowledged"}
            if pubsub_id:
                _seen_pubsub_ids.add(pubsub_id)
                # Keep the set bounded (last 500 IDs is more than enough)
                if len(_seen_pubsub_ids) > 500:
                    _seen_pubsub_ids.pop()

        # Hand off to background task and return 200 immediately
        background_tasks.add_task(process_gmail_notification, pubsub_data)
        return {"status": "acknowledged"}

    except Exception as e:
        logger.error(f"❌ Gmail webhook parse error: {e}", exc_info=True)
        # Still return 200 — a non-200 triggers unlimited Pub/Sub retries
        return {"status": "error", "detail": str(e)}


async def process_gmail_notification(pubsub_data: dict):
    """
    Background task: fetch new emails → run agent → send reply.

    Steps
    -----
    1. Ask Gmail API for messages added since last historyId
    2. Skip emails that are SENT by us or FROM our own address
    3. Upsert customer record in PostgreSQL
    4. Create conversation + log inbound message
    5. Run TaskVault agent
    6. Log outbound message + send Gmail reply
    7. Mark original as read, apply "TaskVault/Processed" label
    """
    try:
        handler  = get_gmail_handler()
        messages = await handler.process_pubsub_notification(pubsub_data)

        if not messages:
            logger.info("   📭 No new inbound emails to process")
            return

        for email_msg in messages:
            sender = email_msg["customer_email"].lower()

            # --- Loop guard: never reply to our own outbound messages ---
            if sender == OWN_EMAIL:
                logger.info(f"   🔁 Skipping email from self ({sender})")
                continue

            logger.info(f"📧 Processing | from={sender} | subject={email_msg['subject']!r}")

            # 1. Customer
            customer_id = await get_or_create_customer(
                name=email_msg.get("customer_name"),
                email=sender,
            )
            logger.info(f"   👤 Customer ID: {customer_id}")

            # 2. Conversation
            conversation_id = await start_conversation(customer_id, "email")
            logger.info(f"   💬 Conversation ID: {conversation_id}")

            # 3. Log inbound
            await log_message(
                conversation_id=conversation_id,
                channel="email",
                direction="inbound",
                role="customer",
                content=email_msg["content"],
            )

            # 4. Agent
            full_message = f"Subject: {email_msg['subject']}\n\n{email_msg['content']}"
            agent_response = await process_customer_message(
                customer_id=customer_id,
                conversation_id=conversation_id,
                channel="email",
                message=full_message,
            )
            logger.info(f"   🤖 Agent response ready ({len(agent_response)} chars)")

            # 5. Log outbound
            await log_message(
                conversation_id=conversation_id,
                channel="email",
                direction="outbound",
                role="agent",
                content=agent_response,
            )

            # 6. Send reply
            reply = await handler.send_reply(
                to_email=sender,
                subject=email_msg["subject"],
                body=agent_response,
                thread_id=email_msg.get("thread_id"),
                in_reply_to=email_msg.get("metadata", {}).get("headers", {}).get("message-id"),
            )
            logger.info(f"   ✉️  Reply status: {reply['delivery_status']}")

            # 7. Housekeeping
            await handler.mark_as_read(email_msg["channel_message_id"])
            await handler.add_label(email_msg["channel_message_id"], "TaskVault/Processed")
            logger.info(f"   ✅ Done — email labelled & marked as read")

    except Exception as e:
        logger.error(f"❌ process_gmail_notification failed: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# WhatsApp webhook
# ---------------------------------------------------------------------------

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    WhatsApp Twilio webhook.

    Twilio calls this when a new message is received.
    We validate the signature (unless in DEV_MODE), acknowledge immediately,
    and process in the background.
    """
    try:
        handler = get_whatsapp_handler()

        # 1. Validate signature if not in DEV_MODE
        if not DEV_MODE:
            is_valid = await handler.validate_webhook(request)
            if not is_valid:
                logger.warning("⚠️ WhatsApp webhook: Invalid signature")
                raise HTTPException(status_code=403, detail="Invalid signature")

        # 2. Extract form data
        form_data = await request.form()
        payload = dict(form_data)

        message_sid = payload.get("MessageSid")
        from_number = payload.get("From", "").replace("whatsapp:", "")

        logger.info(f"📱 WhatsApp webhook | sid={message_sid} | from={from_number}")

        # 3. Idempotency check
        with _seen_lock:
            if message_sid and message_sid in _seen_whatsapp_ids:
                logger.info(f"   ⏭️  Duplicate WhatsApp SID {message_sid} — skipping")
                return {"status": "acknowledged"}
            if message_sid:
                _seen_whatsapp_ids.add(message_sid)
                if len(_seen_whatsapp_ids) > 500:
                    _seen_whatsapp_ids.pop()

        # 4. Loop guard — normalize both sides to digits-only for safe comparison
        from_normalized = from_number.replace("+", "").strip()
        if from_normalized == OWN_WHATSAPP:
            logger.info(f"   🔁 Skipping WhatsApp from self ({from_number})")
            return {"status": "acknowledged"}

        # 5. Background processing
        background_tasks.add_task(process_whatsapp_message, payload)

        # Twilio expects TwiML response, but empty response is also okay
        # We return a simple XML to satisfy Twilio's default behavior
        return {"status": "acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}


async def process_whatsapp_message(payload: dict):
    """
    Background task: process WhatsApp message → run agent → send reply.
    """
    try:
        handler = get_whatsapp_handler()
        msg_data = await handler.process_webhook(payload)

        customer_phone = msg_data["customer_phone"]
        customer_name = msg_data["metadata"].get("profile_name")
        content = msg_data["content"]

        logger.info(f"📱 Processing WhatsApp | from={customer_phone} | content={content[:50]}...")

        # 1. Customer
        customer_id = await get_or_create_customer(
            name=customer_name,
            phone=customer_phone
        )
        logger.info(f"   👤 Customer ID: {customer_id}")

        # 2. Conversation
        conversation_id = await start_conversation(customer_id, "whatsapp")
        logger.info(f"   💬 Conversation ID: {conversation_id}")

        # 3. Log inbound
        await log_message(
            conversation_id=conversation_id,
            channel="whatsapp",
            direction="inbound",
            role="customer",
            content=content,
        )

        # 4. Agent
        agent_response = await process_customer_message(
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel="whatsapp",
            message=content,
        )
        logger.info(f"   🤖 Agent response ready ({len(agent_response)} chars)")

        # 5. Log outbound
        await log_message(
            conversation_id=conversation_id,
            channel="whatsapp",
            direction="outbound",
            role="agent",
            content=agent_response,
        )

        # 6. Send reply (split if needed)
        messages = handler.format_response(agent_response)
        for msg_body in messages:
            reply = await handler.send_message(
                to_phone=customer_phone,
                body=msg_body
            )
            logger.info(f"   📱 Reply status: {reply['delivery_status']}")

        logger.info(f"   ✅ Done — WhatsApp response sent")

    except Exception as e:
        logger.error(f"❌ process_whatsapp_message failed: {e}", exc_info=True)


@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """WhatsApp webhook verification."""
    return {"status": "ok"}
