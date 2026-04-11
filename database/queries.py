# database/queries.py
import os
import asyncpg
import logging
import json
import asyncio
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import uuid

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize local embedding model (Free & Local)
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# --- Singleton Connection Pool ---
# One pool shared across the entire app lifetime — never create a new pool per query.
_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()


async def get_db_pool() -> asyncpg.Pool:
    """Return the shared DB pool, creating it once safely if needed."""
    global _pool
    # If it exists, return immediately (fast path)
    if _pool is not None:
        return _pool

    # If not, acquire lock and create it (safe path)
    async with _pool_lock:
        if _pool is None:
            _pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL"),
                min_size=2,   # Keep at least 2 connections ready
                max_size=10,  # Never exceed 10 connections
            )
            logger.info("✅ Database pool created (min=2, max=10)")
    return _pool


async def close_db_pool():
    """Gracefully close the pool on app shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("🔌 Database pool closed")


async def generate_embedding(text: str) -> List[float]:
    """Generate a vector embedding using a local SentenceTransformer model."""
    try:
        embedding = embedding_model.encode(text.replace("\n", " "))
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Local embedding generation failed: {e}")
        raise e


# --- Customer & Identifier Management ---

async def get_or_create_customer(name: str = None, email: str = None, phone: str = None) -> str:
    """
    Find a customer by email/phone or create a new one.
    Uses INSERT ... ON CONFLICT to avoid race conditions.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # 1. Search for existing customer first
        if email:
            customer = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", email)
            if customer:
                return str(customer['id'])
        if phone:
            customer = await conn.fetchrow("SELECT id FROM customers WHERE phone = $1", phone)
            if customer:
                return str(customer['id'])

        # 2. Use INSERT ... ON CONFLICT to safely upsert
        if email:
            customer_id = await conn.fetchval("""
                INSERT INTO customers (name, email, phone)
                VALUES ($1, $2, $3)
                ON CONFLICT (email) DO UPDATE SET name = COALESCE(EXCLUDED.name, customers.name)
                RETURNING id
            """, name or "Unknown Customer", email, phone)
        elif phone:
            customer_id = await conn.fetchval("""
                INSERT INTO customers (name, email, phone)
                VALUES ($1, $2, $3)
                ON CONFLICT (phone) DO UPDATE SET name = COALESCE(EXCLUDED.name, customers.name)
                RETURNING id
            """, name or "Unknown Customer", email, phone)
        else:
            customer_id = await conn.fetchval(
                "INSERT INTO customers (name) VALUES ($1) RETURNING id",
                name or "Unknown Customer"
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
    """Save a message to the database."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        tool_calls_json = json.dumps(tool_calls)
        await conn.execute("""
            INSERT INTO messages (conversation_id, channel, direction, role, content, tokens_used, latency_ms, tool_calls)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, uuid.UUID(conversation_id), channel, direction, role, content, tokens, latency, tool_calls_json)


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
        embedding_str = str(query_embedding)
        results = await conn.fetch("""
            SELECT title, content, category, 1 - (embedding <=> $1) as similarity
            FROM knowledge_base
            ORDER BY embedding <=> $1
            LIMIT $2
        """, embedding_str, limit)
        return [dict(r) for r in results]


# --- Metrics ---

async def log_agent_metrics(metric_name: str, metric_value: float, channel: str = None, dimensions: Dict = {}):
    """Log performance metrics for monitoring."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        dimensions_json = json.dumps(dimensions)
        await conn.execute("""
            INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
            VALUES ($1, $2, $3, $4)
        """, metric_name, metric_value, channel, dimensions_json)
