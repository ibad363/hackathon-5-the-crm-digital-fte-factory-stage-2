import sys
import os
import asyncio

# Add project root to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import search_knowledge_base

async def test_search():
    queries = [
        "integrate Slack with TaskVault notifications task status done",
        "How to Set Up a Slack Integration"
    ]
    
    for q in queries:
        print(f"\n==============================================")
        print(f"Searching for: '{q}'")
        print(f"==============================================")
        
        # 1. Normal semantic search
        results = await search_knowledge_base(q, limit=3)
        if not results:
            print("No results found!")
        else:
            for r in results:
                print(f"\nTitle: {r['title']}")
                print(f"Similarity: {r['similarity']}")
                print(f"Content preview: {r['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_search())
