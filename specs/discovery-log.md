# Discovery Log — TaskVault Customer Success Digital FTE

**Date:** 2026-03-12
**Phase:** Exploration & Context Analysis
**Data Analyzed:** 60 sample support tickets across 3 channels, company profile, product docs, escalation rules, brand voice guide

---

## 1. Channel Patterns Discovered

### Email (20 tickets: ticket_001 – ticket_020)

| Pattern | Detail |
|---|---|
| **Message Length** | Consistently long (100–300 words). Customers provide background, context, and specific details. |
| **Tone** | Formal to semi-formal. Customers use greetings, sign-offs, and full sentences. |
| **Structure** | Often includes: greeting → problem description → impact statement → account details → sign-off. |
| **Technical Detail** | Customers frequently include plan info, account emails, browser versions, and steps already tried. |
| **Expectations** | Customers expect thorough, structured responses. They want complete solutions in a single reply. |
| **Escalation Rate** | 10 out of 20 (50%) require escalation — highest of all channels. Email attracts more complex/high-stakes issues. |
| **Subject Lines** | Descriptive and specific. Useful for automated routing and priority detection. |

### WhatsApp (20 tickets: ticket_021 – ticket_040)

| Pattern | Detail |
|---|---|
| **Message Length** | Very short (5–50 words typical). Some are single words ("human") or completely empty. |
| **Tone** | Casual, informal. Heavy use of lowercase, abbreviations ("u", "thx", "im"), and missing punctuation. |
| **Structure** | No structure. Stream-of-consciousness. No greetings or sign-offs. |
| **Vagueness** | High. Many messages lack context (e.g., "it's not working", empty message, no project/account info). |
| **Multi-language** | 2 tickets contain mixed languages (French in ticket_024, Spanish in ticket_029). |
| **Emotional Intensity** | More raw. Anger is expressed with ALL CAPS, excessive punctuation, and threats. Positive feedback is bubbly with emojis. |
| **Escalation Rate** | 7 out of 20 (35%). Driven by security concerns, refund requests, outages, and the "human" keyword. |
| **Topic Switching** | Ticket_028 switches from GitHub integration → Slack → task duplication in one message. |
| **Edge Cases** | Empty message (ticket_038), single-word "human" (ticket_027), emoji-heavy positive feedback (ticket_031). |

### Web Form (20 tickets: ticket_041 – ticket_060)

| Pattern | Detail |
|---|---|
| **Message Length** | Medium (50–150 words). More structured than WhatsApp but less verbose than email. |
| **Tone** | Semi-formal. Professional but concise. |
| **Structure** | Often uses numbered questions or bullet points. Subject line provides clear context. |
| **Technical Detail** | Moderate. Customers include relevant details but don't write essays. |
| **Category Awareness** | Customers self-categorize well (subject lines are descriptive, categories match content). |
| **Escalation Rate** | 3 out of 20 (15%) — lowest of all channels. Web form attracts how-to and feature questions. |
| **Cross-Reference** | Tickets 041 and 043 are from the same company (Bluewave) — related issues from different people. |

### Channel Comparison Summary

| Metric | Email | WhatsApp | Web Form |
|---|---|---|---|
| Avg message length | ~200 words | ~25 words | ~100 words |
| Escalation rate | 50% | 35% | 15% |
| Clarification needed | Rarely | Very often | Sometimes |
| Emotional intensity | Medium-High | High (both ends) | Low-Medium |
| Technical detail provided | High | Low | Medium |

---

## 2. Common Issue Categories

### Distribution Across All 60 Tickets

| Category | Count | Percentage |
|---|---|---|
| **Technical** | 26 | 43.3% |
| **General** | 16 | 26.7% |
| **Billing** | 10 | 16.7% |
| **Bug Report** | 5 | 8.3% |
| **Feedback** | 3 | 5.0% |

### Top 5 Most Common Issue Types (by specific topic)

1. **Access & Authentication Issues** (8 tickets) — Login problems, password resets, account lockouts, SSO configuration, 2FA setup. Most common single issue type.

2. **Integration Setup & Troubleshooting** (7 tickets) — Slack disconnection after migration, GitHub OAuth failures, Google Drive setup questions, Zapier capabilities, webhook issues. Integrations are a major pain point.

3. **How-To / Feature Discovery** (7 tickets) — Customers asking how to do things that are already possible (export data, create recurring tasks, use calendar view, add members, bulk move tasks). Signals documentation discoverability issues.

4. **Billing & Subscription Questions** (6 tickets) — Refund requests, double charges, prorated charges confusion, plan comparison, invoice access. Billing questions often carry high emotional weight.

5. **Data Loss & Recovery** (4 tickets) — Missing tasks, deleted workspaces, accidental project deletion. These are always high-urgency and often require escalation.

---

## 3. Escalation Patterns

### Overall Escalation Rate

- **Total escalate:** 20 out of 60 tickets (33.3%)
- **Total resolve:** 40 out of 60 tickets (66.7%)

### Escalation by Channel

| Channel | Escalate | Resolve | Escalation Rate |
|---|---|---|---|
| Email | 10 | 10 | 50.0% |
| WhatsApp | 7 | 13 | 35.0% |
| Web Form | 3 | 17 | 15.0% |

### Most Frequent Escalation Triggers

| Trigger | Count | Tickets |
|---|---|---|
| **Refund / billing dispute** | 5 | 005, 020, 024, 040, 055 |
| **Account security / compromise** | 3 | 018, 032, (+ partial in others) |
| **Legal threat or compliance** | 3 | 008, 015, (GDPR in 008) |
| **Cancellation / churn risk** | 3 | 003, 012, 035 |
| **Data loss / system outage** | 3 | 003, 026, 055 |
| **"Human" keyword (WhatsApp)** | 1 | 027 |
| **Confirmed bug (reproducible)** | 2 | 016, 048 |
| **Enterprise pricing / sales** | 1 | 006 |
| **Repeated contact / SLA breach** | 2 | 015, 035 |

### Escalation Routing Distribution

| Target Team | Count |
|---|---|
| Billing Team | 5 |
| Engineering (On-Call or Triage) | 4 |
| Security Team | 3 |
| Support Lead | 3 |
| Sales Team | 1 |
| Retention Team | 2 |
| Legal / Privacy Team | 2 |

---

## 4. Edge Cases Found

| # | Edge Case | Ticket | Handling Requirement |
|---|---|---|---|
| 1 | **Empty message** | ticket_038 | Must prompt customer to rephrase. Don't close or ignore. |
| 2 | **Extremely vague message** ("it's not working") | ticket_022 | Must ask exactly one clarifying question — not multiple. |
| 3 | **Single-word human handoff** ("human") | ticket_027 | Immediately escalate per WhatsApp channel rules. No questions. |
| 4 | **Mixed languages** (French + English) | ticket_024 | Respond in English but acknowledge the language. Don't correct. |
| 5 | **Mixed languages** (Spanish + English) | ticket_029 | Same as above. Answer in English. |
| 6 | **Customer switching topics mid-message** | ticket_028 | Address all topics systematically. Don't ignore any. |
| 7 | **Legal threat** ("I will sue you") | ticket_015 | Immediate escalation. Don't argue or dismiss. |
| 8 | **Chargeback threat** | ticket_005, ticket_020, ticket_040 | Escalate to Billing. Don't promise refund directly. |
| 9 | **Cross-channel / same company** | ticket_041 + ticket_043 | Both from Bluewave, related issues. Agent should recognize the connection if possible. |
| 10 | **Feature already exists but customer doesn't know** | ticket_039 | Calendar view exists. Don't log as feature request — educate instead. |
| 11 | **Repeated contact with no prior response** | ticket_015, ticket_035 | SLA breach. Highest urgency escalation. Apologize for delay. |
| 12 | **Positive feedback / compliment** | ticket_019, ticket_031 | Don't escalate. Thank warmly. Forward to #customer-love. |
| 13 | **Non-English subject line** | ticket_017 | Subject is in German. Agent must handle gracefully. |
| 14 | **Enterprise customer with data loss** | ticket_003 | Critical severity. Immediate engineering escalation + account manager. |
| 15 | **Prorated billing confusion** | ticket_052 | Requires math explanation. Agent must be able to explain billing logic. |

---

## 5. Questions That Need Clarification

These are open questions discovered during analysis that need answers before building the agent:

### Product & Data Questions

1. **Does TaskVault actually support bulk task selection in the web UI?** Ticket_059 references multi-select, but this isn't confirmed in the product docs. Need to verify.

2. **Is 2FA actually available?** Ticket_060 asks about it. The product docs mention SSO (Enterprise) but don't explicitly mention 2FA for Pro users. Need clarification.

3. **Is dark mode available on web?** Ticket_025 asks. Docs mention mobile dark mode only. Need to confirm web status.

4. **What languages does TaskVault support?** Ticket_017 asks about German. Docs don't mention language/i18n support at all.

### Agent Behavior Questions

5. **Should the AI agent identify itself as an AI?** Must it disclose? Is there a legal or ethical requirement for this in the supported markets?

6. **Should the AI attempt to retain customers who say they want to cancel?** Or should it escalate immediately without any retention effort?

7. **For WhatsApp, should the agent send multiple short messages or one longer one?** Brand voice says "break into multiple short messages" but APIs typically send single messages.

8. **How should the agent handle repeated contacts?** Does it have access to ticket history to know this is the 3rd or 4th contact?

9. **Can the agent access customer plan data?** To answer billing questions accurately, the agent needs to know the customer's plan. Is a CRM lookup available?

10. **What is the agent's operating name/identity?** Should it sign emails as "TaskVault Support" or have a name like "Alex from TaskVault Support"?

### Technical Questions

11. **How will the agent distinguish between channel sources at runtime?** Will there be separate inbound routes (Gmail API, WhatsApp Business API, web form webhook)?

12. **Does the agent need to handle attachments?** Some tickets reference files, screenshots, etc.

13. **What CRM/ticketing system will escalations be routed through?** Does one exist, or are we building from scratch?

---

## 6. Recommendations for Agent Behavior

### Core Behavior Model

1. **Channel-Adaptive Responses:** The agent MUST detect the channel and adjust its tone, length, and formatting accordingly:
   - Email: 150–300 words, formal structure, numbered steps, sign-off
   - WhatsApp: under 300 characters, casual, 1-2 emojis max, break into messages
   - Web Form: 100–200 words, semi-formal, include relevant doc links

2. **Clarification-First for Vague Messages:** On WhatsApp especially, the agent should ask exactly one focused clarifying question before attempting to solve. Never ask 3+ questions at once.

3. **Escalation Confidence Scoring:** Rather than binary escalate/resolve, the agent should maintain a confidence score:
   - **Resolve with high confidence:** Answer directly from product docs
   - **Resolve with medium confidence:** Answer but add "If this doesn't solve it, I'll connect you with a team member"
   - **Escalate:** When trigger keywords, sentiment, or topic rules match

4. **Empathy Before Solution:** Every response to a frustrated customer must start with acknowledgment. The E.A.R. method (Empathize, Acknowledge, Resolve) should be baked into the prompt template.

### Edge Case Handling

5. **Empty Messages:** Respond with a friendly prompt ("Hey! Looks like your message didn't come through. How can I help?"). Don't close the ticket.

6. **Mixed Language:** Detect non-English words. Always respond in English but don't correct the customer's language. If the message is predominantly non-English, acknowledge the language barrier and offer English support.

7. **Topic Switching:** Parse multiple intents from a single message. Address each one in order. Use numbered responses.

8. **Feature Already Exists:** Before logging a feature request, check the product docs to verify the feature doesn't already exist. If it does, educate the customer.

### Safety Rails

9. **Never Promise What You Can't Deliver:**
   - Don't promise refunds — escalate to Billing
   - Don't promise data recovery — escalate to Engineering
   - Don't promise features on the roadmap — acknowledge and log
   - Don't quote custom pricing — escalate to Sales

10. **Escalation is Not Failure:** The agent should be comfortable escalating. A well-crafted escalation with full context is better than a bad AI answer. Target: 65–70% self-resolution rate, with 30–35% clean escalations.

11. **Max AI Turns Before Escalation:** On WhatsApp, if the issue isn't resolved after 5 exchanges, auto-escalate with a summary. On email, if the second response doesn't resolve it, escalate.

### Architecture Recommendations

12. **Knowledge Retrieval:** Use the product-docs.md and escalation-rules.md as the primary knowledge base for RAG (Retrieval-Augmented Generation). Chunk the docs by section for more precise retrieval.

13. **Ticket Context Window:** The agent should have access to the current message AND any prior messages in the same conversation thread. This is critical for WhatsApp multi-turn conversations.

14. **Structured Output:** The agent's internal decision should produce a structured output before generating the customer-facing response:
    ```json
    {
      "intent": "password_reset",
      "channel": "email",
      "sentiment": "frustrated",
      "priority": "high",
      "action": "resolve",
      "confidence": 0.92,
      "escalation_needed": false,
      "response_draft": "..."
    }
    ```

15. **Testing Strategy:** Use the 60 sample tickets as a regression test suite. Each ticket has `expected_action` (resolve/escalate) — run the agent against all 60 and measure accuracy. Target: 95%+ correct action classification.

---

## Summary Statistics

| Metric | Value |
|---|---|
| Total tickets analyzed | 60 |
| Channels covered | 3 (Email, WhatsApp, Web Form) |
| Categories covered | 5 (Technical, General, Billing, Bug Report, Feedback) |
| Overall escalation rate | 33.3% (20/60) |
| Highest escalation channel | Email (50%) |
| Lowest escalation channel | Web Form (15%) |
| Edge cases identified | 15 |
| Open questions | 13 |
| Unique escalation target teams | 7 |
