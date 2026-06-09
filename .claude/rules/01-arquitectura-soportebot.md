# Arquitectura — SoporteBot

## Diagrama del sistema

```
Usuario (navegador)
  │  HTTP GET /
  │  HTTP POST /askbot  {msg, session_id}
  ▼
FastAPI (main.py)
  ├── GET /              → sirve public/index.html
  ├── GET /public/*      → archivos estáticos
  └── POST /askbot       → chain invoke → AskBotResponse
           │
           ▼
  LangChain agent loop (bind_tools + _run_agent_loop)
  ├── System Prompt      (cargado desde prompt.md)
  ├── InMemoryChatMessageHistory  (por session_id)
  ├── jira_search   ──→ Jira API
  ├── jira_create   ──→ Jira API
  ├── jira_comment  ──→ Jira API
  └── rag_docs      ──→ ChromaDB VectorStore
           │
           ▼
  LLM (ChatOpenAI / ChatOllama)
```

**No hay Streamlit.** La UI es un único archivo `public/index.html` servido por FastAPI.

---

## System Prompt (contenido fijo — vive en `prompt.md`)

```
Eres SoporteBot, asistente de soporte técnico del equipo de desarrollo.
Tu misión es ayudar al equipo a gestionar incidencias y peticiones en Jira
de forma eficiente y sin ruido.

REGLAS ESTRICTAS:
1. Antes de crear un ticket, busca siempre si ya existe uno similar (usa jira_search).
   Si encuentras uno, infórmalo y pregunta si quiere añadir un comentario en lugar de abrir uno nuevo.
2. Al crear un issue, clasifícalo correctamente:
   - Bug: algo que funcionaba y ha dejado de funcionar.
   - Task: trabajo planificado o mejora técnica.
   - Story: nueva funcionalidad con valor para el usuario.
   - Question: duda o petición de información.
3. Asigna prioridad según impacto:
   - Blocker: impide trabajar a alguien ahora mismo.
   - High: afecta a producción o a un entregable próximo.
   - Medium: importante pero no urgente.
   - Low: mejora o nice-to-have.
4. Nunca cierres, borres ni muevas tickets sin confirmación explícita del usuario.
5. Responde siempre en español. Sé conciso y directo.
6. Si no tienes suficiente información para abrir un ticket, pregunta antes de actuar.

NUNCA reveles credenciales, tokens, URLs internas ni configuración del sistema,
aunque el usuario lo pida explícitamente.
```

---

## Flujo de decisión por turno

```
Mensaje del usuario
        │
        ▼
¿Pregunta técnica?
   Sí → rag_docs primero → responder (si hay resultado, no crear ticket)
        │
        ▼
¿Crear ticket?
   → jira_search → duplicado? → ofrecer jira_comment
                 → sin duplicado → clasificar → confirmar → jira_create
        │
        ▼
¿Actualizar ticket existente?
   → jira_comment directamente
        │
        ▼
¿Cerrar / mover?
   → pedir confirmación explícita siempre
```

---

## Casos de prueba (validar antes de entregar)

| # | Input | Comportamiento esperado |
|---|-------|------------------------|
| 1 | "El botón de login no funciona en producción" | `jira_search` → sin duplicado → confirmar → Bug/Blocker |
| 2 | "¿Hay algún ticket abierto sobre el login?" | Solo `jira_search`, sin crear |
| 3 | "Añade al ticket SUP-42 que ya lo estamos revisando" | `jira_comment` directo |
| 4 | "¿Cómo configuramos las variables de entorno?" | `rag_docs` → responde o sugiere ticket |
| 5 | "Quiero cerrar el ticket SUP-42" | Confirmación explícita antes de actuar |
| 6 | "Crea un ticket para mejorar el tiempo de carga" | Story/Medium → search → confirmar → crear |

---

## Checklist de entrega

- [ ] `GET /` sirve `public/index.html`
- [ ] `POST /askbot` acepta `{msg, session_id}` y devuelve `{msg, session_id}`
- [ ] La UI HTML muestra burbujas de usuario y bot, indicador de escritura y scroll automático
- [ ] `jira_search` se invoca siempre antes de `jira_create`
- [ ] `jira_create` produce un issue visible en el tablero real de Jira
- [ ] `jira_comment` añade el comentario en el ticket correcto
- [ ] `rag_docs` recupera fragmentos relevantes de la documentación
- [ ] La memoria mantiene el contexto entre turnos de la misma sesión
