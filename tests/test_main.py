"""Test suite for the FastAPI chatbot backend.

Covers:
- GET  /                  — root serves index.html
- GET  /public/{filename} — static file serving with path-traversal protection
- POST /askbot            — chat endpoint with session-scoped history
- Graceful error when chain is unavailable

The LangChain chain is mocked so tests run without an API key.
"""

import ast
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestRootRoute:
    """Root URL must serve the chat UI (index.html)."""

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200


    def test_root_serves_index_html_content(self, client):
        response = client.get("/")
        assert "Chatbot" in response.text or "Asistente" in response.text

    def test_root_content_type_is_html(self, client):
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# GET /public/{filename}
# ---------------------------------------------------------------------------


class TestServePublic:
    def test_serves_existing_file(self, client):
        response = client.get("/public/index.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_returns_404_for_missing_file(self, client):
        response = client.get("/public/nonexistent.txt")
        assert response.status_code == 404

    def test_blocks_path_traversal_parent(self, client):
        response = client.get("/public/../main.py")
        assert response.status_code != 200

    def test_blocks_path_traversal_deep(self, client):
        response = client.get("/public/../../etc/passwd")
        assert response.status_code != 200

    def test_blocks_path_traversal_encoded(self, client):
        response = client.get("/public/..%2Fmain.py")
        assert response.status_code != 200


# ---------------------------------------------------------------------------
# POST /askbot
# ---------------------------------------------------------------------------


class TestAskBotValidation:
    """Validation / error cases — chain is never invoked."""

    def test_missing_msg_returns_422(self, client):
        response = client.post(
            "/askbot",
            json={"session_id": "s1"},
        )
        assert response.status_code == 422

    def test_missing_session_id_returns_422(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "hello"},
        )
        assert response.status_code == 422

    def test_empty_msg_returns_422(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "", "session_id": "s1"},
        )
        assert response.status_code == 422

    def test_empty_session_id_returns_422(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "hello", "session_id": ""},
        )
        assert response.status_code == 422

    def test_whitespace_only_msg_returns_422(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "   ", "session_id": "s1"},
        )
        assert response.status_code == 422

    def test_no_body_returns_error(self, client):
        response = client.post("/askbot")
        assert response.status_code in (400, 422)


class TestAskBotHappyPath:
    """Happy-path tests — the chain is mocked to return canned replies."""

    @patch("main.chat")
    def test_json_body_returns_bot_reply(self, mock_chat, client):
        mock_chat.ainvoke = AsyncMock(return_value="Hello! How can I help you today?")

        response = client.post(
            "/askbot",
            json={"msg": "Hi", "session_id": "s1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["msg"] == "Hello! How can I help you today?"
        assert data["session_id"] == "s1"

    def test_form_encoded_body_returns_422(self, client):
        response = client.post(
            "/askbot",
            content=b"msg=Hi&session_id=s2",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 422

    @patch("main.chat")
    def test_chain_receives_correct_session_config(self, mock_chat, client):
        mock_chat.ainvoke = AsyncMock(return_value="ok")

        client.post("/askbot", json={"msg": "test", "session_id": "abc-123"})

        mock_chat.ainvoke.assert_called_once()
        _, kwargs = mock_chat.ainvoke.call_args
        assert kwargs["config"]["configurable"]["session_id"] == "abc-123"

    @patch("main.chat")
    def test_chain_receives_user_input(self, mock_chat, client):
        mock_chat.ainvoke = AsyncMock(return_value="ok")

        client.post(
            "/askbot",
            json={"msg": "I need to book an appointment", "session_id": "s1"},
        )

        call_args = mock_chat.ainvoke.call_args
        assert call_args[0][0]["input"] == "I need to book an appointment"


class TestSessionPersistence:
    """Session store populates correctly across calls."""

    @patch("main.chat")
    def test_two_calls_same_session_invoke_twice(self, mock_chat, client):
        mock_chat.ainvoke = AsyncMock(side_effect=["First reply", "Second reply"])

        r1 = client.post(
            "/askbot", json={"msg": "hi", "session_id": "persist"}
        )
        r2 = client.post(
            "/askbot", json={"msg": "follow-up", "session_id": "persist"}
        )

        assert r1.json()["msg"] == "First reply"
        assert r2.json()["msg"] == "Second reply"
        assert mock_chat.ainvoke.call_count == 2

        for call in mock_chat.ainvoke.call_args_list:
            _, kw = call
            assert kw["config"]["configurable"]["session_id"] == "persist"

    @patch("main.chat")
    def test_different_sessions_are_independent(self, mock_chat, client):
        mock_chat.ainvoke = AsyncMock(return_value="ok")

        client.post("/askbot", json={"msg": "a", "session_id": "sess-A"})
        client.post("/askbot", json={"msg": "b", "session_id": "sess-B"})

        configs = [
            c[1]["config"]["configurable"]["session_id"]
            for c in mock_chat.ainvoke.call_args_list
        ]
        assert configs == ["sess-A", "sess-B"]


class TestSessionStore:
    """Direct unit tests for the in-memory session store."""

    def test_new_session_creates_history(self):
        from main import _get_session_history

        history = _get_session_history("brand-new")
        assert history is not None
        assert len(history.messages) == 0

    def test_same_id_returns_same_history(self):
        from main import _get_session_history

        h1 = _get_session_history("same-id")
        h2 = _get_session_history("same-id")
        assert h1 is h2


# ---------------------------------------------------------------------------
# No-tools constraint
# ---------------------------------------------------------------------------


class TestNoToolsConstraint:
    """The implementation must not use LangChain tools or AgentExecutor."""

    def test_main_does_not_import_agent_executor(self):
        source = Path(__file__).resolve().parent.parent / "main.py"
        code = source.read_text()
        assert "AgentExecutor" not in code

    def test_main_does_not_define_tools(self):
        source = Path(__file__).resolve().parent.parent / "main.py"
        code = source.read_text()
        assert "@tool" not in code

    def test_main_does_not_import_tool_decorator(self):
        source = Path(__file__).resolve().parent.parent / "main.py"
        tree = ast.parse(source.read_text())
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
        assert "tool" not in imported_names
        assert "AgentExecutor" not in imported_names


# ---------------------------------------------------------------------------
# Graceful error when chain is unavailable
# ---------------------------------------------------------------------------


class TestGracefulChainError:
    """When the LLM chain fails to initialize, /askbot returns 503 instead of crashing."""

    @patch("main.chat", None)
    def test_askbot_returns_503_when_chain_is_none(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "hello", "session_id": "s1"},
        )
        assert response.status_code == 503

    @patch("main.chat", None)
    def test_503_body_contains_descriptive_message(self, client):
        response = client.post(
            "/askbot",
            json={"msg": "hello", "session_id": "s1"},
        )
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 10


# ---------------------------------------------------------------------------
# Vercel configuration
# ---------------------------------------------------------------------------


class TestVercelConfig:
    """vercel.json must exist and have the correct structure."""

    def test_vercel_json_exists(self):
        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        assert vercel_json.is_file()


    def test_vercel_json_has_builds_and_routes(self):
        import json

        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        config = json.loads(vercel_json.read_text())
        assert "builds" in config, "vercel.json must define builds"
        assert "routes" in config, "vercel.json must define routes"

    def test_vercel_json_uses_python_builder(self):
        import json

        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        config = json.loads(vercel_json.read_text())
        builders = [b.get("use", "") for b in config.get("builds", [])]
        assert any("python" in b for b in builders), (
            "vercel.json must use @vercel/python builder"
        )

    def test_vercel_json_routes_askbot(self):
        import json

        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        config = json.loads(vercel_json.read_text())
        route_srcs = [r.get("src", "") for r in config.get("routes", [])]
        assert any("askbot" in s for s in route_srcs), (
            "vercel.json must route /askbot"
        )

    def test_vercel_json_root_rewrite_to_index_html(self):
        import json

        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        config = json.loads(vercel_json.read_text())
        routes = config.get("routes", [])
        root_rewrite = [
            r for r in routes
            if r.get("dest") == "/index.html" or "/index.html" in str(r.get("dest", ""))
        ]
        assert len(root_rewrite) >= 1, (
            "vercel.json must rewrite root (/) to /index.html for CDN static serving"
        )

    def test_vercel_json_no_catch_all_to_main(self):
        import json

        vercel_json = Path(__file__).resolve().parent.parent / "vercel.json"
        config = json.loads(vercel_json.read_text())
        routes = config.get("routes", [])
        catch_all_to_main = [
            r for r in routes
            if "(.*)" in r.get("src", "") and r.get("dest") == "main.py"
        ]
        assert len(catch_all_to_main) == 0, (
            "vercel.json must not use a catch-all route to main.py (static files served by CDN)"
        )
