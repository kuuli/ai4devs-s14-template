"""LangChain tools for the chatbot.

This file is the single place to define all tools available to the agent loop
in main.py. Every function decorated with @tool and added to the TOOLS list is
automatically picked up by the agent at startup — no other file needs changing.

How to add a new tool
---------------------
1. Import @tool from langchain_core.tools (or use BaseTool + args_schema for
   tools that need Pydantic v2 field-level validation on their inputs).
2. Define the function with a complete docstring — the LLM reads the docstring
   to decide when to call the tool, so vague docstrings produce wrong invocations.
3. Catch all exceptions inside the function and return a string error message.
   Tools must never raise — any exception propagates to the agent loop and breaks
   the conversation.
4. Add the function to the TOOLS list at the bottom of this file.

Example — minimal read-only tool
---------------------------------
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    '''Search the knowledge base for relevant information.

    Use this BEFORE creating a Jira ticket to check if the answer is already
    documented. Returns the three most relevant document excerpts.

    Parameters
    ----------
    query : str
        The user's question in natural language.
    '''
    # Your implementation here
    return f"Results for: {query}"

TOOLS = [search_knowledge_base]

How to wire up the RAG tool (rag_docs) with embeddings
-------------------------------------------------------
When implementing the rag_docs tool that searches the FAISS vector store, import
get_embeddings() from llm_provider to get the correct embeddings object for
whichever backend is configured (OpenAI or HuggingFace/local):

    from llm_provider import get_embeddings
    from langchain_community.vectorstores import FAISS

    FAISS_INDEX_PATH = "./faiss_index"
    _embeddings = get_embeddings()   # reads LLM_PROVIDER from env, returns the right object

    if os.path.exists(FAISS_INDEX_PATH):
        _vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, _embeddings, allow_dangerous_deserialization=True
        )
    else:
        # Build index from docs/ on first run, then save for future restarts.
        ...

This pattern ensures that when LLM_PROVIDER=openai the FAISS index uses
OpenAIEmbeddings, and when LLM_PROVIDER=ollama it uses the local HuggingFace
model — with no changes to the tool code itself.

Jira tool note
--------------
Tools that write to Jira (jira_create, jira_comment) must:
  - Call jira_search first (enforced by the system prompt, not by code).
  - Return a string with the created issue key so the agent can confirm success.
  - Catch jira.exceptions.JIRAError explicitly and return a descriptive message.
  - Never log the issue description or user message (PII).
"""

# ── Skeleton: rag_docs tool (not yet implemented) ─────────────────────────────
# Uncomment and flesh out this block when adding RAG support.
#
# import os
# from langchain_core.tools import tool
# from langchain_community.vectorstores import FAISS
# from llm_provider import get_embeddings
#
# FAISS_INDEX_PATH = "./faiss_index"
# _embeddings = get_embeddings()
#
# if os.path.exists(FAISS_INDEX_PATH):
#     _vectorstore = FAISS.load_local(
#         FAISS_INDEX_PATH, _embeddings, allow_dangerous_deserialization=True
#     )
# else:
#     # First run: build index from docs/*.md, chunk, embed, save.
#     from langchain_community.document_loaders import DirectoryLoader, TextLoader
#     from langchain_text_splitters import RecursiveCharacterTextSplitter
#     loader = DirectoryLoader("docs/", glob="**/*.md", loader_cls=TextLoader)
#     docs = loader.load()
#     splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
#     chunks = splitter.split_documents(docs)
#     _vectorstore = FAISS.from_documents(chunks, _embeddings)
#     _vectorstore.save_local(FAISS_INDEX_PATH)
#
# @tool
# def rag_docs(pregunta: str) -> str:
#     """Search the internal technical documentation (guides, ADRs, READMEs).
#
#     Use this when the user asks a technical question BEFORE opening a Jira ticket.
#     If the answer is already in the docs, return it — avoid creating Jira noise.
#
#     Parameters
#     ----------
#     pregunta : str
#         The user's technical question in natural language.
#     """
#     docs = _vectorstore.similarity_search(pregunta, k=3)
#     if not docs:
#         return "No relevant information found in the internal documentation."
#     return "\n\n---\n\n".join(d.page_content for d in docs)

# ── Active tools ──────────────────────────────────────────────────────────────
# Add tool functions to this list to make them available to the agent.
# The order here does not affect which tool the LLM chooses — that is driven
# entirely by the docstrings and the system prompt in prompt.md.
TOOLS = []
