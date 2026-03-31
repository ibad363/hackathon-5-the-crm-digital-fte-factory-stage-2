import os
import asyncpg
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI Client for embeddings
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

async def log_agent_metrics(conversation_id: str, tokens: int, latency: int, success: bool = True):
    """Log performance metrics for the agent's interaction."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_metrics (conversation_id, tokens_used, latency_ms, success)
            VALUES ($1, $2, $3, $4)
        """, conversation_id, tokens, latency, success)
