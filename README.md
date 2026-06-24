# LangChain Chatbot Template

A ready-to-use template for building chatbots with LangChain + FastAPI. Includes a web UI, session management, a tool-calling agent loop, and optional WhatsApp integration via Meta Cloud API.

## Tech stack

- **FastAPI** — HTTP backend
- **LangChain** — agent loop, tool use, conversation history
- **OpenAI** — LLM (configurable model)
- **Vercel** — serverless deployment

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in OPENAI_API_KEY
uvicorn main:app --reload
```

Open `http://localhost:8000` to use the chat UI.

## Project structure

```
main.py           — FastAPI app, LangChain chain, session management
tools.py          — LangChain tools (add your own here)
prompt.md         — System prompt (edit to change bot behaviour)
public/index.html — Chat web UI
vercel.json       — Vercel deployment config
.env.example      — Environment variable reference
tests/
  conftest.py
  test_main.py
```

## Adding a tool

1. Define it in `tools.py` with `@tool`.
2. Add it to the `TOOLS` list at the bottom of `tools.py`.
3. Describe when to call it in `prompt.md`.

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """What this tool does."""
    return f"result for {param}"

TOOLS = [my_tool]
```

## WhatsApp integration

Set the following env vars and point the Meta webhook to `POST /webhook`:

```
WHATSAPP_VERIFY_TOKEN=your_token
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

## Deployment (Vercel)

```bash
vercel deploy
```

Set `OPENAI_API_KEY` (and optionally `WHATSAPP_*`) in the Vercel project environment variables.

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use (see below) |
| `WHATSAPP_VERIFY_TOKEN` | No | — | Token you define in the Meta Developer Console |
| `WHATSAPP_ACCESS_TOKEN` | No | — | Meta app access token |
| `WHATSAPP_PHONE_NUMBER_ID` | No | — | Phone number ID from Meta Developer Console |

### `OPENAI_MODEL` options

| Model | Context window | Best for | Cost |
|-------|---------------|----------|------|
| `gpt-4o-mini` | 128 k | Default — fast, cheap, good tool-calling | $ |
| `gpt-4o` | 128 k | Better reasoning, longer context | $$ |
| `gpt-4o-2024-11-20` | 128 k | Pinned `gpt-4o` snapshot for reproducibility | $$ |
| `gpt-4-turbo` | 128 k | Previous-gen GPT-4, broad availability | $$$ |
| `o1-mini` | 128 k | Fast reasoning model, lower cost than o1 | $$ |
| `o1` | 200 k | Strongest reasoning, complex multi-step tasks | $$$$ |
| `o3-mini` | 200 k | Latest compact reasoning model | $$ |
| `o3` | 200 k | Latest full reasoning model | $$$$ |

Set it in `.env`:

```dotenv
OPENAI_MODEL=gpt-4o-mini
```

> **Note:** `o1` / `o3` models do not support `temperature` — the app defaults to `temperature=0.3` which is ignored by reasoning models and only applies to `gpt-4*` models.

## Running with Ollama (Gemma 2 — local, free, no API key)

Instead of OpenAI you can run the chatbot entirely on your machine using
[Ollama](https://ollama.com) and Gemma 2. No internet required after setup,
no API costs, no data sent to third parties.

### Step 1 — Install Ollama

```bash
brew install ollama          # macOS
# Linux:  curl -fsSL https://ollama.com/install.sh | sh
# Windows: download installer from https://ollama.com/download
```

### Step 2 — Pull the Gemma 2 model

```bash
ollama pull gemma2:2b        # ~1.7 GB — 8 GB RAM, CPU only, fastest
# ollama pull gemma2:9b      # ~5.4 GB — 16 GB RAM, better quality
# ollama pull gemma2:27b     # ~16 GB  — 32 GB RAM, best (GPU recommended)
```

Wait for the download to finish, then verify:

```bash
ollama list                  # gemma2:2b should appear in the list
```

### Step 3 — Configure `.env`

```dotenv
LLM_PROVIDER=ollama
OLLAMA_MODEL=gemma2:2b
OLLAMA_BASE_URL=http://localhost:11434   # default — only change if Ollama runs elsewhere
```

`OPENAI_API_KEY` is not required when using Ollama.

### Step 4 — Start the server

Make sure the Ollama daemon is running (it starts automatically on macOS after install), then:

```bash
uvicorn main:app --reload
```

Look for this line in the startup logs to confirm Ollama is active:

```
INFO:main:LLM provider: ollama
```

Open `http://localhost:8000` — the chatbot is now running fully local on Gemma 2.

### Switching back to OpenAI

Set `LLM_PROVIDER=openai` in `.env` and restart the server. No code changes needed.

---

## Running tests

```bash
pytest
```
