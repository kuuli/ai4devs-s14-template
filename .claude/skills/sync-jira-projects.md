# Skill: Sincronizar Metadatos de Proyectos de Jira

Descarga la lista de proyectos y tipos de incidencias (*issue types*) activos en la instancia
de Jira para usarlos como contexto o allowlist de validación en el agente.

## Propósito

Asegurar que el chatbot conozca los `project_key` reales que existen en la organización
para evitar intentar crear tickets en proyectos inexistentes o con tipos de incidencia inválidos.

## Requisitos previos

- Conectividad verificada (ejecutar `verify_jira_connection` primero).
- Script de sincronización en `scripts/sync_projects.py`.
- Directorio `config/` creado en la raíz del proyecto.

## Comando de ejecución

```bash
python scripts/sync_projects.py
```

## Salida esperada

Genera o actualiza `config/jira_projects.json`:

```json
[
  {
    "key": "SUP",
    "name": "Soporte TI",
    "issue_types": ["Bug", "Task", "Story", "Question", "Incident"]
  },
  {
    "key": "DEV",
    "name": "Desarrollo",
    "issue_types": ["Bug", "Task", "Story", "Epic"]
  }
]
```

## Cuándo usar esta skill

- Al configurar el proyecto por primera vez.
- Cuando se añadan nuevos proyectos a la instancia de Jira.
- Cuando `jira_create` devuelva errores 400 por `project_key` o `issue_type` inválido.
- Como paso previo a actualizar las allowlists en `guardrails/validation.py`.

## Implementación del script

```python
# scripts/sync_projects.py
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from jira import JIRA
from jira.exceptions import JIRAError

load_dotenv()

jira = JIRA(
    server=os.getenv("JIRA_URL"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))
)

projects = jira.projects()
result = []

for project in projects:
    try:
        issue_types = jira.issue_types_for_project(project.id)
        result.append({
            "key": project.key,
            "name": project.name,
            "issue_types": [it.name for it in issue_types if not getattr(it, "subtask", False)]
        })
        print(f"  ✅ {project.key}: {project.name}")
    except JIRAError as e:
        print(f"  ⚠️  {project.key}: no se pudieron obtener tipos ({e.status_code})")

output_path = Path("config/jira_projects.json")
output_path.parent.mkdir(exist_ok=True)
output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

print(f"\n✅ {len(result)} proyectos guardados en {output_path}")
```

## Uso del archivo generado en guardrails

```python
# guardrails/validation.py
import json
from pathlib import Path

_projects_cache = None

def load_allowed_projects() -> dict[str, list[str]]:
    global _projects_cache
    if _projects_cache is None:
        data = json.loads(Path("config/jira_projects.json").read_text())
        _projects_cache = {p["key"]: p["issue_types"] for p in data}
    return _projects_cache

def validate_project_and_type(project_key: str, issue_type: str) -> str | None:
    """Returns error message or None if valid."""
    allowed = load_allowed_projects()
    if project_key not in allowed:
        return f"Proyecto '{project_key}' no existe. Proyectos disponibles: {', '.join(allowed)}"
    if issue_type not in allowed[project_key]:
        return f"Tipo '{issue_type}' no válido en {project_key}. Tipos disponibles: {', '.join(allowed[project_key])}"
    return None
```
