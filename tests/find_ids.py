import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from database.queries import get_db_pool

async def main():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer = await conn.fetchrow("SELECT id, name, email FROM customers LIMIT 1")
        if customer:
            print(f"CUSTOMER_ID={customer['id']}")
            conversation = await conn.fetchrow("SELECT id FROM conversations WHERE customer_id = $1 LIMIT 1", customer['id'])
            if conversation:
                print(f"CONVERSATION_ID={conversation['id']}")
            else:
                print("No conversation found for this customer.")
        else:
            print("No customers found in DB.")

if __name__ == "__main__":
    asyncio.run(main())
