# TaskVault Customer Success FTE Specification

## 1. Goal
To build a production-ready, AI-driven Digital FTE that autonomously handles customer inquiries across multiple channels (Email, WhatsApp, Web Form) while maintaining continuous conversation memory, detecting sentiment, and gracefully escalating complex issues to human agents according to SLA policies.

## 2. Core Personas
1. **The Customer:** Reaches out via any channel; expects fast, accurate answers or a seamless hand-off to a human.
2. **The AI FTE (TaskVault Support):** The first line of defense; polite, channel-aware, and strictly adheres to the brand voice and escalation rules.
3. **The Human Agent:** Receives escalated tickets with full context, sentiment analysis, and categorized reasons (e.g., Billing, Security, Legal).

## 3. Supported Channels
1. **Email (Gmail API):** Formal, supports formatting, no emojis, full-length responses.
2. **WhatsApp (Twilio):** Casual, maximum 280 characters, minimal emojis (1-2), no markdown.
3. **Web Form (Next.js/FastAPI):** Similar to Email, but responses are sent via the email provided in the form submission.

## 4. Key Workflows

### Standard Inquiry Workflow
1. Customer message is ingested via Kafka from any channel.
2. Agent normalizes the text and retrieves the customer's `ConversationState` from PostgreSQL (using email as primary key).
3. Agent analyzes sentiment and detects topics.
4. Agent queries the knowledge base and formulates a channel-appropriate response.
5. Response is dispatched, and the interaction is logged in the database.

### Escalation Workflow
1. Message triggers an escalation rule (keyword match or sentiment < 0.25).
2. Agent marks the ticket status as `escalated`.
3. Agent formats an `ESCALATION REPORT` containing the ticket ID, channel, customer info, sentiment, and full conversation context.
4. An auto-reply is sent to the customer acknowledging the escalation and providing an SLA timeline.
5. The ticket is routed to the appropriate human team (Billing, Security, Legal, Support).

## 5. Required Production Stack
*   **Orchestration:** Python 3.13, OpenAI Agents SDK (`@function_tool`), FastAPI
*   **Message Broker:** Apache Kafka (for unified ingestion and decoupling)
*   **Database:** PostgreSQL (for durable state, tickets, and conversation memory)
*   **Deployment:** Docker, Kubernetes
*   **External APIs:** Gmail API, Twilio API

## 6. Success Criteria
*   **Accuracy:** Agent correctly answers questions from `product-docs.md` 95% of the time.
*   **Safety:** Agent *never* attempts to resolve a billing dispute, legal threat, or security breach independently.
*   **Continuity:** A customer can start a conversation on Email and continue it on WhatsApp without the agent losing context.
*   **Tone:** The agent consistently applies the E.A.R. (Empathy, Accountability, Resolution) method and adheres to the emoji policy.