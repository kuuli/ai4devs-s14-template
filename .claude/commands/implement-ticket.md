---
description: Implement a Jira ticket end-to-end (In Progress → code → tests → PR → Code Review)
subagent_type: langchain-developer
---

# implement-ticket

Implement a Jira ticket end-to-end: move it through the board (To Do → In Progress → Code Review), write the code, run tests, and open a PR.

## Usage

```
/implement-ticket <TICKET-KEY>
```

Example: `/implement-ticket L1DR-60`

---

## What this command does

1. **Fetches** the ticket from Jira and reads its description, acceptance criteria, and current status.
2. **Moves** the ticket to **In Progress**.
3. **Creates** a feature branch named after the ticket key.
4. **Implements** the code changes described in the ticket, with maximum comments.
5. **Runs** the test suite and fixes any failures before continuing.
6. **Commits** all changes with a message referencing the ticket key.
7. **Pushes** the branch and opens a **Pull Request** on GitHub.
8. **Moves** the ticket to **Code Review** and adds the PR URL as a comment on the ticket.

---

## Instructions

You are acting as a senior engineer on this project. Follow these steps exactly and in order. Do not skip steps.

### Step 1 — Read the ticket

Fetch the Jira ticket passed as `$ARGUMENTS` using the Atlassian MCP tool.

- Cloud ID: `kuuli.atlassian.net`
- Read: `summary`, `description`, `status`, `issuetype`, `priority`, `assignee`
- If the ticket does not exist or is already **Done**, stop and tell the user.
- Print a one-line summary: `📋 <KEY>: <summary> [<status>] [<priority>]`

### Step 2 — Move to In Progress

Transition the ticket to **In Progress** using the Atlassian MCP tool.

- Call `getTransitionsForJiraIssue` to find the transition ID for "In Progress".
- Call `transitionJiraIssue` with that ID.
- Confirm: `🔄 Moved <KEY> → In Progress`

### Step 3 — Create a feature branch

Branch naming convention: `feature/<KEY>-<slug>` where slug is the ticket summary lowercased, spaces replaced with hyphens, max 5 words.

```bash
git checkout main
git pull origin main
git checkout -b feature/<KEY>-<slug>
```

### Step 4 — Implement the code

Read the ticket description carefully. Implement exactly what the acceptance criteria describe.

Rules:
- Follow all patterns in `CLAUDE.md` and `.claude/rules/`.
- Add comments explaining every non-obvious decision — this is a teaching codebase.
- Do not add features beyond what the ticket describes.
- Keep changes minimal and focused.
- If the ticket references a design doc in `docs/`, read it before writing code.

### Step 5 — Run tests

```bash
pytest tests/ -v
```

- If tests fail, fix the failures before continuing. Do not skip or comment out tests.
- If new behaviour requires new tests, add them in `tests/`.
- All tests must pass before proceeding.

### Step 6 — Commit

Stage only the files you changed (never `git add -A` blindly).

Commit message format:
```
[<KEY>] <short imperative summary>

<one paragraph explaining what changed and why, referencing the ticket>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Step 7 — Push and open a PR

```bash
git push -u origin feature/<KEY>-<slug>
```

Create the PR with `gh pr create`:
- **Title**: `[<KEY>] <ticket summary>`
- **Body** must include:
  - `## Summary` — bullet list of what changed
  - `## Test plan` — checklist of what to verify manually
  - `Closes <KEY>` at the bottom
  - `🤖 Generated with Claude Code`

### Step 8 — Move to Code Review and comment on ticket

1. Transition the ticket to **Code Review** (or the equivalent column — use `getTransitionsForJiraIssue` to find the right transition ID).
2. Add a comment on the Jira ticket with the PR URL:

```
PR opened for review: <PR_URL>

Changes: <one-line summary of what was implemented>
```

Confirm: `✅ <KEY> moved → Code Review | PR: <PR_URL>`

---

## Error handling

| Situation | Action |
|-----------|--------|
| Ticket not found | Stop. Tell the user the key doesn't exist. |
| Ticket already Done | Stop. Tell the user it's already closed. |
| Ticket already In Progress | Skip step 2, continue from step 3. |
| Tests fail after 2 fix attempts | Stop. List the failing tests and ask the user how to proceed. |
| "Code Review" transition not found | Move to the closest equivalent (e.g. "In Review") and note it. |
| PR already exists for this branch | Skip `gh pr create`, add the existing PR URL to the Jira comment. |

---

## Acceptance checklist (verify before finishing)

- [ ] Ticket is in **Code Review** in Jira
- [ ] Feature branch exists on remote
- [ ] PR is open with title referencing the ticket key
- [ ] PR body contains summary, test plan, and `Closes <KEY>`
- [ ] Jira ticket has a comment with the PR URL
- [ ] All tests pass
- [ ] No secrets, credentials, or `.env` files committed
