# PR Review Command — Workflow Reference

Edge cases, decision trees, and error handling for the pr-review command.

## Input Parsing

### PR number formats
- `42`, `#42` → use `42` as the PR number.
- Full PR URL → extract the number from the URL path.

### Ticket key extraction priority
1. Explicit key provided by user (e.g. `pr-review #42 PROJ-10`).
2. PR title pattern: `[PROJ-10]` or `(PROJ-10)`.
3. Branch name pattern: `feature/PROJ-10-some-slug` or `fix/PROJ-45-something`.
4. PR body: first match of the project ticket pattern.
5. If none found → ask the user.

### No ticket linked
- If the user confirms there is no ticket, skip Phase 2 and Phase 4.
- Adjust the verdict criteria: without AC, base the review on code quality only.
- Note in the summary: "No Jira ticket linked — review based on code quality only."

## PR State Edge Cases

### PR is closed or merged
- Warn: "This PR is already `<state>`. The review will still run, but findings cannot be acted on through this PR."
- Continue the review — it can still be useful for learning or auditing.

### PR is a draft
- Note: "This is a draft PR. Review findings are advisory."
- Continue normally.

### PR has no diff (0 changes)
- Tell the user: "PR #`<number>` has no file changes. Nothing to review."
- Stop.

### PR has merge conflicts
- Flag in the summary: "This PR has merge conflicts that must be resolved before merging."
- Continue the code review on the current diff.

### Very large PR (>20 files or >1000 lines changed)
- Warn: "This is a large PR (`<N>` files, `<M>` lines). Consider splitting it for easier review."
- Continue but focus on:
  1. Files related to the ticket's AC first.
  2. New files (more likely to have issues).
  3. Test files (verify coverage).
  4. Modified core files.

## Jira Ticket Edge Cases

### Ticket not found
- Warn: "Jira ticket `<KEY>` not found. Proceeding with code-only review."
- Skip Phase 4 (AC verification).
- Adjust verdict: no AC coverage matrix.

### Ticket has no AC
- Warn: "Ticket `<KEY>` has no acceptance criteria. Cannot verify AC coverage."
- Skip Phase 4.
- Suggest: "Consider running `enrich <KEY>` to add acceptance criteria before review."

### Ticket is not in expected status
- If ticket is in "To Do" (not started): note "Ticket is still in 'To Do' — implementation may be incomplete."
- If ticket is "Done": note "Ticket is already 'Done' — this may be a post-merge review."
- Continue review regardless.

### AC is vague or untestable
- If an AC cannot be mapped to code because it is vague, classify as "Cannot verify" in the matrix.
- Add a finding: severity `suggestion`, recommending the AC be rewritten.

## Code Review Decision Trees

### Severity classification

```
Is there a bug or data loss risk?
  ├─ Yes → critical
  └─ No
      ├─ Could this cause incorrect behavior under normal use?
      │   ├─ Yes → warning
      │   └─ No
      │       ├─ Would fixing this improve maintainability or clarity?
      │       │   ├─ Yes → suggestion
      │       │   └─ No → nitpick
      └─ Is this a security vulnerability?
          └─ Yes → critical
```

### When to flag vs ignore

```
Is the issue introduced by this PR (in the diff)?
  ├─ Yes → always flag
  └─ No (pre-existing)
      ├─ Is it critical (bug, security)?
      │   ├─ Yes → flag as critical, note "pre-existing"
      │   └─ No → do not flag (out of scope for this review)
```

### Project-specific checks

```
Does the diff touch domain rule enforcement (tools, validators)?
  ├─ Yes → verify all business rules from docs/business-rules.md are still enforced
  │   ├─ Enforced → note as strength
  │   └─ Not enforced → critical finding
  └─ No → skip

Does the diff touch LangChain / chatbot code?
  ├─ Yes → check LCEL patterns, structured output, tool design
  └─ No → skip

Does the diff change user-facing behavior?
  ├─ Yes → check if docs/README updated
  │   ├─ Updated → note as strength
  │   └─ Not updated → suggestion finding
  └─ No → skip
```

## Verdict Decision Tree

```
Any critical findings?
  ├─ Yes → Request Changes
  └─ No
      ├─ Any warning findings?
      │   ├─ Yes → Request Changes
      │   └─ No
      │       ├─ Any AC not covered?
      │       │   ├─ Yes → Request Changes
      │       │   └─ No
      │       │       ├─ Any suggestions or nitpicks?
      │       │       │   ├─ Yes → Comment
      │       │       │   └─ No → Approve
      │       └─ (no AC available) → base on code quality alone
```

## Posting Review — Edge Cases

### gh CLI not authenticated
- If `gh pr view` fails with auth error: tell the user "GitHub CLI is not authenticated. Run `gh auth login` and try again."
- Stop.

### Atomic review API fails
- The primary posting method is `gh api repos/.../pulls/<number>/reviews` with inline `comments`.
- **422 "Validation Failed"** — usually means a `line` value is not within the diff hunk for that file.
  - Remove the offending comment from the `comments` array.
  - Move that finding into the review body text.
  - Retry the API call. Repeat until the call succeeds or all comments are moved to the body.
- **403 / auth error** — tell the user to check `gh auth status` and ensure the token has `repo` scope.
- **404** — PR number does not exist or repo access denied. Stop and inform the user.
- **Other errors** — fall back to `gh pr review <number> --body "<body>" --<event>` (no inline comments).

### Inline comment line is outside the diff
- GitHub only allows inline comments on lines that appear in the diff hunks.
- If a finding's line is outside all hunks for that file, classify it as body-only.

### Large number of findings (>30 inline comments)
- If there are more than 30 inline findings, batch them:
  1. Post the first 25 as inline comments in the atomic review.
  2. Include the remaining findings in the review body.
- Warn the user: "This PR has many findings. Some are included in the review body instead of inline."

### `--local` flag handling
- If the user includes `--local`, `local`, or phrases like "don't post" or "keep it local", skip all GitHub posting.
- Output the full review in the conversation only.

### Jira comment post fails
- If `addCommentToJiraIssue` fails: show the error and suggest the user add the comment manually.
- Do not block the review output.

### Bot / CI token limitations
- Some tokens cannot post reviews with `APPROVE` or `REQUEST_CHANGES` events.
- If the API returns an error about review event permissions, retry with `"event": "COMMENT"` and note the limitation.

## Review Etiquette

- Use a professional, constructive tone.
- Frame suggestions as questions when possible.
- Do not pile on — if the same pattern repeats across files, flag it once.
- Balance negative and positive — acknowledge what was done well.

## Integration with Other Commands

### After pr-review, user wants fixes
- Suggest running `implement` on the ticket, or making manual fixes on the PR branch. The pr-review command itself does not edit code.

### Re-review after changes
- The user can run `pr-review <number>` again after the PR is updated. The command is idempotent.

### Review + enrich
- If the review reveals missing or vague AC, suggest: "Run `enrich <KEY>` to improve the acceptance criteria, then re-review."
