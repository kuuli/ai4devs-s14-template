# Stack LangChain — SoporteBot (FastAPI)

## Dependencias (requirements.txt)

```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.3.0        # o langchain-ollama para modelo local
langgraph>=0.2.0
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.0.0
jira>=3.5.0
python-dotenv>=1.0.0
```

## Modelo LLM

```python
# Opción A — Cloud (por defecto, mismo patrón que vet chatbot)
from langchain_openai import ChatOpenAI
_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

# Opción B — Local Ollama (para práctica sin API key)
from langchain_ollama import ChatOllama
_llm = ChatOllama(model="gemma2:2b", temperature=0)
```

`temperature=0` obligatorio — el agente escribe datos reales en Jira.

## Imports obligatorios en main.py

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
```

## Session store — mismo patrón que vet chatbot

```python
_store: dict[str, InMemoryChatMessageHistory] = {}

def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]
```

## Agent loop — bind_tools + loop manual (patrón vet chatbot)

```python
TOOLS = [jira_search, jira_create, jira_comment, rag_docs]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
MAX_AGENT_ROUNDS = 5

def _run_agent_loop(messages: list) -> tuple[list, str]:
    llm_with_tools = _llm.bind_tools(TOOLS)
    for _ in range(MAX_AGENT_ROUNDS):
        response = llm_with_tools.invoke(messages)
        if not getattr(response, "tool_calls", None):
            return messages + [response], (response.content or "")
        tool_messages = []
        for tc in response.tool_calls:
            name = tc.get("name") or ""
            args = tc.get("args") or {}
            tool_id = tc.get("id", "")
            out = TOOLS_BY_NAME[name].invoke(args) if name in TOOLS_BY_NAME else f"Unknown tool: {name}"
            tool_messages.append(ToolMessage(content=out, tool_call_id=tool_id))
        messages = messages + [response] + tool_messages
    last = messages[-1] if messages else AIMessage(content="")
    return messages, getattr(last, "content", "") or ""

def _agent_loop_runnable(prompt_value) -> str:
    messages = prompt_value.messages if hasattr(prompt_value, "messages") else prompt_value
    _, content = _run_agent_loop(messages)
    return content
```

## Chain con historial (RunnableWithMessageHistory)

```python
_prompt_template = ChatPromptTemplate.from_messages([
    ("system", _load_prompt()),          # cargado desde prompt.md
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

_chain = _prompt_template | RunnableLambda(_agent_loop_runnable)

chat = RunnableWithMessageHistory(
    _chain,
    _get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
```

El system prompt se carga desde `prompt.md` en disco — nunca hardcodeado en main.py.

## Invocación

```python
bot_reply = await chat.ainvoke(
    {"input": user_message},
    config={"configurable": {"session_id": session_id}},
)
```

## Carga del prompt desde archivo

```python
BASE_DIR = Path(__file__).resolve().parent

def _load_prompt() -> str:
    return (BASE_DIR / "prompt.md").read_text(encoding="utf-8")
```

## Prohibiciones

- No usar `create_tool_calling_agent` + `AgentExecutor` — usar `bind_tools` + loop manual (patrón vet chatbot).
- No usar `st.session_state` — no hay Streamlit en este proyecto.
- No hardcodear el system prompt en main.py — siempre desde `prompt.md`.
- No usar `chain.run()` — siempre `chain.invoke()` o `chain.ainvoke()`.
