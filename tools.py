"""LangChain tools for the chatbot.

Define your tools here and add them to the TOOLS list at the bottom.
Each tool becomes available to the agent loop in main.py automatically.

Example
-------
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    '''Search the knowledge base for relevant information.'''
    # Your implementation here
    return f"Results for: {query}"

TOOLS = [search_knowledge_base]
"""

TOOLS = []
