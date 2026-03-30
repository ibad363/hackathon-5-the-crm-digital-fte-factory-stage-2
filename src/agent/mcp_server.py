"""MCP server exposing the Customer Success FTE prototype tools.
================================================================
This server uses the Model Context Protocol (MCP) SDK to make the prototype
functions available to external clients (e.g. a UI, other services, or a test
harness).

The implementation is intentionally lightweight – it re‑uses the prototype’s
`CustomerSuccessFTE` class for knowledge‑base search and customer‑history
lookup, and provides simple in‑memory ticket tracking for the remaining
tools.
"""

import uuid
from pathlib import Path
from typing import Dict

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent
from enum import Enum

# Import the prototype implementation
from prototype import (
    CustomerSuccessFTE,
    CustomerMessage,
    _search_docs,  # internal helper – safe to reuse here
)

# ---------------------------------------------------------------------------
#  Simple in‑memory ticket store
# ---------------------------------------------------------------------------

_TICKETS: Dict[str, Dict] = {}


def _store_ticket(customer_id: str, issue: str, priority: str, channel: str) -> str:
    ticket_id = str(uuid.uuid4())
    _TICKETS[ticket_id] = {
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "history": [],
    }
    return ticket_id


def _append_history(ticket_id: str, message: str) -> None:
    if ticket_id in _TICKETS:
        _TICKETS[ticket_id]["history"].append(message)

# ---------------------------------------------------------------------------
#  MCP server definition
# ---------------------------------------------------------------------------

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

# Resolve the path to the product documentation (used by the prototype).
DOCS_PATH = Path(__file__).parents[2] / "context" / "product-docs.md"
agent = CustomerSuccessFTE(str(DOCS_PATH))

server = FastMCP("customer-success-fte")

# ---------------------------------------------------------------------------
#  Tool: search_knowledge_base
# ---------------------------------------------------------------------------

@server.tool("search_knowledge_base")
async def search_kb(query: str) -> str:
    """Search the product knowledge‑base and return the top matching snippets.

    The prototype already contains a private helper `_search_docs` that performs
    ranking and truncation. We reuse it here to keep the behaviour identical to the
    interactive CLI.
    """
    # Use the same scoring logic as the prototype.
    result = _search_docs(agent.kb, query)
    return result or "No relevant documentation found."

# ---------------------------------------------------------------------------
#  Tool: create_ticket
# ---------------------------------------------------------------------------

@server.tool("create_ticket")
async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str,
    channel: Channel,
) -> str:
    """Create a support ticket and return its identifier.

    The ticket store is in‑memory for the incubation phase. In production this would
    be replaced by a persistent database.
    """
    ticket_id = _store_ticket(customer_id, issue, priority, channel.value)
    # Record the initial issue text in the ticket history.
    _append_history(ticket_id, f"Issue: {issue}")
    return ticket_id

# ---------------------------------------------------------------------------
#  Tool: get_customer_history
# ---------------------------------------------------------------------------

@server.tool("get_customer_history")
async def get_customer_history(customer_id: str) -> str:
    """Return a printable summary of all interactions for a customer.

    This mirrors the `CustomerSuccessFTE.get_summary` method used by the CLI.
    """
    return agent.get_summary(customer_id)

# ---------------------------------------------------------------------------
#  Tool: escalate_to_human
# ---------------------------------------------------------------------------

@server.tool("escalate_to_human")
async def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Mark a ticket as escalated and return an escalation identifier.

    For the prototype we generate a UUID to represent the escalation event.
    """
    escalation_id = str(uuid.uuid4())
    # Add a note to the ticket history so the escalation is visible.
    _append_history(ticket_id, f"Escalated: {reason} (escalation_id={escalation_id})")
    return escalation_id

# ---------------------------------------------------------------------------
#  Tool: send_response
# ---------------------------------------------------------------------------

@server.tool("send_response")
async def send_response(
    ticket_id: str,
    message: str,
    channel: Channel,
) -> str:
    """Record that a response was sent for a ticket.

    The function stores the outbound message in the ticket's history and returns a
    simple status string. In a real deployment this would integrate with the
    appropriate outbound channel (SMTP, Twilio, etc.).
    """
    _append_history(ticket_id, f"Sent via {channel.value}: {message}")
    return "sent"

# ---------------------------------------------------------------------------
#  Server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # The server will listen on the default MCP port (usually 8000) and expose the
    # tools defined above. Clients can discover the tool signatures via the MCP
    # discovery endpoint.
    server.run()
