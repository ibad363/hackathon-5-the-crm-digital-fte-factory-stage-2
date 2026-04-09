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

2. **Knowledge Base & Embeddings**
   - Successfully integrated a free, local SentenceTransformer model (`all-MiniLM-L6-v2`).
   - Script created to seed the knowledge base with product documentation.

3. **Agent Setup & Tool Alignment**
   - Agent initialized using OpenAI Agents SDK.
   - Tools aligned with the database schema: `search_knowledge_base`, `create_ticket`, `get_customer_history`, `escalate_to_human`, `send_response`.
   - System prompt meticulously crafted to match the TaskVault company profile, brand voice, and escalation rules (including the E.A.R. method for angry customers).

4. **Gmail Integration (Push-Based via Pub/Sub)**
   - **OAuth Flow:** Configured desktop app credentials (`gmail_auth.py`).
   - **Pub/Sub Webhook:** FastAPI endpoint (`/api/webhooks/gmail`) receiving real-time push notifications from Google.
   - **State Persistence:** Created `integration_state` table to persist `last_history_id`, surviving server restarts and preventing infinite backlog flushing.
   - **Filtering Logic:** Added robust filters to ignore our own sent messages, automated bounces (`mailer-daemon`, `noreply`), and messages older than 15 minutes.
   - **End-to-End Flow:** Successfully tested receiving an email, finding/creating the customer, logging the message, running the agent, sending a threaded reply, and marking the original email as read with a custom label (`TaskVault/Processed`).

### 🚧 What is In Progress / Needs Debugging
- **LLM Model Stability:** We encountered rate limit issues with the Gemini free tier (429 errors) and tool hallucination issues (`create_ticket_ide`) with another model. We are currently utilizing OpenRouter models to balance free access with reliable tool calling.

### ❌ What is Remaining (Next Steps)
1. **WhatsApp Integration:** Implement the Twilio webhook handler (`/api/webhooks/whatsapp`) following the same robust pattern used for Gmail.
2. **Web Support Form:** Build the React/Next.js frontend and connect it to the existing `/api/webhooks/web-form` endpoint.
3. **Event-Driven Architecture:** Fully implement Kafka topics (`fte.tickets.incoming`, etc.) to decouple message intake from agent processing.
4. **Testing & Infrastructure:** 
   - Write Locust scripts for load testing.
   - Dockerize the application.
   - Set up Kubernetes (K8s) manifests with Horizontal Pod Autoscaler (HPA).
5. **The Final 24-Hour Challenge:** Pressure test the system with 100+ web forms, 50+ emails, and 50+ WhatsApp messages with zero data loss.

---

## 🧠 Chat Context & Developer Experience Log

This section documents the hurdles overcome during development to serve as a reference for future debugging:

* **The Database Connection Crisis:** Initially, the code created a new connection pool for every query. When multiple webhooks hit simultaneously, it instantly crashed PostgreSQL with a `TooManyConnectionsError` (sorry, too many clients already). **Fix:** Implemented a global Singleton pool in `database/queries.py`.
* **The "Infinite Logs" Webhook Flood:** Google Pub/Sub's history API is relentless. Because the `GmailHandler` kept losing its `_last_history_id` on server reloads, Google would flush the entire inbox history every time, resulting in endless logs of bounce messages and old emails. **Fix:** Created the `integration_state` table to persistently save the history ID to the database, added a 15-minute age cutoff, and explicitly filtered out `mailer-daemon` and `noreply` addresses.
* **The Webhook Double-Slash Bug:** Pub/Sub was returning unlimited 404 errors. **Fix:** Removed a typo in the Google Cloud Console subscription URL (`//api/...` -> `/api/...`).
* **Tool Hallucination (`create_ticket_ide`):** While testing, the agent crashed because the LLM tried to call a tool that didn't exist. **Fix:** This is a known issue with smaller/fine-tuned models injecting IDE suffixes. Switching to a more robust model via OpenRouter resolves this.
* **JSONB Serialization:** PostgreSQL `JSONB` columns strictly require valid JSON strings. Python lists/dicts must be passed through `json.dumps()` before inserting via `asyncpg`.
* **Vector Casting:** When inserting embeddings into `pgvector`, the Python list of floats must be cast to a string `str(embedding_list)` before executing the query.

---
*Last Updated: 2026-04-09*