# RAG Tool — Documentación interna

## Propósito

`rag_docs` busca en la documentación técnica interna del equipo (guías, ADRs, READMEs)
antes de sugerir abrir un ticket. Si la respuesta ya está en los docs, el agente la devuelve
sin crear ruido en Jira.

## Setup del vectorstore (una sola vez al arrancar)

```python
import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

FAISS_INDEX_PATH = "./faiss_index"

# Embeddings multilingüe, corre en CPU
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

if os.path.exists(FAISS_INDEX_PATH):
    # Cargar índice existente (evita reindexar en cada reinicio)
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    # Crear desde cero (primera vez)
    loader = DirectoryLoader("docs/", glob="**/*.md", loader_cls=TextLoader)
    documentos = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documentos)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✅ Índice FAISS creado con {len(chunks)} chunks")
```

- Embeddings multilingüe corriendo en CPU (sin GPU requerida).
- El índice se persiste en `./faiss_index/` — dos ficheros: `index.faiss` e `index.pkl`.
- `allow_dangerous_deserialization=True` es necesario para cargar el índice desde disco con pickle; solo usar con ficheros propios.
- Si no hay documentos en `docs/`, crear al menos un archivo de ejemplo con guías del equipo.

## Dependencias

```
faiss-cpu>=1.8.0
langchain-community>=0.3.0
sentence-transformers>=3.0.0
```

No añadir `chromadb` — este proyecto usa FAISS exclusivamente.

## Tool: `rag_docs`

```python
from langchain_core.tools import tool

@tool
def rag_docs(pregunta: str) -> str:
    """
    Busca en la documentación técnica interna del equipo (guías, ADRs, READMEs).
    Úsalo cuando el usuario haga una pregunta técnica ANTES de abrir un ticket.
    Puede que la respuesta ya esté en los docs y no sea necesario crear un issue.

    Parámetro: pregunta (str) — la pregunta técnica del usuario.
    Devuelve los fragmentos más relevantes de la documentación interna.
    """
    docs = vectorstore.similarity_search(pregunta, k=3)
    if not docs:
        return "No se encontró información relevante en la documentación interna."
    return "\n\n---\n\n".join([d.page_content for d in docs])
```

## Orden de llamada en el agente

```
Pregunta técnica del usuario
        │
        ▼
1. rag_docs(pregunta)
        │
        ├── Respuesta encontrada → devolver al usuario, no crear ticket
        └── Sin respuesta → jira_search → (si no hay duplicado) → jira_create
```

El agente NO debe llamar a `jira_search` si `rag_docs` ya resolvió la duda.

## Documentos indexados y su propósito

El directorio `docs/` es la única fuente que `rag_docs` consulta. Cada fichero tiene un rol concreto:

| Fichero | Qué contiene | Cuándo lo necesita el agente |
|---------|-------------|------------------------------|
| `bussiness-rules.md` | **Proceso conversacional** (3 pasos), **SLA de 24 h**, horario de corte (viernes 17:00 Europe/Madrid), plantilla de ticket, taxonomía de etiquetas, reglas de slug y body | Siempre que el usuario pregunte sobre plazos, horarios, qué campos necesita, cómo funciona el proceso o cuándo estará publicado su artículo |
| `architecture.md` | Arquitectura del chatbot, endpoints, stack técnico | Preguntas técnicas sobre el sistema |
| `exercise.md` | Especificación de la práctica S14 | Contexto del ejercicio |
| `openapi.ymal` | Contrato de la API REST | Preguntas sobre los endpoints |

Añadir aquí cualquier documento nuevo que deba ser consultable por el agente.

### Información clave de `bussiness-rules.md` que el agente debe saber citar

- **SLA**: 24 horas laborables (lunes–viernes) desde la creación del ticket.
- **Corte de fin de semana**: solicitudes recibidas el viernes después de las 17:00 (Europe/Madrid) o en fin de semana → el plazo empieza el lunes siguiente a las 09:00.
- **Campos obligatorios** para crear el ticket: `dominio`, `título`, `fecha`, `slug` y `body`.
- **Identificador del proyecto de blog**: el dominio del sitio (p.ej. `empresa.com`).
- **Proceso**: 3 pasos — recopilación por preguntas → verificación de tickets existentes en Jira → creación con confirmación explícita.

Si el usuario pregunta cuándo estará publicado su artículo, el agente debe citar el SLA y el horario de corte extraídos de `bussiness-rules.md`, no inventarlos.

## Forzar reindexado

Borrar el directorio del índice y reiniciar el servidor:

```bash
rm -rf ./faiss_index
uvicorn main:app --reload
```

El índice se regenera automáticamente al arrancar.

## `.gitignore` — excluir el índice del repositorio

```
faiss_index/
```

El índice se regenera desde `docs/` en cada entorno — no tiene sentido versionarlo.
