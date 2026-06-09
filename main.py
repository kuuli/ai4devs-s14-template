"""LangChain Chatbot — FastAPI backend.

Single-file FastAPI app with:
- GET  /                   — serves the chat UI (index.html)
- GET  /public/{filename}  — static file serving with path-traversal protection
- POST /askbot             — chat endpoint with session-scoped conversation history
- GET  /webhook            — Meta/WhatsApp webhook verification
- POST /webhook            — receive and reply to incoming WhatsApp messages

Uses a LangChain agent loop with tools defined in tools.py. Max 5 tool-call rounds.
"""

import logging
import os
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

from tools import TOOLS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(
    title="Chatbot API",
    description=(
        "LangChain-powered chatbot with session-scoped conversation history. "
        "Supports a web UI, a REST chat endpoint, and an optional WhatsApp Business integration via Meta Cloud API."
    ),
    version="1.0.0",
    docs_url="/api-docs",
    redoc_url="/api-redoc",
    openapi_url="/api-docs/openapi.json",
    contact={"name": "Kuuli Tech", "email": "jmarco@kuuli.tech"},
    license_info={"name": "MIT"},
)


# ── Prompt ──────────────────────────────────────────────────────────────────


def _load_prompt() -> str:
    raw = (BASE_DIR / "prompt.md").read_text(encoding="utf-8")
    # ChatPromptTemplate treats {x} as template variables. Escape every brace so
    # the markdown examples reach the LLM verbatim, then re-open only {today},
    # which is the single real variable injected at request time.
    escaped = raw.replace("{", "{{").replace("}", "}}")
    return escaped.replace("{{today}}", "{today}")


# ── Session store ───────────────────────────────────────────────────────────

_store: dict[str, InMemoryChatMessageHistory] = {}


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]


# ── Tools and agent loop ───────────────────────────────────────────────────

TOOLS_BY_NAME = {t.name: t for t in TOOLS}
MAX_AGENT_ROUNDS = 5


def _run_agent_loop(messages: list) -> tuple[list, str]:
    """Run LLM with tool-calling; handle tool_calls and return (updated_messages, final_content)."""
    llm_with_tools = _llm_with_tools
    for _ in range(MAX_AGENT_ROUNDS):
        response = llm_with_tools.invoke(messages)
        if not getattr(response, "tool_calls", None):
            return messages + [response], (response.content or "")
        tool_messages = []
        for tc in response.tool_calls:
            name = tc.get("name") or ""
            args = tc.get("args") or {}
            tool_id = tc.get("id", "")
            if name in TOOLS_BY_NAME:
                logger.info("Tool llamada: %s | args: %s", name, args)
                try:
                    out = TOOLS_BY_NAME[name].invoke(args)
                except Exception as e:
                    out = str(e)
            else:
                out = f"Unknown tool: {name}"
            tool_messages.append(ToolMessage(content=out, tool_call_id=tool_id))
        messages = messages + [response] + tool_messages
    last = messages[-1] if messages else AIMessage(content="")
    return messages, getattr(last, "content", "") or ""


def _agent_loop_runnable(prompt_value) -> str:
    """Runnable that takes prompt output (ChatPromptValue or messages) and returns final reply content."""
    messages = prompt_value.messages if hasattr(prompt_value, "messages") else prompt_value
    _, content = _run_agent_loop(messages)
    return content


# ── Chain (agent with tools) ───────────────────────────────────────────────
# Wrapped in try/except so the module loads even if the API key is missing.
# Static routes (/ and /public/*) remain available; /askbot returns 503.

chat = None
_init_error: str | None = None
_llm_with_tools = None

try:
    from langchain_core.runnables import RunnableLambda

    _prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt()),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    _llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )
    _llm_with_tools = _llm.bind_tools(TOOLS)

    _chain = _prompt_template | RunnableLambda(_agent_loop_runnable)

    chat = RunnableWithMessageHistory(
        _chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
except Exception as exc:
    _init_error = str(exc)
    logger.error("Failed to initialize LLM chain: %s", _init_error)


# ── Request / Response models ────────────────────────────────────────────────


class AskBotRequest(BaseModel):
    msg: str = Field(..., description="Message from the user", min_length=1)
    session_id: str = Field(..., description="Unique session identifier for the conversation", min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [{"msg": "What can you help me with?", "session_id": "user-123"}]
        }
    }

    @field_validator("msg", mode="before")
    @classmethod
    def strip_msg(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("msg must not be blank")
        return stripped


class AskBotResponse(BaseModel):
    msg: str = Field(..., description="Reply from the bot")
    session_id: str = Field(..., description="Same session identifier echoed back")

    model_config = {
        "json_schema_extra": {
            "examples": [{"msg": "I can answer questions, help with tasks, and more!", "session_id": "user-123"}]
        }
    }


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
async def root():
    """Serve the chat UI at the root URL."""
    index = PUBLIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index)


@app.get("/public/{filename:path}", include_in_schema=False)
async def serve_public(filename: str):
    """Serve a file from the public directory. Rejects path traversal."""
    file_path = (PUBLIC_DIR / filename).resolve()

    if not str(file_path).startswith(str(PUBLIC_DIR.resolve())):
        raise HTTPException(status_code=404, detail="Not found")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(file_path)


# ── WhatsApp Business (Meta Cloud API) ──────────────────────────────────────

_WA_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
_WA_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
_WA_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
_WA_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"


async def _send_whatsapp_message(to: str, text: str) -> None:
    url = _WA_API_URL.format(phone_number_id=_WA_PHONE_NUMBER_ID)
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        "Authorization": f"Bearer {_WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.error("Meta API error %s: %s", resp.status_code, resp.text)


@app.get(
    "/webhook",
    tags=["WhatsApp"],
    summary="Meta webhook verification",
    response_class=PlainTextResponse,
    responses={
        200: {"description": "Challenge echoed back to Meta — webhook verified"},
        403: {"description": "Invalid verification token"},
    },
)
async def whatsapp_verify(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification handshake (subscribe mode)."""
    if mode == "subscribe" and token == _WA_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verificado correctamente")
        return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Token de verificación incorrecto")


@app.post(
    "/webhook",
    tags=["WhatsApp"],
    summary="Receive WhatsApp messages",
    responses={200: {"description": "Always 200 — Meta requires fast acknowledgement"}},
)
async def whatsapp_receive(request: Request):
    """Receive incoming WhatsApp messages from Meta and reply via the bot."""
    body = await request.json()

    # Meta expects 200 quickly regardless of message type
    try:
        entry = body.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0].get("value", {})
        messages = change.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg = messages[0]
        if msg.get("type") != "text":
            return {"status": "ok"}

        sender: str = msg["from"]
        text: str = msg["text"]["body"].strip()
        session_id = f"wa_{sender}"

        if not text:
            return {"status": "ok"}

        if chat is None:
            await _send_whatsapp_message(sender, "El servicio no está disponible en este momento.")
            return {"status": "ok"}

        bot_reply = await chat.ainvoke(
            {"input": text, "today": date.today().isoformat()},
            config={"configurable": {"session_id": session_id}},
        )
        await _send_whatsapp_message(sender, bot_reply)

    except Exception:
        logger.exception("Error procesando mensaje de WhatsApp")

    return {"status": "ok"}


@app.post(
    "/askbot",
    tags=["Chat"],
    summary="Send a message to the bot",
    response_model=AskBotResponse,
    responses={
        200: {
            "description": "Bot reply",
            "content": {
                "application/json": {
                    "example": {"msg": "Hello! How can I help you today?", "session_id": "user-123"}
                }
            },
        },
        422: {"description": "Validation error — msg is blank or missing required fields"},
        503: {"description": "LLM chain failed to initialise (missing API key or config error)"},
    },
)
async def askbot(body: AskBotRequest) -> AskBotResponse:
    """Send a user message and receive a bot reply.

    - **msg**: the user's message (must not be blank)
    - **session_id**: opaque string that scopes the conversation history; create one per user/thread
    """
    if chat is None:
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unavailable: {_init_error or 'chain not initialized'}",
        )

    response = await chat.ainvoke(
        {"input": body.msg, "today": date.today().isoformat()},
        config={"configurable": {"session_id": body.session_id}},
    )

    return AskBotResponse(msg=response, session_id=body.session_id)
