# 🏭 The CRM Digital FTE Factory: Hackathon 5 Complete Guide

## 📌 Project Overview & Goals
The objective is to build a **24/7 Digital FTE (Full-Time Equivalent)** — an autonomous AI Customer Success Employee designed for a SaaS company. The project evolves from a general prototype to a production-grade specialized agent capable of operating across multiple communication channels (Email, WhatsApp, Web Form) at a fraction of a human's cost (<$1,000/year).

**Core Philosophy:** General Agents (Claude Code) are used as the "Factory" to build, test, and deploy Custom Agents (OpenAI SDK Specialists).

---

## 🛠️ Unified Tech Stack
- **Agent Framework:** OpenAI Agents SDK (for the Custom Specialist Agent).
- **Development & Orchestration:** Claude Code (for building the Specialist).
- **Backend Framework:** FastAPI (Python) with Uvicorn.
- **Messaging & Streaming:** Apache Kafka (using `aiokafka`).
- **Database / CRM:** PostgreSQL 16 with `pgvector` & `asyncpg`.
- **Integrations:** Gmail API (via Google API Client/PubSub), Twilio API (for WhatsApp).
- **Frontend:** React / Next.js (for the required Web Support Form component).
- **Infrastructure:** Docker, Docker Compose, Kubernetes (K8s) with Horizontal Pod Autoscaler (HPA).
- **Testing:** Pytest (Async), Locust (Load Testing).

---

## 🚀 Stage 1: Incubation (Discovery & Prototyping)
*Goal: Explore the problem space, discover requirements, and build a core-loop prototype.*

- **Key Activities:**
  - **Exploration:** Use Claude Code to analyze sample customer tickets and identify multi-channel patterns.
  - **Core Loop Prototype:** Implement a basic script for message normalization, knowledge base search, response generation, and escalation logic.
  - **MCP Server Development:** Create a Model Context Protocol server providing essential tools: `search_knowledge_base`, `create_ticket`, `get_customer_history`, `escalate_to_human`, and `send_response`.
  - **Skill Formalization:** Define specific capabilities like Sentiment Analysis, Channel-Aware Formatting, and Cross-Channel Identity Resolution.
- **Deliverables:**
  - `specs/discovery-log.md`: Documenting insights and edge cases found during exploration.
  - `specs/customer-success-fte-spec.md`: Detailed system design and functional requirements.
  - **Working Prototype:** A script demonstrating multi-channel interaction handling.

---

## 🔄 The Transition (Incubation to Specialization)
*Goal: Transform exploratory code into production-ready components.*

- **Methodology:** Use Claude Code to rewrite the prototype into a modular, production-grade system.
- **Transformation Mapping:**
  - Prototype scripts → Modular directories (`agent/`, `api/`, `workers/`, `channels/`).
  - MCP Tools → OpenAI SDK `@function_tool` decorators with strict Pydantic schemas.
  - In-memory state → Persistent PostgreSQL storage (CRM).
  - Local configuration → Environment variables and Kubernetes ConfigMaps/Secrets.

---

## 🏗️ Stage 2: Specialization (Production Build)
*Goal: Build a reliable, scalable, autonomous agent system.*

### 1. Custom CRM & Database Design (PostgreSQL)
A custom PostgreSQL schema acts as the single source of truth (CRM), tracking:
- **Customers:** Unified profiles with multiple identifiers (Email, Phone, Name).
- **Conversations:** Sentiment tracking, state management, and full history across all channels.
- **Tickets:** Lifecycle management (Open, Investigating, Escalated, Resolved).
- **Knowledge Base:** Semantic vector-enabled storage (`pgvector`) for product documentation.
- **Analytics:** Tokens used, latency metrics, and success/resolution rates.

### 2. Multi-Channel Intake Handlers
- **Gmail Handler:** Webhook integration via Google Pub/Sub (preferred) or polling; sending replies via Gmail API.
- **WhatsApp Handler:** Webhook handling via Twilio; managing the 1600-character message limit and Twilio signature validation.
- **Web Support Form (Mandatory):** A standalone React/Next.js UI component with real-time submission, validation, and ticket status lookup.

### 3. Specialist Agent Implementation (OpenAI SDK)
- **Strict Instructions:** Constraints on pricing (escalate), refunds (escalate), and undocumented feature promises.
- **Channel-Aware Tone:**
  - **Email:** Formal, structured, professional greetings/closings.
  - **WhatsApp:** Concise, helpful, under 300 characters, no lengthy blocks.
  - **Web Form:** Clear, semi-formal.
- **Core Toolset:** `search_knowledge_base`, `create_ticket`, `get_customer_history`, `escalate_to_human`, `send_response`.

### 4. Event-Driven Architecture (Kafka)
- Decouples message intake from agent processing for high availability.
- Core Topics: `fte.tickets.incoming`, `fte.channels.whatsapp.inbound`, `fte.channels.gmail.inbound`, `fte.escalations`, `fte.metrics`.

---

## 🧪 Stage 3: Integration & Chaos Testing
*Goal: Ensure 24/7 reliability and performance at scale.*

- **End-to-End Testing:** Verification of the complete lifecycle across all three channels simultaneously.
- **Cross-Channel Identity Resolution:** Ensuring the system recognizes a customer moving from an email conversation to a WhatsApp message.
- **Load Testing:** Using Locust to simulate high-concurrency scenarios and validating Kubernetes Horizontal Pod Autoscaling (HPA).
- **Chaos Testing:** Verifying zero message loss and graceful recovery during random pod terminations or database failovers.

---

## 📋 Final Submission & Grading Criteria (100 pts Total)
### 1. Technical Implementation (50 pts)
- **Web Support Form (10 pts):** Complete React/Next.js frontend with backend integration.
- **Agent Functionality (10 pts):** Proper tool execution, strict instruction adherence, and channel tone.
- **Integrations (10 pts):** Functional Gmail and WhatsApp (Twilio) handlers.
- **Core Infrastructure (10 pts):** Operational PostgreSQL, Kafka, and Kubernetes deployment.
- **Database Schema (10 pts):** Robust, well-indexed CRM schema including vector search.

### 2. Operational Readiness (25 pts)
- **24/7 Autonomy:** Uptime > 99.9% and survival of service restarts.
- **Cross-Channel Continuity:** Successful merging of history based on customer identifiers.

### 3. Quality & Documentation (25 pts)
- **System Spec:** Completeness and clarity of `specs/customer-success-fte-spec.md`.
- **Testing:** Comprehensive test coverage and successful load test results.
- **Code Quality:** Adherence to strict typing, async patterns, and error handling.

---

## 🏁 The Final 24-Hour Challenge
The system must successfully handle a live "pressure test" consisting of:
- 100+ Web Form submissions.
- 50+ Emails and 50+ WhatsApp messages.
- P95 Latency below 3 seconds.
- Zero data/message loss during simulated failures.
