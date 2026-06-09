import logging

from jira.exceptions import JIRAError
from langchain_core.tools import tool

import services.jira_client as jira_client
from services.jira_client import JIRA_PROJECT, JIRA_URL
from guardrails.validation import validate_tipo, validate_prioridad

logger = logging.getLogger("soportebot.tools")


@tool
def jira_create(
    resumen: str,
    descripcion: str,
    tipo: str = "Task",
    prioridad: str = "Medium",
) -> str:
    """
    Crea un nuevo issue en Jira en el proyecto L1DR bajo el epic L1DR-53.
    SOLO llamar tras confirmación explícita del usuario ("sí").
    tipo: Bug | Task | Story | Question
    prioridad: Blocker | High | Medium | Low
    """
    err = validate_tipo(tipo)
    if err:
        return err

    err = validate_prioridad(prioridad)
    if err:
        return err

    try:
        issue = jira_client.create_issue(
            resumen=resumen,
            descripcion=descripcion,
            tipo=tipo,
            prioridad=prioridad,
        )
    except JIRAError as e:
        if e.status_code == 400:
            return f"❌ Datos inválidos: {e.text}"
        elif e.status_code == 401:
            return "❌ Error de autenticación con Jira. Verifica las credenciales."
        elif e.status_code == 403:
            return f"❌ Sin permisos para crear issues en {JIRA_PROJECT}."
        elif e.status_code == 404:
            return f"❌ El proyecto '{JIRA_PROJECT}' no existe o no es accesible."
        else:
            return f"❌ Error de Jira ({e.status_code}): {e.text}"
    except Exception as e:
        return f"❌ Error inesperado al crear el issue: {e}"

    logger.info(
        "TICKET_CREATED project=%s key=%s type=%s priority=%s",
        JIRA_PROJECT,
        issue.key,
        tipo,
        prioridad,
    )
    return f"✅ Issue creado: {issue.key} — {JIRA_URL}/browse/{issue.key}"


@tool
def jira_comment(issue_key: str, comentario: str) -> str:
    """
    Añade un comentario a un issue existente en Jira.
    Usar cuando el usuario quiera actualizar un ticket ya abierto en lugar de crear uno nuevo.
    Parámetros: issue_key (str) — clave del ticket (ej: L1DR-42), comentario (str) — texto del comentario.
    """
    if not issue_key or not issue_key.strip():
        return "❌ Se necesita la clave del ticket (ej: L1DR-42)."
    if not comentario or not comentario.strip():
        return "❌ El texto del comentario no puede estar vacío."

    try:
        jira_client.add_comment(issue_key.strip(), comentario)
    except JIRAError as e:
        if e.status_code == 401:
            return "❌ Error de autenticación con Jira. Verifica las credenciales."
        elif e.status_code == 403:
            return f"❌ Sin permisos para comentar en {issue_key}."
        elif e.status_code == 404:
            return f"❌ El ticket '{issue_key}' no existe o no es accesible."
        else:
            return f"❌ Error de Jira ({e.status_code}): {e.text}"
    except Exception as e:
        return f"❌ Error inesperado al añadir comentario: {e}"

    logger.info("COMMENT_ADDED issue=%s", issue_key)
    return f"✅ Comentario añadido a {issue_key}."


TOOLS = [jira_create, jira_comment]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
