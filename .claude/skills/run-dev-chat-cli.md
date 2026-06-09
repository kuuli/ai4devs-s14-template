# Skill: Ejecutar Chat de Soporte en Consola

Inicia una sesión de chat interactiva en la terminal para interactuar con el agente
LangChain y evaluar su comportamiento conversacional de extremo a extremo.

## Propósito

Probar manualmente el flujo completo: recopilación de información, decisiones del agente,
confirmación del ticket y llamada a Jira — sin necesidad de levantar la interfaz web.
Útil para iterar rápido sobre `prompt.md` y las tools.

## Requisitos previos

- Dependencias instaladas (`pip install -r requirements.txt`).
- `.env` con `OPENAI_API_KEY` y variables `JIRA_*` configuradas.
- Script del agente en `scripts/cli_chat.py`.
- Conectividad con Jira verificada (`verify_jira_connection`).

## Comando de ejecución

```bash
python scripts/cli_chat.py
```

## Salida esperada

Un bucle interactivo en consola:

```
SoporteBot iniciado. Escribe 'salir' para terminar.

User: El login no funciona en producción
Bot:  He buscado en Jira... [respuesta del agente]
[Tool llamada: jira_search | args: {'query': 'login producción'}]

User: Sí, crea el ticket
Bot:  Voy a crear este ticket:
      - Proyecto: SUP
      - Tipo: Bug
      ...
      ¿Confirmas?
```

Incluye logs de tool calls en modo `verbose=True` para depuración.

## Cuándo usar esta skill

- Al desarrollar o modificar `prompt.md` para validar cambios de comportamiento.
- Al añadir una nueva tool y verificar que el agente la invoca correctamente.
- Para reproducir un bug de conversación sin necesidad de la UI web.
- Como smoke test rápido antes de lanzar `pytest`.

## Implementación del script

```python
# scripts/cli_chat.py
import os
import logging
from dotenv import load_dotenv
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pathlib import Path

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Importar tools desde el proyecto
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import TOOLS

TOOLS_BY_NAME = {t.name: t for t in TOOLS}
MAX_ROUNDS = 5

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
llm_with_tools = llm.bind_tools(TOOLS)

def run_agent_loop(prompt_value) -> str:
    messages = prompt_value.messages
    for _ in range(MAX_ROUNDS):
        response = llm_with_tools.invoke(messages)
        if not getattr(response, "tool_calls", None):
            return response.content or ""
        tool_msgs = []
        for tc in response.tool_calls:
            name, args, tid = tc.get("name",""), tc.get("args",{}), tc.get("id","")
            print(f"  [Tool: {name} | args: {args}]")
            out = TOOLS_BY_NAME[name].invoke(args) if name in TOOLS_BY_NAME else f"Unknown tool: {name}"
            tool_msgs.append(ToolMessage(content=out, tool_call_id=tid))
        messages = messages + [response] + tool_msgs
    return getattr(messages[-1], "content", "") or ""

prompt = Path("prompt.md").read_text()
template = ChatPromptTemplate.from_messages([
    ("system", prompt),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
chain = RunnableWithMessageHistory(
    template | RunnableLambda(run_agent_loop),
    lambda sid: InMemoryChatMessageHistory(),
    input_messages_key="input",
    history_messages_key="history",
)

SESSION_ID = "cli_dev_session"
print("SoporteBot iniciado. Escribe 'salir' para terminar.\n")
while True:
    user_input = input("User: ").strip()
    if user_input.lower() in ("salir", "exit", "quit"):
        break
    if not user_input:
        continue
    reply = chain.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": SESSION_ID}}
    )
    print(f"Bot:  {reply}\n")
```
