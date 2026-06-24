"""LLM Provider Factory — llm_provider.py

This module acts as a single switching point between LLM backends. All code that
needs an LLM or embeddings object imports from here rather than directly from
langchain_openai or langchain_ollama. Switching providers therefore requires only
a .env change + server restart — no code changes needed.

Supported providers
-------------------
openai  (default) — ChatOpenAI via the OpenAI API.
                    Requires OPENAI_API_KEY in the environment.
                    Good choice for production: reliable, fast, no local GPU needed.

ollama            — ChatOllama via a locally-running Ollama daemon.
                    Requires Ollama installed and the model pulled:
                      brew install ollama   (macOS)
                      ollama pull gemma2:2b
                    Good choice for development/offline: free, private, no API key.

Environment variables
---------------------
LLM_PROVIDER           "openai" or "ollama" (default: "openai")

-- OpenAI provider --
OPENAI_API_KEY         Required. Your OpenAI secret key (sk-...).
OPENAI_MODEL           Model name (default: "gpt-4o-mini").
OPENAI_EMBEDDING_MODEL Embedding model (default: "text-embedding-3-small").

-- Ollama provider --
OLLAMA_MODEL           Ollama model tag (default: "gemma2:2b").
                       Model size guide:
                         gemma2:2b  — ~1.7 GB,  8 GB RAM,  CPU only, fastest
                         gemma2:9b  — ~5.4 GB, 16 GB RAM, better quality
                         gemma2:27b — ~16 GB,  32 GB RAM, best (GPU recommended)
OLLAMA_BASE_URL        URL of the Ollama daemon (default: "http://localhost:11434").
EMBEDDING_MODEL        HuggingFace sentence-transformers model for local embeddings
                       (default: "sentence-transformers/all-MiniLM-L12-v2").
                       This model runs on CPU — no GPU required.

Why lazy imports?
-----------------
Each provider branch imports its package only when that provider is actually
selected. This means:
  - If you use "openai", langchain_ollama and sentence_transformers are never
    imported, so missing those packages does not cause an ImportError at startup.
  - If you use "ollama", langchain_openai is still imported by main.py for the
    openai error classes — but no ChatOpenAI instance is created, so no API key
    is needed.

Usage in main.py
----------------
    from llm_provider import get_llm, LLM_PROVIDER

    _llm = get_llm()                   # returns the right BaseChatModel
    logger.info("LLM provider: %s", LLM_PROVIDER)

Usage in tools.py (for RAG embeddings)
---------------------------------------
    from llm_provider import get_embeddings

    embeddings = get_embeddings()      # returns the right Embeddings object
"""

import os

# ── Provider selection ────────────────────────────────────────────────────────
# Read once at import time. .lower() makes "OpenAI", "OPENAI", "openai" all work.
# Storing as a module-level constant lets callers inspect it for logging without
# calling get_llm() first.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()


# ── get_llm() ─────────────────────────────────────────────────────────────────

def get_llm():
    """Return the appropriate BaseChatModel for the configured LLM_PROVIDER.

    Returns
    -------
    langchain_core.language_models.BaseChatModel
        ChatOpenAI if LLM_PROVIDER == "openai"
        ChatOllama  if LLM_PROVIDER == "ollama"

    Raises
    ------
    ValueError
        If LLM_PROVIDER is set to an unrecognised value.
    """

    if LLM_PROVIDER == "openai":
        # Lazy import: langchain_openai is only loaded when this branch runs.
        # If someone sets LLM_PROVIDER=ollama they don't need langchain_openai
        # installed (apart from the openai error classes imported separately in
        # main.py for exception handling).
        from langchain_openai import ChatOpenAI  # noqa: PLC0415

        # temperature=0.3 matches the original behaviour in main.py.
        # For tools that write to external systems (Jira) the prompt.md rules
        # enforce determinism at the prompt level, but a small temperature
        # allows more natural phrasing in conversational turns.
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
        )

    if LLM_PROVIDER == "ollama":
        # Lazy import: langchain_ollama is only loaded when this branch runs.
        # Install with: pip install langchain-ollama>=0.2.0
        # The Ollama daemon must be running before the server starts:
        #   ollama serve  (or it auto-starts on macOS after `brew install ollama`)
        from langchain_ollama import ChatOllama  # noqa: PLC0415

        # temperature=0 is required when the LLM controls Jira writes.
        # Local models like Gemma 2 are less instruction-tuned than GPT-4o-mini,
        # so determinism is even more important to avoid hallucinated actions.

        # GEMMA_MODEL selects the Gemma 2 variant to run:
        #   gemma2:2b  — fastest, lowest RAM (8 GB), good for development
        #   gemma2:9b  — balanced quality/speed (16 GB RAM)
        #   gemma2:27b — best quality (32 GB RAM, GPU recommended)
        # Falls back to OLLAMA_MODEL for backward compatibility, then to gemma2:2b.
        model = (
            os.getenv("GEMMA_MODEL")        # preferred: specific Gemma 2 variant
            or os.getenv("OLLAMA_MODEL")    # legacy fallback
            or "gemma2:2b"                  # default: smallest model
        )
        return ChatOllama(
            model=model,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            # System prompt alone is ~3,600 tokens; Ollama defaults to 2048.
            # Without this, the prompt is truncated and history never fits.
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
        )

    # Unknown provider — fail loudly at startup rather than silently at first request.
    raise ValueError(
        f"Unknown LLM_PROVIDER='{LLM_PROVIDER}'. "
        "Supported values: 'openai', 'ollama'.\n"
        "To fix: set LLM_PROVIDER=openai (requires OPENAI_API_KEY) or\n"
        "        set LLM_PROVIDER=ollama (requires Ollama daemon + pip install langchain-ollama)."
    )


# ── get_embeddings() ──────────────────────────────────────────────────────────

def get_embeddings():
    """Return the appropriate Embeddings object for the configured LLM_PROVIDER.

    Used by the RAG pipeline (rag_docs tool in tools.py) to embed documents
    and queries into vector space before similarity search.

    Returns
    -------
    langchain_core.embeddings.Embeddings
        OpenAIEmbeddings       if LLM_PROVIDER == "openai"
        HuggingFaceEmbeddings  if LLM_PROVIDER == "ollama"

    Raises
    ------
    ValueError
        If LLM_PROVIDER is set to an unrecognised value.

    Notes
    -----
    The HuggingFace model is downloaded once and cached in ~/.cache/huggingface
    on first use. Subsequent starts load from cache — no internet needed.
    The all-MiniLM-L12-v2 model is ~120 MB and runs comfortably on CPU.
    """

    if LLM_PROVIDER == "openai":
        # Lazy import: only needed for the openai provider branch.
        from langchain_openai import OpenAIEmbeddings  # noqa: PLC0415

        # text-embedding-3-small is OpenAI's most cost-efficient embedding model
        # as of 2024. It outperforms the older text-embedding-ada-002 on most
        # benchmarks at a lower price per token.
        return OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        )

    if LLM_PROVIDER == "ollama":
        # Lazy import: sentence-transformers is only loaded for the ollama branch.
        # Install with: pip install sentence-transformers>=3.0.0
        # This model runs entirely on CPU — no GPU or API key required.
        from langchain_community.embeddings import HuggingFaceEmbeddings  # noqa: PLC0415

        return HuggingFaceEmbeddings(
            model_name=os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L12-v2",
            ),
        )

    # Mirror the same ValueError from get_llm() for consistency.
    raise ValueError(
        f"Unknown LLM_PROVIDER='{LLM_PROVIDER}'. "
        "Supported values: 'openai', 'ollama'."
    )
