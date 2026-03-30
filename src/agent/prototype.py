"""
TaskVault Customer Success FTE — Prototype v2 (Exercise 1.3)
============================================================
Core interaction loop WITH conversation memory and state tracking.

Memory tracks per customer (keyed by email/customer_id):
  - Full message history (cross-channel)
  - Sentiment trend (is the interaction going well?)
  - Topics discussed (for daily reporting)
  - Resolution status (solved / pending / escalated)
  - Original channel + any channel switches
"""

import os
import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List


# ─────────────────────────────────────────────
#  Data models
# ─────────────────────────────────────────────

@dataclass
class CustomerMessage:
    """Incoming message from any channel."""
    content: str
    channel: str            # email | whatsapp | web_form
    customer_id: str        # primary key — use email address


@dataclass
class Turn:
    """A single exchange (customer message + agent response) stored in memory."""
    timestamp: str
    channel: str
    customer_text: str
    agent_text: str
    sentiment_score: float  # 0.0 (angry) → 1.0 (happy)
    topics: List[str]
    escalated: bool


@dataclass
class ConversationState:
    """
    All persistent state for one customer across all channels and sessions.
    Keyed by customer_id (email address).
    """
    customer_id: str
    original_channel: str
    channel_history: List[str] = field(default_factory=list)   # e.g. ["email", "whatsapp"]
    turns: List[Turn] = field(default_factory=list)
    all_topics: List[str] = field(default_factory=list)        # deduplicated topic list
    sentiment_scores: List[float] = field(default_factory=list)
    status: str = "open"                                       # open | pending | solved | escalated
    escalation_reason: Optional[str] = None
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── helpers ──────────────────────────────

    @property
    def current_channel(self) -> str:
        return self.channel_history[-1] if self.channel_history else self.original_channel

    @property
    def avg_sentiment(self) -> float:
        if not self.sentiment_scores:
            return 0.5
        return round(sum(self.sentiment_scores) / len(self.sentiment_scores), 2)

    @property
    def sentiment_label(self) -> str:
        s = self.avg_sentiment
        if s < 0.25:   return "angry"
        if s < 0.45:   return "frustrated"
        if s < 0.65:   return "neutral"
        if s < 0.85:   return "satisfied"
        return "happy"

    def switched_channel(self) -> bool:
        """True when this customer has used more than one channel."""
        return len(set(self.channel_history)) > 1

    def recent_context(self, n: int = 3) -> str:
        """Return the last n turns as a plain-text summary for the agent prompt."""
        recent = self.turns[-n:]
        lines = []
        for t in recent:
            lines.append(f"[{t.channel}] Customer: {t.customer_text}")
            lines.append(f"[{t.channel}] Agent:    {t.agent_text}")
        return "\n".join(lines)


@dataclass
class AgentResponse:
    """What the agent returns after processing one message."""
    content: str
    escalated: bool
    escalation_reason: Optional[str] = None
    topics_detected: List[str] = field(default_factory=list)
    sentiment_score: float = 0.5


# ─────────────────────────────────────────────
#  Sentiment — simple heuristic
# ─────────────────────────────────────────────

_NEGATIVE_WORDS = [
    "angry", "furious", "terrible", "horrible", "awful", "useless", "broken",
    "ridiculous", "unacceptable", "worst", "disgusting", "fraud", "scam",
    "cancel", "refund", "lawsuit", "sue", "chargeback", "waste",
]
_POSITIVE_WORDS = [
    "love", "great", "amazing", "awesome", "thank", "thanks", "helpful",
    "perfect", "excellent", "brilliant", "fantastic", "wonderful", "appreciate",
]

def _score_sentiment(text: str) -> float:
    """Returns a float 0.0–1.0 (lower = more negative)."""
    tl = text.lower()
    score = 0.5

    # ALL CAPS penalty
    alpha = [c for c in text if c.isalpha()]
    if alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.5:
        score -= 0.15

    # Excessive punctuation
    if text.count("!") >= 3 or text.count("?") >= 3:
        score -= 0.05

    for w in _NEGATIVE_WORDS:
        if w in tl:
            score -= 0.10
    for w in _POSITIVE_WORDS:
        if w in tl:
            score += 0.10

    return round(max(0.0, min(1.0, score)), 2)


# ─────────────────────────────────────────────
#  Topic detection — keyword-to-topic mapping
# ─────────────────────────────────────────────

_TOPIC_MAP = {
    "billing":       ["billing", "invoice", "charge", "payment", "refund", "subscription", "plan", "upgrade", "downgrade", "pricing"],
    "password":      ["password", "login", "log in", "sign in", "forgot", "reset", "locked out", "access"],
    "integration":   ["slack", "github", "gitlab", "google drive", "zapier", "webhook", "integration", "connect"],
    "tasks":         ["task", "subtask", "create task", "delete task", "move task", "assign", "recurring", "due date"],
    "projects":      ["project", "board", "kanban", "timeline", "gantt", "calendar view", "list view"],
    "mobile":        ["mobile", "app", "ios", "android", "iphone", "phone", "crash"],
    "notifications": ["notification", "email alert", "push", "digest", "spam"],
    "api":           ["api", "rate limit", "endpoint", "authentication", "bearer", "401", "403"],
    "data_export":   ["export", "csv", "json", "download"],
    "security":      ["hacked", "compromised", "breach", "unauthorized", "two-factor", "2fa", "sso", "saml"],
    "cancellation":  ["cancel", "cancellation", "close account", "delete account"],
    "feedback":      ["feature request", "suggestion", "feedback", "love", "great product"],
    "performance":   ["slow", "loading", "lag", "timeout", "performance"],
}

def _detect_topics(text: str) -> List[str]:
    tl = text.lower()
    found = []
    for topic, keywords in _TOPIC_MAP.items():
        if any(kw in tl for kw in keywords):
            found.append(topic)
    return found or ["general"]


# ─────────────────────────────────────────────
#  Escalation rules
# ─────────────────────────────────────────────

_ESCALATION_TRIGGERS = [
    ("refund",            "refund_request"),
    ("chargeback",        "chargeback_threat"),
    ("money back",        "refund_request"),
    ("cancel",            "cancellation_request"),
    ("lawsuit",           "legal_threat"),
    ("sue",               "legal_threat"),
    ("lawyer",            "legal_threat"),
    ("attorney",          "legal_threat"),
    ("hacked",            "security_incident"),
    ("compromised",       "security_incident"),
    ("unauthorized access","security_incident"),
    ("data breach",       "security_incident"),
    ("gdpr",              "compliance_request"),
    ("human",             "human_handoff_requested"),
    ("real person",       "human_handoff_requested"),
    ("representative",    "human_handoff_requested"),
    ("outage",            "outage_report"),
    ("system down",       "outage_report"),
    ("data loss",         "data_loss"),
    ("all my data",       "data_loss"),
]

def _check_escalation(text: str):
    """Return (should_escalate: bool, reason: str|None)."""
    tl = text.lower()
    for phrase, reason in _ESCALATION_TRIGGERS:
        if phrase in tl:
            return True, reason
    return False, None


# ─────────────────────────────────────────────
#  Knowledge base loader
# ─────────────────────────────────────────────

def _load_docs(docs_path: str) -> Dict[str, str]:
    kb = {}
    if not os.path.exists(docs_path):
        return kb
    with open(docs_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Split on ## and ### headings
    for section in re.split(r"\n(?=#{1,3} )", content):
        lines = section.strip().split("\n")
        if lines:
            title = lines[0].lstrip("#").strip()
            body  = "\n".join(lines[1:]).strip()
            if title and body:
                kb[title] = body
    return kb


def _search_docs(kb: Dict[str, str], query: str, max_results: int = 2) -> str:
    """Return the top matching KB snippets as a single string."""
    words = {w for w in query.lower().split() if len(w) > 3}
    scored = []
    for title, body in kb.items():
        combined = (title + " " + body).lower()
        score = sum(combined.count(w) for w in words)
        # Title match is worth extra
        score += sum(3 for w in words if w in title.lower())
        if score > 0:
            scored.append((score, title, body))

    scored.sort(reverse=True)
    results = scored[:max_results]

    if not results:
        return ""

    parts = []
    for _, title, body in results:
        parts.append(f"[{title}]\n{body[:400]}")
    return "\n\n---\n\n".join(parts)


# ─────────────────────────────────────────────
#  Channel formatters
# ─────────────────────────────────────────────

def _format_email(customer_name: str, body: str) -> str:
    name = customer_name.split("@")[0].capitalize()
    return (
        f"Hi {name},\n\n"
        f"{body}\n\n"
        f"Let me know if you have any other questions.\n\n"
        f"Best regards,\nTaskVault Support"
    )

def _format_whatsapp(body: str) -> str:
    # Strip markdown, keep it short and casual
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", body)     # remove bold
    clean = re.sub(r"`(.+?)`", r"\1", clean)           # remove code
    clean = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", clean)  # remove links
    # Truncate to ~280 characters, break at last sentence boundary
    if len(clean) > 280:
        cut = clean[:280].rfind(".")
        clean = clean[: cut + 1] if cut > 150 else clean[:280] + "…"
    return clean

def _format_web_form(customer_name: str, body: str) -> str:
    name = customer_name.split("@")[0].capitalize()
    return (
        f"Hi {name}, thanks for submitting your request.\n\n"
        f"{body}\n\n"
        f"If you have follow-up questions, just reply to this email.\n\n"
        f"Best regards,\nTaskVault Support"
    )

def _apply_channel_format(raw: str, channel: str, customer_id: str) -> str:
    if channel == "email":
        return _format_email(customer_id, raw)
    elif channel == "whatsapp":
        return _format_whatsapp(raw)
    elif channel == "web_form":
        return _format_web_form(customer_id, raw)
    return raw


# ─────────────────────────────────────────────
#  Core agent
# ─────────────────────────────────────────────

class CustomerSuccessFTE:
    """
    Stateful customer success agent with cross-channel conversation memory.
    Each customer (keyed by customer_id / email) gets one ConversationState
    that persists across channels and turns.
    """

    def __init__(self, docs_path: str):
        self.kb = _load_docs(docs_path)
        # In-memory store: customer_id → ConversationState
        self._memory: Dict[str, ConversationState] = {}

    # ── memory helpers ────────────────────────

    def _get_or_create_state(self, customer_id: str, channel: str) -> ConversationState:
        if customer_id not in self._memory:
            self._memory[customer_id] = ConversationState(
                customer_id=customer_id,
                original_channel=channel,
                channel_history=[channel],
            )
        else:
            state = self._memory[customer_id]
            # Record channel switch
            if channel != state.current_channel:
                state.channel_history.append(channel)
        return self._memory[customer_id]

    def _update_state(self, state: ConversationState, turn: Turn):
        state.turns.append(turn)
        state.last_active = datetime.now().isoformat()
        state.sentiment_scores.append(turn.sentiment_score)
        # Merge new topics (deduplicated)
        for t in turn.topics:
            if t not in state.all_topics:
                state.all_topics.append(t)

    def get_summary(self, customer_id: str) -> str:
        """Return a printable memory summary for a customer."""
        if customer_id not in self._memory:
            return f"No history found for {customer_id}"
        s = self._memory[customer_id]
        lines = [
            f"  Customer ID    : {s.customer_id}",
            f"  Status         : {s.status}",
            f"  Original ch.   : {s.original_channel}",
            f"  Channel history: {' → '.join(s.channel_history)}",
            f"  Channel switch : {'YES' if s.switched_channel() else 'no'}",
            f"  Topics         : {', '.join(s.all_topics) or 'none'}",
            f"  Avg sentiment  : {s.avg_sentiment} ({s.sentiment_label})",
            f"  Turns          : {len(s.turns)}",
            f"  Last active    : {s.last_active}",
        ]
        if s.escalation_reason:
            lines.append(f"  Escalation     : {s.escalation_reason}")
        return "\n".join(lines)

    # ── main processing loop ──────────────────

    def process_message(self, msg: CustomerMessage) -> AgentResponse:
        """
        Full interaction loop with memory:
          1. Load / create ConversationState for this customer.
          2. Normalise message.
          3. Detect sentiment.
          4. Detect topics.
          5. Check escalation triggers.
          6. Search KB (augmented with prior context).
          7. Build response.
          8. Format for channel.
          9. Persist turn to memory.
        """

        # 1. State
        state = self._get_or_create_state(msg.customer_id, msg.channel)

        # 2. Normalise
        normalized = " ".join(msg.content.split()).lower()

        # 3. Sentiment
        sentiment = _score_sentiment(msg.content)

        # 4. Topics
        topics = _detect_topics(normalized)

        # 5. Escalation  (also escalate if sentiment has been consistently angry)
        escalate, reason = _check_escalation(normalized)
        if not escalate and sentiment < 0.25:
            escalate, reason = True, "very_negative_sentiment"

        if escalate:
            state.status = "escalated"
            state.escalation_reason = reason

            channel_note = ""
            if state.switched_channel():
                channel_note = (
                    f" I can see you've also reached out via "
                    f"{' and '.join(set(state.channel_history) - {msg.channel})} — "
                    f"I've included that context for the agent."
                )

            if msg.channel == "whatsapp":
                response_text = (
                    f"Got it! I'm connecting you with a team member now.{channel_note} "
                    f"They'll respond shortly. Hang tight! 🙌"
                )
            else:
                response_text = (
                    f"Thank you for reaching out.{channel_note} "
                    f"I've escalated your request to our specialist team "
                    f"who will follow up with you shortly."
                )

            turn = Turn(
                timestamp=datetime.now().isoformat(),
                channel=msg.channel,
                customer_text=msg.content,
                agent_text=response_text,
                sentiment_score=sentiment,
                topics=topics,
                escalated=True,
            )
            self._update_state(state, turn)

            return AgentResponse(
                content=_apply_channel_format(response_text, msg.channel, msg.customer_id),
                escalated=True,
                escalation_reason=reason,
                topics_detected=topics,
                sentiment_score=sentiment,
            )

        # 6. Build search query — blend current message with recent topic context
        search_query = normalized
        if state.all_topics:
            search_query += " " + " ".join(state.all_topics[-3:])

        doc_snippet = _search_docs(self.kb, search_query)

        # 7. Build raw response
        prior_context = state.recent_context(n=2)

        if state.switched_channel():
            context_note = (
                f"(Continuing from your earlier {state.original_channel} conversation) "
            )
        elif len(state.turns) > 0:
            context_note = "(Following up on your earlier message) "
        else:
            context_note = ""

        if doc_snippet:
            raw = f"{context_note}{doc_snippet}"
        else:
            raw = (
                f"{context_note}I wasn't able to find specific documentation on that. "
                f"Could you share a bit more detail so I can pinpoint the right answer?"
            )

        # Mark as pending if still open and we gave an answer
        if state.status == "open":
            state.status = "pending"

        # 8. Format for channel
        formatted = _apply_channel_format(raw, msg.channel, msg.customer_id)

        # 9. Persist turn
        turn = Turn(
            timestamp=datetime.now().isoformat(),
            channel=msg.channel,
            customer_text=msg.content,
            agent_text=raw,
            sentiment_score=sentiment,
            topics=topics,
            escalated=False,
        )
        self._update_state(state, turn)

        return AgentResponse(
            content=formatted,
            escalated=False,
            topics_detected=topics,
            sentiment_score=sentiment,
        )


# ─────────────────────────────────────────────
#  Interactive test CLI
# ─────────────────────────────────────────────

CHANNELS = ["email", "whatsapp", "web_form"]

def main():
    docs_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "context", "product-docs.md"
    )
    docs_path = os.path.normpath(docs_path)
    agent = CustomerSuccessFTE(docs_path)

    print("=" * 60)
    print("  TaskVault Customer Success FTE  —  Interactive Test")
    print("=" * 60)
    print("Commands:")
    print("  'summary'  → show memory for the current customer")
    print("  'switch'   → change channel mid-conversation")
    print("  'new'      → start a new customer session")
    print("  'quit'     → exit")
    print("=" * 60)

    customer_id = input("\nCustomer email (primary key) [test@example.com]: ").strip() or "test@example.com"
    channel     = input(f"Channel {CHANNELS} [email]: ").strip().lower() or "email"

    while True:
        try:
            user_input = input(f"\n[{channel}] {customer_id} > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nBye!")
            break

        if user_input.lower() == "summary":
            print("\n── Conversation Memory ──")
            print(agent.get_summary(customer_id))
            continue

        if user_input.lower() == "switch":
            channel = input(f"New channel {CHANNELS}: ").strip().lower()
            print(f"  ↳ Channel switched to [{channel}]")
            continue

        if user_input.lower() == "new":
            customer_id = input("New customer email: ").strip() or "test2@example.com"
            channel     = input(f"Channel {CHANNELS} [email]: ").strip().lower() or "email"
            continue

        msg  = CustomerMessage(content=user_input, channel=channel, customer_id=customer_id)
        resp = agent.process_message(msg)

        print(f"\n  Sentiment : {resp.sentiment_score} | Topics: {', '.join(resp.topics_detected)}")
        if resp.escalated:
            print(f"  ⚠  ESCALATED — reason: {resp.escalation_reason}")
        print(f"\n── Agent Response ──────────────────────────")
        print(resp.content)
        print("────────────────────────────────────────────")


if __name__ == "__main__":
    main()
