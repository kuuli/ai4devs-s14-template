---
name: jira-tickets
description: Writes clear Jira ticket descriptions and testable acceptance criteria for user stories, tasks, and epics. Use when creating or editing Jira tickets, user stories, acceptance criteria, backlog items, epics, or when the user asks for ticket text or story format.
---

# Jira Tickets: Descriptions and Acceptance Criteria

Apply when drafting or improving the **description** and **acceptance criteria** of a Jira ticket (user story, task, epic, or bug). Aim for clarity, testability, and alignment with the intended outcome.

## When to Use

- Creating or editing a Jira ticket (story, task, epic, bug)
- Writing or refining acceptance criteria
- User asks for "Jira ticket," "user story," "acceptance criteria," or "backlog item"
- Converting a requirement or conversation into ticket text

## Ticket Description: Best Practices

The description gives **context and scope** so anyone can understand the ticket without extra conversation.

1. **Purpose** – Why this work matters (user need, business goal, or problem solved). One or two sentences.
2. **Scope** – What is in and out of scope. Be explicit about boundaries.
3. **Context** – Relevant background: link to epic, doc, or prior ticket; mention constraints or API contracts.
4. **Success** – What "done" looks like in one sentence.

Avoid: vague goals, implementation details in the description, or walls of text. Keep it scannable (short paragraphs or bullets).

## Description Template

```markdown
## Purpose
[Why we're doing this – user need or problem.]

## Scope
- In scope: [what will be delivered]
- Out of scope: [what we are not doing in this ticket]

## Context
[Links to epic, doc, or related tickets; relevant constraints or rules.]

## Done when
[One sentence: what "done" means for this ticket.]
```

## Acceptance Criteria: Best Practices

Acceptance criteria (AC) are **testable conditions** that must be true for the ticket to be done.

1. **Testable** – Each criterion can be verified. Avoid "should work well"; use observable behaviour.
2. **User- or outcome-focused** – Prefer "When [condition], then [observable result]."
3. **Independent** – Each criterion stands alone; no "and" chains.
4. **Complete** – Cover happy path, key edge cases, and error/validation cases.
5. **Unambiguous** – Use concrete terms; reference business rules by name or link when relevant.

## AC Formats

**Option A – Given/When/Then (BDD-style)**
Good for flows and scenarios.

- Given [precondition / current state]
- When [action or trigger]
- Then [observable outcome]

**Option B – Bullet list (checkable)**
Good for feature lists and config.

- [ ] [Observable condition 1]
- [ ] [Observable condition 2]

Use one format per ticket. Prefer Given/When/Then for user flows; bullets for discrete checks.

## AC Template (Given/When/Then)

```markdown
## Acceptance criteria

- **Happy path**
  - Given [precondition], when [user action], then [expected result].

- **Validation / errors**
  - Given [precondition], when [invalid or edge input], then [expected message or behaviour].

- **Edge cases** (if needed)
  - Given [precondition], when [edge case], then [expected result].
```

## Quality Checklist

Before finalising a ticket:

- [ ] Description has purpose, scope, context, and "done when."
- [ ] Scope clearly states what is out of scope.
- [ ] Every acceptance criterion is testable.
- [ ] AC covers at least the happy path and main validation/error case.
- [ ] No vague or subjective wording in AC ("user-friendly," "works well").
- [ ] Business rules are named or linked and reflected in AC.
- [ ] One format (Given/When/Then or bullets) used for AC in this ticket.

## Language

Write descriptions and acceptance criteria in **English** unless the team or project uses another language for Jira.
