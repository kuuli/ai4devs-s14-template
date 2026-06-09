# Índice — SoporteBot

Chatbot de soporte técnico que crea y gestiona tickets en Jira mediante conversación natural.
FastAPI en backend, HTML/JS vanilla en frontend, LangChain con `bind_tools` + agent loop manual.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + uvicorn |
| LLM | ChatOpenAI `gpt-4o-mini` (o ChatOllama `gemma2:2b` en local) |
| Orquestación | LangChain — `bind_tools` + `_run_agent_loop` + `RunnableWithMessageHistory` |
| Estado | `InMemoryChatMessageHistory` por `session_id` |
| Jira | librería `jira` Python ≥ 3.5 |
| RAG | ChromaDB + HuggingFaceEmbeddings |
| Frontend | `public/index.html` — HTML/CSS/JS vanilla (jQuery + marked.js) |
| Flujo avanzado | LangGraph (estado tipado, nodos, confirmación) |
| Validación | Pydantic v2 |

---

## Rules

| Archivo | Contiene |
|---------|----------|
| `01-arquitectura-soportebot.md` | Diagrama, system prompt, flujo de decisión, casos de prueba, checklist |
| `02-langchain-stack.md` | Agent loop con bind_tools, RunnableWithMessageHistory, imports, prompt desde archivo |
| `03-jira-libreria.md` | Cliente jira, tools: `jira_search`, `jira_create`, `jira_comment` |
| `04-rag-tool.md` | ChromaDB, `rag_docs` tool, load-or-reuse, orden de llamada |
| `05-seguridad-y-errores.md` | Credenciales, validación de intención, human-in-the-loop, anti-injection, auditoría |
| `06-arquitectura-archivos.md` | Estructura de ficheros, endpoints FastAPI, modelos Pydantic v2, reglas UI HTML |
| `07-reglas-desarrollo.md` | LangGraph state schema, confirmación obligatoria, @tool vs BaseTool, Pydantic v2 |
| `08-testing-strategy.md` | Pirámide de tests, conftest.py fixtures, 14 casos requeridos, cobertura mínima 80% |

---

## Agents

| Archivo | Rol |
|---------|-----|
| `agents/langchain-developer.md` | Implementación LangChain, FastAPI, tools, RAG, Jira library |
| `agents/product-owner.md` | Requisitos, triage policy, confirmación, 6 casos de aceptación |
| `agents/qa-engineer.md` | Estrategia de tests, cobertura, fixtures, casos de seguridad |

---

## Skills

| Archivo | Comando | Cuándo |
|---------|---------|--------|
| `skills/verify-jira-connection.md` | `python scripts/verify_jira.py` | Antes de cualquier operación Jira |
| `skills/sync-jira-projects.md` | `python scripts/sync_projects.py` | Al configurar o cuando cambian proyectos |
| `skills/run-dev-chat-cli.md` | `python scripts/cli_chat.py` | Iterar sobre prompt.md y tools |
| `skills/test-langchain-agent.md` | `pytest tests/ -v` | Antes de cada commit |
| `skills/lint-and-format.md` | `black . && flake8 . && mypy ...` | Antes de cada commit |

---

## Reglas de oro

> 1. `jira_search` siempre antes de `create_jira_issue`.
> 2. Nunca crear, cerrar ni mover tickets sin confirmación explícita.
> 3. `rag_docs` antes de sugerir abrir ticket ante una pregunta técnica.
> 4. Sin Streamlit — la UI es `public/index.html` servido por FastAPI en `GET /`.
> 5. El system prompt vive en `prompt.md`, nunca hardcodeado en Python.
> 6. No se afirma éxito sin un `issue_key` real de Jira en la respuesta.

---

## Variables de entorno (`.env`)

```
JIRA_URL=https://tu-empresa.atlassian.net
JIRA_EMAIL=tu@email.com
JIRA_TOKEN=tu_api_token
JIRA_PROJECT=SUP
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
