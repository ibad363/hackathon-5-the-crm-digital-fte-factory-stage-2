# production/agent/customer_success_agent.py
import os
import sys
import logging
from typing import Optional

# Add project root to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, SQLiteSession, enable_verbose_stdout_logging
from agents.exceptions import MaxTurnsExceeded
from agent.setupconfig import config
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response
)

# enable_verbose_stdout_logging()

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 1. Define the TaskVault Specialist Agent ---

taskvault_agent = Agent(
    name="TaskVault Success FTE",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response
    ]
)

# --- 2. Main Processing Logic ---

async def process_customer_message(
    customer_id: str,
    conversation_id: str,
    channel: str,
    message: str,
    db_path: str = "chat_history.db"
) -> str:
    """
    Process an incoming message through the TaskVault Agent.

    Args:
        customer_id: The unique UUID of the customer.
        conversation_id: The unique UUID of the current conversation thread.
        channel: The incoming channel (email/whatsapp/web_form).
        message: The raw text content from the customer.
        db_path: Path to the SQLite database for session persistence.

    Returns:
        The final output from the agent (though send_response tool is usually the last step).
    """
    try:
        # 1. Initialize persistent session using conversation_id as the session key
        session = SQLiteSession(conversation_id, db_path)
        logger.info(f"Session initialized for conversation: {conversation_id}")

        # 2. Enrich the input with context variables as per the system prompt
        enriched_input = (
            f"CONTEXT:\n"
            f"- customer_id: {customer_id}\n"
            f"- conversation_id: {conversation_id}\n"
            f"- channel: {channel}\n"
            f"\n"
            f"MESSAGE: {message}"
        )
        logger.info(f"Processing message on channel '{channel}': {message[:50]}...")

        # 3. Execute the agent through the Runner
        print(f"\n🔄 Starting agent run (max_turns=10 by default)...")
        result = await Runner.run(
            taskvault_agent,
            enriched_input,
            session=session,
            run_config=config,
            max_turns=20
        )

        # Debug: Print what happened
        print(f"\n📊 Agent Run Complete!")
        print(f"   Final output: {result.final_output[:200] if result.final_output else 'None'}")

        logger.info(f"Agent finished processing for {conversation_id}.")
        return result.final_output

    except MaxTurnsExceeded as e:
        logger.error(f"Max turns exceeded for {conversation_id}. Agent may be stuck in a loop.")
        logger.error(f"Consider simplifying the agent's instructions or checking tool responses.")
        return "I apologize, but I'm having trouble processing your request. A human agent will assist you shortly."

    except Exception as e:
        logger.error(f"Agent processing failed for {conversation_id}: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "I'm sorry, I encountered an internal error. Please try again or wait for a human agent."

if __name__ == "__main__":
    # Quick local test loop with real database integration
    import asyncio

    from database.queries import get_or_create_customer, start_conversation, log_message

    async def test():
        print("="*60)
        print("🏭 Testing TaskVault Agent with Database Integration")
        print("="*60)

        # Step 1: Create a real customer
        print("\n📝 Step 1: Creating test customer...")
        customer_id = await get_or_create_customer(
            name="Test User",
            email="testuser@example.com",
            phone="+1555123456"
        )
        print(f"   ✅ Customer ID: {customer_id}")

        # Step 2: Start a conversation
        print("\n📝 Step 2: Starting conversation...")
        conversation_id = await start_conversation(customer_id, "whatsapp")
        print(f"   ✅ Conversation ID: {conversation_id}")

        # Step 3: Log the inbound message
        # test_message = "How do I create a new Kanban board?"
        test_message = "HI"
        print(f"\n📝 Step 3: Logging customer message: '{test_message}'")
        await log_message(
            conversation_id=conversation_id,
            channel="whatsapp",
            direction="inbound",
            role="customer",
            content=test_message
        )
        print("   ✅ Message logged!")

        # Step 4: Process through the agent
        print("\n🤖 Step 4: Processing through TaskVault Agent...")
        print("-"*60)
        resp = await process_customer_message(
            customer_id, conversation_id, "whatsapp", test_message
        )
        print("-"*60)
        print(f"\n📤 Agent Response:\n{resp}")

        print("\n" + "="*60)
        print("✅ Test Complete! Check your database for the new records.")
        print("="*60)

    asyncio.run(test())

