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

## Running tests

```bash
pytest
```
