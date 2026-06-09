# Arquitectura de Archivos — SoporteBot

## Estructura de ficheros

```
soportebot/
├── main.py              ← FastAPI: endpoints, chain, session store, agent loop
├── tools.py             ← @tool definitions: jira_search, jira_create
├── prompt.md            ← System prompt (cargado en runtime, nunca hardcodeado)
├── public/
│   └── index.html       ← UI de chat — HTML/CSS/JS en un solo archivo, sin frameworks
├── requirements.txt
├── .env.example
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_tools.py
└── docs/
    ├── exercise.md
    ├── architecture.md
    ├── bussiness-rules.md
    └── openapi.ymal          ← OpenAPI 3.1.0 spec (Swagger) — fuente de verdad de la API
```

---

## Responsabilidades por archivo

### `main.py`
- FastAPI app con exactamente 4 rutas: `GET /`, `GET /public/{filename:path}`, `POST /askbot`, `GET /api-docs`
- Session store (`_store: dict[str, InMemoryChatMessageHistory]`)
- Inicialización del chain (`RunnableWithMessageHistory`)
- Agent loop (`_run_agent_loop`, `_agent_loop_runnable`)
- Carga del prompt desde `prompt.md`
- Modelos Pydantic v2: `AskBotRequest`, `AskBotResponse`
- Protección path-traversal en `/public/{filename:path}`

### `tools.py`
- **2 tools en scope**: `jira_search` y `jira_create`
- `jira_comment` (update) y cualquier operación de delete están **fuera de alcance** por el momento
- `@tool` para ambas (o `BaseTool` + `args_schema` si se necesita validación Pydantic v2 en inputs)
- Cliente Jira inicializado aquí, no en `main.py`
- Validaciones de inputs dentro de cada tool; devuelven strings, nunca lanzan excepciones

```python
TOOLS = [jira_search, jira_create]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
```

### `prompt.md`
- System prompt completo en texto plano
- Se edita directamente sin tocar código Python
- Se recarga en cada restart, no en cada request

### `public/index.html`
- Un único archivo HTML/CSS/JS vanilla (ver reglas de UI más abajo)
- Sirve la interfaz de chat y llama a `POST /askbot`

### `docs/openapi.ymal`
- Especificación OpenAPI 3.1.0 — fuente de verdad de todos los endpoints de la API
- Documenta: `GET /`, `POST /askbot`, `GET /api-docs`, `GET /api-docs/redoc`, `GET /api-docs/openapi.json`
- Incluye ejemplos de request/response para los 4 escenarios conversacionales principales
- Se sirve en runtime en `GET /api-docs/openapi.json` (generado por FastAPI automáticamente)
- El fichero `.ymal` en `docs/` es la especificación de referencia editable; el JSON en `/api-docs/openapi.json` lo genera FastAPI a partir del código

Validar el spec con:
```bash
npx @stoplight/spectral-cli lint docs/openapi.ymal
# o
npx swagger-cli validate docs/openapi.ymal
```

---

## Endpoints de FastAPI

### `POST /askbot`

```python
from pydantic import BaseModel, Field, field_validator

class AskBotRequest(BaseModel):
    msg: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)

    @field_validator("msg", mode="before")
    @classmethod
    def strip_msg(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("msg must not be blank")
        return stripped

class AskBotResponse(BaseModel):
    msg: str
    session_id: str
```

Request: `{ "msg": "El login no funciona", "session_id": "sess_abc123" }`
Response: `{ "msg": "He buscado en Jira y...", "session_id": "sess_abc123" }`

### `GET /public/{filename:path}` — protección path traversal

```python
@app.get("/public/{filename:path}")
async def serve_public(filename: str):
    file_path = (PUBLIC_DIR / filename).resolve()
    if not str(file_path).startswith(str(PUBLIC_DIR.resolve())):
        raise HTTPException(status_code=404, detail="Not found")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(file_path)
```

---

## Reglas de la UI HTML (`public/index.html`)

Un único archivo HTML/CSS/JS vanilla sin frameworks. Todo el layout, estilos y lógica en el mismo fichero.

### Estructura del DOM

```html
<body>
  <div.chat-container>
    <div.chat-header>     ← título del bot
    <div.chat-messages>   ← burbujas, scroll independiente (overflow-y: auto)
    <div.chat-input-area>
      <input#msgInput placeholder="Escribe tu mensaje...">
      <button#sendBtn>Enviar</button>
  </div>
</body>
```

No hay header global, footer, ni elementos decorativos. Layout centrado con `flexbox` en `body`.

### Session ID

```js
var sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
```

Generado una vez al cargar la página. Variable local en el IIFE — no persiste en `localStorage`.

### Clases de mensajes

```css
.message.user  { align-self: flex-end;   background: #007bff; color: #fff; border-bottom-right-radius: 4px; }
.message.bot   { align-self: flex-start; background: #e9ecef; color: #333; border-bottom-left-radius: 4px; }
.message.error { align-self: flex-start; background: #f8d7da; color: #721c24; border-bottom-left-radius: 4px; }
```

### Renderizado de texto

- Mensajes del **bot**: `marked.parse(text)` — renderiza Markdown
- Mensajes del **usuario**: `escapeHtml(text)` — protección XSS obligatoria

```js
function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function appendMessage(text, role) {
    var bubble = $('<div class="message ' + role + '"></div>');
    if (role === "bot") {
        bubble.html(marked.parse(text));
    } else {
        bubble.html(escapeHtml(text));
    }
    $("#chatMessages").append(bubble);
    var c = document.getElementById("chatMessages");
    c.scrollTop = c.scrollHeight;
}
```

### Llamada a la API

```js
function sendMessage() {
    var text = $("#msgInput").val().trim();
    if (!text) return;
    appendMessage(text, "user");
    $("#msgInput").val("");

    $.ajax({
        url: "/askbot",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ msg: text, session_id: sessionId }),
        dataType: "json",
        success: function(res) {
            appendMessage(res.msg, "bot");
        },
        error: function(xhr) {
            var detail = "Something went wrong. Please try again.";
            try { var b = JSON.parse(xhr.responseText); if (b.detail) detail = b.detail; } catch(e) {}
            appendMessage("Error: " + detail, "error");
        }
    });
}

$("#sendBtn").on("click", sendMessage);
$("#msgInput").on("keypress", function(e) { if (e.which === 13) sendMessage(); });
```

### Mensaje de bienvenida

```js
appendMessage("¡Hola! Soy SoporteBot. ¿En qué puedo ayudarte hoy?", "bot");
```

Llamada directa al cargar — sin petición al backend.

### Dependencias CDN (las únicas permitidas)

```html
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

### Todo el código JS en un IIFE

```js
(function () {
    var sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
    // ... funciones y event handlers aquí
})();
```

### Prohibiciones en la UI

- No usar React, Vue, Angular ni ningún otro framework JS
- No usar `innerHTML` con texto del usuario — siempre `escapeHtml()`
- No persistir historial en `localStorage` — el estado vive en el backend (`_store`)
- No hacer llamadas a otros endpoints que no sea `POST /askbot`

---

## FastAPI app initialization

```python
from fastapi import FastAPI

app = FastAPI(
    title="SoporteBot API",
    description="Jira support chatbot — AI4Devs 202602 Seniors",
    version="1.0.0",
    docs_url="/api-docs",
    redoc_url="/api-docs/redoc",
    openapi_url="/api-docs/openapi.json",
)
```

- `GET /api-docs` → Swagger UI (interactive)
- `GET /api-docs/redoc` → ReDoc (read-only)
- `GET /api-docs/openapi.json` → raw OpenAPI 3.1.0 JSON

Never use the FastAPI default `/docs` or `/redoc` — always `/api-docs`.

---

## Inicio de la app

```bash
uvicorn main:app --reload --port 8000
# UI en     http://localhost:8000
# Swagger   http://localhost:8000/api-docs
# ReDoc     http://localhost:8000/api-docs/redoc
# OAS JSON  http://localhost:8000/api-docs/openapi.json
```

## `.env.example`

```
JIRA_URL=https://tu-empresa.atlassian.net
JIRA_EMAIL=tu@email.com
JIRA_TOKEN=tu_api_token
JIRA_PROJECT=SUP
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
