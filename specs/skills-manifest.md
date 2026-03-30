# TaskVault Customer Success FTE — Skills Manifest

This document outlines the discrete capabilities (skills) demonstrated by the prototype agent during the Incubation phase. These skills will be converted to OpenAI `@function_tool` tools in Phase 2.

## 1. Knowledge Retrieval
*   **Description**: Searches the product documentation for relevant answers to customer inquiries.
*   **Trigger**: When a user asks a "how-to" or product-feature question (e.g., "How do I reset my password?").
*   **Current Implementation**: Heuristic keyword scoring against `product-docs.md` (`_search_docs`).
*   **Production Implementation**: Vector search or semantic search across a broader knowledge base.

## 2. Sentiment Analysis
*   **Description**: Analyzes the emotional tone of incoming messages to identify frustration or anger.
*   **Trigger**: On every incoming message.
*   **Current Implementation**: Keyword matching and rule-based scoring (e.g., ALL CAPS penalty, `_NEGATIVE_WORDS`).
*   **Production Implementation**: LLM-based sentiment scoring or dedicated sentiment analysis model.

## 3. Escalation Decision
*   **Description**: Determines if a ticket should be routed to a human based on rules, keywords, or sentiment.
*   **Trigger**: When negative sentiment drops below `0.25`, or specific triggers like "sue", "cancel", "refund", or "hacked" are detected.
*   **Current Implementation**: Rule-based matching in `_check_escalation()`.
*   **Production Implementation**: LLM structured output classification based on `escalation-rules.md`.

## 4. Channel Adaptation
*   **Description**: Formats the agent's response to fit the medium the customer is using.
*   **Trigger**: Before sending the final message.
*   **Current Implementation**: `_apply_channel_format()` logic (e.g., stripping Markdown for WhatsApp, adding formal greetings for Email).
*   **Production Implementation**: System prompt instructions directing the LLM to output channel-specific formatting natively.

## 5. Conversation Memory (Customer Identification)
*   **Description**: Maintains context across multiple turns and channels using the customer's email as the primary key.
*   **Trigger**: On every incoming message (to retrieve past turns and topics).
*   **Current Implementation**: In-memory `ConversationState` dictionary keyed by `customer_id`.
*   **Production Implementation**: Persistent storage in PostgreSQL, retrieving chat history prior to LLM generation.