from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
import uuid
import logging

from database.queries import (
    get_or_create_customer,
    start_conversation,
    log_message,
    get_db_pool,
    create_ticket,
)
from agent.customer_success_agent import process_customer_message
from channels.gmail_handler import get_gmail_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support-form"])

class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""
    name: str
    email: EmailStr
    subject: str
    category: str  # 'general', 'technical', 'billing', 'feedback'
    message: str
    priority: Optional[str] = 'medium'
    attachments: Optional[list[str]] = []  # Base64 encoded files or URLs

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()

    @validator('message')
    def message_must_have_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()

    @validator('category')
    def category_must_be_valid(cls, v):
        valid_categories = ['general', 'technical', 'billing', 'feedback', 'bug_report']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v

class SupportFormResponse(BaseModel):
    """Response model for form submission."""
    ticket_id: str
    message: str
    estimated_response_time: str

async def process_web_form_background(submission: SupportFormSubmission, ticket_ref: str, customer_id: str, conversation_id: str):
    """Background task for web-form submissions."""
    try:
        # 1. Log the inbound message
        enhanced_subject = f"[{submission.category.upper()}] {submission.subject}"
        full_message = f"Subject: {enhanced_subject}\n\n{submission.message}"

        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="inbound",
            role="customer",
            content=full_message,
        )

        # 2. Run the AI agent
        agent_response = await process_customer_message(
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel="web_form",
            message=full_message,
        )
        logger.info(f"   🤖 Agent response ready ({len(agent_response)} chars)")

        # 3. Log the outbound message
        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="outbound",
            role="agent",
            content=agent_response,
        )

        # 4. Update ticket status to resolved if it wasn't escalated
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE tickets
                SET status = 'resolved', resolved_at = NOW()
                WHERE external_ref = $1 AND status = 'open'
            """, ticket_ref)

        # 5. Send the email reply via Gmail API
        try:
            handler = get_gmail_handler()
            await handler.send_reply(
                to_email=submission.email,
                subject=f"Re: {submission.subject} [{ticket_ref}]",
                body=agent_response,
            )
            logger.info(f"   ✉️  Email response sent to {submission.email}")
        except Exception as mail_err:
            logger.error(f"   ❌ Failed to send email response: {mail_err}")

    except Exception as e:
        logger.error(f"❌ process_web_form_background failed: {e}", exc_info=True)


@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission, background_tasks: BackgroundTasks):
    """
    Handle support form submission.

    This endpoint:
    1. Validates the submission
    2. Creates a ticket ID immediately
    3. Saves ticket to DB immediately to avoid 404 race condition
    4. Triggers the AI Agent in the background
    """
    logger.info(f"🌐 Web form | from={submission.name} <{submission.email}> | subject={submission.subject!r}")

    # 1. Generate unique ticket ID
    ticket_ref = f"WEB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # 2. Create customer and conversation immediately (in main thread)
    customer_id = await get_or_create_customer(
        name=submission.name,
        email=submission.email,
    )
    conversation_id = await start_conversation(customer_id, "web_form")

    # 3. Create ticket immediately so the lookup doesn't 404
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Use a transaction block to ensure data is committed before we return
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, external_ref)
                VALUES ($1, $2, 'web_form', $3, $4, $5)
            """, conversation_id, customer_id,
                submission.category, submission.priority or 'medium', ticket_ref)

    logger.info(f"   🎫 Ticket created and COMMITTED: {ticket_ref}")

    # 4. Process the heavy AI logic in the background
    background_tasks.add_task(process_web_form_background, submission, ticket_ref, customer_id, conversation_id)

    return SupportFormResponse(
        ticket_id=ticket_ref,
        message=f"Thank you, {submission.name}! We've received your request and will respond to {submission.email} shortly.",
        estimated_response_time="Usually within 5 minutes"
    )

@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    from database.queries import get_db_pool

    logger.info(f"🔍 Looking up ticket status for: {ticket_id}")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Fetch ticket details
        ticket = await conn.fetchrow("""
            SELECT id, status, created_at, category, priority, conversation_id, external_ref
            FROM tickets
            WHERE id::text = $1 OR conversation_id::text = $1 OR external_ref = $1
        """, ticket_id)

        if not ticket:
            # Let's check if there are ANY tickets to see if the table is empty or connection is wrong
            count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
            logger.warning(f"❌ Ticket {ticket_id} NOT found in DB. Total tickets in DB: {count}")
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        logger.info(f"✅ Found ticket {ticket_id} (Internal ID: {ticket['id']})")

        # Use external_ref as ticket_id for the UI if it exists
        display_id = ticket['external_ref'] or str(ticket['id'])

        # Fetch conversation messages to show progress
        messages = await conn.fetch("""
            SELECT role, content, created_at, direction
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """, ticket['conversation_id'])

        return {
            "ticket_id": display_id,
            "status": ticket['status'],
            "created_at": ticket['created_at'],
            "category": ticket['category'],
            "priority": ticket['priority'],
            "messages": [dict(m) for m in messages]
        }