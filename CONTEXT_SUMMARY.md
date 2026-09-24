# 🏭 TaskVault Digital FTE: Context Summary

> **Concise Reference Guide** condensing the 2,800+ line Hackathon 5 specification (`The CRM Digital FTE Factory Final Hackathon 5.md`) and the domain documents in `context/`.

---

## 🎯 1. Project Mission & Objective
Build an autonomous **24/7 Digital FTE (Full-Time Equivalent)** Customer Success Employee for **TaskVault** (a B2B SaaS project management platform).
- **Core Target:** Replace/augment a $75,000/yr human support FTE with an autonomous agent operating at **<$1,000/yr**.
- **Operation:** 24/7 availability, zero downtime, multi-channel intake, consistent brand voice, strict escalation handling, and unified CRM ticket lifecycle.

---

## 🏗️ 2. High-Level Architecture & Event Pipeline

```text
[Gmail API / PubSub]   [Twilio WhatsApp]   [Next.js Web Form]
         │                     │                   │
         ▼                     ▼                   ▼
    FastAPI Webhook Endpoints (/api/webhooks/*, /api/support/submit)
                               │
                Publishes Event to Kafka Topic:
                    `fte.tickets.incoming`
                               │
                               ▼
        Unified Kafka Worker (`workers/unified_processor.py`)
                               │
               ┌───────────────┴───────────────┐
               │   OpenAI Agents SDK Specialist│
               │   - Semantic Search (pgvector)│
               │   - Context & Tone Formatting │
               │   - Strict Escalation Checks  │
               └───────────────┬───────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       PostgreSQL CRM DB              Channel Dispatcher
  (Customers, Tickets, Messages)   (Gmail / Twilio / Email)
```

---

## 🌐 3. Multi-Channel Rules & Tone Matrix

| Channel | Format & Tone | Constraints | Delivery Method |
| :--- | :--- | :--- | :--- |
| **Email (Gmail)** | Formal, professional, structured, standard greetings & sign-offs | Detailed explanations, links to docs, no emojis | Gmail API (OAuth2 / Pub/Sub) |
| **WhatsApp (Twilio)** | Conversational, direct, polite | **Strictly under 300 characters**, max 1–2 emojis, no markdown | Twilio WhatsApp API |
| **Web Form (Next.js)** | Semi-formal, clear, actionable | Returns ticket ID (`WEB-YYYYMMDD...`), instant status lookup | Next.js UI + Email confirmation |

**Cross-Channel Identity Resolution:**
- Primary customer key: **Email address**.
- If a customer switches from WhatsApp to Email (or vice versa), their identity is linked in `customer_identifiers` and past conversation history is preserved.

---

## 🛠️ 4. Specialist Agent & Toolset

The agent is powered by **OpenAI Agents SDK** and equipped with 5 core tools:
1. `search_knowledge_base(query)`: Queries PostgreSQL vector store using `all-MiniLM-L6-v2` embeddings for accurate documentation snippets.
2. `create_ticket(customer_id, title, issue, priority, channel)`: Creates or checks existing ticket in PostgreSQL CRM, generating a channel-prefixed ID (e.g., `WEB-...`, `EMA-...`, `WHA-...`).
3. `get_customer_history(customer_id)`: Fetches previous tickets and messages across all channels for context.
4. `escalate_to_human(ticket_id, reason, team)`: Escalates issues to Human tiers (Billing, Security, Legal, Support) when policies require human intervention.
5. `send_response(ticket_id, message, channel)`: Logs and dispatches the formulated response.

---

## 🚨 5. Escalation Guardrails

The agent **never** attempts to resolve the following independently:
- **Billing & Refunds:** Any pricing dispute, cancellation request, or refund over $50 -> Escalate to `Billing`.
- **Security & Vulnerabilities:** Bug bounties, breach reports, token leaks, penetration testing -> Escalate to `Security`.
- **Legal Threats:** Mention of lawyers, GDPR/CCPA formal requests, or regulatory violations -> Escalate to `Legal`.
- **Negative Sentiment:** Customer sentiment score `< 0.25` or repeated unresolved questions -> Escalate to `Tier-2 Support`.

---

## 📚 6. Knowledge Base & Domain Context (`context/`)

- `company-profile.md`: TaskVault tiers (Starter @ $12/user/mo, Pro @ $29/user/mo, Enterprise @ custom), SLAs (Starter: 48h, Pro: 12h, Enterprise: 1h).
- `product-docs.md`: Core features (Task boards, Automations, API keys, Role-based permissions, Webhooks, Integrations).
- `brand-voice.md`: Apply the **E.A.R.** framework: **E**mpathy, **A**ccountability, **R**esolution.
- `escalation-rules.md`: Precise triggers and handoff procedures.
- `sample-tickets.json`: 50+ benchmark inquiries across email, chat, and form used for evaluation.
