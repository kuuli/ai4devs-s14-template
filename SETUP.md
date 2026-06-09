# SETUP — New Bot Bootstrap

This file is a prompt for Claude Code. When starting a new bot from this template, tell Claude Code:

> "Follow SETUP.md"

Claude Code will collect the information below and apply all changes automatically.

---

## Instructions for Claude Code

You are setting up a new chatbot project from the LangChain + FastAPI template. Follow these phases in order.

### Phase 1 — Collect information

Ask the user ALL of the following questions at once. Wait for answers before making any changes.

**Project identity**
1. What is the name of this bot / project? _(used in titles, headers, README)_
2. What is the GitHub repository URL? _(owner/repo, e.g. `kuuli/hotel-chatbot`)_
3. Does this project have a Jira board? If yes: project key (e.g. `HOTEL`), Cloud ID, and Atlassian site URL.

**Bot purpose**
4. In one or two sentences: what does this bot do and for whom?
5. What language should the bot speak to users? _(Spanish / English / other)_
6. What tone should it have? _(e.g. professional, friendly, formal)_

**Domain and rules**
7. What are the main business rules or constraints the bot must enforce? _(e.g. operating hours, capacity limits, required fields, forbidden actions)_ — or say "none yet" to leave the docs as placeholders.
8. Is there operational information the bot should know? _(e.g. service description, pre/post conditions, contact details)_ — or say "none yet".

**Tools**
9. Does the bot need to call any external API or perform actions (lookups, bookings, sending data)? If yes, describe each tool briefly: name, what it does, what inputs it needs.

**Channels**
10. Will this bot use WhatsApp (Meta Cloud API)? _(yes / no)_

**Environment**
11. What OpenAI model should it use? _(default: `gpt-4o-mini`)_

---

### Phase 2 — Apply changes

Once you have the answers, apply ALL of the following changes. Use the answers to fill in each file. Do not leave placeholders unfilled if the user provided the information.

#### `.cursor/rules/repository.mdc`
- Replace `<owner>` and `<repo-name>` with the GitHub owner and repo name from answer 2.

#### `.cursor/rules/jira-config.mdc`
- If answer 3 is "no Jira": add a note at the top: `> No Jira board for this project.` and leave the rest as-is.
- If yes: replace `<your-jira-cloud-id>`, `<your-org>`, and update the project key throughout.

#### `public/index.html`
- `<title>`: set to bot name (answer 1).
- `.chat-header`: set to bot name or a short tagline.
- Welcome message in `appendMessage(...)`: write a short, on-brand greeting using the bot's purpose (answer 4) and language (answer 5).

#### `prompt.md`
- Replace the placeholder content with a real system prompt using:
  - Answer 4 (bot purpose) → "You are…" opening line.
  - Answer 5 (language) → add an instruction like "Always respond in [language]."
  - Answer 6 (tone) → add a tone/persona instruction.
  - Answer 7 (business rules) → add a "## Rules" section with each rule.
  - Answer 9 (tools) → add instructions on when to call each tool.
- Keep the `{today}` variable at the top.

#### `docs/business-rules.md`
- If answer 7 is "none yet": leave the file as a placeholder.
- If rules were provided: replace the placeholder sections with the actual rules, one per section. Include where each rule is enforced (tool / prompt / both).

#### `docs/considerations.md`
- If answer 8 is "none yet": leave the file as a placeholder.
- If information was provided: fill in the relevant sections (service profile, process overview, contact details, etc.).

#### `tools.py`
- If answer 9 is "no tools": leave `TOOLS = []` as-is.
- If tools were described: create a stub `@tool` function for each one with the correct name, parameters, docstring describing purpose and inputs, and a `# TODO: implement` body. Add them to `TOOLS`.

#### `CLAUDE.md`
- Update the title to the bot name.
- If a Jira project key was provided (answer 3): add a line at the bottom: `## Jira project` / `Issues are tracked as \`<KEY>-*\` tickets.`
- If tools were added (answer 9): update the key files table to include the new tools with their purpose.

#### `README.md`
- Replace the generic title and description with the bot name and purpose (answers 1 and 4).
- Update the tech stack or notes if anything is project-specific.

#### `vercel.json`
- If answer 10 is "no WhatsApp": remove the `{ "src": "/webhook", "dest": "main.py" }` route.
- If yes: leave it as-is.

#### `.env` setup
- Tell the user: "Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`" + any other vars needed based on answers 9 and 10.
- Do NOT create or edit `.env` yourself.

#### `main.py`
- If answer 10 is "no WhatsApp": remove the WhatsApp section (the `_WA_*` variables, `_send_whatsapp_message`, and the `GET /webhook` and `POST /webhook` endpoints).
- If yes: leave it as-is.

---

### Phase 3 — Confirm and run tests

1. Show the user a summary of all files changed.
2. Run `pytest` and confirm all tests pass.
3. If any test fails due to content changes (e.g. the index.html content check), fix the test to match the new content.
4. Tell the user what to do next:
   - Fill in `.env` with the real API key.
   - Complete any `# TODO` stubs in `tools.py`.
   - Fill in `docs/` files if left as placeholders.
   - Run `uvicorn main:app --reload` to test locally.
