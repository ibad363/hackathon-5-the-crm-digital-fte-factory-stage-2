import os
import asyncpg
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
import uuid

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI Client for embeddings
client = AsyncOpenAI(api_key=os.getenv("OPENROUTER_API_KEY"))

async def get_db_pool():
    """Create a connection pool for the CRM database."""
    return await asyncpg.create_pool(os.getenv("DATABASE_URL"))

async def generate_embedding(text: str) -> List[float]:
    """Generate a vector embedding using OpenAI's latest embedding model."""
    try:
        response = await client.embeddings.create(
            input=[text.replace("\n", " ")],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise e

# --- Customer & Identifier Management ---

async def get_or_create_customer(name: str = None, email: str = None, phone: str = None) -> str:
    """Find a customer by email/phone or create a new one."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # 1. Search for existing customer
        if email:
            customer = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", email)
            if customer: return str(customer['id'])
        if phone:
            customer = await conn.fetchrow("SELECT id FROM customers WHERE phone = $1", phone)
            if customer: return str(customer['id'])

        # 2. Create if not found
        customer_id = await conn.fetchval(
            "INSERT INTO customers (name, email, phone) VALUES ($1, $2, $3) RETURNING id",
            name or "Unknown Customer", email, phone
        )
        return str(customer_id)

async def add_customer_identifier(customer_id: str, identifier_type: str, identifier_value: str):
    """Add a channel-specific identifier to a customer (e.g., WhatsApp number, session ID)."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
            VALUES ($1, $2, $3)
            ON CONFLICT (identifier_type, identifier_value) DO NOTHING
        """, uuid.UUID(customer_id), identifier_type, identifier_value)

# --- Conversation & Message Management ---

async def start_conversation(customer_id: str, initial_channel: str) -> str:
    """Initialize a new conversation thread."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        conv_id = await conn.fetchval(
            "INSERT INTO conversations (customer_id, initial_channel) VALUES ($1, $2) RETURNING id",
            uuid.UUID(customer_id), initial_channel
        )
        return str(conv_id)

async def log_message(conversation_id: str, channel: str, direction: str, role: str, content: str,
                      tokens: int = 0, latency: int = 0, tool_calls: List = []):
    """Save a message to the database and update conversation sentiment."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO messages (conversation_id, channel, direction, role, content, tokens_used, latency_ms, tool_calls)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, uuid.UUID(conversation_id), channel, direction, role, content, tokens, latency, tool_calls)

        # Update last_message_at in conversation (if needed, though schema didn't include it explicitly, we can add it later)
        # Note: Your schema has started_at and ended_at, we might want to track recent activity in the metadata.

# --- Ticket Management ---

async def create_ticket(conversation_id: str, customer_id: str, channel: str, subject: str,
                        priority: str = 'medium', category: str = None) -> str:
    """Create a new support ticket linked to a conversation."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        ticket_id = await conn.fetchval("""
            INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, uuid.UUID(conversation_id), uuid.UUID(customer_id), channel, category, priority)
        return str(ticket_id)

# --- Knowledge Base Search ---

async def search_knowledge_base(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Perform a semantic search on the knowledge base using pgvector."""
    query_embedding = await generate_embedding(query)
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Calculate cosine similarity using pgvector's <=> operator
        results = await conn.fetch("""
            SELECT title, content, category, 1 - (embedding <=> $1) as similarity
            FROM knowledge_base
            ORDER BY embedding <=> $1
            LIMIT $2
        """, query_embedding, limit)
        return [dict(r) for r in results]

# --- Metrics ---

async def log_agent_metrics(metric_name: str, metric_value: float, channel: str = None, dimensions: Dict = {}):
    """Log performance metrics for monitoring."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
            VALUES ($1, $2, $3, $4)
        """, metric_name, metric_value, channel, dimensions)
