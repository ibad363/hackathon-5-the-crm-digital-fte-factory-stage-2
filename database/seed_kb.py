import os
import asyncio
import logging
from typing import List
import sys

# Add the project root to sys.path to import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import generate_embedding, get_db_pool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_knowledge_base():
    """Read documents from context/ and seed the knowledge base table."""
    # Correct path to context directory relative to this script
    context_dir = os.path.join(os.path.dirname(__file__), '..', 'context')

    docs = [
        {"file": "company-profile.md", "category": "Company"},
        {"file": "product-docs.md", "category": "Product"},
        {"file": "brand-voice.md", "category": "Voice"},
        {"file": "escalation-rules.md", "category": "Escalation"},
    ]

    pool = await get_db_pool()
    if not pool:
        logger.error("Failed to connect to the database. Check your DATABASE_URL.")
        return

    async with pool.acquire() as conn:
        for doc in docs:
            file_path = os.path.join(context_dir, doc["file"])
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                title = doc["file"].replace(".md", "").replace("-", " ").title()

                logger.info(f"Generating embedding for {title}...")
                try:
                    embedding = await generate_embedding(content)
                    embedding_str = str(embedding)

                    await conn.execute("""
                        INSERT INTO knowledge_base (title, content, category, embedding)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                    """, title, content, doc["category"], embedding_str)
                    logger.info(f"Successfully seeded: {title}")
                except Exception as e:
                    logger.error(f"Failed to seed {title}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
