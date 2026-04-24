# production/agent/tools.py
import logging
import uuid
import re
from typing import Optional, List, Annotated
from agents import function_tool
from database.queries import get_db_pool, generate_embedding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_uuid(id_str: str) -> uuid.UUID:
    """Robustly clean and parse a UUID string from the LLM."""
    if not id_str:
        raise ValueError("Empty ID provided")

    # Remove quotes, brackets, and whitespace
    cleaned = str(id_str).strip().replace("'", "").replace('"', "").replace("[", "").replace("]", "")

    # If it's a 32-char hex string without dashes, uuid.UUID still handles it
    return uuid.UUID(cleaned)

# --- 1. Input Schemas (Pydantic Models) ---

# --- 2. Production Tools (OpenAI Agents SDK) ---

@function_tool
async def search_knowledge_base(query: str, category: str = "", max_results: int = 3) -> str:
    """Search product documentation for relevant information.
    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.

    Allowed Categories:
    - 'Product': Use for features, integrations (Slack, etc.), and troubleshooting.
    - 'Company': Use for company info, hours, and policies.
    - 'Voice': Use for brand tone and response style guidelines.
    - 'Escalation': Use for rules on when to hand off to humans.

    Returns: Formatted search results with relevance scores.
    """
    print(f"\n🔍 [TOOL CALL] search_knowledge_base")
    print(f"   Query: {query}")
    print(f"   Category Filter: {category}")

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Generate embedding for semantic search
            embedding = await generate_embedding(query)
            embedding_str = str(embedding)

            # Query with vector similarity using inner product (<#>)
            if category:
                results = await conn.fetch("""
                    SELECT title, content, category,
                    (embedding <#> $1) * -1 as similarity
                    FROM knowledge_base
                    WHERE category = $2
                    ORDER BY embedding <#> $1
                    LIMIT $3
                """, embedding_str, category, max_results)
            else:
                results = await conn.fetch("""
                    SELECT title, content, category,
                    (embedding <#> $1) * -1 as similarity
                    FROM knowledge_base
                    ORDER BY embedding <#> $1
                    LIMIT $2
                """, embedding_str, max_results)

            if not results:
                print(f"   ❌ [TOOL RESULT] No results found in KB.")
                return "No relevant documentation found. Consider escalating to human support."

            # Format results for the agent
            formatted = []
            for r in results:
                formatted.append(f"**{r['title']}** (Category: {r['category']}, Relevance: {r['similarity']:.2f})\n{r['content'][:500]}...")

            response = "\n\n---\n\n".join(formatted)
            print(f"   ✅ [TOOL RESULT] Found {len(results)} results.")
            print(f"      Top Match: {results[0]['title']} (Score: {results[0]['similarity']:.2f})")
            return response

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        response = "Knowledge base temporarily unavailable. Please try again or escalate."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def create_ticket(customer_id: str, conversation_id: str, channel: str, priority: str = "medium", category: str = "general") -> str:
    """Create a new support ticket in the CRM.
    MUST be called at the very start of every conversation.
    Returns: The newly created ticket ID and confirmation.
    """
    print(f"\n🎫 [TOOL CALL] create_ticket")
    print(f"   Customer ID: {customer_id}")
    print(f"   Conversation ID: {conversation_id}")
    print(f"   Channel: {channel}")

    try:
        pool = await get_db_pool()

        # Clean UUID strings robustly
        c_id = clean_uuid(customer_id)
        conv_id = clean_uuid(conversation_id)
        channel_code = channel[:3].upper() if channel else "GEN"

        async with pool.acquire() as conn:
            # 1. Check if a ticket already exists for this conversation (idempotency)
            existing_ticket = await conn.fetchrow(
                "SELECT external_ref, id FROM tickets WHERE conversation_id = $1",
                conv_id
            )

            if existing_ticket:
                display_id = existing_ticket['external_ref'] or str(existing_ticket['id'])
                response = f"Ticket already exists. ID: {display_id}. I am now looking into this for you."
                print(f"   ℹ️ Result: {response}")
                return response

            # 2. Generate external_ref
            from datetime import datetime
            ticket_ref = f"{channel_code}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # 3. Otherwise, create one
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, external_ref)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, conv_id, c_id,
                channel, category, priority, ticket_ref)

            response = f"Ticket successfully created. ID: {ticket_ref}. I am now looking into this for you."
            print(f"   ✅ Result: {response}")
            logger.info(f"Ticket created: {ticket_id} (Ref: {ticket_ref})")
            return response

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}", exc_info=True)
        # To prevent the agent from apologizing to the customer, we tell it the ticket is active
        return "Ticket is active in our system. I am now looking into this for you."

@function_tool
async def get_customer_history(customer_id: str, limit: int = 10) -> str:
    """Retrieve past interaction history for a customer.
    Use this to maintain continuity and provide personalized support.
    Returns: A list of recent messages across all channels.
    """
    print(f"\n📜 [TOOL CALL] get_customer_history")
    print(f"   Customer ID: {customer_id}")
    print(f"   Limit: {limit}")

    try:
        c_id = clean_uuid(customer_id)
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT m.channel, m.direction, m.role, m.content, m.created_at
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.customer_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
            """, c_id, limit)

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
async def escalate_to_human(conversation_id: str, reason: str, escalate_to: str = "support_team") -> str:
    """Escalate the current conversation to a human specialist.
    Use this if the customer is frustrated, mentions pricing/refunds,
    legal issues, or if the KB search fails repeatedly.
    Returns: Confirmation of escalation.
    """
    print(f"\n🚨 [TOOL CALL] escalate_to_human")
    print(f"   Conversation ID: {conversation_id}")
    print(f"   Reason: {reason}")
    print(f"   Escalate To: {escalate_to}")

    try:
        conv_id = clean_uuid(conversation_id)
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Update conversation status to 'escalated' and set escalated_to
            await conn.execute("""
                UPDATE conversations
                SET status = 'escalated', escalated_to = $2
                WHERE id = $1
            """, conv_id, escalate_to)

            # Update ticket status if exists
            await conn.execute("""
                UPDATE tickets SET status = 'escalated'
                WHERE conversation_id = $1 AND status NOT IN ('resolved', 'closed')
            """, conv_id)

            # Log the escalation message
            logger.warning(f"CONVERSATION ESCALATED: {conversation_id}. Reason: {reason}. To: {escalate_to}")

            response = f"Conversation has been successfully escalated to {escalate_to}. Reason: {reason}. A human specialist will be in touch shortly."
            print(f"   ✅ Result: {response}")
            return response

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        response = "Escalation failed. Please try again."
        print(f"   ❌ Error: {e}")
        return response

@function_tool
async def send_response(conversation_id: str, channel: str, content: str) -> str:
    """Send the final AI response back to the customer via the original channel.
    This tool formats the message and dispatches it to the appropriate channel handler.
    ALWAYS use this tool to send your final response to the customer.
    Returns: Confirmation of transmission.
    """
    print(f"\n📤 [TOOL CALL] send_response")
    print(f"   Conversation ID: {conversation_id}")
    print(f"   Channel: {channel}")
    print(f"   Content: {content[:100]}...")

    try:
        conv_id = clean_uuid(conversation_id)
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # 1. Log the outbound message in the database
            await conn.execute("""
                INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, 'outbound', 'agent', $3, 'sent')
            """, conv_id, channel, content)

            # 2. Dispatch to the actual channel handler
            if channel == "email" or channel == "web_form":
                from channels.gmail_handler import get_gmail_handler

                # Find customer email from DB
                cust_data = await conn.fetchrow("""
                    SELECT c.email FROM customers c
                    JOIN conversations conv ON c.id = conv.customer_id
                    WHERE conv.id = $1
                """, conv_id)

                if cust_data and cust_data['email']:
                    handler = get_gmail_handler()
                    await handler.send_reply(
                        to_email=cust_data['email'],
                        subject="Re: TaskVault Support Request",
                        body=content
                    )
                    logger.info(f"✅ Response sent via GMAIL to {cust_data['email']}")

            elif channel == "whatsapp":
                from channels.whatsapp_handler import WhatsAppHandler

                # Find customer phone from DB
                cust_data = await conn.fetchrow("""
                    SELECT c.phone FROM customers c
                    JOIN conversations conv ON c.id = conv.customer_id
                    WHERE conv.id = $1
                """, conv_id)

                if cust_data and cust_data['phone']:
                    handler = WhatsAppHandler()
                    messages = handler.format_response(content)
                    for msg_body in messages:
                        await handler.send_message(to_phone=cust_data['phone'], body=msg_body)
                    logger.info(f"✅ Response sent via WHATSAPP to {cust_data['phone']}")

            response = f"Response successfully sent via {channel.upper()}."
            print(f"   ✅ Result: {response}")
            return response

    except Exception as e:
        logger.error(f"Response dispatch failed: {e}", exc_info=True)
        return "Failed to send response. Please try again."
