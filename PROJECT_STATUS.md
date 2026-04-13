# 🏭 PROJECT_STATUS.md
# The CRM Digital FTE Factory: Hackathon 5

## 📌 Project Overview & Goals
The objective of this project is to build a **24/7 Digital FTE (Full-Time Equivalent)** — an autonomous AI Customer Success Employee designed for a SaaS company (TaskVault). 
The project evolves from a general prototype to a production-grade specialized agent capable of operating across multiple communication channels (Email, WhatsApp, Web Form) at a fraction of a human's cost.

**Core Philosophy:** General Agents (Claude Code) are used as the "Factory" to build, test, and deploy Custom Agents (OpenAI SDK Specialists).

### 🛠️ Unified Tech Stack
- **Agent Framework:** OpenAI Agents SDK (Custom Specialist Agent)
- **Development & Orchestration:** Claude Code
- **Backend Framework:** FastAPI (Python) with Uvicorn
- **Messaging & Streaming:** Apache Kafka (using `aiokafka`) - *Pending full integration*
- **Database / CRM:** PostgreSQL 16 with `pgvector` & `asyncpg`
- **Embeddings:** Free local model (`sentence-transformers/all-MiniLM-L6-v2`)
- **LLM Inference:** OpenRouter API (`meta-llama/llama-3.3-70b-instruct:free` or `qwen/qwen3.6-plus:free`)
- **Integrations:** Gmail API (via Google Pub/Sub), Twilio API (for WhatsApp - *Pending*)
- **Frontend:** React / Next.js (for the Web Support Form - *Pending*)

---

## 📊 Current State of the Project

### ✅ What is Completed
1. **Database & Schema Setup**
   - Custom PostgreSQL schema created with tables for: `customers`, `customer_identifiers`, `conversations`, `messages`, `tickets`, `knowledge_base`, `channel_configs`, and `agent_metrics`.
   - `pgvector` extension enabled for semantic search.
   - Singleton connection pooling implemented via `asyncpg` to prevent "too many clients" errors.
   - Database queries written for all core operations.
   - **Database Migration:** Added `external_ref` column to `tickets` table to support human-readable Web Form IDs (`WEB-YYYYMMDD...`).

2. **Knowledge Base & Embeddings**
   - Successfully integrated a free, local SentenceTransformer model (`all-MiniLM-L6-v2`).
   - **Markdown Chunking:** Implemented a robust chunking script in `seed_kb.py` that splits product documentation by H2/H3 headers, significantly improving search relevance.
   - **Search Optimization:** Switched `pgvector` operators from Cosine Distance (`<=>`) to Inner Product (`<#>`) and added vector normalization, resulting in similarity scores jumping from 0.17 to 0.80 for technical queries.

3. **Agent Setup & Tool Alignment**
   - Agent initialized using OpenAI Agents SDK.
   - Tools aligned with the database schema: `search_knowledge_base`, `create_ticket`, `get_customer_history`, `escalate_to_human`, `send_response`.
   - **Idempotency:** Updated `create_ticket` tool to handle existing tickets gracefully, preventing the agent from "Technical Difficulty" loops when a ticket was already created by a webhook.
   - System prompt meticulously crafted to match the TaskVault company profile, brand voice, and escalation rules (including the E.A.R. method for angry customers).

4. **Gmail Integration (Push-Based via Pub/Sub)**
   - **OAuth Flow:** Configured desktop app credentials (`gmail_auth.py`).
   - **Pub/Sub Webhook:** FastAPI endpoint (`/api/webhooks/gmail`) receiving real-time push notifications from Google.
   - **State Persistence:** Created `integration_state` table to persist `last_history_id`, surviving server restarts and preventing infinite backlog flushing.
   - **Filtering Logic:** Added robust filters to ignore our own sent messages, automated bounces (`mailer-daemon`, `noreply`), and messages older than 15 minutes.
   - **End-to-End Flow:** Successfully tested receiving an email, finding/creating the customer, logging the message, running the agent, sending a threaded reply, and marking the original email as read with a custom label (`TaskVault/Processed`).

5. **Web Support Form (Production Grade)**
   - **Frontend:** Completed React/Next.js frontend with Tailwind CSS. Features real-time validation and character counting.
   - **Ticket Tracking:** Built a dedicated **Ticket Status Portal** (`/ticket/[id]`) that allows users to track their conversation with the AI in real-time using a chat-bubble UI.
   - **Integration:** Successfully wired the Next.js API proxy to a dedicated FastAPI `web_form_handler.py`.
   - **Real-time Updates:** Implemented auto-polling on the ticket status page to show AI responses as they are generated.

### 🚧 What is In Progress / Needs Debugging
- **Network Resilience:** The local Windows environment occasionally aborts established connections (`WinError 10053`) during long-running Gmail API calls.
- **LLM Context management:** Fine-tuning the balance between chunk size and LLM context window to ensure the most accurate responses.

### ❌ What is Remaining (Next Steps)
1. **WhatsApp Integration:** Implement the Twilio webhook handler (`/api/webhooks/whatsapp`) following the same robust pattern used for Gmail and Web Form.
2. **Event-Driven Architecture:** Fully implement Kafka topics (`fte.tickets.incoming`, etc.) to decouple message intake from agent processing and solve connection abort issues.
3. **Testing & Infrastructure:** 
   - Write Locust scripts for load testing.
   - Dockerize the application.
   - Set up Kubernetes (K8s) manifests with Horizontal Pod Autoscaler (HPA).
4. **The Final 24-Hour Challenge:** Pressure test the system with 100+ web forms, 50+ emails, and 50+ WhatsApp messages with zero data loss.

---

## 🧠 Chat Context & Developer Experience Log

This section documents the hurdles overcome during development to serve as a reference for future debugging:

* **The Database Connection Crisis:** Initially, the code created a new connection pool for every query. When multiple webhooks hit simultaneously, it instantly crashed PostgreSQL with a `TooManyConnectionsError` (sorry, too many clients already). **Fix:** Implemented a global Singleton pool in `database/queries.py`.
* **The "Infinite Logs" Webhook Flood:** Google Pub/Sub's history API is relentless. Because the `GmailHandler` kept losing its `_last_history_id` on server reloads, Google would flush the entire inbox history every time, resulting in endless logs of bounce messages and old emails. **Fix:** Created the `integration_state` table to persistently save the history ID to the database, added a 15-minute age cutoff, and explicitly filtered out `mailer-daemon` and `noreply` addresses.
* **The Webhook Double-Slash Bug:** Pub/Sub was returning unlimited 404 errors. **Fix:** Removed a typo in the Google Cloud Console subscription URL (`//api/...` -> `/api/...`).
* **The Vector Similarity Gap:** Semantic search was returning scores as low as 0.17 for exact matches. **Fix:** Normalized embeddings to length 1 and switched the `pgvector` operator from `<=>` (Cosine Distance) to `<#>` (Inner Product/Dot Product). Similarity scores improved to 0.80+.
* **The Massive Doc Context Crash:** Searching the KB with unsplit documents caused the LLM to get lost in irrelevant noise or hit token limits. **Fix:** Implemented header-based markdown chunking in the seed script.
* **The "Ticket Already Exists" AI Loop:** When a webhook created a ticket before the agent started, the agent's `create_ticket` tool would crash, causing the AI to apologize for "technical difficulties." **Fix:** Made the `create_ticket` tool idempotent by checking for existing `conversation_id` before inserting.
* **The UUID Formatting Strictness:** The `uuid.UUID()` constructor is extremely sensitive to whitespace/quotes passed by the LLM. **Fix:** Added robust string cleaning (stripping quotes, brackets, and spaces) inside the tool.
* **The Offline Model Crash:** `SentenceTransformer` attempts an internet check on every boot, crashing the server if internet is unstable. **Fix:** Added `local_files_only=True` to the initialization.

---
*Last Updated: 2026-04-14*