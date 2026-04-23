import sys, os
import asyncio
import logging
import io

# Force utf-8 stdout to avoid crash on emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.customer_success_agent import process_customer_message
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()
logging.getLogger("agents").setLevel(logging.DEBUG)

CUSTOMER_ID = "a66d1ce2-95d7-4e70-8e1d-deb2fb1ee2cd"
CONVERSATION_ID = "54907615-a400-493c-ae00-e83fe53cde1e"

async def main():
    print("="*60)
    print("DEBUGGING AGENT LOGIC DIRECTLY")
    print("="*60)
    test_message = "Hi, my dashboard keeps crashing when I click the save button."
    print(f"\nSending message: '{test_message}'")
    try:
        response = await process_customer_message(
            customer_id=CUSTOMER_ID,
            conversation_id=CONVERSATION_ID,
            channel="web_form",
            message=test_message
        )
        print("\n" + "="*60)
        print("AGENT FINISHED SUCCESSFULLY")
        print("="*60)
        print(f"Final Response: {response}")
    except Exception as e:
        print("\n" + "="*60)
        print(f"AGENT FAILED: {e}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
