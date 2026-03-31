# Patterns and examples

Use this file when the user asks for concrete usage patterns or code.

## 1) Smallest hello world

Use for first-run onboarding.

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant"
)

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```

Why this pattern:
- minimal API surface
- fastest way to verify setup works

## 2) Async run pattern

Use in async apps (FastAPI, async workers, etc.).

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="Be concise.")
    result = await Runner.run(agent, "Summarize event-driven architecture in 3 bullets.")
    print(result.final_output)

asyncio.run(main())
```

Why this pattern:
- aligns with async frameworks
- avoids forcing sync wrappers into async codebases

## 3) Function tool pattern

Use when the user wants an agent to call local Python logic.

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: sunny, 23C"

agent = Agent(
    name="Weather assistant",
    instructions="Use tools when needed.",
    tools=[get_weather],
)

result = Runner.run_sync(agent, "What's the weather in Cairo?")
print(result.final_output)
```

Why this pattern:
- clear demonstration of `@function_tool`
- easy transition from plain Python functions to tool-enabled agents

## 4) Structured output pattern

Use when users need typed/validated results instead of free text.

```python
from pydantic import BaseModel
from agents import Agent, Runner

class Ticket(BaseModel):
    priority: str
    team: str
    summary: str

agent = Agent(
    name="Router",
    instructions="Classify support requests.",
    output_type=Ticket,
)

result = Runner.run_sync(agent, "Payment API returns 500 for enterprise customers")
print(result.final_output)
```

Why this pattern:
- easier downstream automation
- predictable output contracts

## 5) Handoffs (specialist takeover)

Use when a specialist should own the next reply.

```python
from agents import Agent, Runner

billing_agent = Agent(
    name="Billing specialist",
    instructions="Handle billing questions.",
)

support_agent = Agent(
    name="Support triage",
    instructions="Route to the best specialist.",
    handoffs=[billing_agent],
)

result = Runner.run_sync(support_agent, "I was charged twice this month")
print(result.final_output)
```

When to prefer:
- role-specialized teams
- clear ownership transfer

## 6) Agents as tools (manager retains control)

Use when one orchestrator must keep final-response control.

```python
from agents import Agent, Runner

spanish_agent = Agent(name="Spanish", instructions="Translate text to Spanish.")

manager = Agent(
    name="Manager",
    instructions="Use tools to help, then provide final response yourself.",
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate English text to Spanish"
        )
    ],
)

result = Runner.run_sync(manager, "Translate: The release is scheduled for tomorrow.")
print(result.final_output)
```

When to prefer:
- central formatting/policy control
- manager-worker topology

## 7) Session-based multi-turn pattern

Use when users ask for memory across turns.

Pseudo-pattern (conceptual):

1. create/configure a session backend
2. pass session into runner calls
3. avoid manually stitching history every turn

Alternative:
- manual history with `to_input_list()` when explicit control is desired

Decision hint:
- choose sessions for conversational apps
- choose manual history for full custom control

## 8) Streaming pattern

Use when the app must show incremental progress.

Pseudo-pattern (conceptual):

1. call `Runner.run_streamed(...)`
2. iterate stream events
3. render partial output/progress in UI
4. wait until stream completion before treating run as final

Decision hint:
- streaming for interactive UX
- non-streamed for batch scripts and simpler flows

## 9) Guardrails placement pattern

Use when users ask about validation/safety boundaries.

Practical checklist:
- validate user input before expensive model/tool work
- validate agent outputs before downstream side effects
- enforce constraints at boundaries where bad data hurts most

Decision hint:
- keep toy examples light
- add guardrails in production workflows with cost/risk

## 10) Tracing-first debugging pattern

Use when users say "it behaves weirdly" or orchestration is unclear.

Practical flow:
1. enable/check tracing configuration
2. run the problematic scenario
3. inspect generation/tool/handoff timeline
4. isolate where behavior diverges from expectation
5. adjust prompt/tool/handoff design based on observed trace

Why this pattern:
- avoids blind trial-and-error
- makes multi-agent/tool behavior explainable

## 11) MCP integration pattern

Use when users need external tool ecosystems via MCP.

Practical flow:
1. choose transport (stdio/HTTP style supported by server)
2. connect MCP server(s)
3. expose only needed tools (filtering)
4. apply approvals for sensitive actions
5. consider caching tool discovery for latency

Why this pattern:
- keeps tool surface intentional
- improves safety and performance

## 12) Common "how do I" mapping

Use these mappings to answer quickly:

- "How do I get started?" → hello world + setup
- "How do I call Python functions?" → `@function_tool`
- "How do I keep context between turns?" → sessions vs `to_input_list()`
- "How do I orchestrate multiple agents?" → handoffs vs agents-as-tools tradeoff
- "How do I show partial output live?" → `run_streamed` + event iteration
- "How do I debug multi-agent runs?" → tracing workflow
- "How do I control unsafe flows?" → guardrails + approval boundaries
- "How do I use MCP tools?" → transport, filtering, approvals, caching

## 13) Tradeoff answers to reuse

### Handoffs vs agents-as-tools
- Handoffs: transfer control to specialist.
- Agents-as-tools: keep control with orchestrator.

### Sessions vs manual history
- Sessions: easier state management for conversational apps.
- Manual history: maximum control and explicit state handling.

### Streaming vs sync
- Streaming: better UX for progressive responses.
- Sync: simpler for scripts and non-interactive tasks.

### Guardrails depth
- Light for prototypes.
- stronger boundaries for production workflows with cost/side effects.

## 14) Response template for coding help

When giving code help, follow this compact structure:

1. **Recommendation**: one-sentence choice.
2. **Why**: 1-3 bullets.
3. **Code**: minimal runnable snippet.
4. **Next step**: one practical follow-up.

This keeps answers actionable and avoids overwhelming the user.
