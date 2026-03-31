---
name: openai-agents-python-sdk-skill
description: Help with the OpenAI Agents Python SDK from https://openai.github.io/openai-agents-python/. Use this skill whenever the user mentions openai-agents, OpenAI Agents SDK, agent orchestration in Python with OpenAI, tools, handoffs, guardrails, sessions, tracing, MCP, streaming, realtime agents, or asks to build, explain, debug, or migrate code using the OpenAI Agents Python SDK — even if they do not know the exact package name.
---

# OpenAI Agents Python SDK Skill

Use this skill to help the user work with the OpenAI Agents Python SDK accurately and practically.

## What this skill should do

When this skill is triggered:

1. Identify what the user needs:
   - concept explanation
   - API usage help
   - code example
   - architecture guidance
   - debugging help
   - migration or comparison guidance
2. Answer using the official OpenAI Agents Python SDK concepts and patterns.
3. Distinguish this SDK from Claude Code skills, Anthropic agent tooling, and unrelated OpenAI SDK features when the names are similar.
4. Prefer concise Python examples that the user can copy into a real project.
5. Avoid inventing undocumented APIs or behavior.

## Working method

Follow this workflow:

1. Clarify the user's goal in SDK terms.
   - Are they building a single agent, multi-agent workflow, tools, approvals, sessions, tracing, MCP integration, or streaming UX?
2. Choose the smallest relevant topic area.
   - Do not dump the whole SDK when the user asked about one feature.
3. Explain the concept briefly.
   - Lead with the practical mental model.
4. Show the recommended pattern.
   - Use current SDK terminology like `Agent`, `Runner`, `run_sync`, `run_streamed`, `@function_tool`, handoffs, sessions, and `RunResult`.
5. If writing code, keep examples realistic and composable.
   - Include imports.
   - Keep examples short unless the user asked for a full implementation.
6. If the user is choosing between two SDK features, explain the tradeoff.
   - Example: handoffs vs agents-as-tools, sessions vs manual history, streaming vs sync runs.

## Topic map

Read the matching reference file as needed:

- `references/core-concepts.md`
  - Use for installation, setup, mental models, core APIs, sessions, results, guardrails, tracing, MCP, streaming, realtime, and voice.
- `references/patterns-and-examples.md`
  - Use for practical coding patterns, starter examples, orchestration patterns, and common "how do I" requests.

## Response guidelines

- Prefer the official docs as the source of truth.
- Be explicit when something is a high-level concept versus a concrete API.
- If the user asks for code, provide Python unless they asked for something else.
- If the user provides existing code, adapt to their code instead of rewriting everything from scratch.
- If an answer depends on app architecture, explain the decision criteria instead of pretending there is one universal best choice.
- If a feature area is advanced or situational, say when it is worth using and when it is unnecessary.

## Common request patterns

This skill should be especially useful for requests like:

- "show me a hello world with openai-agents"
- "how do tools work in the OpenAI Agents Python SDK?"
- "should I use handoffs or agents-as-tools?"
- "how do I keep conversation memory across turns?"
- "add tracing and guardrails to this agent"
- "how do I stream partial output from Runner.run_streamed()?"
- "help me integrate an MCP server with an OpenAI agent"
- "convert this Python workflow to the OpenAI Agents SDK"
- "explain RunResult, final_output, and to_input_list()"
- "when should I use realtime or voice features?"

## Output style

- Start with the direct answer.
- Keep explanations compact unless the user asks for depth.
- Use short code snippets for examples.
- Use bullet points for tradeoffs and design choices.
- Mention the exact SDK objects and methods that matter.

## If the request is broad

If the user asks something broad like "teach me the OpenAI Agents SDK," structure the response like this:

1. What the SDK is for
2. The core primitives
3. The usual build path
4. A small working example
5. The next topic they should learn

## If the request is about debugging

When debugging SDK usage:

1. Identify whether the issue is with setup, model execution, tool wiring, orchestration, session state, streaming, or approvals.
2. Point to the most likely API surface involved.
3. Suggest the smallest fix first.
4. Mention tracing when visibility into runs, tools, or handoffs would help.
