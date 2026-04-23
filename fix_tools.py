import re

with open('agent/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove Pydantic imports and schemas completely
content = re.sub(r'from pydantic import BaseModel, Field\n', '', content)
content = re.sub(r'class KnowledgeSearchInput\(BaseModel\):[\s\S]*?# --- 2. Production Tools \(OpenAI Agents SDK\) ---', '# --- 2. Production Tools (OpenAI Agents SDK) ---', content)

# 1. Update search_knowledge_base
content = re.sub(
    r'@function_tool\nasync def search_knowledge_base\(input: KnowledgeSearchInput\) -> str:',
    '@function_tool\nasync def search_knowledge_base(query: str, category: str = "", max_results: int = 3) -> str:',
    content
)
content = content.replace('input.query', 'query')
content = content.replace('input.category', 'category')
content = content.replace('input.max_results', 'max_results')

# 2. Update create_ticket
content = re.sub(
    r'@function_tool\nasync def create_ticket\(input: TicketCreationInput\) -> str:',
    '@function_tool\nasync def create_ticket(customer_id: str, conversation_id: str, channel: str, priority: str = "medium", category: str = "general") -> str:',
    content
)
content = content.replace('input.customer_id', 'customer_id')
content = content.replace('input.conversation_id', 'conversation_id')
content = content.replace('input.channel', 'channel')
content = content.replace('input.category', 'category')
content = content.replace('input.priority', 'priority')

# 3. Update get_customer_history
content = re.sub(
    r'@function_tool\nasync def get_customer_history\(input: CustomerHistoryInput\) -> str:',
    '@function_tool\nasync def get_customer_history(customer_id: str, limit: int = 10) -> str:',
    content
)
content = content.replace('input.limit', 'limit')

# 4. Update escalate_to_human
content = re.sub(
    r'@function_tool\nasync def escalate_to_human\(input: EscalationInput\) -> str:',
    '@function_tool\nasync def escalate_to_human(conversation_id: str, reason: str, escalate_to: str = "support_team") -> str:',
    content
)
content = content.replace('input.reason', 'reason')
content = content.replace('input.escalate_to', 'escalate_to')

# 5. Update send_response
content = re.sub(
    r'@function_tool\nasync def send_response\(input: ResponseInput\) -> str:',
    '@function_tool\nasync def send_response(conversation_id: str, channel: str, content: str) -> str:',
    content
)
content = content.replace('input.content', 'content')

with open('agent/tools.py', 'w', encoding='utf-8') as f:
    f.write(content)
