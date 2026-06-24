# Multi-LLM Provider Design

This document describes how to extend the chatbot template to support multiple LLM
providers — **OpenAI / ChatGPT** (cloud, default) and **Gemma 2 via Ollama** (local,
open-source) — with a single codebase and zero code changes when switching between them.

---

## Mental model

Every LangChain-compatible LLM object (`ChatOpenAI`, `ChatOllama`, …) exposes the same
`invoke / ainvoke / bind_tools` interface. The rest of the application — tools, RAG,
system prompt, agent loop, session store — is **provider-agnostic**. The only thing that
changes per provider is:

1. **The chat LLM object** returned by the factory.
2. **The embedding model** used for FAISS / RAG indexing.
3. **The environment variables** required at runtime.

All three are isolated in a single new file: `llm_provider.py`.

---

## Architecture overview

```
.env  →  LLM_PROVIDER=openai | ollama
              │
              ▼
      llm_provider.py
      ┌──────────────────────────────────────────┐
      │  get_llm()  →  ChatOpenAI | ChatOllama   │
      │  get_embeddings()  →  OpenAIEmbeddings   │
      │               or HuggingFaceEmbeddings   │
      └──────────────────────────────────────────┘
              │                     │
              ▼                     ▼
         main.py               tools.py / rag
    (agent loop, chain)    (tool calls, FAISS index)
              │
      ─────────────────────────────────
      │            │           │      │
  prompt.md    TOOLS[]     RAG docs  session store
  (unchanged)  (unchanged) (unchanged) (unchanged)
```

Tools, the system prompt, and the session store are completely untouched by provider
selection. Only `llm_provider.py` is provider-aware.

---

## Provider comparison

| | OpenAI (ChatGPT) | Ollama + Gemma 2 |
|---|---|---|
| **Model IDs** | `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo` | `gemma2:2b`, `gemma2:9b`, `gemma2:27b` |
| **Tool calling** | Native (full JSON schema) | Supported via `langchain-ollama` ≥ 0.2 |
| **Embeddings** | `text-embedding-3-small` / `large` (API) | `sentence-transformers/all-MiniLM-L12-v2` (CPU local) |
| **Internet required** | Yes | No (after first model pull) |
| **Cost** | Pay-per-token | Free (local GPU/CPU) |
| **Privacy** | Data sent to OpenAI | Fully local |
| **Speed** | Fast (cloud) | Depends on hardware |
| **Setup** | `OPENAI_API_KEY` env var | Ollama installed + `ollama pull gemma2:2b` |

---

## File: `llm_provider.py`

New file at the repo root. `main.py` imports `get_llm()` and `get_embeddings()` from here.

```python
"""LLM and embeddings factory.

Controlled by:
  LLM_PROVIDER=openai   (default)  →  ChatOpenAI + OpenAIEmbeddings
  LLM_PROVIDER=ollama              →  ChatOllama + HuggingFaceEmbeddings

Set in .env or as a shell environment variable.
"""

import os
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()


def get_llm() -> BaseChatModel:
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gemma2:2b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
    # default: openai
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )


def get_embeddings() -> Embeddings:
    if LLM_PROVIDER == "ollama":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L12-v2"
            )
        )
    # default: openai
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
```

---

## Changes to `main.py`

Replace the hardcoded `ChatOpenAI` import and instantiation with the factory:

```python
# Before
from langchain_openai import ChatOpenAI
_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.3)

# After
from llm_provider import get_llm
_llm = get_llm()
```

Everything else in `main.py` stays the same — `_llm.bind_tools(TOOLS)` and the agent
loop work identically for both providers.

---

## Changes to RAG (`tools.py` / RAG setup)

Replace the hardcoded embeddings with the factory:

```python
# Before
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

# After
from llm_provider import get_embeddings
embeddings = get_embeddings()
```

> **Important**: the FAISS index is built with a specific embeddings model. If you switch
> `LLM_PROVIDER` (and therefore the embeddings model), delete `./faiss_index/` and let it
> rebuild on next startup. Mixing index files from different embeddings causes silent
> wrong results.

---

## System prompt (`prompt.md`)

No changes needed. The system prompt is provider-agnostic. The LLM reads it the same way
regardless of whether it is ChatGPT or Gemma 2.

However, keep in mind:
- **Gemma 2** (especially `gemma2:2b`) has a smaller context window and may follow complex
  multi-rule prompts less reliably than GPT-4o-mini. Keep the prompt under ~2 000 tokens.
- **Tool calling** works on Gemma 2 via Ollama, but smaller models may call tools less
  reliably. If a specific tool is critical, include a short usage example in the prompt.

---

## Tools (`tools.py`)

No changes needed. LangChain `@tool` decorated functions are provider-agnostic — the same
tool list is passed to `bind_tools()` regardless of which LLM is active.

```python
# tools.py — same for both providers
TOOLS = [jira_search, jira_create, rag_docs]
```

---

## Environment variables

### `.env.example` — full reference

```dotenv
# ── LLM Provider ──────────────────────────────────────────────────────────────
# "openai" (default, cloud) or "ollama" (local Gemma 2)
LLM_PROVIDER=openai

# ── OpenAI (used when LLM_PROVIDER=openai) ───────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ── Ollama / Gemma 2 (used when LLM_PROVIDER=ollama) ─────────────────────────
# Install Ollama: https://ollama.com/download
# Then: ollama pull gemma2:2b
OLLAMA_MODEL=gemma2:2b
OLLAMA_BASE_URL=http://localhost:11434
# CPU-based embeddings — no API key needed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L12-v2
```

Only the variables for the active provider need to be set. Missing variables for the
inactive provider are safely ignored.

---

## Dependencies

### `requirements.txt` — additions

```
# OpenAI provider (already present)
langchain-openai>=0.3.0

# Ollama provider
langchain-ollama>=0.2.0

# Local embeddings (Ollama mode; also works with OpenAI mode as a fallback)
sentence-transformers>=3.0.0
langchain-community>=0.3.0

# RAG vector store
faiss-cpu>=1.8.0
```

All packages can coexist — unused provider packages have no runtime cost.

---

## Ollama setup (Gemma 2 — step-by-step)

```bash
# 1. Install Ollama (macOS)
brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: download installer from https://ollama.com/download

# 2. Start the Ollama daemon (runs on http://localhost:11434)
ollama serve

# 3. Pull the model (one-time download)
ollama pull gemma2:2b      # ~1.7 GB — runs on CPU, 8 GB RAM minimum
# ollama pull gemma2:9b    # ~5.4 GB — better quality, needs 16 GB RAM
# ollama pull gemma2:27b   # ~16 GB  — best quality, needs 32 GB RAM + GPU

# 4. Verify
ollama run gemma2:2b "hello"

# 5. Set in .env
echo "LLM_PROVIDER=ollama" >> .env
echo "OLLAMA_MODEL=gemma2:2b" >> .env

# 6. Start the app
uvicorn main:app --reload
```

---

## Switching providers at runtime

The provider is read once at **startup** from `LLM_PROVIDER`. To switch:

1. Change `LLM_PROVIDER` in `.env` (or as a shell export).
2. If also switching embeddings (openai ↔ ollama), delete `./faiss_index/` to force reindex.
3. Restart the server: `uvicorn main:app --reload`.

There is no hot-reload — the LLM object is built once on import, which keeps the agent
loop simple and avoids per-request overhead.

---

## Embedding strategy by provider

| | OpenAI embeddings | HuggingFace (local) |
|---|---|---|
| **Model** | `text-embedding-3-small` | `all-MiniLM-L12-v2` |
| **Dimensions** | 1 536 | 384 |
| **Quality** | Higher | Good for most use cases |
| **Cost** | ~$0.02 / 1M tokens | Free |
| **Speed** | Fast (API) | Slower on CPU, fast on GPU |
| **Privacy** | Data sent to OpenAI | Fully local |
| **When to use** | Production, best retrieval quality | Local dev, air-gapped, cost-sensitive |

Both produce a `FAISS` index that the `rag_docs` tool queries identically.

---

## Testing with multiple providers

Add a fixture in `conftest.py` to parametrize provider selection:

```python
import pytest

@pytest.fixture(params=["openai", "ollama"])
def provider(request, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", request.param)
    return request.param
```

For CI/CD:
- Run `LLM_PROVIDER=openai` tests with a mocked `ChatOpenAI` (already done).
- Skip `LLM_PROVIDER=ollama` tests in CI unless Ollama is available:
  ```python
  ollama_available = pytest.mark.skipif(
      not _ollama_reachable(), reason="Ollama not running"
  )
  ```

---

## Decision guide — which provider to use

```
Starting a new project?
  → LLM_PROVIDER=openai (easiest, best tool calling, no extra setup)

Local development without internet?
  → LLM_PROVIDER=ollama + gemma2:2b

Privacy / data residency requirement?
  → LLM_PROVIDER=ollama + gemma2:9b or 27b

Production, latency-sensitive?
  → LLM_PROVIDER=openai + gpt-4o-mini

Production, cost-sensitive + own GPU server?
  → LLM_PROVIDER=ollama + gemma2:27b
```

---

## File checklist

| File | Change |
|------|--------|
| `llm_provider.py` | **New** — factory for LLM and embeddings |
| `main.py` | Replace `ChatOpenAI(...)` with `get_llm()` |
| `tools.py` (RAG section) | Replace hardcoded embeddings with `get_embeddings()` |
| `requirements.txt` | Add `langchain-ollama`, `sentence-transformers`, `faiss-cpu` |
| `.env.example` | Add `LLM_PROVIDER`, `OLLAMA_*`, `EMBEDDING_MODEL` vars |
| `docs/llm-provider-design.md` | This file |
| `.gitignore` | Ensure `faiss_index/` is listed |
