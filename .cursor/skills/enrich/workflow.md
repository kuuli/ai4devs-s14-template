# Enrich Command — Workflow Reference

Edge cases and decision flow for the enrich command.

## Ticket Reading

### Ticket not found
- If `getJiraIssue` fails or returns empty: tell the user "Ticket `<KEY>` not found. Check the key and Atlassian MCP connection." Stop.

### Extract key from URL
- From `https://<org>.atlassian.net/browse/PROJ-9` → use `PROJ-9`.
- From a board URL → do not assume a key; ask for a direct ticket link (`.../browse/<KEY>`).

## Gap Analysis

### Empty description
- Treat as "missing all description structure". Draft full Purpose, Scope, Context, Done when from the summary and type. If the summary is too vague, ask the user for one sentence on purpose before drafting.

### Description present but weak
- Fill only missing sections; refine vague sentences per jira-tickets skill. Do not replace clear, correct text unless it improves testability or scope clarity.

### No acceptance criteria
- Draft AC from the description and ticket type. Prefer Given/When/Then for flows; bullets for config or checklist-style work. Ask the user to confirm or extend.

## Phase 3 — Clarifying Questions

### No questions
- If the ticket and gap analysis leave nothing unclear, state: "No clarifying questions — the ticket is clear enough for implementation." Ask the user to confirm before Phase 4.

### User defers or answers "figure it out"
- Note the open point in **Technical notes** or **Context** (e.g. "Technical approach TBD; implement to propose and document."). Do not block the draft.

### Follow-up questions
- If answers from Phase 3 reveal new ambiguities, ask follow-up questions. Once satisfied, proceed to Phase 4.

### Answers must appear in the ticket
- Every material answer from Phase 3 must be reflected in the enriched description, AC, or technical notes so that implement does not have to re-ask.

## Pushing to Jira

### editJiraIssue fails (e.g. "Failed to convert markdown to ADF")
- Offer the full description as **markdown** for the user to paste manually into Jira.

### User wants only summary updated
- Call `editJiraIssue` with `fields: { summary: "New summary" }`. Confirm the exact text with the user first.

### Comment after update
- If the user asked to push, you may add a short comment via `addCommentToJiraIssue`. Do not add a comment if the user chose copy-paste only.

## Skill Interaction

- **Enrich** runs before **implement**. Enrich adds specs and AC; implement uses them.
- When enriching a ticket that involves LangChain / chatbot logic, optionally reference `.cursor/skills/langchain-chatbot-expert/SKILL.md` for technical notes. Only add context that belongs in the ticket (e.g. tool names, relevant domain constraints from `docs/business-rules.md`).

## Quality Checklist (from jira-tickets)

Before finalising enriched content:

- [ ] Description has Purpose, Scope, Context, Done when
- [ ] Scope states what is out of scope
- [ ] Every AC is testable
- [ ] AC covers happy path and at least one validation/error case
- [ ] No vague wording ("user-friendly", "works well")
- [ ] Business rules named or linked and reflected in AC
- [ ] One AC format (Given/When/Then or bullets) used
