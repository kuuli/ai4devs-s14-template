# Testing Strategy — SoporteBot

## Test pyramid

```
        ┌─────────────────┐
        │  E2E / manual   │  run-dev-chat-cli (CLI chat session)
        ├─────────────────┤
        │  Integration    │  test_main.py (FastAPI TestClient + mock Jira)
        ├─────────────────┤
        │  Unit           │  test_tools.py · test_schemas.py · test_guardrails.py
        └─────────────────┘
```

Unit tests must pass without any network access.
Integration tests mock Jira — never call real Jira in CI.
Manual E2E via `run-dev-chat-cli` before any release.

---

## File structure

```
tests/
├── __init__.py
├── conftest.py          ← fixtures, mock Jira, clear _store, dummy API key
├── test_main.py         ← endpoint tests, confirmation flow, security
├── test_tools.py        ← tool unit tests, JIRAError handling, Pydantic validation
├── test_schemas.py      ← CreateTicketInput, TicketDraft field validation
└── test_guardrails.py   ← allowlist checks, PII detection, injection patterns
```

---

## conftest.py — mandatory fixtures

```python
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
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
    with patch("tools.jira") as mock:
        mock.search_issues.return_value = []
        mock.create_issue.return_value = MagicMock(key="SUP-42")
        mock.add_comment.return_value = None
        yield mock
```

---

## Required coverage — 14 cases

| # | Category | What to assert |
|---|----------|---------------|
| 1 | Intent | `create` intent → `jira_search` called before `create_jira_issue` |
| 2 | Intent | `consult` intent → only `jira_search`, no creation |
| 3 | Draft | All 4 required fields extracted correctly |
| 4 | Validation | Missing `project_key` → agent asks, no API call |
| 5 | Validation | Missing `summary` → agent asks, no API call |
| 6 | Confirmation | `create_jira_issue` not called without explicit "sí" |
| 7 | Jira 400 | Invalid field → user sees which field failed |
| 8 | Jira 401/403 | Auth/permission error → friendly message, no stack trace |
| 9 | Allowlist | Disallowed `project_key` → blocked before API call |
| 10 | Allowlist | Disallowed `issue_type` → blocked before API call |
| 11 | Duplicate | `jira_search` finds match → agent offers `jira_comment` instead |
| 12 | Security | Prompt injection → agent continues following rules, no bypass |
| 13 | Security | Sensitive data in input → not logged, not echoed in response |
| 14 | Integrity | Response without `issue_key` → must not claim ticket was created |

---

## Test rules

- **Assert behaviour, not wording** — `assert "confirma" in reply.lower()` not exact strings.
- **One fixture per external dependency** — `mock_jira` for Jira, separate mock for LLM.
- **Regression test for every bug** — name them `test_regression_<description>`.
- **Schema tests independent of agent** — test `CreateTicketInput` directly with `pytest.raises(ValidationError)`.
- **No `time.sleep()` in tests** — if timing matters, mock `asyncio.sleep`.

---

## Running tests

```bash
pytest tests/ -v                          # full suite
pytest tests/test_tools.py -v             # tools only
pytest tests/ -k "confirmation" -v        # filter by name
pytest tests/ --cov=. --cov-report=term-missing  # with coverage
```

Minimum coverage threshold: **80%** on `tools.py`, `schemas/`, and `guardrails/`.
