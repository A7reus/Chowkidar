# Chowkidar — Build Log

**Last updated:** 2026-10-23  
**Status:** Active  
**Purpose:** Record how the build was produced, especially the master prompt execution, confirmation triggers, and manual changes. This supports the submission's "Build Level" and "Prompt Library" fields.

---

## 1. Rules

1. Record the **master prompt version** used.
2. Record the **model/tool** used to execute it (Claude Code, Cursor, etc.).
3. Record **confirmation triggers** used after the initial execution.
4. Record **manual changes** with reason, author, and files.
5. Record **model/prompt versions** for runtime agents.
6. Never claim a build level that is not true.
7. Link commits/PRs where possible.

---

## 2. Current build status

| Item | Status |
|---|---|
| Master prompt | v0.1 draft (`prompts/MASTER_PROMPT.md`) |
| Execution | Not started |
| Repo scaffold | Not started |
| Product code | Not started |
| Evals | Not started |
| Deployment | Not started |

---

## 3. Session log

### 2026-10-23 — Planning session
- Reviewed MCP knowledge base, public event data, and Risk Sentinel brief.
- Chose JusticeSphere → Risk Sentinel → Chowkidar.
- Confirmed team strengths (AI/full-stack, data engineering), no legal advisor, no per-domain counts.
- User confirmed final name **Chowkidar**, team **JU_StackMind**, one-prompt rule applies to the **whole build**, AI agent builds the base alone, team modifies later.
- User added requirements: clean, human-followable commit history; ask before every stack decision.
- Created planning docs: `STRATEGY.md`, `DECISIONS.md`, `PRODUCT_SPEC.md`, `BUILD_PLAN.md`, `prompts/MASTER_PROMPT.md`, `README.md`, `docs/DATA_SOURCES.md`, `docs/BUILD_LOG.md`, `docs/COMMIT_CONVENTIONS.md`.
- No product code written yet; waiting on stack decisions.

---

## 4. Master prompt execution log

| Date | Prompt version | Tool/model | Scope | Confirmation triggers | Manual changes | Commit |
|---|---|---|---|---|---|---|
| TBD | v0.1 | TBD | TBD | TBD | TBD | TBD |

### Execution notes template
```
Date:
Prompt version:
Tool/model:
Command/IDE:
Scope generated:
Files created:
Confirmation triggers used:
Manual changes:
Known issues:
Next:
```

---

## 5. Runtime prompt versions

| Agent | Prompt file | Version | Model | Last eval |
|---|---|---|---|---|
| Monitor | `prompts/runtime/monitor.md` | TBD | TBD | TBD |
| Extractor | `prompts/runtime/extractor.md` | TBD | TBD | TBD |
| Mapper | `prompts/runtime/mapper.md` | TBD | TBD | TBD |
| Scorer | `prompts/runtime/scorer.md` | TBD | TBD | TBD |
| Remediator | `prompts/runtime/remediator.md` | TBD | TBD | TBD |
| Verifier | `prompts/runtime/verifier.md` | TBD | TBD | TBD |
| Reporter | `prompts/runtime/reporter.md` | TBD | TBD | TBD |

---

## 6. Manual change log

| Date | File(s) | Change | Reason | Author |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

---

## 7. Submission claims checklist

- [ ] Build level is accurate.
- [ ] Master prompt version matches the submitted prompt.
- [ ] Runtime prompts are included in the Prompt Library.
- [ ] Manual changes are documented.
- [ ] Model/tool names are accurate.
- [ ] No exaggerated claims about legal capability.
- [ ] Disclaimers are present.
