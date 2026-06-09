# Reglas de Desarrollo — SoporteBot

## Perfil del asistente de desarrollo

Experto en Python, LangChain (y LangGraph), y la API REST de Jira.
Objetivo: construir y mantener un chatbot de soporte que interactúe con los clientes
para registrar incidencias de forma estructurada.

---

## Stack tecnológico principal

- Python 3.10+
- LangChain Core + LangChain Community ≥ 0.3
- LangGraph ≥ 0.2 (gestión del flujo conversacional con estado)
- Pydantic v2 (validación de esquemas y modelos de herramientas)
- `jira` Python library ≥ 3.5 (Atlassian Python API)

---

## Gestión del estado conversacional (LangGraph)

Usar un esquema de estado explícito para almacenar la información recolectada:

```python
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class SupportState(TypedDict):
    messages: list                    # historial de mensajes
    project_key: Optional[str]        # clave del proyecto Jira
    summary: Optional[str]            # título del ticket
    description: Optional[str]        # descripción del problema
    issue_type: str                   # "Bug" | "Task" | "Story" | "Question"
    confirmed: bool                   # True solo cuando el usuario confirma explícitamente
    ticket_key: Optional[str]         # clave del ticket creado (ej: SUP-42)
```

**No invocar la creación del ticket** hasta que estos 4 campos estén completos y `confirmed=True`:
- `project_key`
- `summary`
- `description`
- `issue_type`

---

## Confirmación obligatoria antes de crear

Antes de llamar a `create_jira_ticket`, el agente SIEMPRE genera este resumen y espera respuesta:

```
¿Deseas que proceda a crear este ticket con la información proporcionada?

📋 Resumen del ticket:
   Proyecto:     {project_key}
   Tipo:         {issue_type}
   Título:       {summary}
   Descripción:  {description}

Responde "sí" para confirmar o "no" para cancelar.
```

`confirmed` se establece a `True` solo cuando el usuario responde afirmativamente.
El agente nunca asume confirmación implícita.

---

## Definición de herramientas (Tools)

Usar `@tool` de LangChain o heredar de `BaseTool`. Los docstrings son la interfaz
que el LLM lee para decidir cuándo invocar la herramienta — deben ser precisos y completos.

### Firma requerida para `create_jira_ticket`

```python
from langchain_core.tools import tool

@tool
def create_jira_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task"
) -> str:
    """
    Crea un ticket en Jira con los datos proporcionados.
    SOLO llamar después de confirmación explícita del usuario.
    Llamar a jira_search primero para evitar duplicados.

    Parámetros:
        project_key (str): clave del proyecto, ej: 'SUP'
        summary (str): título corto del problema (< 255 caracteres)
        description (str): descripción detallada del problema o error
        issue_type (str): Bug | Task | Story | Question (default: Task)

    Devuelve la clave y URL del ticket creado.
    """
    ...
```

### Validación con Pydantic v2 en tools

Para tools con inputs complejos, usar `BaseModel` de Pydantic v2 como esquema:

```python
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class CreateTicketInput(BaseModel):
    project_key: str = Field(..., description="Clave del proyecto Jira, ej: 'SUP'")
    summary: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    issue_type: str = Field(default="Task", pattern="^(Bug|Task|Story|Question)$")

class CreateJiraTicketTool(BaseTool):
    name: str = "create_jira_ticket"
    description: str = "Crea un ticket en Jira. Requiere confirmación previa del usuario."
    args_schema: type[BaseModel] = CreateTicketInput

    def _run(self, project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        ...
```

Usar `BaseTool` + `args_schema` cuando la validación de inputs sea crítica.
Usar `@tool` cuando la tool sea simple y la firma sea suficiente.

---

## Flujo LangGraph (nodos principales)

```python
from langgraph.graph import StateGraph, END

def collect_info_node(state: SupportState) -> SupportState:
    """Recoge información del usuario hasta tener los 4 campos obligatorios."""
    ...

def search_duplicates_node(state: SupportState) -> SupportState:
    """Llama a jira_search. Si hay duplicado, actualiza estado."""
    ...

def confirm_node(state: SupportState) -> SupportState:
    """Muestra resumen y espera confirmación explícita."""
    ...

def create_ticket_node(state: SupportState) -> SupportState:
    """Llama a create_jira_ticket solo si confirmed=True."""
    ...

# Grafo
builder = StateGraph(SupportState)
builder.add_node("collect", collect_info_node)
builder.add_node("search", search_duplicates_node)
builder.add_node("confirm", confirm_node)
builder.add_node("create", create_ticket_node)

builder.set_entry_point("collect")
builder.add_edge("collect", "search")
builder.add_edge("search", "confirm")
builder.add_conditional_edges(
    "confirm",
    lambda s: "create" if s["confirmed"] else END,
)
builder.add_edge("create", END)

graph = builder.compile()
```

---

## Reglas de código

- Pydantic v2 para todos los modelos de request/response en FastAPI y en tools con `BaseTool`.
- No mezclar Pydantic v1 y v2 en el mismo proyecto.
- LangGraph para flujos con estado multi-paso; LCEL simple para cadenas sin bifurcaciones.
- Cada nodo del grafo tiene una única responsabilidad.
- No llamar `create_jira_ticket` desde ningún nodo que no sea `create_ticket_node`.
- `jira_search` se llama siempre en `search_duplicates_node` antes de `confirm_node`.
