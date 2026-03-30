# 🏭 Hackathon 5: Transition Checklist (Prototype to Production)

This document provides a detailed status of the transition from Stage 1 (Incubation) to Stage 2 (Specialization/Production).

---

## ✅ Completed Tasks (Stage 1: Incubation)
*These tasks represent the "Discovery" and "Prototype" phase that is now finalized.*

- [x] **Problem Exploration:** Analyzed sample tickets and identified multi-channel support patterns.
- [x] **Core Loop Prototype:** Created basic Python logic for message ingestion, normalization, and response generation.
- [x] **Requirement Discovery:** Identified the need for persistent CRM state, Kafka event streaming, and channel-aware agent behavior.
- [x] **MCP Server (Prototype):** Built an MCP server with the 5 core tools: `search_knowledge_base`, `create_ticket`, `get_customer_history`, `escalate_to_human`, and `send_response`.
- [x] **Project Specification:** Drafted the `specs/customer-success-fte-spec.md` and initial transition plans.
- [x] **Context Layer:** Created a detailed `CLAUDE.md` to guide all future development.

---

## 🛠️ Remaining Tasks (Stage 2: Specialization)
*These tasks are required to build the production-grade Custom Agent system.*

### 1. Production Project Restructuring
- [ ] **Define Root Directory Structure:**
  - `agent/`: Core OpenAI SDK implementation.
  - `api/`: FastAPI webhook endpoints and routes.
  - `channels/`: Integrations for Gmail, WhatsApp, and Web Form.
  - `workers/`: Kafka consumer logic for background processing.
  - `database/`: PostgreSQL schemas, migrations, and async models.
  - `web-form/`: React/Next.js UI component for the support form.
  - `k8s/`: Kubernetes manifests for production deployment.
- [ ] **Environment Configuration:** Create `.env.example` with placeholders for `OPENAI_API_KEY`, `KAFKA_BOOTSTRAP_SERVERS`, `DATABASE_URL`, `TWILIO_ACCOUNT_SID`, `GMAIL_CLIENT_ID`, etc.

### 2. Infrastructure & Data Layer (Custom CRM)
- [ ] **PostgreSQL 16 Setup:**
  - Install `pgvector` extension for semantic search capabilities.
  - **Tooling:** Use `asyncpg` for non-blocking database queries and `SQLAlchemy` (optional) for ORM mapping.
- [ ] **Custom CRM Schema Design:**
  - **Customers:** `id`, `name`, `email`, `phone`, `created_at`.
  - **Customer_Identifiers:** Map various channel IDs (Twilio SID, Gmail address) to a single Customer ID.
  - **Conversations:** `id`, `customer_id`, `status` (Open/Closed), `last_sentiment`, `last_message_at`.
  - **Messages:** `id`, `conversation_id`, `channel` (Gmail/WhatsApp/Web), `direction` (Inbound/Outbound), `content`, `timestamp`.
  - **Tickets:** `id`, `customer_id`, `status`, `subject`, `priority`.
  - **Knowledge_Base:** `id`, `content`, `embedding` (VECTOR(1536)).
- [ ] **Apache Kafka Configuration:**
  - **Tooling:** Use `aiokafka` for async producer/consumer logic.
  - **Topics:** `fte.tickets.incoming`, `fte.channels.whatsapp.inbound`, `fte.channels.gmail.inbound`, `fte.escalations`, `fte.metrics`, `fte.dlq` (Dead Letter Queue).

### 3. The Specialist Agent (OpenAI SDK)
- [ ] **Core Implementation:** Rewrite the agent logic using the `OpenAI Agents SDK` instead of MCP.
- [ ] **Tool Transformation:** Convert prototype skills into strictly typed `@function_tool` decorators.
  - **Tooling:** Use `Pydantic` `BaseModel` for validation of every tool input/output.
- [ ] **System Prompt Formalization:**
  - Implement the **E.A.R. Methodology** (Empathy, Answer, Resolve).
  - Enforce **Channel-Aware Tone**:
    - WhatsApp: Concise, <300 characters, conversational.
    - Email: Formal, detailed, structured.
- [ ] **Hard Constraints:** Code-level checks to ensure the agent *never* discusses pricing/refunds and *always* creates a ticket at the start.

### 4. Multi-Channel Intake Handlers (FastAPI)
- [ ] **Gmail Integration:**
  - Use `google-api-python-client` and `google-auth`.
  - Implement a handler to ingest messages via **Google Pub/Sub** push notifications or periodic polling.
- [ ] **WhatsApp (Twilio) Integration:**
  - Use Twilio's webhook endpoint.
  - **Security:** Implement `RequestValidator` to verify Twilio signatures.
  - **Constraint:** Implement message splitting for content exceeding 1600 characters.
- [ ] **Web Support Form UI:**
  - **Frontend:** Build a standalone `SupportForm.jsx` in **React/Next.js** using `Tailwind CSS`.
  - **Backend:** Create a `/support/submit` endpoint in FastAPI to ingest the form data and push to Kafka.

### 5. Unified Message Processor Worker
- [ ] **Kafka Consumer Worker:** Build a resilient `message_processor.py` that pulls from all channel topics.
- [ ] **Customer Identity Resolver:** Create logic to lookup or create a Customer record based on the channel's unique identifier (email or phone).
- [ ] **History Stitcher:** Logic to fetch the last 10-20 messages for the conversation before calling the Agent.
- [ ] **Response Dispatcher:** Logic to route the Agent's output back to the specific Kafka `outgoing` topic or trigger the channel's API directly.

### 6. Testing, Load & Chaos (Stage 3 Ready)
- [ ] **Testing Suite:**
  - **Unit Tests:** `pytest-asyncio` for `@function_tool` functions.
  - **Load Testing:** `Locust` to simulate 100+ concurrent users and verify P95 latency < 3s.
  - **Chaos Testing:** Randomly terminate Worker/API pods to verify zero message loss and Kafka persistence.

### 7. Kubernetes Deployment (K8s)
- [ ] **Manifests:** Write YAML for `Deployment`, `Service`, `ConfigMap`, `Secret`, and `Ingress`.
- [ ] **Scaling:** Configure **Horizontal Pod Autoscaler (HPA)** based on CPU/Memory or Kafka lag.
- [ ] **Observability:** Implement structured JSON logging for indexing in an ELK or Loki stack.

---

## 📅 Roadmap to Completion
1. **Week 1:** Database/CRM Schema, Kafka Setup, Project Structure.
2. **Week 2:** Gmail/Twilio Integrations, Web Form UI, Identity Resolver.
3. **Week 3:** Specialist Agent (OpenAI SDK) and Unified Message Processor.
4. **Week 4:** E2E Testing, Load Testing, Kubernetes Deployment.
