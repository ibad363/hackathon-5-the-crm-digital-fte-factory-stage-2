import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

async def test_connection():
    db_url = os.getenv("DATABASE_URL")
    print(f"Attempting to connect to: {db_url}")

    if not db_url:
        print("Error: DATABASE_URL not found in .env file.")
        return

    try:
        # Attempt to create a connection pool
        pool = await asyncpg.create_pool(db_url)
        async with pool.acquire() as conn:
            # Run a simple query to verify the connection
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                print("✅ Successfully connected to the database!")

                # Check for the vector extension
                has_vector = await conn.fetchval("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")
                if has_vector:
                    print("✅ pgvector extension is enabled.")
                else:
                    print("❌ pgvector extension is NOT enabled. Please run 'CREATE EXTENSION IF NOT EXISTS vector;' in pgAdmin.")

                # Check if tables exist
                tables = await conn.fetch("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                print(f"Found {len(tables)} tables in the 'public' schema.")
                for table in tables:
                    print(f"  - {table['table_name']}")
            else:
                print("❌ Connection successful, but query failed.")
        await pool.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
