---
name: technical-documentation
description: Produces clear, accurate technical documentation for codebases and APIs. Use when writing or improving README files, API docs, architecture or design docs, specs, runbooks, or when the user asks for documentation, docstrings, or technical writing.
---

# Technical Documentation

Apply when creating or revising technical documentation. Aim for audience-first, accurate, and scannable content with concrete examples.

## When to Use

- Writing or updating README, API reference, architecture docs, or specs
- Adding or improving docstrings and inline comments for public APIs
- Creating runbooks, contributing guides, or onboarding docs
- User asks for "documentation," "docs," or "technical writing"

## Principles

1. **Audience first** – Identify who will read it (developers, operators, end users) and what they need to do (run, integrate, debug, contribute).
2. **Accurate** – Match the current code or behaviour; do not describe removed or planned features as current. When in doubt, infer from the codebase.
3. **Scannable** – Use clear headings, short paragraphs, bullet lists, and code blocks. Put the most important information near the top.
4. **Concrete** – Prefer examples, commands, and minimal snippets over long prose. Show input/output or before/after when it helps.
5. **Consistent** – Use the same terms and structure across the doc (e.g. "API endpoint" not mixed with "route" or "path").

## Document Types

| Type | Purpose | Typical sections |
|------|---------|------------------|
| **README** | Project overview, quick start | Goal, tech stack, install/run, config, repo link |
| **API / reference** | How to call APIs or use modules | Endpoints or functions, parameters, return values, errors, examples |
| **Architecture / design** | How the system works | Components, data flow, decisions, diagrams |
| **Spec / RFC** | Intended behaviour or change | Context, goals, non-goals, design, alternatives |
| **Runbook** | How to operate or fix something | Prerequisites, steps, checks, rollback, contacts |
| **Contributing** | How to contribute | Setup, style, PR process, where to ask |

## Structure

- **Title (H1)** – One clear title per document.
- **Short intro** – One or two sentences on what this doc covers and for whom.
- **Headings (H2, H3)** – Logical order (e.g. Overview → Getting started → Reference → Examples).
- **Code blocks** – Use fenced blocks with language (e.g. ` ```bash `, ` ```python `). Keep examples runnable when possible.
- **Links** – Link to related docs, repo, or code; use relative paths for in-repo links.

## README Template

```markdown
# Project Name

One-line description of what the project does and for whom.

## Goal / Overview

- Main purpose
- Key capabilities or constraints

## Tech Stack

- Language, framework, key libraries

## Getting Started

### Prerequisites

- Runtime, tools, accounts

### Install / Run

\`\`\`bash
# Commands to clone, install, run
\`\`\`

### Configuration

- Env vars, config files, or flags

## Usage / API

- How to use (commands, endpoints, or main entry points)
- Link to detailed docs if needed

## Repository

- URL or link to repo

## Documentation

- Link to `docs/` or other docs
```

## API / Reference Template

For each endpoint or public function:

- **Name and purpose** – One line.
- **Signature or route** – Method, path, or function signature.
- **Parameters** – Name, type, required/optional, short description.
- **Returns** – Type and meaning.
- **Errors** – Possible errors or status codes and when they occur.
- **Example** – Minimal request/response or call snippet.

## Quality Checklist

Before finalising a doc:

- [ ] Audience and goal are clear in the intro
- [ ] Headings reflect the actual content and order
- [ ] Code examples are valid and consistent with the repo
- [ ] No outdated or incorrect claims (e.g. old API, removed feature)
- [ ] Links work and use the right path (relative for in-repo)
- [ ] Terminology is consistent (e.g. same name for the same concept)

## Anti-Patterns

- **Vague intros** – Avoid "This document describes things." Prefer "This doc explains how to run the service locally and which env vars are required."
- **No examples** – Prefer at least one concrete command, request, or code snippet per major section.
- **Wall of text** – Break long paragraphs into lists or subheadings.
- **Mixed terminology** – Pick one term per concept and stick to it.
- **Future as current** – Do not document planned behaviour as if it already exists; label it as "Planned" or omit until implemented.

## Language

Write documentation in **English** unless the project explicitly uses another language for docs. Keep tone neutral and professional.
