# Chowkidar — Commit Conventions

**Last updated:** 2026-10-23  
**Status:** Active  
**Purpose:** Keep the git history clean, logical, and easy for a human to follow.

---

## 1. Principles

1. **One logical change per commit.** Do not mix unrelated changes.
2. **Every commit should leave the repo in a coherent state.** Ideally buildable; at minimum, the changed area should be understandable.
3. **Write commit messages for a human reviewer**, not for the AI.
4. **Commit early and often**, but not so often that the history becomes noise.
5. **Do not rewrite history after the base is shared** unless the team agrees.
6. **Link issues/PRs** where applicable.

---

## 2. Format

Use **Conventional Commits**:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | Use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding/updating tests |
| `chore` | Build, tooling, dependencies, config |
| `perf` | Performance improvement |
| `style` | Formatting, no logic change |
| `ci` | CI/CD changes |
| `db` | Schema/migration changes |
| `security` | Security-related changes |

### Scopes

Examples: `web`, `api`, `agents`, `ingest`, `db`, `auth`, `evals`, `docs`, `infra`, `ui`, `mcp`.

### Examples

```
chore(repo): initialize monorepo and planning docs
feat(api): add risk register endpoints
feat(web): add dashboard shell and risk table
feat(agents): add extractor and mapper pipeline
db: add obligations, risks, and approvals schema
docs: add architecture and local setup guide
test(evals): add golden set for EU regulatory changes
ci: add lint, typecheck, and test workflow
```

---

## 3. Commit size

- **Good:** one endpoint + its test; one UI screen + its data hook; one schema migration + seed update.
- **Too small:** “fix typo” 10 times in a row; “wip” commits.
- **Too large:** “build entire app” in one commit after the initial scaffold.
- **Rule of thumb:** if the commit message needs “and” three times, split it.

---

## 4. Branching

- `main` is the stable branch.
- For the initial build, commit directly to `main` in logical steps (the AI agent is the sole builder).
- After the base is shared with the team, use short-lived feature branches:
  - `feat/risk-register`
  - `fix/approval-rbac`
  - `docs/submission-story`
- Merge via PR when the team is collaborating; squash only if the PR has noisy commits.

---

## 5. Commit body

Use the body to explain **why**, not just **what**:

```
feat(agents): add verifier agent for citation checks

The extractor can produce plausible but unsupported claims. The verifier
checks each claim against retrieved source spans and marks unsupported
claims as "insufficient evidence" before they reach the risk register.

Refs: #12
```

---

## 6. What not to commit

- Secrets, API keys, `.env` files.
- Large raw datasets (use `data/` with `.gitignore` or object storage).
- `node_modules`, `.next`, `__pycache__`, `.venv`.
- Generated build artifacts.
- Personal notes that should not be public.

---

## 7. Initial build sequence (planned)

The AI agent will build the base in one pass, with commits like:

1. `chore(repo): initialize git, gitignore, and project docs`
2. `chore(tooling): add project manifest and dev scripts`
3. `feat(api): add FastAPI app skeleton and health endpoint`
4. `db: add core schema and seed data`
5. `feat(ingest): add source registry and mock connectors`
6. `feat(agents): add extraction, mapping, scoring, and remediation pipeline`
7. `feat(api): add risk, approval, and report endpoints`
8. `feat(web): add dashboard and risk register`
9. `feat(web): add risk detail and approval workflow`
10. `feat(web): add report and admin screens`
11. `test: add API and agent tests`
12. `docs: add architecture, setup, API, and demo guide`
13. `ci: add lint, test, and build workflow`
14. `chore(deploy): add Docker Compose and deployment config`

> The exact sequence will be adjusted once the stack is approved. The goal is a history a human can read top-to-bottom and understand how the base was built.

---

## 8. Review checklist

Before committing:

- [ ] The change is one logical unit.
- [ ] The message follows the convention.
- [ ] Tests pass (or the reason is documented).
- [ ] No secrets or generated files.
- [ ] Docs updated if behavior changed.
- [ ] The commit can be understood without reading the diff first.
