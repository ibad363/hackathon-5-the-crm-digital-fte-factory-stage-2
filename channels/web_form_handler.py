from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
import uuid

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

@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission):
    """
    Handle support form submission.
    
    This endpoint:
    1. Validates the submission
    2. Creates a ticket in the system
    3. Publishes to Kafka for agent processing
    4. Returns confirmation to user
    """
    ticket_id = str(uuid.uuid4())
    
    # Create normalized message for agent
    message_data = {
        'channel': 'web_form',
        'channel_message_id': ticket_id,
        'customer_email': submission.email,
        'customer_name': submission.name,
        'subject': submission.subject,
        'content': submission.message,
        'category': submission.category,
        'priority': submission.priority,
        'received_at': datetime.utcnow().isoformat(),
        'metadata': {
            'form_version': '1.0',
            'attachments': submission.attachments
        }
    }
    
    # Publish to Kafka
    await publish_to_kafka('fte.tickets.incoming', message_data)
    
    # Store initial ticket
    await create_ticket_record(ticket_id, message_data)
    
    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes"
    )

@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {
        'ticket_id': ticket_id,
        'status': ticket['status'],
        'messages': ticket['messages'],
        'created_at': ticket['created_at'],
        'last_updated': ticket['last_updated']
    }