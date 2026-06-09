# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in OPENAI_API_KEY
```

**Run dev server:**
```bash
uvicorn main:app --reload
```

**Run tests:**
```bash
pytest
pytest tests/test_main.py::TestAskBotHappyPath   # single class
```

## Architecture

The backend is a single-process FastAPI app (`main.py`) that wraps a LangChain agent loop. There is no build step — it runs directly with `uvicorn`.

**Request flow:**
```
POST /askbot
  → RunnableWithMessageHistory        # injects per-session InMemoryChatMessageHistory
  → ChatPromptTemplate (prompt.md)
  → _run_agent_loop()                 # up to MAX_AGENT_ROUNDS=5 LLM calls
      ├── ChatOpenAI (gpt-4o-mini)
      └── tools defined in tools.py
```

**Session state** is kept in the in-memory `_store` dict (`main.py`) keyed by `session_id` supplied by the client. It resets on server restart.

**Static files** — `GET /` and `GET /public/{filename}` serve the chat UI from `public/index.html`. Path traversal is explicitly blocked.

**WhatsApp** — `GET /webhook` and `POST /webhook` handle the Meta Cloud API integration. Set the `WHATSAPP_*` env vars to enable it.

## Key files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, LangChain chain setup, agent loop |
| `tools.py` | LangChain tools — define new tools here and add them to `TOOLS` |
| `prompt.md` | System prompt — edit here to change bot behaviour |
| `public/index.html` | Chat web UI |

## Adding a new tool

1. Define the tool in `tools.py` using the `@tool` decorator.
2. Add it to the `TOOLS` list at the bottom of `tools.py`.
3. Describe when to call it in `prompt.md`.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model name (default: `gpt-4o-mini`) |
| `WHATSAPP_VERIFY_TOKEN` | No | Token you define and set in Meta Developer Console |
| `WHATSAPP_ACCESS_TOKEN` | No | Meta app access token |
| `WHATSAPP_PHONE_NUMBER_ID` | No | Phone number ID from Meta Developer Console |

## Deployment

Deployed to Vercel (serverless Python 3.12). Config lives in `vercel.json`. The app initialises the LLM chain at startup; if the chain fails, `/askbot` returns 503 while `/` and `/public/*` still serve static files.

## Testing

Tests use `unittest.mock.patch` against the LangChain chain — no real API calls. `conftest.py` injects a dummy `OPENAI_API_KEY` and resets the `_store` between tests. Main test file: `tests/test_main.py`.
