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

async def process_web_form_background(submission: SupportFormSubmission, ticket_ref: str):
    """Background task for web-form submissions."""
    try:
        # 1. Get or create customer
        customer_id = await get_or_create_customer(
            name=submission.name,
            email=submission.email,
        )
        logger.info(f"   👤 Customer ID: {customer_id}")

        # 2. Start a new conversation thread
        conversation_id = await start_conversation(customer_id, "web_form")
        logger.info(f"   💬 Conversation ID: {conversation_id}")

        # 3. Log the inbound message
        enhanced_subject = f"[{submission.category.upper()}] {submission.subject}"
        full_message = f"Subject: {enhanced_subject}\n\n{submission.message}"

        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="inbound",
            role="customer",
            content=full_message,
        )

        # 4. Run the AI agent
        agent_response = await process_customer_message(
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel="web_form",
            message=full_message,
        )
        logger.info(f"   🤖 Agent response ready ({len(agent_response)} chars)")

        # 5. Log the outbound message
        await log_message(
            conversation_id=conversation_id,
            channel="web_form",
            direction="outbound",
            role="agent",
            content=agent_response,
        )

        # 6. Send the email reply via Gmail API
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
    2. Creates a ticket ID
    3. Triggers the AI Agent in the background
    4. Returns confirmation to user immediately
    """
    logger.info(f"🌐 Web form | from={submission.name} <{submission.email}> | subject={submission.subject!r}")

    # Generate unique ticket ID
    ticket_ref = f"WEB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Process the actual AI logic in the background
    background_tasks.add_task(process_web_form_background, submission, ticket_ref)

    return SupportFormResponse(
        ticket_id=ticket_ref,
        message=f"Thank you, {submission.name}! We've received your request and will respond to {submission.email} shortly.",
        estimated_response_time="Usually within 5 minutes"
    )

@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    from database.queries import get_db_pool

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Simplified for now just to return basic DB ticket check
        ticket = await conn.fetchrow("""
            SELECT id, status, created_at, category, priority
            FROM tickets
            WHERE id::text = $1 OR conversation_id::text = $1
        """, ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        return dict(ticket)