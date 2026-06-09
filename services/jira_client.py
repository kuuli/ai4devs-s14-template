import logging
import os

from jira import JIRA
from jira.exceptions import JIRAError  # noqa: F401 — re-exported for callers

logger = logging.getLogger("soportebot.jira")

JIRA_URL: str = os.getenv("JIRA_URL", "")
JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
JIRA_TOKEN: str = os.getenv("JIRA_TOKEN", "")
JIRA_PROJECT: str = os.getenv("JIRA_PROJECT", "L1DR")
JIRA_EPIC: str = os.getenv("JIRA_EPIC", "L1DR-53")

_jira: JIRA | None = None


def get_jira() -> JIRA:
    """Return the shared JIRA client, initialising it on first call.

    Raises RuntimeError if required environment variables are missing.
    """
    global _jira
    if _jira is None:
        missing = [
            k
            for k, v in {
                "JIRA_URL": JIRA_URL,
                "JIRA_EMAIL": JIRA_EMAIL,
                "JIRA_TOKEN": JIRA_TOKEN,
            }.items()
            if not v
        ]
        if missing:
            raise RuntimeError(
                f"Variables de entorno Jira faltantes: {', '.join(missing)}"
            )
        _jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_TOKEN))
    return _jira


def search_issues(query: str, max_results: int = 5) -> list:
    """Search for open issues matching *query* in the configured project.

    Uses JQL:  project = {JIRA_PROJECT} AND text ~ "{query}"
               AND statusCategory != Done ORDER BY created DESC

    Raises JIRAError on API failure — callers are responsible for handling it.
    """
    jql = (
        f'project = {JIRA_PROJECT} AND text ~ "{query}" '
        f"AND statusCategory != Done ORDER BY created DESC"
    )
    return get_jira().search_issues(jql, maxResults=max_results)


def create_issue(
    resumen: str,
    descripcion: str,
    tipo: str,
    prioridad: str,
) -> object:
    """Create a Jira issue under the configured project and epic.

    Raises JIRAError on API failure — callers are responsible for handling it.
    """
    fields: dict = {
        "project": {"key": JIRA_PROJECT},
        "summary": resumen[:255],
        "description": descripcion,
        "issuetype": {"name": tipo},
        "priority": {"name": prioridad},
        "parent": {"key": JIRA_EPIC},
    }
    return get_jira().create_issue(fields=fields)


def add_comment(issue_key: str, comentario: str) -> None:
    """Add *comentario* to the issue identified by *issue_key*.

    Raises JIRAError on API failure — callers are responsible for handling it.
    """
    get_jira().add_comment(issue_key, comentario)
