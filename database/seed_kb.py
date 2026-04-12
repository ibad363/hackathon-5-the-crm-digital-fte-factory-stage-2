import os
import asyncio
import logging
import re
from typing import List, Dict
import sys

# Add the project root to sys.path to import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import generate_embedding, get_db_pool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def chunk_markdown(text: str, file_title: str) -> List[Dict[str, str]]:
    """Splits a markdown document into smaller chunks based on H2 and H3 headers."""
    chunks = []

    # Split by H2 or H3 headers (## or ###)
    # We use capturing group to keep the header as part of the split result
    sections = re.split(r'\n(##+ .*?)\n', text)

    # The first element is everything before the first header (often just the H1 title)
    if sections[0].strip():
        chunks.append({
            "title": f"{file_title} - Overview",
            "content": sections[0].strip()
        })

    # Process the header-content pairs
    for i in range(1, len(sections), 2):
        header_raw = sections[i]
        # The content following this header
        content_raw = sections[i+1] if i+1 < len(sections) else ""

        # Clean up the header to use as the title (remove the ## marks)
        title_text = re.sub(r'^##+\s+', '', header_raw).strip()

        if content_raw.strip():
            chunks.append({
                "title": f"{file_title} - {title_text}",
                "content": f"{header_raw}\n{content_raw}".strip()
            })

    # If the file had no H2/H3 headers at all, return it as one big chunk
    if not chunks:
        chunks.append({
            "title": file_title,
            "content": text.strip()
        })

    return chunks

async def seed_knowledge_base():
    """Read documents from context/ and seed the knowledge base table with chunks."""
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
        # Clear existing entries to prevent duplicates or stale massive chunks
        logger.info("Clearing existing knowledge_base table...")
        await conn.execute("TRUNCATE TABLE knowledge_base RESTART IDENTITY")

        for doc in docs:
            file_path = os.path.join(context_dir, doc["file"])
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_title = doc["file"].replace(".md", "").replace("-", " ").title()

                logger.info(f"Chunking {file_title}...")
                chunks = chunk_markdown(content, file_title)
                logger.info(f"Generated {len(chunks)} chunks for {file_title}.")

                for i, chunk in enumerate(chunks):
                    logger.info(f"Generating embedding for chunk {i+1}/{len(chunks)}: {chunk['title']}...")
                    try:
                        embedding = await generate_embedding(chunk["content"])
                        embedding_str = str(embedding)

                        await conn.execute("""
                            INSERT INTO knowledge_base (title, content, category, embedding)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT DO NOTHING
                        """, chunk["title"], chunk["content"], doc["category"], embedding_str)
                    except Exception as e:
                        logger.error(f"Failed to seed chunk {chunk['title']}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
