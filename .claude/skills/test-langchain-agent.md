# Skill: Ejecutar Pruebas de Agente y Herramientas

Ejecuta la suite de pruebas unitarias y de integración para verificar que las tools
de LangChain formatean correctamente las solicitudes a Jira y que el agente sigue
el flujo de confirmación obligatorio.

## Propósito

Garantizar la estabilidad del código tras cambios en `prompt.md`, definición de tools,
schemas Pydantic o lógica de guardrails.

## Requisitos previos

- `pytest` instalado (`pip install -r requirements.txt`).
- Variable `OPENAI_API_KEY` en `.env` (los tests usan mocks — no llaman a la API real).
- Jira mockeado en todos los tests — no se llama a Jira real en CI.
- Tests configurados en `tests/`.

## Comando de ejecución

```bash
# Suite completa
pytest tests/ -v

# Solo tools
pytest tests/test_tools.py -v

# Solo el agente (main)
pytest tests/test_main.py -v

# Un caso específico
pytest tests/test_tools.py::test_create_jira_issue_requires_confirmation -v

# Con cobertura
pytest tests/ --cov=. --cov-report=term-missing
```

## Salida esperada

```
tests/test_tools.py::test_jira_search_returns_results PASSED
tests/test_tools.py::test_create_requires_confirmation PASSED
tests/test_tools.py::test_create_invalid_project_key PASSED
tests/test_main.py::test_askbot_happy_path PASSED
tests/test_main.py::test_askbot_no_ticket_without_confirmation PASSED
...
```

Todos los tests en estado `PASSED`. En caso de fallo, detalle del assert y del
comportamiento obtenido vs esperado.

## Cuándo usar esta skill

- Antes de hacer commit o abrir un PR.
- Tras modificar `prompt.md`, `tools.py`, `schemas/`, o `guardrails/`.
- Para verificar un bug de regresión en el flujo de confirmación.
- En CI/CD como gate obligatorio antes de deploy.

## Casos de prueba mínimos requeridos

Los tests deben cubrir como mínimo:

| Caso | Archivo |
|------|---------|
| Clasificación de intención | `test_tools.py` |
| Extracción de borrador (todos los campos) | `test_tools.py` |
| Validación de campos mínimos obligatorios | `test_tools.py` |
| Confirmación obligatoria antes de crear | `test_main.py` |
| Error 400 de Jira (campo inválido) | `test_tools.py` |
| Error 401/403 (credenciales/permisos) | `test_tools.py` |
| `project_key` no permitido | `test_tools.py` |
| `issue_type` no permitido | `test_tools.py` |
| Detección de duplicado potencial | `test_tools.py` |
| Intento de prompt injection | `test_main.py` |
| Datos sensibles en el input | `test_main.py` |
| Respuesta final sin `issue_key` no puede afirmar éxito | `test_main.py` |

## Estructura de conftest.py

```python
# tests/conftest.py
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app, _store

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clear_session_store():
    _store.clear()
    yield
    _store.clear()

@pytest.fixture
def mock_jira():
    """Mock the Jira client for all tests — never call real Jira in CI."""
    with patch("tools.jira") as mock:
        mock.search_issues.return_value = []
        mock.create_issue.return_value = MagicMock(key="SUP-42")
        mock.add_comment.return_value = None
        yield mock
```

## Ejemplo de test de confirmación obligatoria

```python
# tests/test_main.py
from unittest.mock import patch, MagicMock

def test_no_ticket_created_without_confirmation(client, mock_jira):
    """El agente no debe llamar a jira_create sin confirmación explícita."""
    response = client.post("/askbot", json={
        "msg": "Crea un ticket: el login falla en producción",
        "session_id": "test_session_1"
    })
    assert response.status_code == 200
    # Jira no debe haberse llamado — el agente debe pedir confirmación primero
    mock_jira.create_issue.assert_not_called()
    # La respuesta debe contener la pregunta de confirmación
    assert "confirma" in response.json()["msg"].lower()
```
