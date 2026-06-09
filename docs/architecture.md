# Architecture — SoporteBot

Jira support chatbot — AI4Devs 202602 Seniors · Práctica S14

---

## System overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser                                                            │
│  public/index.html                                                  │
│  HTML/CSS/JS vanilla · jQuery · marked.js                           │
│  session_id generated once per tab (Math.random)                    │
└────────────────────┬────────────────────────────────────────────────┘
                     │  POST /askbot  {msg, session_id}
                     │  GET  /
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI  (main.py)                                                 │
│                                                                     │
│  GET  /                      → FileResponse public/index.html       │
│  GET  /public/{file}         → static files (path-traversal guard)  │
│  POST /askbot                → AskBotRequest → chain → AskBotResponse│
│  GET  /api-docs              → Swagger UI                           │
│  GET  /api-docs/redoc        → ReDoc UI                             │
│  GET  /api-docs/openapi.json → raw OpenAPI 3.1.0 schema             │
│                                                                     │
│  app = FastAPI(docs_url="/api-docs", redoc_url="/api-docs/redoc",   │
│               openapi_url="/api-docs/openapi.json")                 │
│  Session store: _store: dict[str, InMemoryChatMessageHistory]       │
└────────────────────┬────────────────────────────────────────────────┘
                     │  RunnableWithMessageHistory
                     │  (injects history per session_id)
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LangChain Agent Loop  (_run_agent_loop)                            │
│                                                                     │
│  ChatPromptTemplate                                                 │
│    system  ← prompt.md (loaded at startup)                          │
│    history ← InMemoryChatMessageHistory                             │
│    human   ← {input}                                                │
│                                                                     │
│  llm.bind_tools(TOOLS) → up to MAX_AGENT_ROUNDS=5 LLM calls        │
│                                                                     │
│  Tools (tools.py):                                                  │
│    jira_search        ─────────────────────────────┐               │
│    create_jira_issue  (after confirmation only)     ├──► JiraClient │
│    jira_comment       ─────────────────────────────┘  (services/)  │
│    rag_docs           ──────────────────────────► ChromaDB         │
└────────────────────┬───────────────────────────┬────────────────────┘
                     │                           │
          ┌──────────▼──────────┐    ┌───────────▼──────────┐
          │  LLM                │    │  ChromaDB             │
          │  ChatOpenAI         │    │  + HuggingFace        │
          │  gpt-4o-mini        │    │  Embeddings           │
          │  temperature=0      │    │  all-MiniLM-L12-v2   │
          │                     │    │  (docs/ indexed)      │
          │  or ChatOllama      │    └──────────────────────┘
          │  gemma2:2b (local)  │
          └─────────────────────┘
```

---

## Conversation flow

```
User message
     │
     ▼
┌─────────────────────────────────┐
│  Guardrail (pre-agent)          │
│  · prompt injection check       │
│  · PII detection                │
│  · scope validation             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Intent classification          │
│                                 │
│  consult ──► jira_search        │
│  technical question ──► rag_docs│
│  create ticket ──► draft flow   │
│  update ticket ──► jira_comment │
│  close/move ──► confirm first   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Draft extraction               │
│  (progressive data collection)  │
│                                 │
│  project_key  ✓/✗               │
│  issue_type   ✓/✗               │
│  summary      ✓/✗               │
│  description  ✓/✗               │
│                                 │
│  If any missing → ask user      │
└────────────┬────────────────────┘
             │  all 4 fields present
             ▼
┌─────────────────────────────────┐
│  jira_search (duplicate check)  │
│                                 │
│  duplicate found                │
│    → inform + offer comment     │
│  no duplicate                   │
│    → continue to confirmation   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Confirmation summary           │
│                                 │
│  Voy a crear este ticket:       │
│  - Proyecto:  {project_key}     │
│  - Tipo:      {issue_type}      │
│  - Resumen:   {summary}         │
│  - Prioridad: {priority}        │
│  - Desc:      {description}     │
│                                 │
│  ¿Confirmas que lo cree?        │
└────────────┬────────────────────┘
             │  explicit "sí"
             ▼
┌─────────────────────────────────┐
│  create_jira_issue              │
│  · validate project_key         │  ← allowlist: config/jira_projects.json
│  · validate issue_type          │
│  · delegate to JiraClient       │
│  · return issue_key + URL       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Guardrail (post-agent)         │
│  · block false success claims   │
│  · verify issue_key present     │
└─────────────────────────────────┘
```

---

## File structure

```
soportebot/
├── main.py                       ← FastAPI, agent loop, session store, endpoints
├── tools.py                      ← @tool definitions; exports TOOLS list
├── prompt.md                     ← System prompt (loaded at runtime)
│
├── services/
│   └── jira_client.py            ← Isolated Jira HTTP client (auth, retries, errors)
│
├── schemas/
│   └── ticket.py                 ← Pydantic v2: TicketDraft, CreateTicketInput, JiraResponse
│
├── guardrails/
│   └── validation.py             ← Pre/post validation, PII, prompt injection, allowlists
│
├── public/
│   └── index.html                ← Chat UI: single-file HTML/CSS/JS
│
├── config/
│   └── jira_projects.json        ← Generated by scripts/sync_projects.py
│
├── scripts/
│   ├── verify_jira.py            ← Validate Jira credentials
│   ├── sync_projects.py          ← Download project metadata to config/
│   └── cli_chat.py               ← Interactive terminal chat for dev testing
│
├── docs/
│   ├── architecture.md           ← This file
│   ├── business-rules.md         ← Domain constraints
│   ├── considerations.md         ← Operational context
│   └── exercise.md               ← Practice S14 specification
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               ← pytest fixtures, mock Jira, clear _store
│   ├── test_main.py              ← endpoint tests, confirmation flow, injection
│   └── test_tools.py             ← tool unit tests, Pydantic validation, error handling
│
├── requirements.txt
├── .env.example
├── CLAUDE.md
└── vercel.json
```

---

## Module responsibilities

| Module | Responsibility | Must NOT |
|--------|---------------|----------|
| `main.py` | FastAPI app, agent loop, session store | Contain business logic or Jira HTTP calls |
| `tools.py` | Tool definitions, input validation | Read credentials from prompts or user input |
| `services/jira_client.py` | All Jira HTTP: auth, retries, error mapping | Be called from chain or controllers directly |
| `schemas/ticket.py` | Pydantic v2 models for drafts and API payloads | Contain tool logic or HTTP calls |
| `guardrails/validation.py` | Pre/post validation, allowlists, PII, injection | Block normal conversation flows |
| `prompt.md` | System prompt (role, rules, classification policy) | Contain secrets or implementation details |
| `public/index.html` | Chat UI, session ID, API call to `/askbot` | Store history or call other endpoints |

---

## Data models

### `TicketDraft` (internal state)

```python
class TicketDraft(BaseModel):
    project_key:  str | None = None
    issue_type:   str | None = None
    summary:      str | None = None
    description:  str | None = None
    priority:     str = "Medium"
    labels:       list[str] = []
    confirmed:    bool = False
```

### `CreateTicketInput` (tool args schema, Pydantic v2)

```python
class CreateTicketInput(BaseModel):
    project_key:  str = Field(..., description="Jira project key, e.g. 'SUP'")
    issue_type:   str = Field(..., pattern="^(Bug|Task|Story|Question|Incident)$")
    summary:      str = Field(..., min_length=5, max_length=255)
    description:  str = Field(..., min_length=10)
    priority:     str = Field(default="Medium", pattern="^(Blocker|High|Medium|Low)$")
```

### `AskBotRequest / AskBotResponse` (FastAPI endpoints)

```python
class AskBotRequest(BaseModel):
    msg:        str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)

class AskBotResponse(BaseModel):
    msg:        str
    session_id: str
```

---

## Tech stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Python | 3.10+ |
| Backend | FastAPI + uvicorn | ≥ 0.115 |
| LLM (cloud) | ChatOpenAI `gpt-4o-mini` | langchain-openai ≥ 0.3 |
| LLM (local) | ChatOllama `gemma2:2b` | langchain-ollama ≥ 0.1 |
| Orchestration | LangChain Core + Community | ≥ 0.3 |
| Flow (advanced) | LangGraph | ≥ 0.2 |
| Jira client | jira (Atlassian Python API) | ≥ 3.5 |
| RAG vector store | ChromaDB | ≥ 0.5 |
| RAG embeddings | HuggingFace all-MiniLM-L12-v2 | sentence-transformers ≥ 3.0 |
| Validation | Pydantic v2 | ≥ 2.0 |
| Frontend | HTML/CSS/JS + jQuery + marked.js | vanilla |
| Tests | pytest | ≥ 8.0 |

---

## Environment variables

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=serviceaccount@yourorg.com
JIRA_TOKEN=your_api_token
JIRA_PROJECT=SUP
```

---

## Security constraints

- **No mutative Jira action without explicit confirmation** — enforced in prompt and guardrails.
- **`jira_search` always before `create_jira_issue`** — enforced in prompt and tool docstrings.
- **All Jira HTTP through `JiraClient`** — tools never build HTTP calls directly.
- **Credentials from env only** — never from prompts, fixtures, or Markdown.
- **Allowlist validation** before any Jira write (`config/jira_projects.json`).
- **No false success** — response never claims ticket created without a real `issue_key` from Jira.
