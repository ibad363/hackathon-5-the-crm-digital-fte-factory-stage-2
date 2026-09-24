# 🏭 TaskVault CRM — Digital FTE Factory (Hackathon 5)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-Distributed%20Streaming-231F20?style=flat&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI%20Agents%20SDK-Specialist%20FTE-412991?style=flat&logo=openai&logoColor=white)](https://openai.com)

> An autonomous **24/7 Digital FTE (Full-Time Equivalent)** Customer Success AI Employee designed for **TaskVault** (a B2B SaaS project management platform).  
> It ingests customer inquiries across **Email (Gmail)**, **WhatsApp**, and a **Web Support Form**, streams events through **Apache Kafka**, queries product docs using **pgvector semantic search**, and formulates channel-tailored responses or escalates to human agents.

---

## 📌 About the Project

Customer support in fast-growing SaaS companies often drowns in repetitive technical and account inquiries. A traditional human FTE costs upwards of **$75,000/year** plus overhead, vacations, and shift handoffs.

**The Mission:** Build an autonomous AI employee operating 24/7 at **<$1,000/year** with zero downtime, instant response times, and bulletproof safety guardrails.

### 🌟 Key Highlights
- **Omnichannel Intake:** Unified processing across **Email** (Gmail API + Google Cloud Pub/Sub), **WhatsApp** (Twilio Webhooks), and a dedicated **Next.js Web Support Form**.
- **Decoupled Event-Driven Core:** FastAPI endpoints act as high-speed producers that push events to **Apache Kafka**, while background workers consume and execute AI tasks asynchronously.
- **Self-Built CRM (PostgreSQL):** Stores unified customer profiles, cross-channel identifier mapping (`email`, `phone`), conversations, tickets, and message logs.
- **Semantic Vector Search:** Embedded documentation powered by `sentence-transformers/all-MiniLM-L6-v2` and PostgreSQL `pgvector` for accurate context retrieval.
- **Strict Human Escalation Guardrails:** Automatically detects billing disputes, refund requests, security bugs, and legal threats to route tickets directly to human teams with SLA tracking.
- **Customer Status Portal:** Real-time web portal where customers can track ticket resolution status and review AI responses using unique ticket references (e.g. `WEB-2026...`).

---

## 🏗️ Architecture Overview

```
 ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
 │   Gmail Inbox   │       │ WhatsApp Client │       │   Web Browser   │
 │ (Pub/Sub Push)  │       │ (Twilio Webhook)│       │ (Next.js Form)  │
 └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
          │                         │                         │
          ▼                         ▼                         ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                      FastAPI Gateway (Port 8000)                    │
 │               /api/webhooks/gmail   /api/webhooks/whatsapp          │
 │                      /api/support/submit                            │
 └──────────────────────────────────┬──────────────────────────────────┘
                                    │
                       (Produces event in <10ms)
                                    ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     Apache Kafka Message Broker                     │
 │                     Topic: `fte.tickets.incoming`                   │
 └──────────────────────────────────┬──────────────────────────────────┘
                                    │
                       (Consumes event asynchronously)
                                    ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │           Unified AI Worker (workers/unified_processor.py)          │
 │                                                                     │
 │   ┌─────────────────────────────────────────────────────────────┐   │
 │   │               OpenAI Agents SDK Specialist                  │   │
 │   │  • Cross-Channel Identity Resolution (Customer History)     │   │
 │   │  • Semantic Search via pgvector                             │   │
 │   │  • Channel Tone Adaptation (Email vs WhatsApp vs Web)       │   │
 │   │  • Escalation Evaluator (Billing, Legal, Security)          │   │
 │   └──────────────────────────────┬──────────────────────────────┘   │
 └──────────────────────────────────┼──────────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
 ┌──────────────────────┐                       ┌──────────────────────┐
 │    PostgreSQL CRM    │                       │  Outbound Dispatch   │
 │ • customers          │                       │ • Gmail API Reply    │
 │ • conversations      │                       │ • Twilio WhatsApp    │
 │ • tickets            │                       │ • Ticket Web Portal  │
 │ • knowledge_base     │                       └──────────────────────┘
 └──────────────────────┘
```

---

## 📁 Repository Structure

```text
├── agent/                         # OpenAI Agents SDK Specialist implementation
│   ├── customer_success_agent.py  # Agent definition, runner & session management
│   ├── tools.py                   # Function tools (KB search, ticket create, escalate)
│   ├── prompts.py                 # System instructions & TaskVault persona
│   └── setupconfig.py             # LLM provider config (OpenRouter / Gemini / NineRouter)
├── api/                           # FastAPI Application
│   ├── main.py                    # Server startup, CORS, lifespan & background loops
│   └── webhooks.py                # Webhook endpoints for Gmail & WhatsApp
├── channels/                      # Channel-specific intake & dispatch handlers
│   ├── gmail_handler.py           # Gmail API client, Pub/Sub processing, OAuth
│   ├── whatsapp_handler.py        # Twilio WhatsApp webhook & message sender
│   └── web_form_handler.py        # Web form submission & ticket status lookup API
├── context/                       # TaskVault business context & domain rules
│   ├── company-profile.md         # Product plans, tiers, and SLAs
│   ├── product-docs.md            # Features, API docs, settings
│   ├── brand-voice.md             # E.A.R. framework & channel style guide
│   ├── escalation-rules.md        # Hard & soft human escalation triggers
│   └── sample-tickets.json        # 50+ benchmark multi-channel tickets
├── database/                      # PostgreSQL CRM & Vector Store
│   ├── schema.sql                 # CRM tables & pgvector DDL
│   ├── queries.py                 # Asyncpg singleton connection pool & CRUD logic
│   ├── seed_kb.py                 # Markdown chunker & embedding seeder
│   └── test_conn.py               # DB connection & extension verification
├── frontend/                      # Next.js 16 Web Application
│   ├── src/app/page.tsx           # Standalone Web Support Form
│   ├── src/app/ticket/page.tsx    # Live Ticket Status Lookup Portal
│   └── src/components/            # UI components (SupportForm, TicketLookup, Navbar)
├── messaging/                     # Event streaming layer
│   └── kafka_client.py            # Async Kafka Producer & Consumer (aiokafka)
├── workers/                       # Background task processing
│   └── unified_processor.py       # Standalone Kafka consumer & AI executor
├── docker-compose.yml             # Local Kafka & Zookeeper orchestration
├── requirements.txt               # Python package dependencies
├── CONTEXT_SUMMARY.md             # High-density summary of the 2,800+ line project spec
└── PROJECT_STATUS.md              # Engineering log and roadmap
```

---

## 🎭 Multi-Channel Communication Matrix

| Channel | Tone & Formatting | Constraints | Dispatch Method |
| :--- | :--- | :--- | :--- |
| **Email (Gmail)** | Formal, polite, structured, professional greeting and sign-off | Complete steps, links to docs, no emojis | Gmail API (OAuth 2.0) |
| **WhatsApp** | Conversational, direct, warm | **Strictly < 300 characters**, max 1–2 emojis, no markdown | Twilio WhatsApp API |
| **Web Form** | Clear, semi-formal, supportive | Generates human-readable ID (`WEB-YYYYMMDD...`), emails confirmation | Next.js API + Email |

### 🛡️ Escalation Guardrails
The agent resolves product, setup, and navigation queries independently. It **never** independently resolves:
- **Billing & Refunds:** Invoices, disputes, cancellations, or refund requests -> **Billing Team**
- **Security:** Vulnerability disclosures, token leaks, unauthorized access -> **Security Team**
- **Legal:** GDPR, regulatory inquiries, lawyer communications -> **Legal Team**
- **High Frustration:** Sentiment score `< 0.25` or repeated unresolved queries -> **Tier-2 Human Support**

---

## 🚀 Quickstart: How to Run the Project

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Docker Desktop** (for Kafka & Zookeeper)
- **PostgreSQL 16** with the [`pgvector`](https://github.com/pgvector/pgvector) extension

---

### Step 1: Clone & Configure Environment

1. Clone repository and navigate to root:
   ```bash
   cd hackathon-5-the-crm-digital-fte-factory-stage-2
   ```

2. Copy the example environment file:
   ```powershell
   cp .env.example .env
   ```

3. Open `.env` and fill in your values:
   ```ini
   # Database (PostgreSQL with pgvector)
   DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_db

   # Kafka
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092

   # LLM Provider Keys (OpenRouter / Gemini / NineRouter)
   OPENROUTER_API_KEY=your_openrouter_key
   GEMINI_API_KEY=your_gemini_key
   NINEROUTER_API_KEY=your_ninerouter_key

   # (Optional) External Channel Integrations
   GOOGLE_CLOUD_PROJECT=your_gcp_project_id
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

---

### Step 2: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

---

### Step 3: Start Kafka & Zookeeper

Start the distributed event messaging broker in Docker:
```powershell
docker compose up -d
```
Verify containers are running:
```powershell
docker ps
```
*(Zookeeper should be on `2181` and Kafka on `9092`)*

---

### Step 4: Initialize PostgreSQL CRM Database

1. Apply the CRM schema and enable `pgvector`:
   ```powershell
   psql -d crm_db -f database/schema.sql
   ```
2. Verify database connection and tables:
   ```powershell
   python database/test_conn.py
   ```
3. Seed the Knowledge Base with chunked documentation embeddings:
   ```powershell
   python database/seed_kb.py
   ```

---

### Step 5: Start the System (3 Terminals)

#### 🖥️ Terminal 1 — FastAPI Ingestion Server
```powershell
uvicorn api.main:app --reload --port 8000
```
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

#### ⚙️ Terminal 2 — Unified Kafka AI Worker
```powershell
python -m workers.unified_processor
```
- Listens to Kafka topic `fte.tickets.incoming`.
- Runs the OpenAI Agent, checks the knowledge base, updates ticket state in PostgreSQL, and dispatches the answer.

#### 🌐 Terminal 3 — Next.js Frontend (Support Portal)
```powershell
cd frontend
npm install
npm run dev
```
- **Web Support Form:** [http://localhost:3000](http://localhost:3000)
- **Ticket Status Portal:** [http://localhost:3000/ticket](http://localhost:3000/ticket)

---

## 🧪 Testing & Verification

1. **Submit a Ticket via Web Form:**
   - Open [http://localhost:3000](http://localhost:3000).
   - Fill in your name, email, select a category, and ask a question (e.g., *"How do I invite team members to my workspace in TaskVault?"*).
   - Submit the form. You will receive an external Ticket Reference ID (e.g., `WEB-20260414-XXXX`).
2. **Observe Real-Time Processing:**
   - **Terminal 1 (FastAPI):** Acknowledges submission and emits event to Kafka.
   - **Terminal 2 (AI Worker):** Picks up ticket, runs `search_knowledge_base`, generates answer, and updates ticket status to `resolved` or `escalated`.
3. **Lookup Ticket Status:**
   - Open [http://localhost:3000/ticket](http://localhost:3000/ticket).
   - Enter your Ticket ID to see the full resolution, priority, assigned team, and response details.

---

## 📖 Additional Documentation

- [`CONTEXT_SUMMARY.md`](./CONTEXT_SUMMARY.md) — Concise reference guide of the Hackathon requirements and business rules.
- [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) — Current implementation milestones, debugging log, and next steps.
- [`docs/GMAIL_INTEGRATION_GUIDE.md`](./docs/GMAIL_INTEGRATION_GUIDE.md) — Gmail API & Pub/Sub setup walkthrough.
- [`docs/WHATSAPP_INTEGRATION_GUIDE.md`](./docs/WHATSAPP_INTEGRATION_GUIDE.md) — Twilio WhatsApp webhook integration guide.

---

## 📜 License
Distributed under the MIT License for Hackathon 5.
