# Core concepts

This file is the factual reference for the OpenAI Agents Python SDK.

## Installation and setup

Typical setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai-agents
export OPENAI_API_KEY=sk-...
```

Use this package name and environment variable when giving setup instructions unless the user already has a different environment management approach.

## Mental model

The SDK is a Python framework for building agentic applications around a few main building blocks:

- `Agent`: an LLM configured with instructions, tools, and optional orchestration behavior
- `Runner`: the execution entry point that runs the agent loop
- tools: function tools, hosted tools, local runtime tools, or agents used as tools
- handoffs: a way for one agent to delegate control to another agent
- guardrails: validation and safety checks around inputs, outputs, or tool use
- sessions / conversation state: mechanisms for preserving context across turns
- tracing: built-in observability for runs, tools, handoffs, and related events

## Agent

An `Agent` is the core unit of behavior.

Common configuration ideas:

- `name`
- `instructions`
- `tools`
- `handoffs`
- `output_type` for structured outputs
- optional dynamic instructions or runtime hooks depending on the use case

Useful explanation pattern:

- The agent defines capability and intent.
- The runner executes the loop.
- The result object tells you what happened and what came back.

## Runner

The runner exposes three main execution patterns:

- `Runner.run(...)` for async execution
- `Runner.run_sync(...)` for synchronous execution
- `Runner.run_streamed(...)` for streaming updates

Use these distinctions when helping the user choose an execution path:

- use `run_sync` for small scripts and quick examples
- use `run` in async applications
- use `run_streamed` when the UI needs incremental progress or partial output

## Results and output handling

Runner execution returns a result object such as `RunResult` or a streaming variant.

Common surfaces to mention:

- `final_output` for the final answer
- `new_items` for agent/tool/handoff/approval-related artifacts from the run
- `to_input_list()` when the developer wants a replay-ready next-turn input list
- interruption / approval-related state when human approval is involved

Practical explanation:

- `final_output` is what most developers inspect first.
- `to_input_list()` is useful when manually carrying context across turns.
- streaming runs expose stream events and are not complete until the stream finishes.

## Sessions and memory

The SDK supports several ways to preserve conversation state:

### 1. Manual history
Use result helpers like `to_input_list()` and manage the history yourself.

Best when:
- the app already owns conversation state
- the developer wants explicit control

### 2. SDK-managed sessions
Use sessions to automatically keep conversation history.

Best when:
- building interactive chat flows
- local development or app-managed state makes sense

Session storage styles mentioned in docs include:
- SQLite for local/simple usage
- Redis or SQLAlchemy-backed storage for production-style persistence
- encrypted or compacting session variants for special needs

### 3. OpenAI server-managed continuation
Use server-side conversation linking like `conversation_id` or `previous_response_id`.

Best when:
- the app wants OpenAI-managed continuation
- the design favors server-side conversation chaining instead of local session memory

Important distinction:
- sessions are client/app-managed
- conversation IDs are OpenAI-managed
- they are not the same mechanism and should not be mixed casually

## Tools

The docs describe several tool categories.

### Function tools
Most practical starting point for Python developers.

Key pattern:

```python
from agents import function_tool

@function_tool
async def lookup_customer(customer_id: str) -> str:
    return f"customer: {customer_id}"
```

Function tools are useful because the SDK can derive schemas from signatures and docstrings.

### Hosted OpenAI tools
Examples mentioned in docs include capabilities like:
- web search
- file search
- code interpreter
- image generation
- hosted MCP tools

### Local runtime tools
Examples include shell/computer/apply-patch style tools for local or execution-environment tasks.

### Agents as tools
Useful when a manager agent should retain control while calling specialists.

### Tool search / deferred loading
Useful in larger tool sets where not all tools should be fully loaded immediately.

## Multi-agent orchestration

The docs emphasize two major patterns.

### Handoffs
Use handoffs when a specialist agent should take over and respond directly.

Good fit:
- triage + specialist workflows
- situations where ownership of the conversation should transfer

### Agents as tools
Use agents-as-tools when one orchestrator should remain in charge and call specialists like tools.

Good fit:
- manager/worker designs
- central control over tone, policy, or final response formatting

Useful rule of thumb:
- handoff transfers control
- agent-as-tool keeps control centralized

## Guardrails

Guardrails are checks around inputs, outputs, or tool actions.

Use them to explain:
- validation of incoming requests
- blocking unsafe or malformed inputs
- validating outputs before proceeding
- protecting workflows from expensive or inappropriate tool calls

Practical framing:
- use them when workflow boundaries matter
- use them when bad input/output could waste cost or create side effects
- avoid presenting them as mandatory for every toy example

## Streaming

Streaming support is for incremental updates while a run is still in progress.

Key ideas to explain:
- `Runner.run_streamed()` produces events during execution
- developers may inspect raw token events, higher-level run item events, or agent-update events
- approval and interruption workflows may surface while streaming
- the run completes only when the event iteration finishes

This is especially relevant for chat UIs and progress-heavy workflows.

## MCP

The SDK supports MCP integration so agents can access tools provided by MCP servers.

Important concepts to mention:
- multiple transport styles exist, such as stdio and HTTP-based options
- MCP standardizes how external tools/context are exposed to the model
- developers may filter tools, configure approval policies, and tune strict schema behavior
- caching tool discovery can matter for performance

## Tracing

Tracing is built-in observability for agent runs.

Useful points:
- it can track generations, tools, handoffs, guardrails, and custom events
- it helps debugging and monitoring
- traces can be grouped across a workflow
- sensitive data inclusion can be controlled in config
- custom processors may be used for third-party observability systems

This should be mentioned whenever the user needs to debug complex workflows.

## Realtime and voice

The docs include dedicated realtime and voice features.

Use this high-level guidance:
- these are advanced features for live, low-latency, or speech-driven experiences
- they are not required for ordinary text agent workflows
- mention them when the user asks about audio, live interactions, or realtime control loops

## Common explanation shortcuts

Use these if the user wants a fast overview:

- `Agent` defines behavior
- `Runner` executes behavior
- tools extend capability
- handoffs coordinate specialists
- sessions preserve context
- guardrails enforce boundaries
- tracing explains what happened
