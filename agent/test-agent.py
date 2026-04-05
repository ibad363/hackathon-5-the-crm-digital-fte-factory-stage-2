import sys
import os
# Add project root to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import Agent, Runner
from agent.setupconfig import config
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response
)


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


result = Runner.run_sync(
            taskvault_agent,
            "hi",
            run_config=config
        )
print(result.final_output)