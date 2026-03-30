# TaskVault — Escalation Rules

This document defines when and how customer support tickets should be escalated from the AI agent to a human support team member.

---

## 1. Trigger Keywords (Always Escalate)

If ANY of the following keywords or phrases appear in a customer message (case-insensitive), the ticket MUST be escalated immediately:

### Legal & Compliance
- "lawyer", "attorney", "legal action", "sue", "lawsuit", "court"
- "GDPR", "data breach", "privacy violation", "compliance"
- "subpoena", "regulatory"

### Financial & Billing
- "refund", "money back", "chargeback", "dispute"
- "pricing", "quote", "custom plan", "enterprise pricing", "negotiate"
- "overcharged", "double charged", "unauthorized charge"
- "invoice dispute"

### Account Security
- "hacked", "compromised", "unauthorized access", "breach"
- "someone else logged in", "account takeover"
- "two-factor" (if reporting a lockout)

### Cancellation & Churn Risk
- "cancel", "cancellation", "close my account", "delete my account"
- "switching to [competitor]", "moving to", "looking at alternatives"
- "not worth the money", "too expensive"

### Severity Indicators
- "data loss", "all my data is gone", "lost everything"
- "system down", "entire team can't access", "outage"
- "urgent", "emergency", "critical" (when describing system impact, not task priority)

---

## 2. Sentiment-Based Escalation

### Frustration Signals (Escalate if 2+ detected)
- ALL CAPS messages (more than 50% of the message in caps)
- Excessive punctuation (e.g., "!!!", "???")
- Profanity or hostile language
- Phrases like "this is unacceptable", "worst experience", "terrible service"
- Repeated contacts about the same issue (3+ times)
- Explicit threat to leave ("I'm done with TaskVault", "cancelling today")

### Positive Escalation (Route to Account Manager, not Support)
- Enterprise customer expressing strong satisfaction — route to account manager for upsell opportunity
- Customer asking about partnership or reseller opportunities

---

## 3. Topic-Based Routing

### Topics the AI Agent CAN Resolve (Do NOT escalate)
| Topic | Action |
|---|---|
| How-to questions | Answer from product docs |
| Password reset | Guide through self-service reset |
| Feature explanations | Explain from product docs |
| Task/project help | Walk through steps |
| Notification settings | Guide through settings |
| File upload issues (size/format) | Explain limits and workarounds |
| Mobile app troubleshooting | Guide through standard troubleshooting |
| Slow performance | Provide standard optimization tips |
| Integration setup help | Walk through setup steps |
| Deleted task recovery (Trash) | Guide to Trash recovery |
| API authentication help | Explain key setup and header format |
| General product feedback | Log and acknowledge |

### Topics that MUST Be Escalated
| Topic | Route To | Priority |
|---|---|---|
| Billing disputes / refund requests | Billing Team | High |
| Pricing questions / plan negotiations | Sales Team | Medium |
| Account security incidents | Security Team | Critical |
| Data loss (confirmed or suspected) | Engineering On-Call | Critical |
| Platform outage reports | Engineering On-Call | Critical |
| Legal threats or compliance requests | Legal Team | High |
| Enterprise contract questions | Account Manager | Medium |
| Bug reports (confirmed, reproducible) | Engineering Triage | Medium |
| Feature requests (significant) | Product Team | Low |
| Cancellation requests | Retention Team | High |
| SSO / SAML configuration issues | Enterprise Support | Medium |
| Workspace deletion recovery | Support Lead | High |

---

## 4. Priority-Based Escalation Timelines

| Priority | First Response SLA | Escalation If Unresolved |
|---|---|---|
| **Critical** | Immediate (auto-escalate) | Escalate to Engineering On-Call within 5 minutes |
| **High** | 4 hours (Enterprise) / 12 hours (Pro) | Escalate to Team Lead if unresolved after first response |
| **Medium** | 8 hours (Enterprise) / 24 hours (Pro) | Escalate after 48 hours unresolved |
| **Low** | 48 hours | No escalation; log and close after resolution |

---

## 5. Information Required When Escalating

Every escalation MUST include the following structured data:

```
ESCALATION REPORT
─────────────────
Ticket ID:        [ticket_id]
Channel:          [email / whatsapp / web_form]
Customer Name:    [name]
Customer Email:   [email]
Customer Plan:    [Free / Pro / Enterprise]
Priority:         [Critical / High / Medium / Low]
Category:         [billing / technical / security / legal / churn_risk]
─────────────────
Summary:          [2-3 sentence summary of the issue]
Escalation Reason: [Why this requires human intervention]
Customer Sentiment: [calm / frustrated / angry / threatening]
Previous Contacts:  [Number of times customer has contacted about this issue]
─────────────────
Full Conversation: [attached]
```

---

## 6. Channel-Specific Escalation Behavior

### Email (Gmail)
- **Auto-reply on escalation:** "Thank you, [Name]. I've escalated your request to our [Billing/Support/Security] team. You'll hear from a human team member within [SLA time]. Your ticket number is [ID]."
- **CC the escalation team** on the email thread.
- **Do NOT close the ticket** — leave it open and assigned to the escalation target.

### WhatsApp
- **Human handoff keyword:** If a customer types "human", "agent", "real person", or "talk to someone", immediately escalate.
- **Auto-reply on escalation:** "Got it! I'm connecting you with a team member now. They'll respond within [SLA time]. Hang tight! 🙌"
- **Keep the WhatsApp thread active** — the human agent continues in the same conversation.
- **Max AI exchanges before auto-escalation:** If the AI has sent 5 messages without resolving the issue, auto-escalate with a summary.

### Web Form
- **Auto-reply on escalation:** Standard email acknowledgment sent to the customer's email.
- **Ticket is created in the internal CRM** with all form fields + escalation metadata.
- **Category dropdown mapping:** If the customer selected "Billing" or "Account Security" in the form, escalate immediately regardless of message content.

---

## 7. Escalation Routing

| Escalation Type | Routed To | Contact Method |
|---|---|---|
| Billing / Refund | billing-team@taskvault.io | Email + Slack #billing-escalations |
| Sales / Pricing | sales-team@taskvault.io | Email + Slack #sales-inbound |
| Security Incident | security@taskvault.io | Email + PagerDuty alert |
| Data Loss / Outage | oncall@taskvault.io | PagerDuty (immediate) |
| Legal / Compliance | legal@taskvault.io | Email (encrypted) |
| Churn / Cancellation | retention@taskvault.io | Email + Slack #retention-alerts |
| Enterprise Support | enterprise-support@taskvault.io | Email + Dedicated Slack channel |
| Product Feedback | product-feedback@taskvault.io | Email (batched weekly) |
| Bug Reports | engineering-triage@taskvault.io | Email + Jira ticket auto-created |
| General (unresolved) | support-leads@taskvault.io | Email + Slack #support-escalations |

---

## 8. SLA Breach Escalation

If a ticket is about to breach or has breached its SLA:

| Condition | Action |
|---|---|
| 75% of SLA elapsed, no response | Alert assigned agent via Slack |
| SLA breached | Auto-escalate to Team Lead |
| SLA breached + High/Critical priority | Auto-escalate to Support Director |
| SLA breached + Enterprise customer | Notify Account Manager + Support Director |

---

## 9. What NOT to Escalate (Common Mistakes)

The following should NOT be escalated — handle them directly:

| Scenario | Correct Action |
|---|---|
| Customer says "I want to upgrade" | Provide upgrade link and instructions — NOT a sales escalation |
| Customer is mildly frustrated but issue is solvable | Empathize and solve; frustration alone isn't an escalation trigger |
| Customer asks "how much does Pro cost?" | Provide pricing info from docs; only escalate if they want custom/enterprise pricing |
| Customer says "this is a bug" but it's a known how-to issue | Educate politely with the correct steps |
| Customer asks about a feature that doesn't exist | Acknowledge, log as feedback, respond with alternatives |
| Customer says "can I talk to someone?" casually | First ask if you can help; only escalate if they insist |
| Feature request without frustration | Log it, thank the customer, close ticket |
| Customer sends a compliment | Thank them warmly, close ticket, forward to #customer-love Slack channel |
| Password reset request | Guide to self-service; don't escalate to security |
| "My task disappeared" | Guide to Trash recovery; escalate only if task is truly missing from Trash |

---

## 10. Post-Escalation Protocol

After escalating:

1. **Inform the customer** — always tell them what's happening and who will follow up.
2. **Don't ghost** — if the human agent hasn't responded within the SLA, the AI should send a courtesy check-in to the customer.
3. **Log the escalation** — record the escalation reason, timestamp, and target in the ticket metadata.
4. **Learn from it** — if the same type of ticket keeps getting escalated, flag it for product or documentation improvement.
