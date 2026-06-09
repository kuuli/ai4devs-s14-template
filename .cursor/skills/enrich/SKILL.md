---
name: enrich
description: Enriches a Jira ticket with full description, testable acceptance criteria, and technical specs so it is ready for implementation. Use when the user says "enrich" followed by a Jira ticket key or URL (e.g. "enrich PROJ-9").
---

# Enrich Command

Triggered when the user provides a Jira ticket key (or URL) to enrich. The goal is to add or refine the ticket's description, acceptance criteria, and technical context **before** implementation, so the implement command has all information at hand.

**Apply the project skill** at `.cursor/skills/jira-tickets/SKILL.md` for all ticket text.

## Phase 1 — Read the Ticket

1. Get the Jira Cloud ID from `.cursor/rules/jira-config.mdc`.
2. Call `getJiraIssue` (MCP server `user-Atlassian`) with the ticket key.
3. Present to the user:
   - **Summary**, **Type**, **Status**
   - **Current description** (or "empty" if missing)
   - **Acceptance criteria** (or "none")
   - **Labels**, **Components**, **Epic link** (if any)

If the ticket is not found, tell the user and stop.

## Phase 2 — Analyze Gaps

Review the ticket against the jira-tickets skill and identify what is missing or weak:

| Check | What to look for |
|-------|------------------|
| **Description structure** | Purpose, Scope (in/out), Context, Done when — all present and clear? |
| **AC quality** | Testable? Given/When/Then or bullets? Happy path + error cases? |
| **Technical specs** | APIs, endpoints, env vars, file paths mentioned? |
| **Business rules** | Domain rules named and reflected in AC? |
| **Out of scope** | Explicitly stated what is *not* in scope? |

Produce a short **gap summary**.

## Phase 3 — Ask Clarifying Questions

**This phase is mandatory. Do not skip it.**

Build a list of questions whose answers are needed for implementation to proceed without guessing:

| Check | What to look for |
|-------|------------------|
| **Scope boundaries** | In/out of scope unclear? |
| **Technical approach** | Which modules, APIs, or files are affected? |
| **APIs and contracts** | External APIs or endpoints — are they named or do we need URLs/specs? |
| **Business rules** | Domain rules — are they stated in AC? |
| **Dependencies** | Other tickets or services that must be done first? |
| **Ambiguity** | Vague terms that need a concrete definition for AC? |

**Present ALL questions to the user at once.** Wait for answers before proceeding.

**If you have zero questions**, state explicitly: "No clarifying questions — the ticket is clear enough for implementation." and confirm with the user.

## Phase 4 — Gather Context (if needed)

If the ticket refers to external systems, APIs, or constraints:

- Ask the user for **API docs URLs**, **constraint docs**, or **related ticket links**.
- Optionally search the codebase for relevant files.

## Phase 5 — Draft Enriched Content

1. **Incorporate the user's answers** into the description, AC, and technical notes.
2. Apply the jira-tickets skill:
   - Use its **description template** (Purpose, Scope, Context, Done when).
   - Use its **AC template** (Given/When/Then or bullets).
   - Run through its **quality checklist**.
3. Produce:
   - **Enriched description** (full markdown).
   - **Enriched acceptance criteria** (testable, unambiguous).
   - **Technical notes** (optional): API endpoints, env vars, file paths, suggested test scenarios.

## Phase 6 — Update Jira (with confirmation)

1. Present the enriched description and AC to the user.
2. Ask: **"Do you want this pushed to Jira, or only copy-paste?"**
3. If the user confirms **push**:
   - Call `editJiraIssue` with the new description. Use the ticket key and Cloud ID from jira-config.
4. Optionally add a **comment** on the ticket only if the user asked to push.

## Configuration

| Setting | Source |
|---------|--------|
| Jira Cloud ID | `.cursor/rules/jira-config.mdc` |
| Ticket text quality | `.cursor/skills/jira-tickets/SKILL.md` |

## Rules

- **Never invent scope.** Only add or clarify what the ticket type and summary imply; if in doubt, ask.
- **One format per ticket.** Use either Given/When/Then or bullets for AC, not both mixed.
- **English.** Write description and AC in English unless the project uses another language for Jira.
- **No implementation.** Enrich does not create branches, run tests, or implement code; it only improves the ticket content.
