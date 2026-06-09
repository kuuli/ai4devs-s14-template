---
name: implement
description: Implements a Jira ticket end-to-end — reads the ticket, analyzes scope and AC, asks about unknowns, creates a feature branch, moves the ticket to In Progress, follows TDD for features/bugs, and creates a PR when done. Use when the user says "implement" followed by a Jira ticket key (e.g., "implement PROJ-42").
---

# Implement Command

Triggered when the user provides a Jira ticket key to implement. Follow these phases **in order**. Do NOT skip the questioning phase.

## Phase 1 — Read the Ticket

1. Get the Jira Cloud ID from `.cursor/rules/jira-config.mdc`.
2. Call `getJiraIssue` (MCP server `user-Atlassian`) with the ticket key.
3. Extract and present to the user:
   - **Summary** and **Type** (story, task, bug, epic)
   - **Description** (purpose, scope, context, done-when)
   - **Acceptance Criteria**
   - **Status**, **Priority**, **Labels**, **Components**
   - **Epic link** and **Sub-tasks** (if any)

Display a clean summary so the user can confirm you understood the ticket correctly.

## Phase 2 — Analyze and Question

**This phase is mandatory. Never skip it.**

Review every aspect of the ticket and build a list of questions:

| Check | What to look for |
|-------|-----------------|
| **Scope gaps** | Is the in-scope / out-of-scope boundary clear? |
| **AC completeness** | Does every AC have a testable condition? Are edge cases covered? |
| **Technical unknowns** | Which files, modules, APIs, or schemas are affected? |
| **Dependencies** | Does this ticket depend on other tickets, services, or data? |
| **Business rules** | Are domain rules referenced and reflected in AC? |
| **Ambiguity** | Vague words that need concrete definitions? |

**Present ALL questions to the user at once.** Wait for answers before proceeding.

**If you have zero questions**, state explicitly: "I have no questions — the ticket is fully clear" and confirm with the user before moving on.

## Phase 3 — Plan

1. Create a structured implementation plan using `TodoWrite`:
   - Break the work into small, concrete tasks.
   - Order tasks by dependency.
   - Note which tasks need tests first (TDD).

2. **Detect applicable project skills** based on ticket content:
   - Ticket involves LangChain / chatbot → apply `.cursor/skills/langchain-chatbot-expert/SKILL.md`
   - Ticket involves writing Jira content → apply `.cursor/skills/jira-tickets/SKILL.md`
   - Ticket involves documentation → apply `.cursor/skills/technical-documentation/SKILL.md`

3. **Map acceptance criteria to test scenarios.** Each AC becomes one or more test cases. Present the mapping to the user for confirmation.

## Phase 4 — Prepare the Environment

1. **Create a feature branch:**
   ```
   git checkout -b feature/<TICKET-KEY>-<short-slug>
   ```
   Derive `<short-slug>` from the ticket summary (lowercase, hyphens, max 5 words).

2. **Transition the ticket to "In Progress":**
   - Call `getTransitionsForJiraIssue` to find the transition whose name contains "Progress".
   - Call `transitionJiraIssue` with that transition ID.

3. **Add a comment to the Jira ticket:**
   ```
   Implementation started. Branch: `feature/<TICKET-KEY>-<short-slug>`
   ```

## Phase 5 — Implement

### For features and bugs (TDD)

1. **Write failing tests first.** Cover:
   - Happy path (from AC)
   - Validation and error cases (from AC)
   - Edge cases
   - Null/empty/wrong-type inputs
2. Show the tests to the user. Proceed only when approved.
3. **Write implementation** that makes tests pass.
4. **Run tests** and fix until green.

### For documentation or config-only tickets

Implement directly — no test-first step needed.

### Quality during implementation

- Hunt edge cases (pessimistic coder mindset).
- Check for SOLID violations; suggest refactoring if found.
- Run lints after substantive edits and fix introduced errors.
- Enforce project business rules.

## Phase 6 — Finalize

1. **Run full test suite** and verify all AC are satisfied.
2. **Commit changes** with a message referencing the ticket key:
   ```
   feat(<TICKET-KEY>): <summary>
   ```
3. **Push the branch** and **create a Pull Request** using `gh pr create`:
   - Title: `[<TICKET-KEY>] <Summary>`
   - Body: Summary of changes, test plan, link to Jira ticket.
4. **Transition the ticket** to "In Review":
   - Call `getTransitionsForJiraIssue` and `transitionJiraIssue`.
5. **Add a completion comment** to the Jira ticket with the PR link.

## Questioning Rules

- **Never assume.** If the ticket does not say it, ask.
- **Never infer scope.** If it is not in the AC, do not build it.
- **Group questions.** Present all questions at once.
- **Quote the ticket.** Reference the specific part that is unclear.
- **If a question is blocking**, say so explicitly.

## Configuration

| Setting | Source |
|---------|--------|
| Jira Cloud ID | `.cursor/rules/jira-config.mdc` |
| Repository URL | `.cursor/rules/repository.mdc` |
