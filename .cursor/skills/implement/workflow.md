# Implement Command — Workflow Reference

Detailed decision trees, edge cases, and error handling for each phase.

## Ticket Reading — Edge Cases

### Ticket not found
If `getJiraIssue` returns an error or empty result:
- Tell the user: "Ticket `<KEY>` not found. Verify the key and that the Atlassian MCP is connected."
- Stop. Do not proceed.

### Ticket already in progress or done
If the ticket status is already "In Progress", "In Review", or "Done":
- Inform the user of the current status.
- Ask: "This ticket is already `<status>`. Do you want to continue implementing from the current state?"

### Ticket has sub-tasks
If the ticket is an epic or has sub-tasks:
- List all sub-tasks with their status.
- Ask which sub-task(s) to implement, or whether to implement the parent scope.

### Missing description or AC
If the description is empty or there are no acceptance criteria:
- Flag this as a blocker.
- Suggest: "Use the **enrich** command first: `enrich <TICKET-KEY>` to add description and AC, then run implement again."

## Questioning — Decision Tree

```
Read ticket
  │
  ├─ Scope clear?
  │   ├─ Yes → proceed
  │   └─ No  → ask: "What is in/out of scope for <specific area>?"
  │
  ├─ AC testable?
  │   ├─ Yes → proceed
  │   └─ No  → ask: "AC says '<vague text>' — what is the measurable condition?"
  │
  ├─ Technical approach known?
  │   ├─ Yes → proceed
  │   └─ No  → ask: "Which module/API/pattern should handle <feature>?"
  │
  ├─ Dependencies resolved?
  │   ├─ Yes → proceed
  │   └─ No  → ask: "Ticket <DEP-KEY> is not done. Can we proceed, or is it a blocker?"
  │
  ├─ Business rules referenced?
  │   ├─ Yes → proceed
  │   └─ No  → ask: "Should any domain rule from docs/business-rules.md apply here?"
  │
  └─ Any assumptions?
      ├─ None → proceed
      └─ List each → ask: "I'm assuming <X>. Is that correct?"
```

## Branch Naming

Format: `feature/<TICKET-KEY>-<short-slug>`

Rules:
- `<TICKET-KEY>`: exact Jira key, uppercase (e.g., `PROJ-12`)
- `<short-slug>`: from ticket summary, lowercase, hyphens, max 5 words
- Example: `feature/PROJ-12-add-availability-check`

For bug-type tickets, use `fix/` prefix: `fix/PROJ-45-null-date-crash`

## Transition Mapping

Jira workflows vary. The skill discovers transitions dynamically:

1. Call `getTransitionsForJiraIssue` for the ticket.
2. Find the transition by name (case-insensitive partial match):
   - **To start work**: look for "progress" or "start"
   - **To review**: look for "review" or "code review"
   - **To done**: look for "done" or "complete"
3. If no match found, list available transitions and ask the user which one to use.

## TDD Decision

```
Ticket type
  │
  ├─ Story / Feature  → TDD (tests first)
  ├─ Bug              → TDD (reproduce with test, then fix)
  ├─ Task (code)      → TDD (tests first)
  ├─ Task (config)    → Direct implementation
  ├─ Task (docs)      → Direct implementation
  └─ Epic             → Break into sub-tasks, then apply per sub-task
```

## Skill Detection

Match ticket content (description, labels, components) to project skills:

| Signal | Skill to apply |
|--------|---------------|
| Mentions "chatbot", "LangChain", "conversation", "tool", "agent" | `langchain-chatbot-expert` |
| Mentions "Jira", "ticket", "story", "acceptance criteria" | `jira-tickets` |
| Mentions "README", "docs", "documentation", "API reference" | `technical-documentation` |

## Commit Message Convention

Format: `<type>(<ticket-key>): <short description>`

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or correcting tests
- `chore` — config, build, or tooling changes

Examples:
```
feat(PROJ-12): add availability check tool
fix(PROJ-45): handle null date in request body
docs(PROJ-78): add API reference for /askbot endpoint
```

## Pull Request Template

```markdown
## Summary
[<TICKET-KEY>] <Ticket summary>

### Changes
- <bullet 1: what changed and why>
- <bullet 2>

### Acceptance Criteria Verification
- [x] AC 1: <description> — verified by <test or manual check>
- [x] AC 2: <description> — verified by <test or manual check>

## Test Plan
- [ ] Unit tests pass (`pytest`)
- [ ] Acceptance criteria verified
- [ ] No lint errors introduced

## Links
- Jira: [<TICKET-KEY>](<jira-site>/browse/<TICKET-KEY>)
```

## Error Recovery

### MCP call fails
- Retry once. If it fails again, inform the user and suggest checking the Atlassian MCP connection.
- Do not proceed with implementation if the ticket could not be read.

### Tests fail after implementation
- Do not skip or delete failing tests.
- Fix the implementation until tests pass.
- If a test is wrong (not the implementation), explain why and ask the user before modifying it.

### Branch already exists
- Ask the user: "Branch already exists. Switch to it, or create a new one with a different name?"

### PR creation fails
- If `gh pr create` fails, show the error and suggest manual steps.
- Still transition the Jira ticket and add the comment.
