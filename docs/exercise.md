Práctica S14 — Chatbot de soporte conectado con Jira
AI4Devs 202602 Seniors · 9 junio 2026

🎯 Objetivo
Construir un agente conversacional de soporte técnico que, partiendo del chatbot con memoria y RAG de S12, añade conexión real con Jira: busca tickets existentes, crea nuevos issues y añade comentarios, todo desde una interfaz Streamlit con Gemma2:2b en local.

🗺️ Arquitectura del sistema
Usuario
  │
  ▼
Streamlit UI
  │
  ▼
LangChain AgentExecutor
  ├── System Prompt (reglas del agente)
  ├── Memoria conversacional (session_state)
  ├── RAG Tool → VectorStore (documentación interna)
  ├── Jira Search Tool → Jira API (buscar issues por JQL)
  ├── Jira Create Tool → Jira API (crear nuevo issue)
  └── Jira Comment Tool → Jira API (añadir comentario)
  │
  ▼
Gemma2:2b via Ollama (local, sin API key)
El agente razona en cada turno qué herramienta usar. No crea un ticket si ya existe uno similar. No actúa sin confirmar con el usuario cuando la acción es destructiva o irreversible.

📋 Contexto de reglas (System Prompt)
Eres SoporteBot, asistente de soporte técnico del equipo de desarrollo.
Tu misión es ayudar al equipo a gestionar incidencias y peticiones en Jira
de forma eficiente y sin ruido.

REGLAS ESTRICTAS:
1. Antes de crear un ticket, busca siempre si ya existe uno similar (usa jira_search).
   Si encuentras uno, infórmalo y pregunta si quiere añadir un comentario en lugar de abrir uno nuevo.
2. Al crear un issue, clasifícalo correctamente:
   - Bug: algo que funcionaba y ha dejado de funcionar.
   - Task: trabajo planificado o mejora técnica.
   - Story: nueva funcionalidad con valor para el usuario.
   - Question: duda o petición de información.
3. Asigna prioridad según impacto:
   - Blocker: impide trabajar a alguien ahora mismo.
   - High: afecta a producción o a un entregable próximo.
   - Medium: importante pero no urgente.
   - Low: mejora o nice-to-have.
4. Nunca cierres, borres ni muevas tickets sin confirmación explícita del usuario.
5. Responde siempre en español. Sé conciso y directo.
6. Si no tienes suficiente información para abrir un ticket, pregunta antes de actuar.

🛠️ Skills / Herramientas del agente
jira_search — Buscar issues
from langchain.tools import tool
from jira import JIRA

jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_TOKEN))

@tool
def jira_search(query: str) -> str:
    """
    Busca issues en Jira usando texto libre o JQL.
    Devuelve clave, título, estado y asignado de los 5 primeros resultados.
    Usa esto SIEMPRE antes de crear un ticket nuevo.
    """
    issues = jira.search_issues(f'text ~ "{query}" ORDER BY created DESC', maxResults=5)
    if not issues:
        return "No se encontraron issues relacionados."
    resultado = []
    for i in issues:
        resultado.append(f"[{i.key}] {i.fields.summary} | Estado: {i.fields.status.name} | Asignado: {getattr(i.fields.assignee, 'displayName', 'Sin asignar')}")
    return "\n".join(resultado)

jira_create — Crear un issue
@tool
def jira_create(resumen: str, descripcion: str, tipo: str, prioridad: str) -> str:
    """
    Crea un nuevo issue en Jira.
    tipo: Bug | Task | Story | Question
    prioridad: Blocker | High | Medium | Low
    Llama a jira_search primero para evitar duplicados.
    """
    issue = jira.create_issue(fields={
        "project": {"key": JIRA_PROJECT},
        "summary": resumen,
        "description": descripcion,
        "issuetype": {"name": tipo},
        "priority": {"name": prioridad},
    })
    return f"Issue creado: {issue.key} — {JIRA_URL}/browse/{issue.key}"

jira_comment — Añadir comentario a un ticket existente
@tool
def jira_comment(issue_key: str, comentario: str) -> str:
    """
    Añade un comentario a un issue existente.
    Úsalo cuando el usuario quiera actualizar un ticket ya abierto.
    """
    jira.add_comment(issue_key, comentario)
    return f"Comentario añadido a {issue_key}."

rag_docs — Buscar en documentación interna
@tool
def rag_docs(pregunta: str) -> str:
    """
    Busca en la documentación técnica interna del equipo (guías, ADRs, READMEs).
    Úsalo cuando el usuario haga una pregunta técnica antes de abrir un ticket.
    Puede que la respuesta ya esté en los docs.
    """
    docs = vectorstore.similarity_search(pregunta, k=3)
    return "\n\n---\n\n".join([d.page_content for d in docs])

🤖 Subagentes (extensión opcional)
Si el equipo quiere ir un paso más allá, el AgentExecutor principal puede delegar en subagentes especializados:
Subagente
Trigger
Responsabilidad
Triage Agent
Siempre al recibir un problema nuevo
Clasifica tipo y prioridad antes de actuar
Search Agent
Antes de cualquier creación
Busca duplicados en Jira y en docs
Create Agent
Cuando triage confirma que no hay duplicado
Crea el ticket con todos los campos correctos
Update Agent
Cuando el usuario menciona un ticket existente
Añade comentarios o actualiza estado

Implementación con langchain.agents usando create_tool_calling_agent por subagente, orquestados desde el agente principal.

🔧 Setup del entorno (Google Colab)
# Celda 0 — Instalar dependencias
!pip install -q jira langchain langchain-community streamlit ollama chromadb

# Variables de entorno (usar Colab Secrets o input())
import os
JIRA_URL    = "https://tu-empresa.atlassian.net"
JIRA_EMAIL  = "tu@email.com"
JIRA_TOKEN  = "tu_api_token"   # https://id.atlassian.com/manage-profile/security/api-tokens
JIRA_PROJECT = "SUP"           # clave del proyecto en Jira

🔄 Flujo completo del agente
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
import streamlit as st

llm = ChatOllama(model="gemma2:2b", temperature=0)

tools = [jira_search, jira_create, jira_comment, rag_docs]

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("¿En qué te ayudo?")
if user_input:
    response = agent_executor.invoke({
        "input": user_input,
        "chat_history": st.session_state.messages,
    })
    st.session_state.messages.append(("human", user_input))
    st.session_state.messages.append(("ai", response["output"]))

🧪 Casos de prueba para la sesión
Probar en orden. Cada caso valida una skill distinta.
#
Input del usuario
Comportamiento esperado
1
"El botón de login no funciona en producción"
Busca en Jira antes de crear. Si no hay duplicado, pregunta confirmación y crea Bug / Blocker.
2
"¿Hay algún ticket abierto sobre el login?"
Llama a jira_search y lista resultados sin crear nada.
3
"Añade al ticket SUP-42 que ya lo estamos revisando"
Llama a jira_comment directamente sin buscar.
4
"¿Cómo configuramos las variables de entorno en este proyecto?"
Llama a rag_docs primero. Solo si no encuentra respuesta sugiere abrir ticket.
5
"Quiero cerrar el ticket SUP-42"
Pide confirmación explícita antes de actuar (regla 4).
6
"Crea un ticket para mejorar el tiempo de carga del dashboard"
Clasifica como Story / Medium, busca duplicados, pide confirmación.


✅ Checklist de entrega del equipo
[ ] El agente responde en español y sigue las reglas del system prompt
[ ] jira_search se invoca siempre antes de jira_create
[ ] jira_create produce un issue visible en el tablero real de Jira
[ ] jira_comment añade el comentario en el ticket correcto
[ ] rag_docs recupera fragmentos relevantes de la documentación
[ ] La memoria mantiene el contexto entre turnos (el bot recuerda el ticket del que se habló antes)
[ ] El subagente de triage clasifica correctamente tipo y prioridad

