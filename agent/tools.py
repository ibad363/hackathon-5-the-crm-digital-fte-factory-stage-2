# production/agent/tools.py
import logging
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field
from agents import function_tool, RunContextWrapper
from database.queries import get_db_pool, generate_embedding

logger = logging.getLogger(__name__)

# --- 1. Input Schemas (Pydantic Models) ---

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: Annotated[str, Field(description="The customer's question or search query")]
    max_results: Annotated[int, Field(default=5, ge=1, le=10, description="The maximum number of results to return")]
    category: Annotated[Optional[str], Field(default=None, description="Optional category filter")]

class TicketCreationInput(BaseModel):
    """Input schema for ticket creation."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    subject: Annotated[str, Field(description="A brief subject or title for the support issue")]
    description: Annotated[str, Field(description="A detailed description of the problem")]
    priority: Annotated[str, Field(default="medium", pattern="^(low|medium|high|urgent)$", description="The priority level")]

class CustomerHistoryInput(BaseModel):
    """Input schema for fetching customer history."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    limit: Annotated[int, Field(default=10, ge=1, le=50, description="The number of past messages to retrieve")]

class EscalationInput(BaseModel):
    """Input schema for escalating to a human."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    conversation_id: Annotated[str, Field(description="The current conversation ID (UUID)")]
    reason: Annotated[str, Field(description="The specific reason for escalation (e.g., pricing query, legal threat, user frustration)")]

class ResponseInput(BaseModel):
    """Input schema for sending a response back to the customer."""
    conversation_id: Annotated[str, Field(description="The current conversation ID (UUID)")]
    channel: Annotated[str, Field(pattern="^(gmail|whatsapp|web-form)$", description="The communication channel")]
    content: Annotated[str, Field(description="The actual message content (formatted appropriately for the channel)")]

# --- 2. Production Tools (OpenAI Agents SDK) ---

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.
    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    Returns: Formatted search results with relevance scores.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Generate embedding for semantic search
            embedding = await generate_embedding(input.query)

            # Query with vector similarity
            results = await conn.fetch("""
                SELECT title, content, category,
                1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base
                WHERE ($2::text IS NULL OR category = $2)
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding, input.category, input.max_results)

            if not results:
                return "No relevant documentation found. Consider escalating to human support."

            # Format results for the agent
            formatted = []
            for r in results:
                formatted.append(f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:500]}")

            return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."

@function_tool
async def create_ticket(input: TicketCreationInput) -> str:
    """Create a new support ticket in the CRM.
    MUST be called at the very start of every conversation.
    Returns: The newly created ticket ID and confirmation.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (customer_id, subject, description, priority)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, input.customer_id, input.subject, input.description, input.priority)

            return f"Ticket successfully created. ID: {ticket_id}. I am now looking into this for you."

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Failed to create a ticket. Please try again or escalate."

@function_tool
async def get_customer_history(input: CustomerHistoryInput) -> str:
    """Retrieve past interaction history for a customer.
    Use this to maintain continuity and provide personalized support.
    Returns: A list of recent messages across all channels.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT m.channel, m.direction, m.content, m.timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.customer_id = $1
                ORDER BY m.timestamp DESC
                LIMIT $2
            """, input.customer_id, input.limit)

            if not results:
                return "No previous history found for this customer."

            # Format history for the agent
            history = []
            for r in results:
                direction = "OUT" if r['direction'] == 'outbound' else "IN"
                history.append(f"[{r['timestamp'].strftime('%Y-%m-%d %H:%M')}] {r['channel'].upper()} {direction}: {r['content']}")

            return "\n".join(reversed(history))

    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        return "History currently unavailable. Please proceed with the current interaction."

@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """Escalate the current conversation to a human specialist.
    Use this if the customer is frustrated, mentions pricing/refunds,
    legal issues, or if the KB search fails repeatedly.
    Returns: Confirmation of escalation.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Update conversation status to 'escalated'
            await conn.execute("""
                UPDATE conversations SET status = 'escalated'
                WHERE id = $1
            """, input.conversation_id)

            # Update ticket status if exists (assume one open ticket per conversation)
            await conn.execute("""
                UPDATE tickets SET status = 'escalated'
                WHERE customer_id = $1 AND status != 'resolved'
            """, input.customer_id)

            # Log the escalation message
            logger.warning(f"CONVERSATION ESCALATED: {input.conversation_id}. Reason: {input.reason}")

            return f"Conversation has been successfully escalated to a human specialist. Reason: {input.reason}. They will be in touch shortly."

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return "Escalation failed. Please try again."

@function_tool
async def send_response(input: ResponseInput) -> str:
    """Send the final AI response back to the customer via the original channel.
    This tool formats the message and dispatches it to the appropriate channel handler.
    Returns: Confirmation of transmission.
    """
    try:
        # 1. Log the outbound message in the database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages (conversation_id, channel, direction, content)
                VALUES ($1, $2, 'outbound', $3)
            """, input.conversation_id, input.channel, input.content)

            # 2. Trigger the channel dispatcher (this will be picked up by a Kafka producer or specific handler)
            # For now, we simulate success
            logger.info(f"RESPONSE DISPATCHED to {input.channel.upper()}: {input.content[:50]}...")

            return f"Response successfully queued for {input.channel.upper()}."

    except Exception as e:
        logger.error(f"Response dispatch failed: {e}")
        return "Failed to send response. Please try again."
