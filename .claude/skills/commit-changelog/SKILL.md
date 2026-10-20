---
name: commit-changelog
description: >
  Updates CHANGELOG.md from the staged changes and creates an English Conventional
  Commit. Trigger: when the user asks to commit ("commit", "hacé un commit",
  "commiteá", "commit changes", "commitealo").
---

# Commit + Changelog

Every commit in this repo keeps `CHANGELOG.md` in sync with the staged changes.
Everything written (changelog entries AND commit message) is in **English**, even
if the user talks in Spanish.

## Workflow

### 1. Inspect staged changes

```bash
git diff --staged --stat
git diff --staged
```

- If NOTHING is staged → run `git status --short`, show it, and STOP asking the user
  what to stage. NEVER run `git add -A` / `git add .` on your own.
- Only the staged diff counts. Ignore unstaged and untracked files.

### 2. Classify the changes

Map each change to a Keep a Changelog subsection:

| Subsection | Use for |
|------------|---------|
| Added | New features, modules, endpoints, config options |
| Changed | Behavior changes to existing functionality, refactors with visible effect |
| Deprecated | Features scheduled for removal |
| Removed | Features removed |
| Fixed | Bug fixes |
| Security | Vulnerability fixes, hardening (signatures, secrets, auth) |

Pure `chore` / `ci` / `style` / `test` changes with no user-visible effect do NOT
get a changelog entry (say so in the proposal).

### 3. Update `CHANGELOG.md`

- Insert bullets under `## [Unreleased]`.
- Reuse existing subsections; create only the ones needed, in the canonical order
  above (Added, Changed, Deprecated, Removed, Fixed, Security).
- Bullets describe WHAT changed and WHY from a user's point of view — not file lists.
  - Good: `- Postgres-backed delivery queue using SKIP LOCKED leases.`
  - Bad: `- Added src/pg_webhook_gateway/db/queue.py.`
- No duplicate bullets: if an equivalent entry already exists, refine it instead.
- Do NOT touch the header, the HTML comment block, released versions, or the link
  references at the bottom.
- Never create a version section (`## [X.Y.Z]`) unless the user explicitly asks for
  a release.

### 4. Draft the commit message

[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), English:

```
<type>(<scope>): <subject>

<body: optional, explains WHY, wrapped at 72>

<footer: optional, e.g. BREAKING CHANGE: ...>
```

- `type`: feat, fix, refactor, perf, docs, test, build, ci, chore, style, revert.
- `scope` (optional): the `src/pg_webhook_gateway/` subpackage touched — `api`, `db`, `dispatcher`,
  `domain`, `observability`, `security`. Omit when changes span many modules.
- `subject`: imperative mood, lowercase, no trailing period, ≤ 72 chars.
- Breaking change → `!` after type/scope and a `BREAKING CHANGE:` footer.
- **NEVER** add `Co-Authored-By`, "Generated with", or any AI attribution.

### 5. Propose and WAIT

Show the user:
1. The `CHANGELOG.md` diff (`git diff CHANGELOG.md`).
2. The full commit message.

Then STOP and wait for explicit confirmation. Apply any adjustments requested.

### 6. Commit (only after OK)

```bash
git add CHANGELOG.md
git commit -F - <<'EOF'
feat(dispatcher): add retries with exponential backoff and jitter

Failed deliveries were retried immediately, hammering slow endpoints.
EOF
git log -1 --stat
```

- NEVER `--no-verify`: pre-commit hooks must run.
- NEVER push.

### 7. If a pre-commit hook fails

A failed hook means NO commit was created (`git log -1` still shows the previous
one). Retrying is a plain `git commit` again — NEVER `--amend`, that would rewrite
the previous, unrelated commit.

**Auto-fixing hooks** (they report "files were modified by this hook"):
`ruff-format`, `end-of-file-fixer`, `trailing-whitespace`. Note that `ruff-format`
also formats Python code blocks inside `.md` files.

1. Run `git diff <files>` and verify the change is formatting only (whitespace,
   line wrapping, blank lines) — no semantic change.
2. Show the diff to the user with a one-line explanation.
3. `git add <files>` and retry the SAME commit message. No new confirmation needed:
   the content the user approved is unchanged.

**Checking hooks** (`ruff check`, `mypy`, `check-toml`, etc.) or any auto-fix that
changes meaning → show the output and STOP. Propose a fix and wait for the user;
the fix changes what was approved.

## Checklist

- [ ] Only staged changes considered
- [ ] Changelog entries in English, under `[Unreleased]`, correct subsections
- [ ] Commit message in English, Conventional Commits, subject ≤ 72 chars
- [ ] No AI attribution
- [ ] User confirmed before committing
- [ ] `CHANGELOG.md` included in the same commit
- [ ] Hook auto-fixes reviewed, restaged and retried (no `--amend`)
