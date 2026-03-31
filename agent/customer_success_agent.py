# production/agent/customer_success_agent.py
import os
import logging
from typing import Optional
from agents import Agent, Runner, SQLiteSession
from agent.setupconfig import config
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response
)

logger = logging.getLogger(__name__)

# --- 1. Define the TaskVault Specialist Agent ---

taskvault_agent = Agent(
    name="TaskVault Success FTE",
    model="gpt-4o",
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

        # 2. Enrich the input with context variables as per the system prompt
        enriched_input = (
            f"CONTEXT:\n"
            f"- customer_id: {customer_id}\n"
            f"- conversation_id: {conversation_id}\n"
            f"- channel: {channel}\n"
            f"\n"
            f"MESSAGE: {message}"
        )

        # 3. Execute the agent through the Runner
        result = await Runner.run(
            taskvault_agent,
            enriched_input,
            session=session,
            run_config=config
        )

        logger.info(f"Agent finished processing for {conversation_id}. Status: {result.final_output[:50]}...")
        return result.final_output

    except Exception as e:
        logger.error(f"Agent processing failed for {conversation_id}: {e}")
        return "I'm sorry, I encountered an internal error. Please try again or wait for a human agent."

if __name__ == "__main__":
    # Quick local test loop
    import asyncio

    async def test():
        print("Testing TaskVault Agent...")
        resp = await process_customer_message(
            "cust_123", "conv_456", "whatsapp", "How do I create a new Kanban board?"
        )
        print(f"Agent Response: {resp}")

    asyncio.run(test())
