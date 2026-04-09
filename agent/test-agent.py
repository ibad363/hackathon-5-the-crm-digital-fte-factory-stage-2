import sys
import os
import logging

# Suppress all SDK/library logs for this file only
# logging.disable(logging.CRITICAL)

# Add project root to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import Agent, Runner, function_tool, enable_verbose_stdout_logging
from agent.setupconfig import config
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response
)

enable_verbose_stdout_logging()

@function_tool
async def test_tool():
    print("hello from tool call")
    return "TOOL_SUCCESS"
    
taskvault_agent = Agent(
    name="TaskVault Success FTE",
    instructions="you're a CUSTOMER support agent, each time call the tool",
    tools=[
        test_tool,
        # search_knowledge_base,
        # create_ticket,
        # get_customer_history,
        # escalate_to_human,
        # send_response
    ]
)


result = Runner.run_sync(
            taskvault_agent,
            "hi, how are you?",
            run_config=config
        )
print(result.final_output)