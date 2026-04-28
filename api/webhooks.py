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
from messaging.kafka_client import KafkaClient

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
async def gmail_webhook(request: Request):
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

        # Hand off to Kafka and return 200 immediately
        handler = get_gmail_handler()
        messages = await handler.process_pubsub_notification(pubsub_data)

        if messages:
            for email_msg in messages:
                # Add a unique key to prevent re-processing in the worker
                # though idempotency should handle it, this is a clean handoff.
                await KafkaClient.publish("incoming", {
                    "channel": "email",
                    "email_msg": email_msg
                })

        return {"status": "acknowledged"}

    except Exception as e:
        logger.error(f"❌ Gmail webhook parse error: {e}", exc_info=True)
        # Still return 200 — a non-200 triggers unlimited Pub/Sub retries
        return {"status": "acknowledged"}


# ---------------------------------------------------------------------------
# WhatsApp webhook
# ---------------------------------------------------------------------------

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
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

        # 5. Hand off to Kafka
        msg_data = await handler.process_webhook(payload)
        await KafkaClient.publish("incoming", {
            "channel": "whatsapp",
            "msg_data": msg_data
        })

        return {"status": "acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {e}", exc_info=True)
        return {"status": "acknowledged"}


async def process_whatsapp_message(payload: dict):
    """
    DEPRECATED: Background task moved to unified Kafka worker.
    """
    pass


@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """WhatsApp webhook verification."""
    return {"status": "ok"}
