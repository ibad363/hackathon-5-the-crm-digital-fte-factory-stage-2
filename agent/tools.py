# production/agent/tools.py
import logging
import uuid
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field
from agents import function_tool
from database.queries import get_db_pool, generate_embedding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. Input Schemas (Pydantic Models) ---

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: Annotated[str, Field(description="The customer's question or search query")]
    max_results: Annotated[int, Field(default=3, ge=1, le=10, description="The maximum number of results to return")]
    category: Annotated[Optional[str], Field(default=None, description="Optional category filter (Company, Product, Voice, Escalation)")]

class TicketCreationInput(BaseModel):
    """Input schema for ticket creation."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    conversation_id: Annotated[str, Field(description="The current conversation ID (UUID)")]
    channel: Annotated[str, Field(description="The source channel (email, whatsapp, web_form)")]
    category: Annotated[Optional[str], Field(default=None, description="The category of the support issue")]
    priority: Annotated[str, Field(default="medium", pattern="^(low|medium|high|urgent)$", description="The priority level")]

class CustomerHistoryInput(BaseModel):
    """Input schema for fetching customer history."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    limit: Annotated[int, Field(default=10, ge=1, le=50, description="The number of past messages to retrieve")]

class EscalationInput(BaseModel):
    """Input schema for escalating to a human."""
    customer_id: Annotated[str, Field(description="The unique ID of the customer (UUID)")]
    conversation_id: Annotated[str, Field(description="The current conversation ID (UUID)")]
    reason: Annotated[str, Field(description="The specific reason for escalation (e.g., pricing_inquiry, refund_request, legal_threat)")]
    escalate_to: Annotated[Optional[str], Field(default="support_team", description="Who to escalate to")]

class ResponseInput(BaseModel):
    """Input schema for sending a response back to the customer."""
    conversation_id: Annotated[str, Field(description="The current conversation ID (UUID)")]
    channel: Annotated[str, Field(pattern="^(email|whatsapp|web_form)$", description="The communication channel")]
    content: Annotated[str, Field(description="The actual message content (formatted appropriately for the channel)")]

# --- 2. Production Tools (OpenAI Agents SDK) ---

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.
    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    Returns: Formatted search results with relevance scores.
    """
    print(f"\n🔍 [TOOL CALL] search_knowledge_base")
    print(f"   Query: {input.query}")
    print(f"   Category: {input.category}")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Generate embedding for semantic search
            embedding = await generate_embedding(input.query)
            embedding_str = str(embedding)

            # Query with vector similarity
            if input.category:
                results = await conn.fetch("""
                    SELECT title, content, category,
                    1 - (embedding <=> $1) as similarity
                    FROM knowledge_base
                    WHERE category = $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                """, embedding_str, input.category, input.max_results)
            else:
                results = await conn.fetch("""
                    SELECT title, content, category,
                    1 - (embedding <=> $1) as similarity
                    FROM knowledge_base
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, embedding_str, input.max_results)

            if not results:
                response = "No relevant documentation found. Consider escalating to human support."
                print(f"   ❌ Result: {response}")
                return response

            # Format results for the agent
            formatted = []
            for r in results:
                formatted.append(f"**{r['title']}** (Category: {r['category']}, Relevance: {r['similarity']:.2f})\n{r['content'][:500]}...")

            response = "\n\n---\n\n".join(formatted)
            print(f"   ✅ Result: Found {len(results)} results")
            return response

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        response = "Knowledge base temporarily unavailable. Please try again or escalate."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def create_ticket(input: TicketCreationInput) -> str:
    """Create a new support ticket in the CRM.
    MUST be called at the very start of every conversation.
    Returns: The newly created ticket ID and confirmation.
    """
    print(f"\n🎫 [TOOL CALL] create_ticket")
    print(f"   Customer ID: {input.customer_id}")
    print(f"   Conversation ID: {input.conversation_id}")
    print(f"   Channel: {input.channel}")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, uuid.UUID(input.conversation_id), uuid.UUID(input.customer_id),
                input.channel, input.category, input.priority)

            response = f"Ticket successfully created. ID: {ticket_id}. I am now looking into this for you."
            print(f"   ✅ Result: {response}")
            logger.info(f"Ticket created: {ticket_id}")
            return response

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        response = "Failed to create a ticket. Please try again or escalate."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def get_customer_history(input: CustomerHistoryInput) -> str:
    """Retrieve past interaction history for a customer.
    Use this to maintain continuity and provide personalized support.
    Returns: A list of recent messages across all channels.
    """
    print(f"\n📜 [TOOL CALL] get_customer_history")
    print(f"   Customer ID: {input.customer_id}")
    print(f"   Limit: {input.limit}")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT m.channel, m.direction, m.role, m.content, m.created_at
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.customer_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
            """, uuid.UUID(input.customer_id), input.limit)

            if not results:
                response = "No previous history found for this customer. This is a new customer."
                print(f"   ℹ️ Result: {response}")
                return response

            # Format history for the agent
            history = []
            for r in results:
                direction = "OUT" if r['direction'] == 'outbound' else "IN"
                history.append(f"[{r['created_at'].strftime('%Y-%m-%d %H:%M')}] {r['channel'].upper()} {direction} ({r['role']}): {r['content'][:100]}...")

            response = "\n".join(reversed(history))
            print(f"   ✅ Result: Found {len(results)} messages")
            return response

    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        response = "History currently unavailable. Please proceed with the current interaction."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """Escalate the current conversation to a human specialist.
    Use this if the customer is frustrated, mentions pricing/refunds,
    legal issues, or if the KB search fails repeatedly.
    Returns: Confirmation of escalation.
    """
    print(f"\n🚨 [TOOL CALL] escalate_to_human")
    print(f"   Conversation ID: {input.conversation_id}")
    print(f"   Reason: {input.reason}")
    print(f"   Escalate To: {input.escalate_to}")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Update conversation status to 'escalated' and set escalated_to
            await conn.execute("""
                UPDATE conversations
                SET status = 'escalated', escalated_to = $2
                WHERE id = $1
            """, uuid.UUID(input.conversation_id), input.escalate_to)

            # Update ticket status if exists
            await conn.execute("""
                UPDATE tickets SET status = 'escalated'
                WHERE conversation_id = $1 AND status NOT IN ('resolved', 'closed')
            """, uuid.UUID(input.conversation_id))

            # Log the escalation message
            logger.warning(f"CONVERSATION ESCALATED: {input.conversation_id}. Reason: {input.reason}. To: {input.escalate_to}")

            response = f"Conversation has been successfully escalated to {input.escalate_to}. Reason: {input.reason}. A human specialist will be in touch shortly."
            print(f"   ✅ Result: {response}")
            return response

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        response = "Escalation failed. Please try again."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def send_response(input: ResponseInput) -> str:
    """Send the final AI response back to the customer via the original channel.
    This tool formats the message and dispatches it to the appropriate channel handler.
    ALWAYS use this tool to send your final response to the customer.
    Returns: Confirmation of transmission.
    """
    print(f"\n📤 [TOOL CALL] send_response")
    print(f"   Conversation ID: {input.conversation_id}")
    print(f"   Channel: {input.channel}")
    print(f"   Content: {input.content[:100]}...")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Log the outbound message in the database with role='agent'
            await conn.execute("""
                INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, 'outbound', 'agent', $3, 'sent')
            """, uuid.UUID(input.conversation_id), input.channel, input.content)

            # Trigger the channel dispatcher (this will be picked up by a Kafka producer or specific handler)
            logger.info(f"RESPONSE DISPATCHED to {input.channel.upper()}: {input.content[:50]}...")

            response = f"Response successfully sent via {input.channel.upper()}."
            print(f"   ✅ Result: {response}")
            return response

    except Exception as e:
        logger.error(f"Response dispatch failed: {e}")
        response = "Failed to send response. Please try again."
        print(f"   ❌ Error: {e}")
        return response
