import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from database.queries import get_db_pool

async def main():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        print("Checking unique categories in Knowledge Base...")
        rows = await conn.fetch("SELECT category, COUNT(*) FROM knowledge_base GROUP BY category")
        for row in rows:
            print(f"Category: '{row['category']}' | Count: {row['count']}")

if __name__ == "__main__":
    asyncio.run(main())
