import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    await conn.execute("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS external_ref VARCHAR(255)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_external_ref ON tickets(external_ref)")
    print("Migration successful: Added external_ref to tickets")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
