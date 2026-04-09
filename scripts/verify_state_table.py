import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database.queries import get_db_pool

async def verify():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Create table if it doesn't exist yet
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS integration_state (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name        TEXT UNIQUE NOT NULL,
                last_hid    BIGINT,
                updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        # Check it exists
        row = await conn.fetchrow("SELECT count(*) as cnt FROM integration_state")
        print(f"integration_state table exists! Rows: {row['cnt']}")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(verify())
