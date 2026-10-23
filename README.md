# Chowkidar — AI Builders Congress 2026

**Project:** Chowkidar — agentic compliance risk intelligence for export supply chains  
**Event:** International AI Builders Congress 2026  
**Track:** Idea to Unicorn — Preliminary Submission  
**Domain:** JusticeSphere AI  
**Challenge:** Risk Sentinel  
**Deadline:** 2026-10-31, 11:59 PM GMT+6  
**Status:** Planning — stack decisions pending

---

## What is Chowkidar?

Chowkidar monitors regulatory changes, sanctions/watchlists, and global risk signals; maps them to a company's obligations, policies, contracts, suppliers, and controls; and turns them into a prioritized risk register with evidence-backed remediation plans and human approval.

**Tagline:** *See the risk. Approve the fix.*

**Why this wedge:** It matches the official Risk Sentinel brief 1:1 — two data streams, a prioritized risk audit, automated remediation, and a human-in-the-loop approval interface — with a strong Bangladesh beachhead (RMG/leather/agro exports) and a global expansion story.

**Important positioning:** Chowkidar is **compliance risk intelligence, not legal advice**. Every output is source-grounded, conservative, and requires human approval.

---

## Project docs

| Doc | Purpose |
|---|---|
| [`STRATEGY.md`](STRATEGY.md) | Why JusticeSphere/Risk Sentinel, saturation analysis, strategic case, business model |
| [`DECISIONS.md`](DECISIONS.md) | Decision log, constraints, assumptions, open questions, session history |
| [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md) | Personas, workflows, MVP features, data model, agents, RAG, evals, guardrails, demo |
| [`BUILD_PLAN.md`](BUILD_PLAN.md) | 8-day plan, roles, cut list, submission checklist, video script, QA |
| [`prompts/MASTER_PROMPT.md`](prompts/MASTER_PROMPT.md) | Draft single master prompt for the Idea to Unicorn build |
| [`docs/COMMIT_CONVENTIONS.md`](docs/COMMIT_CONVENTIONS.md) | Commit message and history conventions |
| [`docs/`](docs/) | Research, data sources, build log, architecture notes (to be added) |

---

## Current decisions

- **Domain/challenge:** JusticeSphere AI → Risk Sentinel.
- **Product:** Chowkidar — regulatory + supplier risk sentinel for export supply chains.
- **Positioning:** Compliance risk intelligence, not legal advice.
- **Constraint:** No legal/compliance advisor; mitigate with evidence-first design, citations, conservative scope, human approval, and source-grounded evals.
- **Constraint:** Per-domain submission counts are not available; saturation analysis is directional.
- **Build rule:** One master prompt applies to the **whole build**; the AI agent builds the base alone, then the team modifies/improves.
- **Process:** Commit history must be clean and human-followable; every stack decision is approved by the user first.
- **Build window:** 8 days; submit by 6 PM GMT+6 on Oct 31.

See [`DECISIONS.md`](DECISIONS.md) for the full log.

---

## Next steps

1. Answer the stack-decision questions (language, package manager, frontend, backend, DB, auth, AI stack, deployment).
2. Finalize `prompts/MASTER_PROMPT.md` v1.0.
3. Initialize git and commit the planning docs.
4. Execute the master prompt as one build pass with logical commits.
5. Validate data source access from Bangladesh.
6. Keep `DECISIONS.md` updated after every meaningful decision.

---

## Context management

This repo is the project's external memory. At the start of each session, read:

1. `README.md`
2. `DECISIONS.md`
3. `PRODUCT_SPEC.md`
4. `BUILD_PLAN.md`

At the end of each session, append a session log entry to `DECISIONS.md` with what changed, what's next, and blockers.

---

## Contact / links

- Team: JU_StackMind
- Event: https://cloudcampbd.com/ai-builders-congress
- MCP knowledge base: `cloudcamp://knowledge-base` via the event MCP server
- Repo: TBD
- Live demo: TBD
- Video: TBD
