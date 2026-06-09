# Jira Python Library — Tools del agente

## Configuración del cliente

```python
import os
from jira import JIRA

JIRA_URL     = os.getenv("JIRA_URL")     # https://tu-empresa.atlassian.net
JIRA_EMAIL   = os.getenv("JIRA_EMAIL")
JIRA_TOKEN   = os.getenv("JIRA_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "SUP")

jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_TOKEN))
```

Usar la librería `jira` (PyPI: `jira>=3.5`), no raw `requests`. Más idiomático y mejor manejo de errores.

---

## Tool 1: `jira_search`

```python
from langchain.tools import tool

@tool
def jira_search(query: str) -> str:
    """
    Busca issues en Jira usando texto libre o JQL.
    Devuelve clave, título, estado y asignado de los 5 primeros resultados.
    Usa esto SIEMPRE antes de crear un ticket nuevo para evitar duplicados.
    Parámetro: query (str) — descripción del problema o consulta JQL.
    """
    try:
        issues = jira.search_issues(
            f'text ~ "{query}" ORDER BY created DESC',
            maxResults=5
        )
    except Exception as e:
        return f"Error al buscar en Jira: {e}"

    if not issues:
        return "No se encontraron issues relacionados."

    resultado = []
    for i in issues:
        asignado = getattr(i.fields.assignee, "displayName", "Sin asignar") if i.fields.assignee else "Sin asignar"
        resultado.append(
            f"[{i.key}] {i.fields.summary} | Estado: {i.fields.status.name} | Asignado: {asignado}"
        )
    return "\n".join(resultado)
```

---

## Tool 2: `jira_create`

```python
@tool
def jira_create(resumen: str, descripcion: str, tipo: str, prioridad: str) -> str:
    """
    Crea un nuevo issue en Jira en el proyecto configurado.
    IMPORTANTE: llama a jira_search primero para evitar duplicados.
    Solo crear tras confirmación explícita del usuario.

    Parámetros:
        resumen (str): título del ticket (< 255 caracteres)
        descripcion (str): detalle del problema o petición
        tipo (str): Bug | Task | Story | Question
        prioridad (str): Blocker | High | Medium | Low

    Devuelve la clave y URL del issue creado.
    """
    TIPOS_VALIDOS     = {"Bug", "Task", "Story", "Question"}
    PRIORIDADES_VALIDAS = {"Blocker", "High", "Medium", "Low"}

    if tipo not in TIPOS_VALIDOS:
        return f"❌ Tipo inválido: '{tipo}'. Usar: {', '.join(sorted(TIPOS_VALIDOS))}"
    if prioridad not in PRIORIDADES_VALIDAS:
        return f"❌ Prioridad inválida: '{prioridad}'. Usar: {', '.join(sorted(PRIORIDADES_VALIDAS))}"
    if not resumen or len(resumen.strip()) < 5:
        return "❌ El resumen es demasiado corto (mínimo 5 caracteres)."

    try:
        issue = jira.create_issue(fields={
            "project":     {"key": JIRA_PROJECT},
            "summary":     resumen[:255],
            "description": descripcion,
            "issuetype":   {"name": tipo},
            "priority":    {"name": prioridad},
        })
    except Exception as e:
        return f"Error al crear el issue en Jira: {e}"

    return f"✅ Issue creado: {issue.key} — {JIRA_URL}/browse/{issue.key}"
```

---

## Tool 3: `jira_comment`

```python
@tool
def jira_comment(issue_key: str, comentario: str) -> str:
    """
    Añade un comentario a un issue existente en Jira.
    Úsalo cuando el usuario quiera actualizar un ticket ya abierto
    en lugar de crear uno nuevo.

    Parámetros:
        issue_key (str): clave del ticket, ej: 'SUP-42'
        comentario (str): texto del comentario a añadir
    """
    if not issue_key or not comentario.strip():
        return "❌ Se necesitan tanto la clave del ticket como el texto del comentario."

    try:
        jira.add_comment(issue_key, comentario)
    except Exception as e:
        return f"Error al añadir comentario a {issue_key}: {e}"

    return f"✅ Comentario añadido a {issue_key}."
```

---

## Registro de tools

```python
tools = [jira_search, jira_create, jira_comment, rag_docs]
```

El orden no afecta al agente, pero `jira_search` debe aparecer antes de `jira_create`
en el system prompt para reforzar la prioridad semántica.

---

## Mapeo de lenguaje natural a valores válidos

Aplicar antes de llamar a `jira_create`:

| Usuario dice | `tipo` | `prioridad` |
|---|---|---|
| "bug", "error", "fallo", "roto" | `Bug` | — |
| "tarea", "mejora técnica" | `Task` | — |
| "nueva funcionalidad", "feature" | `Story` | — |
| "duda", "pregunta" | `Question` | — |
| "urgente", "crítico", "bloqueante" | — | `Blocker` |
| "importante", "producción" | — | `High` |
| sin especificar | — | `Medium` |
