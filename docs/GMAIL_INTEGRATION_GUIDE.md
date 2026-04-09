# 📧 Gmail Integration Guide — TaskVault CRM
## Production-Ready Gmail Push Notifications via Google Pub/Sub

---

## 📌 Table of Contents
1. [How It Works (Architecture)](#1-how-it-works-architecture)
2. [Prerequisites](#2-prerequisites)
3. [Step-by-Step Setup Guide](#3-step-by-step-setup-guide)
   - [Step 3.1: Google Cloud Project Setup](#step-31-google-cloud-project-setup)
   - [Step 3.2: Enable APIs](#step-32-enable-apis)
   - [Step 3.3: Create OAuth 2.0 Credentials](#step-33-create-oauth-20-credentials)
   - [Step 3.4: Create the Pub/Sub Topic](#step-34-create-the-pubsub-topic)
   - [Step 3.5: Grant Gmail Permission to Publish](#step-35-grant-gmail-permission-to-publish)
   - [Step 3.6: Authenticate Gmail Locally](#step-36-authenticate-gmail-locally)
   - [Step 3.7: Set Up ngrok for Local Development](#step-37-set-up-ngrok-for-local-development)
   - [Step 3.8: Create Pub/Sub Subscription](#step-38-create-pubsub-subscription)
   - [Step 3.9: Set Up Database State Table](#step-39-set-up-database-state-table)
   - [Step 3.10: Activate Gmail Watch](#step-310-activate-gmail-watch)
   - [Step 3.11: Start the Server and Test](#step-311-start-the-server-and-test)
4. [End-to-End Flow Explained](#4-end-to-end-flow-explained)
5. [Environment Variables Reference](#5-environment-variables-reference)
6. [Common Mistakes & How to Avoid Them](#6-common-mistakes--how-to-avoid-them)
   - [Mistake 1: Double Slash in Webhook URL](#mistake-1-double-slash-in-webhook-url)
   - [Mistake 2: OAuth "Access Blocked" Error](#mistake-2-oauth-access-blocked-error)
   - [Mistake 3: Infinite Webhook Flood](#mistake-3-infinite-webhook-flood)
   - [Mistake 4: Too Many Database Connections](#mistake-4-too-many-database-connections)
   - [Mistake 5: Reply Loop (AI Replies to Itself)](#mistake-5-reply-loop-ai-replies-to-itself)
   - [Mistake 6: Tool Name Hallucination](#mistake-6-tool-name-hallucination)
   - [Mistake 7: Free LLM Rate Limits](#mistake-7-free-llm-rate-limits)
   - [Mistake 8: pgvector / JSONB Type Errors](#mistake-8-pgvector--jsonb-type-errors)
   - [Mistake 9: ngrok URL Changes on Restart](#mistake-9-ngrok-url-changes-on-restart)
   - [Mistake 10: Gmail Watch Expires After 7 Days](#mistake-10-gmail-watch-expires-after-7-days)
7. [Key Files Reference](#7-key-files-reference)
8. [Testing Checklist](#8-testing-checklist)

---

## 1. How It Works (Architecture)

The Gmail integration uses a **Push-Based** model. This means Gmail
proactively notifies your server the instant a new email arrives.
There is no polling — it is real-time and efficient.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FULL GMAIL FLOW DIAGRAM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Customer sends email to ibad0352@gmail.com                       │
│         │                                                            │
│         ▼                                                            │
│  2. Google Gmail detects new message in INBOX                        │
│         │                                                            │
│         ▼                                                            │
│  3. Gmail "Watch" publishes a Pub/Sub notification                   │
│     { emailAddress, historyId }                                      │
│     → to topic: projects/taskvault-crm/topics/gmail-notifications    │
│         │                                                            │
│         ▼                                                            │
│  4. Pub/Sub subscription pushes notification to your server          │
│     → POST https://YOUR-NGROK-URL/api/webhooks/gmail                 │
│         │                                                            │
│         ▼                                                            │
│  5. FastAPI webhook receives the ping, acknowledges (200 OK)         │
│     and dispatches a background task immediately                     │
│         │                                                            │
│         ▼                                                            │
│  6. GmailHandler.process_pubsub_notification()                       │
│     a. Load last_history_id from PostgreSQL (integration_state)      │
│     b. If historyId is older than stored → skip (duplicate)         │
│     c. If gap > 500 events → jump to present (skip backlog)         │
│     d. Call Gmail History API with startHistoryId                    │
│     e. Filter: skip SENT, noreply, mailer-daemon, old messages       │
│     f. Save new historyId back to PostgreSQL                         │
│         │                                                            │
│         ▼                                                            │
│  7. For each real inbound email:                                     │
│     a. get_or_create_customer() → PostgreSQL                         │
│     b. start_conversation() → PostgreSQL                             │
│     c. log_message(inbound) → PostgreSQL                             │
│     d. process_customer_message() → TaskVault Agent (LLM)            │
│         │                                                            │
│         ▼                                                            │
│  8. Agent uses tools:                                                │
│     → create_ticket → PostgreSQL                                     │
│     → search_knowledge_base → pgvector semantic search               │
│     → send_response → returns formatted reply text                   │
│         │                                                            │
│         ▼                                                            │
│  9. log_message(outbound) → PostgreSQL                               │
│         │                                                            │
│         ▼                                                            │
│  10. GmailHandler.send_reply()                                       │
│      → Sends threaded reply via Gmail API                            │
│         │                                                            │
│         ▼                                                            │
│  11. Housekeeping:                                                   │
│      → mark_as_read() (removes UNREAD label)                         │
│      → add_label("TaskVault/Processed")                              │
│                                                                      │
│  DONE. Logs stop. No further activity until next real email.         │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- Google sends only a **notification** (not the email content) for security.
- Your server calls the Gmail API to **fetch the actual content**.
- The `historyId` is persisted in PostgreSQL so the system survives restarts.
- Everything after the 200 OK response runs in a **background task** so
  Google never retries due to a slow server response.

---

## 2. Prerequisites

Before you start, make sure you have:

| Requirement | Details |
|-------------|---------|
| Python 3.11+ | With virtual environment activated |
| PostgreSQL 16 | Running locally with pgvector extension |
| Google Account | The Gmail account the AI will use (e.g., ibad0352@gmail.com) |
| Google Cloud Account | Free tier is fine for this project |
| ngrok | For exposing localhost to the internet during development |
| `.env` file | With all required keys (see Section 5) |

**Install required Python packages:**
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

---

## 3. Step-by-Step Setup Guide

### Step 3.1: Google Cloud Project Setup

1. Go to: **https://console.cloud.google.com**
2. Click the project dropdown at the top → **"New Project"**
3. Name it: `taskvault-crm`
4. Note your **Project ID** (e.g., `taskvault-crm-123456`) — you will need this later.

---

### Step 3.2: Enable APIs

1. In GCP Console, go to: **APIs & Services → Library**
2. Search for and enable **both** of these APIs:
   - ✅ **Gmail API**
   - ✅ **Cloud Pub/Sub API**

---

### Step 3.3: Create OAuth 2.0 Credentials

> ⚠️ This is the most important step. Do not skip any substep.

1. Go to: **APIs & Services → Credentials**
2. Click **"+ CREATE CREDENTIALS" → "OAuth client ID"**
3. If prompted to configure the consent screen first:
   - Click **"CONFIGURE CONSENT SCREEN"**
   - User Type: **External**
   - App name: `taskvault-support`
   - Support email: your email
   - Developer contact: your email
   - Click **Save and Continue** through all steps
4. Back in Credentials, click **"+ CREATE CREDENTIALS" → "OAuth client ID"**
5. Application type: **Desktop app**
6. Name: `TaskVault Gmail Client`
7. Click **Create**
8. Click **"DOWNLOAD JSON"**
9. Save this file as: `credentials/gmail_credentials.json`

**Your folder should look like:**
```
credentials/
├── .gitignore              ← prevents committing secrets
└── gmail_credentials.json  ← the file you just downloaded
```

---

### Step 3.4: Create the Pub/Sub Topic

1. In GCP Console, go to: **Pub/Sub → Topics**
2. Click **"+ CREATE TOPIC"**
3. Topic ID: `gmail-notifications`
4. Leave other options as default
5. Click **"CREATE"**

Your full topic name will be:
```
projects/taskvault-crm/topics/gmail-notifications
```
(Replace `taskvault-crm` with your actual Project ID)

---

### Step 3.5: Grant Gmail Permission to Publish

This is a critical step that is easy to miss.
Gmail needs permission to publish to your Pub/Sub topic.

1. Click on your `gmail-notifications` topic
2. Go to the **"PERMISSIONS"** tab (or click "ADD PRINCIPAL")
3. New principals: `gmail-api-push@system.gserviceaccount.com`
4. Role: **Pub/Sub Publisher**
5. Click **"SAVE"**

> ⚠️ If you skip this step, Gmail will silently fail to deliver notifications
> and your webhook will never receive any messages.

---

### Step 3.6: Authenticate Gmail Locally

Run the setup script which will open your browser for OAuth:

```bash
python scripts/setup_gmail.py
```

**What will happen:**
1. Browser opens with Google Sign-In
2. Select your Gmail account (`ibad0352@gmail.com`)
3. You will see: **"Google hasn't verified this app"** — this is expected
4. Click **"Advanced"** → **"Go to taskvault-support (unsafe)"**
5. Click **"Allow"** to grant all permissions
6. Browser shows: "The authentication flow has completed."

> ⚠️ If you see **"Error 403: access_denied"**, it means your Gmail account
> is not added as a test user. Fix:
> Go to GCP Console → APIs & Services → OAuth consent screen →
> Test users → "+ ADD USERS" → add your Gmail address → Save.
> Then try again.

A `credentials/token.json` file will be created automatically.
This file keeps you logged in permanently (auto-refreshes).

---

### Step 3.7: Set Up ngrok for Local Development

Google Pub/Sub requires a **public HTTPS URL** to push notifications to.
During local development, use ngrok to create a secure tunnel.

1. Download ngrok: **https://ngrok.com/download**
2. Sign up for a free account and get your authtoken
3. Run:
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
ngrok http 8000
```

4. You will see output like:
```
Forwarding   https://abc123-xyz.ngrok-free.app -> http://localhost:8000
```

5. Copy the HTTPS URL. You will need it in the next step.

> ⚠️ IMPORTANT: ngrok gives you a NEW URL every time you restart it.
> Every time ngrok restarts, you MUST update the Pub/Sub subscription
> endpoint URL in GCP Console. This is the #1 cause of "no webhook received"
> issues during development.

---

### Step 3.8: Create Pub/Sub Subscription

1. In GCP Console, go to: **Pub/Sub → Subscriptions**
2. Click **"+ CREATE SUBSCRIPTION"**
3. Fill in:
   - Subscription ID: `gmail-notifications-sub`
   - Select a Cloud Pub/Sub topic: `gmail-notifications`
   - Delivery type: **Push** (not Pull)
   - Endpoint URL: `https://YOUR-NGROK-URL/api/webhooks/gmail`
     > ⚠️ Use a SINGLE slash before "api". Double slash (//) causes 404 errors.
4. Click **"CREATE"**

> **Verification:** After setup, go to ngrok's web interface
> (http://localhost:4040) and you should see incoming POST requests
> to /api/webhooks/gmail even before you send any email.
> Google sends a "health check" notification when the subscription is created.

---

### Step 3.9: Set Up Database State Table

This table persists the Gmail `historyId` across server restarts.
Without this, every restart causes a massive backlog flood.

Run the verification script which creates the table if it doesn't exist:

```bash
python scripts/verify_state_table.py
```

You should see:
```
integration_state table exists! Rows: 0
```

---

### Step 3.10: Activate Gmail Watch

This tells Gmail to start publishing to your Pub/Sub topic.

```bash
python scripts/setup_gmail.py
```

When asked on Step 5:
```
Set up Gmail push notifications? (y/n): y
```

You should see:
```
✅ Gmail watch active!
   History ID: 1198552
   Expires: 1712345678000
```

> ⚠️ The Gmail watch expires every **7 days**. You must re-run this command
> weekly (or automate it with a cron job) to keep push notifications active.
> If you forget, the webhook will stop receiving notifications silently.

After running setup, the current `historyId` is stored in the database.
This means your server will ONLY process emails that arrive AFTER this point.
All old emails will be ignored.

---

### Step 3.11: Start the Server and Test

**Terminal 1 — Start the API server:**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Wait until you see:
```
INFO: Application startup complete.
```

**Terminal 2 — Keep ngrok running** (should already be running from Step 3.7)

**Terminal 3 — Send a test email:**
Use a DIFFERENT email account (not the authenticated one) to send an email to
`ibad0352@gmail.com`.

**Subject:** `Question about Kanban boards`
**Body:** `Hi TaskVault! I want to know how to create a Kanban board.`

**Expected server logs (within 5 seconds):**
```
📬 Gmail webhook | pubsubId=xxx | email=ibad0352@gmail.com | historyId=...
📧 Processing | from=your-other-email@gmail.com | subject='Question about Kanban boards'
👤 Customer ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
💬 Conversation ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
🤖 Agent response ready (450 chars)
✉️  Reply status: sent
✅ Done — email labelled & marked as read
```

**Check your test email inbox** — you should have received a professional
reply from TaskVault within 30 seconds!

---

## 4. End-to-End Flow Explained

| Step | What Happens | Where in Code |
|------|-------------|---------------|
| 1 | Email arrives in inbox | Gmail servers |
| 2 | Gmail detects new message | Gmail API watch |
| 3 | Pub/Sub publishes notification | GCP Console topic |
| 4 | Your server receives POST request | `api/webhooks.py` → `gmail_webhook()` |
| 5 | Server returns 200 OK immediately | Same function, before background task |
| 6 | Background task starts | `process_gmail_notification()` |
| 7 | Load persisted historyId | `_load_last_history_id()` → PostgreSQL |
| 8 | Fetch new messages since last historyId | `GmailHandler.process_pubsub_notification()` |
| 9 | Filter spam/bounce/old emails | Inside `process_pubsub_notification()` |
| 10 | Save new historyId to DB | `_save_last_history_id()` → PostgreSQL |
| 11 | Create/find customer in CRM | `get_or_create_customer()` → PostgreSQL |
| 12 | Start new conversation | `start_conversation()` → PostgreSQL |
| 13 | Log inbound message | `log_message()` → PostgreSQL |
| 14 | Run TaskVault Agent | `process_customer_message()` → OpenRouter LLM |
| 15 | Agent searches knowledge base | `search_knowledge_base` tool → pgvector |
| 16 | Agent generates reply | LLM response |
| 17 | Log outbound message | `log_message()` → PostgreSQL |
| 18 | Send reply email | `GmailHandler.send_reply()` → Gmail API |
| 19 | Mark original as read | `GmailHandler.mark_as_read()` |
| 20 | Add processing label | `GmailHandler.add_label("TaskVault/Processed")` |

---

## 5. Environment Variables Reference

Add these to your `.env` file:

```env
# ─────────────────────────────────────────
# Database (PostgreSQL with pgvector)
# ─────────────────────────────────────────
DATABASE_URL=postgresql://postgres:YourPassword@localhost:5432/crm_db

# ─────────────────────────────────────────
# LLM (OpenRouter — recommended for free tier)
# ─────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# ─────────────────────────────────────────
# Gmail Integration
# ─────────────────────────────────────────
GOOGLE_CLOUD_PROJECT=taskvault-crm         # Your GCP Project ID
GMAIL_ADDRESS=ibad0352@gmail.com           # The Gmail the AI controls

# ─────────────────────────────────────────
# OAuth credentials live in files (not env vars)
# credentials/gmail_credentials.json  ← downloaded from GCP
# credentials/token.json              ← auto-generated on first auth
# ─────────────────────────────────────────
```

---

## 6. Common Mistakes & How to Avoid Them

---

### Mistake 1: Double Slash in Webhook URL

**Symptom:**
```
INFO: 74.125.215.101:0 - "POST //api/webhooks/gmail HTTP/1.1" 404 Not Found
INFO: 74.125.215.96:0  - "POST //api/webhooks/gmail HTTP/1.1" 404 Not Found
```
Logs keep repeating endlessly because Google Pub/Sub retries failed
notifications indefinitely.

**Root Cause:**
When creating the Pub/Sub subscription, you accidentally typed
`https://your-ngrok-url.ngrok-free.app//api/webhooks/gmail`
(double slash before "api").

**Fix:**
1. Go to GCP Console → Pub/Sub → Subscriptions → `gmail-notifications-sub`
2. Click Edit
3. Change the endpoint URL to use a **single slash**:
   `https://your-ngrok-url.ngrok-free.app/api/webhooks/gmail`
4. Click Update

**Prevention:**
Always double-check the URL when creating or updating the Pub/Sub
subscription. Copy-paste the ngrok URL and then manually type `/api/webhooks/gmail`.

---

### Mistake 2: OAuth "Access Blocked" Error

**Symptom:**
```
Error 403: access_denied
taskvault-support has not completed the Google verification process.
```

**Root Cause:**
Your Gmail account is not registered as a "test user" in the OAuth
consent screen. Google blocks all unregistered accounts from using
unverified apps.

**Fix:**
1. Go to GCP Console → APIs & Services → OAuth consent screen
2. Scroll down to the **"Test users"** section
3. Click **"+ ADD USERS"**
4. Add your Gmail address (e.g., `ibad0352@gmail.com`)
5. Click **Save**
6. Run `python scripts/setup_gmail.py` again

**Prevention:**
Add all developer and tester Gmail accounts as test users immediately
after creating the OAuth consent screen. Each person who needs to
authenticate must be on this list.

---

### Mistake 3: Infinite Webhook Flood

**Symptom:**
Server starts and immediately floods with hundreds of log lines:
```
📬 Processing Gmail notification for ibad0352@gmail.com (HID: 1198552)
📩 New email from: mailer-daemon@googlemail.com
📩 New email from: noreply-onlineservices@eand.com
📩 New email from: eand.collection@pactcoll.ae
... (continues for minutes)
```

**Root Cause:**
This is caused by **two separate problems combining:**

1. **Lost historyId:** When the server restarts, `_last_history_id` resets
   to `None`. The Gmail History API then returns ALL events since the
   beginning of the watch, which could be thousands of old emails.

2. **Pub/Sub Backlog Flush:** If your server was previously returning 404
   errors (e.g., due to the double-slash bug), Google Pub/Sub queued up
   all the failed notifications. Once the server starts working, Google
   dumps them all at once.

**Fix:**
Three-layer protection is implemented in `channels/gmail_handler.py`:
```python
# Layer 1: Persist historyId in PostgreSQL
self._last_history_id = await _load_last_history_id()

# Layer 2: Skip if history gap is too large (backlog flush)
if history_id - self._last_history_id > 500:
    logger.info("Jumping to present to skip backlog")
    await _save_last_history_id(history_id)
    return []

# Layer 3: Time filter — only emails from the last 15 minutes
recent_cutoff_ms = now_ms - (15 * 60 * 1000)
if msg_date_ms < recent_cutoff_ms:
    continue
```

**Prevention:**
- ALWAYS run `python scripts/setup_gmail.py` BEFORE starting the server
  for the first time. This stores the current historyId in the DB.
- Never delete the `integration_state` table while the system is running.
- If you must reset, run `setup_gmail.py` again to re-anchor the historyId.

---

### Mistake 4: Too Many Database Connections

**Symptom:**
```
asyncpg.exceptions.TooManyConnectionsError: sorry, too many clients already
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
```

**Root Cause:**
The original code created a **new asyncpg connection pool** for every
single database query. When multiple emails arrive simultaneously,
each triggers multiple queries, which each create their own pool
of 10 connections, instantly overwhelming PostgreSQL's connection limit.

**Fix:**
A global singleton pool is used in `database/queries.py`:
```python
_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"),
            min_size=2,
            max_size=10,
        )
    return _pool
```

The same pool instance is reused for all queries throughout the entire
application lifetime.

**Prevention:**
Never call `asyncpg.create_pool()` inside a request handler or database
query function directly. Always use a singleton/module-level pool
that is initialized once and shared everywhere.

---

### Mistake 5: Reply Loop (AI Replies to Itself)

**Symptom:**
The AI sends a reply → Gmail triggers a new Pub/Sub notification for the
sent message → AI processes the sent message → AI sends another reply →
infinite loop, sending dozens of emails.

**Root Cause:**
The Pub/Sub watch fires for ALL changes to the inbox, including
messages you send. Without filtering, the system tries to reply
to its own outgoing emails.

**Fix — Two layers in `api/webhooks.py`:**
```python
# Layer 1: Skip SENT label in gmail_handler.py
if 'SENT' in msg_meta.get('labelIds', []):
    continue

# Layer 2: Skip emails from our own address in webhooks.py
OWN_EMAIL = os.getenv("GMAIL_ADDRESS", "ibad0352@gmail.com").lower()

sender = email_msg["customer_email"].lower()
if sender == OWN_EMAIL:
    logger.info(f"🔁 Skipping email from self ({sender})")
    continue
```

**Prevention:**
Always add `GMAIL_ADDRESS` to your `.env` file and use it as a
filter. Also always check for the `SENT` label in the Gmail history
records before fetching the full message content.

---

### Mistake 6: Tool Name Hallucination

**Symptom:**
```
agents.exceptions.ModelBehaviorError: Tool create_ticket_ide not found in agent TaskVault Success FTE
```

**Root Cause:**
Certain LLMs (especially smaller, fine-tuned, or "proxy" models) add
`_ide` or other suffixes to tool names. This is caused by the model
being fine-tuned on data where IDE tool names had these suffixes.
The OpenAI Agents SDK is strict — if the model calls a tool that does
not exist, it raises a hard error.

**Fix:**
Use a model that is known to follow tool definitions faithfully:
- ✅ `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter)
- ✅ `qwen/qwen3.6-plus:free` (OpenRouter)
- ❌ Avoid custom proxy models or very small models for tool-calling tasks

**Prevention:**
Before using any new LLM model with the OpenAI Agents SDK, test it
with a simple `test_tool` function that has a unique name. If the
model calls it with the correct name, it is safe to use for production.
Use `agent/test-agent.py` for this purpose.

---

### Mistake 7: Free LLM Rate Limits

**Symptom:**
```
openai.RateLimitError: Error code: 429
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
limit: 5 requests per minute
```

**Root Cause:**
Free-tier APIs have very low rate limits. Gemini free tier allows only
5 requests per minute. When an email triggers an agent run, the agent
may make 3–4 LLM calls (one per tool call + one for the final response).
If multiple emails arrive close together, the quota is immediately exceeded.

**Fix:**
Switch to OpenRouter which pools multiple model providers and has higher
effective rate limits on free models:

```python
# agent/setupconfig.py
external_client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
model = OpenAIChatCompletionsModel(
    model="meta-llama/llama-3.3-70b-instruct:free",
    openai_client=external_client,
)
```

**Prevention:**
- Use OpenRouter for routing to free models with better quotas.
- Keep the number of tool calls per agent run minimal (3–4 max).
- Add retry logic with exponential backoff for 429 errors.
- For production: upgrade to a paid tier to eliminate rate limits entirely.

---

### Mistake 8: pgvector / JSONB Type Errors

**Symptom:**
```
asyncpg.exceptions.DataError: expected str, got list
asyncpg.exceptions.UniqueViolationError: duplicate key value violates unique constraint
```

**Root Cause — Two separate issues:**

1. **JSONB columns** — asyncpg does not automatically convert Python
   `list` or `dict` to JSONB. You must serialize them first.
2. **pgvector columns** — The Python list of floats from SentenceTransformer
   must be cast to a string in the format `[0.1, 0.2, ...]`.

**Fix:**
```python
import json

# For JSONB columns (e.g., tool_calls, metadata):
tool_calls_json = json.dumps(tool_calls)  # list → JSON string

# For pgvector columns (e.g., embedding):
embedding = embedding_model.encode(text).tolist()
embedding_str = str(embedding)  # [0.1, 0.2, ...] → "[0.1, 0.2, ...]"
```

**Prevention:**
Create a small utility function for each type conversion and always
use it before any database insert. Never pass raw Python lists to asyncpg.

---

### Mistake 9: ngrok URL Changes on Restart

**Symptom:**
Server receives no webhook calls even though everything was working
before. No logs appear when emails arrive.

**Root Cause:**
Free ngrok accounts get a **new random URL** every time ngrok restarts.
The old URL stored in your Pub/Sub subscription endpoint is now dead.

**Fix — Every time you restart ngrok:**
1. Copy the new HTTPS URL from the ngrok terminal output
2. Go to GCP Console → Pub/Sub → Subscriptions → `gmail-notifications-sub`
3. Click **Edit**
4. Update Endpoint URL to:
   `https://NEW-NGROK-URL/api/webhooks/gmail`
5. Click **Update**

**Prevention — Two options:**
- **Option A (Easy):** Sign up for ngrok's paid plan which gives you
  a static domain that never changes.
- **Option B (Free):** Use a static subdomain via `ngrok http 8000 --subdomain=taskvault-dev`
  (requires a paid plan) or deploy to a proper server with a real domain.
- **Option C (Free alternative):** Use **Cloudflare Tunnel** instead of ngrok
  — it gives you a persistent domain for free:
  ```bash
  cloudflared tunnel --url http://localhost:8000
  ```

---

### Mistake 10: Gmail Watch Expires After 7 Days

**Symptom:**
Everything stops working after ~7 days. No more webhook notifications.
No errors — just silence.

**Root Cause:**
Gmail's `users.watch()` method creates a watch that **automatically expires
after 7 days**. Google does not notify you when it expires.

**Fix:**
Re-run the setup script before the 7-day mark:
```bash
python scripts/setup_gmail.py
# Answer 'y' on Step 5
```

**Prevention — Automate the renewal:**
Add a weekly cron job to your server or use a scheduled task:
```bash
# Add to crontab (runs every 6 days at 9 AM)
0 9 */6 * * cd /path/to/project && python scripts/setup_gmail.py --auto-renew
```

Or add a startup check in `api/main.py` lifespan that automatically
renews the watch if it is older than 6 days.

---

## 7. Key Files Reference

| File | Purpose |
|------|---------|
| `credentials/gmail_credentials.json` | OAuth client secrets (downloaded from GCP) |
| `credentials/token.json` | Auto-generated access/refresh token |
| `channels/gmail_auth.py` | OAuth authentication flow handler |
| `channels/gmail_handler.py` | Core Gmail integration: fetch, parse, send, label |
| `api/main.py` | FastAPI application entry point |
| `api/webhooks.py` | Webhook endpoints: `/gmail`, `/whatsapp`, `/web-form` |
| `database/queries.py` | All async PostgreSQL operations + singleton pool |
| `database/schema.sql` | Full CRM schema including `integration_state` table |
| `scripts/setup_gmail.py` | One-time setup + watch activation script |
| `scripts/verify_state_table.py` | Creates and verifies `integration_state` table |
| `.env` | Environment variables (never commit to git) |

---

## 8. Testing Checklist

Use this checklist every time you set up or reset the Gmail integration:

```
PRE-FLIGHT CHECKS
-----------------
[ ] credentials/gmail_credentials.json exists
[ ] credentials/token.json exists (run setup_gmail.py if not)
[ ] DATABASE_URL is correct in .env
[ ] GOOGLE_CLOUD_PROJECT is correct in .env
[ ] GMAIL_ADDRESS matches the authenticated account in .env
[ ] OPENROUTER_API_KEY is valid in .env
[ ] integration_state table exists in PostgreSQL
[ ] ngrok is running and HTTPS URL is copied

GCP CONSOLE CHECKS
------------------
[ ] Gmail API is enabled
[ ] Cloud Pub/Sub API is enabled
[ ] OAuth consent screen has your Gmail as a test user
[ ] Pub/Sub topic "gmail-notifications" exists
[ ] gmail-api-push@system.gserviceaccount.com is Publisher on the topic
[ ] Pub/Sub subscription "gmail-notifications-sub" exists
[ ] Subscription endpoint = https://CURRENT-NGROK-URL/api/webhooks/gmail (single slash)
[ ] Gmail watch is active (run setup_gmail.py → answer 'y' on Step 5)

CONNECTIVITY TEST
-----------------
[ ] Open in browser: https://YOUR-NGROK-URL/api/webhooks/gmail/ping
    Expected: { "status": "ok", "message": "Gmail webhook endpoint is reachable!" }

[ ] Run in terminal:
    curl -X POST http://localhost:8000/api/webhooks/gmail \
      -H "Content-Type: application/json" \
      -d '{"message":{"data":"eyJlbWFpbEFkZHJlc3MiOiJpYmFkMDM1MkBnbWFpbC5jb20iLCJoaXN0b3J5SWQiOiIxMjM0NTYifQ==","messageId":"test"},"subscription":"test"}'
    Expected: { "status": "acknowledged" }

FULL END-TO-END TEST
--------------------
[ ] Start server: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
[ ] Send email from a DIFFERENT account to ibad0352@gmail.com
[ ] Within 5 seconds, server logs show:
    📬 Gmail webhook | pubsubId=... | email=ibad0352@gmail.com
    📧 Processing | from=your-other-email
    👤 Customer ID: ...
    💬 Conversation ID: ...
    🤖 Agent response ready
    ✉️  Reply status: sent
    ✅ Done — email labelled & marked as read
[ ] Check your test email inbox — reply received from TaskVault
[ ] Check ibad0352@gmail.com — original email is:
    - Marked as Read
    - Has label "TaskVault/Processed"
[ ] Check PostgreSQL — new rows in: customers, conversations, messages, tickets
```

---

*Guide written based on real production experience building the TaskVault CRM Digital FTE Factory.*
*Last Updated: 2026-04-09*
