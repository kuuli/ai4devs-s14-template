# Skill: Lint and Format

Runs code style, formatting, and static type checks across the project to catch
issues before tests or code review.

## Propósito

Mantener consistencia de estilo, detectar errores de tipo y asegurar que el código
Python cumple los estándares del proyecto antes de cualquier commit o PR.

## Requisitos previos

- Dependencias instaladas (`pip install -r requirements.txt`).
- Debe ejecutarse desde la raíz del proyecto.

## Comando de ejecución

```bash
# Formateo automático
black .

# Linting
flake8 . --max-line-length=100 --exclude=.venv,__pycache__

# Comprobación de tipos
mypy main.py tools.py services/ schemas/ guardrails/ --ignore-missing-imports
```

O todos juntos:

```bash
black . && flake8 . --max-line-length=100 --exclude=.venv,__pycache__ && mypy main.py tools.py services/ schemas/ guardrails/ --ignore-missing-imports
```

## Salida esperada

- **black**: `All done! ✨ 🍰 ✨ — N files reformatted` o `N files left unchanged`.
- **flake8**: sin salida si no hay errores.
- **mypy**: `Success: no issues found in N source files`.

Cualquier error de flake8 o mypy debe resolverse antes de hacer commit.

## Cuándo usar esta skill

- Antes de cada commit.
- Antes de abrir un PR.
- Tras modificar `tools.py`, `schemas/ticket.py`, `guardrails/validation.py` o `main.py`.
- Cuando `test-langchain-agent` falla por errores de tipo inesperados.

## Dependencias a añadir en requirements.txt

```
black>=24.0.0
flake8>=7.0.0
mypy>=1.8.0
```

## Configuración recomendada (.flake8 en raíz)

```ini
[flake8]
max-line-length = 100
exclude = .venv, __pycache__, .git
per-file-ignores =
    tests/*: S101
```

## Configuración recomendada (pyproject.toml)

```toml
[tool.black]
line-length = 100
target-version = ["py310"]

[tool.mypy]
python_version = "3.10"
strict = false
ignore_missing_imports = true
```
