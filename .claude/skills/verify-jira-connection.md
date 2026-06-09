# Skill: Verificar Conectividad con Jira API

Permite validar que las credenciales locales de la API de Jira configuradas en el entorno
sean correctas antes de realizar operaciones de lectura o escritura.

## Propósito

Evitar errores de autenticación (401/403) durante el desarrollo y asegurar que la URL
de la instancia y los tokens de acceso sean funcionales.

## Requisitos previos

- Archivo `.env` con las variables:
  - `JIRA_URL`
  - `JIRA_EMAIL`
  - `JIRA_TOKEN`
- Script auxiliar de diagnóstico en `scripts/verify_jira.py`.

## Comando de ejecución

```bash
python scripts/verify_jira.py
```

## Salida esperada

- **Éxito:** Mensaje que confirme la conexión y muestre el nombre de usuario o cuenta
  vinculada al token.
- **Fallo:** Detalle específico del error (credenciales inválidas, error de red,
  variables de entorno faltantes).

## Cuándo usar esta skill

- Al arrancar el proyecto por primera vez en un entorno nuevo.
- Antes de ejecutar cualquier otra skill que interactúe con Jira.
- Cuando `jira_create` o `jira_search` devuelvan errores 401/403 inesperados.
- Tras rotar el `JIRA_TOKEN`.

## Implementación del script

```python
# scripts/verify_jira.py
import os
from dotenv import load_dotenv
from jira import JIRA
from jira.exceptions import JIRAError

load_dotenv()

url   = os.getenv("JIRA_URL")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_TOKEN")

missing = [k for k, v in {"JIRA_URL": url, "JIRA_EMAIL": email, "JIRA_TOKEN": token}.items() if not v]
if missing:
    print(f"❌ Variables de entorno faltantes: {', '.join(missing)}")
    raise SystemExit(1)

try:
    jira = JIRA(server=url, basic_auth=(email, token))
    user = jira.myself()
    print(f"✅ Conexión exitosa — Usuario: {user['displayName']} ({user['emailAddress']})")
except JIRAError as e:
    print(f"❌ Error Jira {e.status_code}: {e.text}")
    raise SystemExit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    raise SystemExit(1)
```
