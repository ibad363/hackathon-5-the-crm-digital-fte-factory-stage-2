"""
Unified Kafka Message Processor Worker
=======================================

This standalone worker runs SEPARATELY from the FastAPI server.
It consumes events from the `fte.tickets.incoming` Kafka topic,
runs the OpenAI Agent, updates PostgreSQL, and sends responses
back through the correct channel handler (Gmail / WhatsApp / Web).

Usage:
    Terminal 1:  uvicorn api.main:app --port 8000
    Terminal 2:  python -m workers.unified_processor
"""

import os
import sys
import logging
import asyncio
import time
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_client import KafkaClient, TOPICS
from database.queries import (
    get_or_create_customer,
    start_conversation,
    log_message,
    get_db_pool,
)
from agent.customer_success_agent import process_customer_message
from channels.gmail_handler import get_gmail_handler
from channels.whatsapp_handler import WhatsAppHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OWN_EMAIL: str = os.getenv("GMAIL_ADDRESS", "ibad0352@gmail.com").lower()


# ---------------------------------------------------------------------------
# Channel-specific processors
# ---------------------------------------------------------------------------

async def process_email_event(payload: Dict[str, Any]) -> None:
    """Process an email event received from Kafka."""
    email_msg = payload.get("email_msg", {})
    sender = email_msg.get("customer_email", "").lower()

    if sender == OWN_EMAIL:
        logger.info("   🔁 Skipping email from self (%s)", sender)
        return

    logger.info(
        "📧 Worker Processing Email | from=%s | subject=%r",
        sender,
        email_msg.get("subject", ""),
    )

    # 1. Customer
    customer_id = await get_or_create_customer(
        name=email_msg.get("customer_name"),
        email=sender,
    )

    # 2. Conversation
    conversation_id = await start_conversation(customer_id, "email")

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
    await process_customer_message(
        customer_id=customer_id,
        conversation_id=conversation_id,
        channel="email",
        message=full_message,
    )
    logger.info("   🤖 Agent processing complete (Response sent via tool)")

    # 5. Housekeeping
    handler = get_gmail_handler()
    await handler.mark_as_read(email_msg["channel_message_id"])
    await handler.add_label(email_msg["channel_message_id"], "TaskVault/Processed")
    logger.info("   ✅ Done — email labelled & marked as read")


async def process_whatsapp_event(payload: Dict[str, Any]) -> None:
    """Process a WhatsApp event received from Kafka."""
    msg_data = payload.get("msg_data", {})
    customer_phone = msg_data.get("customer_phone")
    customer_name = msg_data.get("metadata", {}).get("profile_name")
    content = msg_data.get("content", "")

    logger.info(
        "📱 Worker Processing WhatsApp | from=%s | content=%s...",
        customer_phone,
        content[:50],
    )

    # 1. Customer
    customer_id = await get_or_create_customer(
        name=customer_name, phone=customer_phone
    )

    # 2. Conversation
    conversation_id = await start_conversation(customer_id, "whatsapp")

    # 3. Log inbound
    await log_message(
        conversation_id=conversation_id,
        channel="whatsapp",
        direction="inbound",
        role="customer",
        content=content,
    )

    # 4. Agent
    await process_customer_message(
        customer_id=customer_id,
        conversation_id=conversation_id,
        channel="whatsapp",
        message=content,
    )
    logger.info("   🤖 Agent processing complete (Response sent via tool)")


async def process_web_form_event(payload: Dict[str, Any]) -> None:
    """Process a Web Form event received from Kafka."""
    submission = payload.get("submission", {})
    ticket_ref = payload.get("ticket_ref")
    customer_id = payload.get("customer_id")
    conversation_id = payload.get("conversation_id")

    category = submission.get("category", "general")
    subject = submission.get("subject", "")
    message_content = submission.get("message", "")
    email = submission.get("email", "")

    logger.info(
        "🌐 Worker Processing Web Form | ticket=%s | email=%s", ticket_ref, email
    )

    # 1. Log the inbound message
    enhanced_subject = f"[{category.upper()}] {subject}"
    full_message = f"Subject: {enhanced_subject}\n\n{message_content}"

    await log_message(
        conversation_id=conversation_id,
        channel="web_form",
        direction="inbound",
        role="customer",
        content=full_message,
    )

    # 2. Run the AI agent
    await process_customer_message(
        customer_id=customer_id,
        conversation_id=conversation_id,
        channel="web_form",
        message=full_message,
    )
    logger.info("   🤖 Agent processing complete (Response sent via tool)")

    # 4. Update ticket status to resolved (unless escalated)
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET status = 'resolved', resolved_at = NOW()
            WHERE external_ref = $1 AND status = 'open'
            """,
            ticket_ref,
        )


# ---------------------------------------------------------------------------
# Main event loop
# ---------------------------------------------------------------------------

async def run_worker() -> None:
    """
    Main worker loop.

    Subscribes to the `fte.tickets.incoming` topic and dispatches each event
    to the appropriate channel processor.  After each successful processing
    run it publishes a latency metric to `fte.metrics`.
    """
    logger.info("=" * 60)
    logger.info("🏭 Starting Unified Kafka Message Processor")
    logger.info("=" * 60)

    consumer = await KafkaClient.get_consumer(group_id="fte-unified-worker")
    await consumer.start()

    logger.info("🎧 Listening on topic: %s ...", TOPICS["incoming"])

    try:
        async for msg in consumer:
            payload = msg.value
            channel = payload.get("channel")
            logger.info("📥 Received event | channel=%s | partition=%d | offset=%d",
                        channel, msg.partition, msg.offset)

            start_time = time.time()

            try:
                if channel == "email":
                    await process_email_event(payload)
                elif channel == "whatsapp":
                    await process_whatsapp_event(payload)
                elif channel == "web_form":
                    await process_web_form_event(payload)
                else:
                    logger.warning("⚠️ Unknown channel: %s — skipping", channel)
                    continue

                # Publish processing metrics to the metrics topic
                latency_ms = int((time.time() - start_time) * 1000)
                await KafkaClient.publish(
                    "metrics",
                    {
                        "event_type": "message_processed",
                        "channel": channel,
                        "latency_ms": latency_ms,
                        "timestamp": time.time(),
                    },
                )
                logger.info(
                    "📊 Metrics published | channel=%s | latency=%dms",
                    channel,
                    latency_ms,
                )

            except Exception as e:
                logger.error(
                    "❌ Error processing %s event: %s", channel, e, exc_info=True
                )

    except asyncio.CancelledError:
        logger.info("🛑 Worker shutdown requested...")
    finally:
        logger.info("🔌 Closing Kafka consumer...")
        await consumer.stop()
        await KafkaClient.shutdown()
        logger.info("👋 Worker shut down cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
