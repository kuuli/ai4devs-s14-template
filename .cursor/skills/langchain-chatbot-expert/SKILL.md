---
name: langchain-chatbot-expert
description: Guides design and implementation of conversational chatbots with LangChain — chains, memory, tools, and structured flows. Use when building or discussing chatbots, LangChain agents, conversational AI, or when the user mentions LangChain, chat chains, or bot flows.
---

# LangChain Chatbot Expert

Apply this skill when designing or implementing a chatbot with LangChain. Prefer LCEL, clear separation of prompts/tools/chains, and alignment with project business rules.

## When to Use This Skill

- Designing or implementing a chatbot.
- Choosing or wiring LangChain components (chains, memory, tools).
- Defining conversation flow, slot filling, or validation with LangChain.
- Integrating business rules into the bot logic.

## Core Principles

1. **LCEL first** – Compose with `|` (pipe); keep runnables small and composable.
2. **State in the chain** – Pass conversation state through the runnable sequence; avoid global mutable state.
3. **Tools for side effects** – Use tools for external calls (lookup, booking, validation); keep the LLM as the orchestrator.
4. **Structured output** – Prefer Pydantic or JSON schema for slot extraction, intents, or confirmation payloads.
5. **Business rules in code** – Enforce domain rules in tools or validators, not only in prompt text.

## Conversation Architecture

```
User input → Prompt (system + history + current) → LLM → Parse intent/slots
                                                          ↓
                                              [Tool calls: check_x, create_y, …]
                                                          ↓
                                              Validate → Response
```

- **System prompt**: Role, constraints, and high-level instructions.
- **Message history**: Use LangChain's `InMemoryChatMessageHistory` or a custom store; keep a bounded window if context length is limited.
- **Turn flow**: Each turn = format messages → invoke chain → handle tool calls → validate → format reply.

## Slot Filling and Conversation Flow

- **Slots**: Define required fields for the task. In the prompt, list them and ask for one at a time or in small groups.
- **Extraction**: Prefer structured output (Pydantic model) from the LLM for collected slots so you can validate and pass to tools.
- **Validation**: Before calling an action tool, run validators (e.g. date in future, required fields present). Return clear errors so the LLM can ask the user to correct.
- **Confirmation**: Require explicit confirmation before irreversible actions (e.g. "Confirm: [summary]. Reply yes to proceed.").

## Tools Design

- **Narrow tools**: One tool per logical action (e.g. `check_availability`, `create_record`). Describe parameters and return values clearly so the LLM chooses correctly.
- **Idempotency**: Design write tools so duplicate or retry calls do not create duplicate records.
- **Rules in tools**: Enforce domain constraints inside tools; return structured errors when violated so the LLM can relay them to the user.

## Prompt Design

- **Be specific**: Include the assistant's role, what actions it can take, and what it cannot do (out-of-scope requests).
- **Mention rules**: State any hard constraints the assistant must enforce (e.g. operating hours, required fields, forbidden actions).
- **Persona**: Define tone (professional, empathetic, concise) and how to handle missing info (ask one question at a time).

## Error Handling and Guardrails

- **Tool failures**: Catch tool errors and return a short, user-friendly message.
- **Invalid input**: If the user gives invalid data, say what went wrong and what format/options are valid.
- **Hallucination**: Prefer tools for facts (availability, prices, rules). Do not let the LLM invent data; it should call tools and relay results.

## Testing

- **Unit tests**: Test validators and tool logic with fixed inputs.
- **Flow tests**: Run multi-turn scenarios with a mock LLM or canned responses to assert correct tool calls and final state.
- **Regression**: When changing prompts or tools, re-run key flows to ensure behaviour is unchanged.

## Project Context

- **Repo**: See `.cursor/rules/repository.mdc`
- **Architecture**: See `CLAUDE.md` for the request flow and key files.
- **Tools**: Add new tools in `tools.py` and register them in `TOOLS`; the agent loop in `main.py` picks them up automatically.
