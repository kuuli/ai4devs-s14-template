---
name: pr-review
description: Reviews a GitHub PR against its linked Jira ticket — checks code quality, verifies every acceptance criterion is covered, validates best practices, and posts a structured review. Use when the user says "pr-review" followed by a PR number, URL, or PR number + ticket key (e.g. "pr-review 42", "pr-review #42 PROJ-10").
---

# PR Review Command

Triggered when the user provides a GitHub PR (number or URL) to review. The goal is to verify that the code changes satisfy the linked Jira ticket's acceptance criteria, follow project best practices, and are production-ready.

## Phase 1 — Gather PR Context

1. **Parse the input:**
   - PR number: `42` or `#42` → use directly.
   - PR URL: extract the number from the URL.
   - If a Jira ticket key is also provided (e.g. `pr-review #42 PROJ-10`), use it. Otherwise, extract the ticket key from the PR title, branch name, or body.

2. **Fetch PR metadata** using `gh`:
   ```
   gh pr view <number> --json title,body,state,baseRefName,headRefName,author,files,additions,deletions,commits,labels,reviewDecision,mergeable
   ```

3. **Fetch the full diff:**
   ```
   gh pr diff <number>
   ```

4. **Fetch PR comments and review comments** via `gh api`.

5. **Present a PR summary** to the user:
   - Title, author, branch (`head` → `base`)
   - File count, additions, deletions
   - Linked ticket key (found or "none detected — ask user")
   - PR state and mergeable status

If no ticket key is found and none was provided, ask the user: "I could not detect a linked Jira ticket. Please provide the ticket key, or confirm this PR has no ticket."

## Phase 2 — Fetch the Jira Ticket

Skip this phase if the user confirmed there is no linked ticket.

1. Get the Jira Cloud ID from `.cursor/rules/jira-config.mdc`.
2. Call `getJiraIssue` (MCP server `user-Atlassian`) with the ticket key.
3. Extract: summary, description, acceptance criteria, status, type.

## Phase 3 — Code Review

Evaluate the diff against these dimensions:

| Dimension | What to check |
|-----------|--------------|
| **Correctness** | Does the code do what the ticket says? Are edge cases handled? |
| **AC coverage** | Is every acceptance criterion covered by code and/or tests? |
| **Tests** | Are there tests? Do they cover happy path, errors, and edge cases? |
| **Security** | Injection, auth, secrets in code, input validation at boundaries |
| **Error handling** | Are errors caught, logged, and surfaced appropriately? |
| **Code quality** | Readability, naming, no dead code, no unnecessary complexity |
| **Best practices** | Follows patterns used in the rest of the codebase |

## Phase 4 — Structured Review Output

Present the review in this format:

```
## PR Review: <title> (#<number>)

### Summary
[2-3 sentences: what the PR does and overall verdict]

### Verdict
[ ] Approve  [ ] Request changes  [ ] Comment only

### AC Coverage
| AC | Covered? | Notes |
|----|----------|-------|
| <ac item> | ✅ / ❌ / ⚠️ | <note> |

### Issues
#### Blocking
- [issue] — [file:line if applicable]

#### Non-blocking
- [suggestion]

### Positives
- [what was done well]
```

## Phase 5 — Post Review (optional)

Ask the user: "Do you want me to post this review as a GitHub PR comment?"

If yes, use `gh pr review <number> --comment --body "<review text>"` or `--approve` / `--request-changes` depending on verdict.

## Rules

- **Never approve a PR with blocking issues.**
- **If no Jira ticket**: still review code quality; skip AC coverage section.
- **Be specific**: reference file names and line numbers for issues.
- **Be constructive**: frame issues as suggestions when possible.
