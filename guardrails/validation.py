import json
from pathlib import Path

_CONFIG = json.loads(
    (Path(__file__).resolve().parent.parent / "config" / "jira_projects.json").read_text()
)
ALLOWED_PROJECT_KEYS: set[str] = set(_CONFIG["allowed_project_keys"])

TIPOS_VALIDOS: set[str] = {"Bug", "Task", "Story", "Question"}
PRIORIDADES_VALIDAS: set[str] = {"Blocker", "High", "Medium", "Low"}


def validate_project_key(key: str) -> str | None:
    """Return None if valid, error string if not."""
    if key not in ALLOWED_PROJECT_KEYS:
        return (
            f"❌ Proyecto no permitido: '{key}'. "
            f"Proyectos disponibles: {', '.join(sorted(ALLOWED_PROJECT_KEYS))}"
        )
    return None


def validate_tipo(tipo: str) -> str | None:
    """Return None if valid, error string if not."""
    if tipo not in TIPOS_VALIDOS:
        return f"❌ Tipo inválido: '{tipo}'. Usar: {', '.join(sorted(TIPOS_VALIDOS))}"
    return None


def validate_prioridad(prioridad: str) -> str | None:
    """Return None if valid, error string if not."""
    if prioridad not in PRIORIDADES_VALIDAS:
        return (
            f"❌ Prioridad inválida: '{prioridad}'. "
            f"Usar: {', '.join(sorted(PRIORIDADES_VALIDAS))}"
        )
    return None
