# Chowkidar — Product Design Artifact

**Last updated:** 2026-10-26  
**Owner:** JU_StackMind  
**Public link:** <https://github.com/A7reus/Chowkidar/blob/main/docs/DESIGN.md>
**Status:** Design specification and wireframes for the working pilot. This is the
design artifact submitted in place of a Figma file. No Figma account or file was
created.

> Chowkidar is a **compliance risk intelligence** workspace, not legal advice.
> The interface is designed to make that boundary visible at every decision.

---

## 1. Design intent

Chowkidar is used by a compliance lead who is already late, already has too many
tabs open, and will be asked by a buyer or auditor to prove what they did. The
interface has three jobs:

1. **Triage fast.** Show the highest-exposure risk and why it matters before
   showing a dashboard of everything.
2. **Make evidence inspectable.** Every risk exposes a verbatim quote, a source
   citation, and a verification state. No unsourced claim is presented as fact.
3. **Make the human gate obvious.** Draft actions are not commitments. A named
   approver must decide, and the decision is written to an append-only trail.

**Design principles**

| Principle | What it means in the UI |
|---|---|
| Evidence before opinion | Quote + citation are adjacent to every risk; "needs review" is a first-class state, not an error |
| Calm urgency | Dark, low-glare surface; color is reserved for priority, verification, and live/degraded state |
| One primary action per screen | Run pipeline, approve, export, or sync; secondary actions recede |
| Honest system state | Fixture, live, fallback, degraded, and failed are labelled in words, not only color |
| Human authority | Approvals, role gates, and audit history are visible; the AI never looks autonomous over material actions |
| Bilingual by structure | English and Bengali chrome share the same layout; long translations do not break the grid |

---

## 2. Users and jobs

| Role | Primary job | What they can do |
|---|---|---|
| **Admin** | Keep the workspace trustworthy | Everything an analyst can do, plus audit verification, settings, and role visibility |
| **Analyst** | Turn signals into a defensible risk register | Run the pipeline, review signals/risks, add actions, export reports |
| **Approver** | Decide whether remediation may proceed | Review pending approvals, approve/reject with a rationale |
| **Viewer** | Understand exposure without changing it | Read-only dashboard, risks, evidence, reports, and graph |

**Primary job story**

> When a new regulation or supplier incident appears, I want to see whether it
> applies to us, inspect the exact source text, and prepare a remediation for
> approval — so that we do not miss a shipment or fail an audit.

---

## 3. Information architecture

```text
/login
  └─ Supabase email/password (hosted) or demo role cards (local)

/app
  ├─ /dashboard        Exposure summary, priority queue, source health, pipeline run
  ├─ /signals          Raw stream items, filters, source text, linked risk
  ├─ /sources          Five streams, connector, mode, health, sync action
  ├─ /risks            Filterable risk register
  │   └─ /risks/[id]   Score breakdown, evidence, actions, approvals, status
  ├─ /approvals        Pending decisions, approve/reject with rationale
  ├─ /reports          PDF/JSON/Markdown audit packs, durable download
  ├─ /graph            Company → buyers/suppliers → obligations → risks
  ├─ /search           Cited evidence retrieval (not generated answers)
  ├─ /evals            Golden-set metrics and gate results
  ├─ /audit            Hash-chained events, verification (admin)
  └─ /settings         Workspace, data modes, integrations, role reference
```

**Navigation model**

- Persistent left rail on desktop: primary workspace (Dashboard, Signals,
  Sources, Risks, Approvals, Reports), then Explore (Graph, Search, Evals), then
  Admin (Audit, Settings).
- Top bar: global search, pending-approval count, language toggle, user menu.
- Mobile: the rail collapses to a sheet; the top bar keeps search and approvals.
- The current route is indicated by a teal left marker and a raised surface, not
  by color alone.

---

## 4. Core flows

### 4.1 First look — "what needs me now?"

```text
Login → Dashboard
  1. Read the exposure strip: open risks, critical/high, pending approvals.
  2. Scan the priority queue: top 5 by score, with supplier and verification.
  3. Check source health: five streams, mode badge, last sync.
  4. If a run exists, read the pipeline panel: ingest → … → verify → repair.
  5. Open the top risk, not a generic list.
```

### 4.2 Evidence review — "can I defend this?"

```text
Risk detail
  1. Header: title, priority, score ring, status, verification badge.
  2. Score breakdown: severity, likelihood, exposure, formula.
  3. Evidence card: verbatim quote, citation label, source URL.
  4. Why this matters: rationale, obligation, jurisdiction, supplier.
  5. Actions: owner, due date, priority, state.
  6. Decision history: who approved/rejected and why.
  7. If evidence is weak: "needs review" is shown, not hidden.
```

### 4.3 Approval — "who authorized this?"

```text
Approvals (approver/admin)
  1. Open a pending item.
  2. Read the risk, the proposed action, and the evidence.
  3. Choose Approve or Reject.
  4. Enter a rationale (required for reject; recommended for approve).
  5. Confirm; the API enforces the role and appends an audit event.
  6. The item leaves the pending queue and appears in the risk's history.
```

### 4.4 Source sync — "is this live or a replay?"

```text
Sources
  1. Read the banner: five streams, live where the source allows.
  2. Each card shows role, jurisdiction, cadence, mode badge, status, last sync.
  3. Click Sync now.
  4. The API returns mode = live | fixture | fixture_fallback | live_failed.
  5. The card and toast repeat the mode in words. A fallback is amber; a failed
     live run is rose and returns an error, never a fake healthy state.
```

### 4.5 Audit — "can I prove the trail?"

```text
Audit (admin)
  1. Filter by action, actor, entity, or date.
  2. Inspect before/after payload.
  3. Click Verify chain.
  4. The API recomputes every SHA-256 link and reports the first break, if any.
```

---

## 5. Screen wireframes

### 5.1 Dashboard (desktop, 1440 px)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Chowkidar   [Search risks, signals, evidence…]        [EN/বn]  [3 pending]  │
├──────────────┬───────────────────────────────────────────────────────────────┤
│ WORKSPACE    │  Good morning, Ayesha                    [Run pipeline]       │
│ ▸ Dashboard  │  Padma Apparel · Gazipur · RMG                                │
│   Signals    │                                                               │
│   Sources    │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│   Risks      │  │ Open risks │ │ Critical   │ │ High       │ │ Approvals  │  │
│   Approvals  │  │     8      │ │     3      │ │     3      │ │  4 pending │  │
│   Reports    │  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│ EXPLORE      │                                                               │
│   Graph      │  ┌──────────────────────────────┐ ┌─────────────────────────┐ │
│   Search     │  │ Priority queue               │ │ Source health           │ │
│   Evals      │  │ 01 UFLPA cotton trace   98   │ │ BD Bank    ● healthy    │ │
│ ADMIN        │  │ 02 CSDDD supplier map   91   │ │ EUR-Lex    ● healthy    │ │
│   Audit      │  │ 03 Export proceeds      84   │ │ UFLPA      ● healthy    │ │
│   Settings   │  │ 04 Factory fire         77   │ │ GDELT      ◐ fallback   │ │
│              │  │ 05 Grievance logs       41   │ │ Fed Reg    ● live       │ │
│              │  └──────────────────────────────┘ └─────────────────────────┘ │
│              │  ┌──────────────────────────────┐ ┌─────────────────────────┐ │
│              │  │ Agent activity               │ │ Latest signals          │ │
│              │  │ Ingest 12 → Extract 11 → …   │ │ • BIS Entity List …     │ │
│              │  │ Verify 8 → Repair 1 → 7/8    │ │ • Port strike …         │ │
│              │  └──────────────────────────────┘ └─────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────────────────────┘
```

**Notes**

- The exposure strip is four equal cards; numbers use the display font, labels
  use small caps.
- The priority queue is ranked, not sorted by date. Each row shows score,
  priority, supplier, and verification state.
- Source health shows mode words, not only dots. A fallback is amber and the
  tooltip explains the live connector failed.

### 5.2 Risk detail (desktop, 1440 px)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Risks          Cotton origin documentation is incomplete   [Critical 98]  │
│                  US-bound order LT-4412 · Dhaka Knit · verified             │
├───────────────────────────────────────────────┬──────────────────────────────┤
│ Evidence                                      │ Score                        │
│ ┌───────────────────────────────────────────┐ │  ┌──────────────┐            │
│ │ “The newly listed entities are connected  │ │  │     98       │  Critical  │
│ │ to the production and sale of goods made  │ │  └──────────────┘            │
│ │ in Xinjiang … and include cotton and      │ │  Severity   4 × 0.40 = 1.60 │
│ │ garments.”                                │ │  Likelihood 4 × 0.35 = 1.40 │
│ │ DHS UFLPA Entity List · 2026-07-31        │ │  Exposure   4 × 0.25 = 1.00 │
│ │ [Open source ↗]                            │ │  Raw 4.00 → 100             │
│ └───────────────────────────────────────────┘ │                              │
│ Why this matters                              │ Status                       │
│ UFLPA rebuttable presumption; cotton and      │ [Open ▾]                     │
│ garment inputs face enhanced traceability.    │                              │
│                                               │ Supplier                     │
│ Proposed actions (4)                          │ Dhaka Knit Composite Ltd.    │
│ ┌───────────────────────────────────────────┐ │ 850 workers · 2 factories    │
│ │ Collect batch-level origin docs  High  P1 │ │                              │
│ │ Owner: Compliance · Due 2026-11-04        │ │ Decision history             │
│ │ [Mark in progress]                        │ │ Approved by Nusrat Jahan     │
│ └───────────────────────────────────────────┘ │ 2026-10-24 · rationale       │
│ [+ Add action]                                │                              │
└───────────────────────────────────────────────┴──────────────────────────────┘
```

**Notes**

- The quote is set in a larger, readable body size and is never truncated by
  default. A long quote scrolls inside the card.
- Verification state is a badge next to the title: `verified`,
  `needs_review`, or `insufficient_evidence`.
- The score breakdown is always visible; the score is not a black box.
- Actions show owner and due date before status controls.

### 5.3 Sources (desktop, 1440 px)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Sources                                      [5 streams]                    │
│ Five streams, live where the source allows.                                  │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ i  Bangladesh Bank and EUR-Lex are primary fixture-backed streams.       │ │
│ │    UFLPA is supporting evidence. GDELT and the US Federal Register run    │ │
│ │    through live connectors in hybrid mode. A fallback is labelled and     │ │
│ │    is never reported as a live sync.                                      │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐   │
│ │ 🏛 Bangladesh Bank      [Primary]│ │ ⚖ EUR-Lex              [Primary]│   │
│ │ Regulatory · BD · every 6 hours  │ │ Regulatory · EU · daily          │   │
│ │ [Fixture] ● healthy  2 signals   │ │ [Fixture] ● healthy  3 signals   │   │
│ │ Last sync 2h ago      [Sync now] │ │ Last sync 20h ago     [Sync now] │   │
│ └──────────────────────────────────┘ └──────────────────────────────────┘   │
│ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐   │
│ │ 🛡 DHS UFLPA          [Support]  │ │ 📰 GDELT                  [News] │   │
│ │ Sanctions · US · daily           │ │ News · GLOBAL · hourly           │   │
│ │ [Fixture] ● healthy  3 signals   │ │ [Fallback] ◐ degraded 4 signals  │   │
│ │ Last sync 20h ago     [Sync now] │ │ Last sync 6h ago      [Sync now] │   │
│ └──────────────────────────────────┘ └──────────────────────────────────┘   │
│ ┌──────────────────────────────────┐                                        │
│ │ 📄 US Federal Register  [Rules]  │   Ingestion path                       │
│ │ Regulatory · US · daily          │   01 Schedule → 02 Fetch → 03 Chunk →  │
│ │ [Live] ● healthy  9 signals      │   04 Agent pipeline                    │
│ │ Last sync 14m ago     [Sync now] │                                        │
│ └──────────────────────────────────┘                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Notes**

- The mode badge is the first thing after the role badge: `Live` (emerald),
  `Fixture` (slate), `Fallback` (amber), `Failed` (rose).
- The sync toast repeats the mode and the number of new signals.
- The ingestion path is explanatory, not a fake live status.

### 5.4 Approvals (desktop)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Approvals                                          [4 pending]              │
│ Material actions wait for a named human decision.                           │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Critical · UFLPA cotton trace · Dhaka Knit                               │ │
│ │ Proposed: Collect batch-level origin documentation for order LT-4412     │ │
│ │ Owner: Compliance · Due 2026-11-04 · Evidence verified                   │ │
│ │ [Review]                                                                 │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ High · CSDDD supplier mapping · Chattogram Spinning                      │ │
│ │ Proposed: Align supplier code and risk mapping with CSDDD due diligence  │ │
│ │ Owner: Compliance · Due 2026-11-10 · Evidence verified                   │ │
│ │ [Review]                                                                 │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Decision dialog**

```text
┌──────────────────────────────────────────────┐
│ Approve remediation?                         │
│ Risk: Cotton origin documentation …          │
│ Action: Collect batch-level origin docs      │
│                                              │
│ Rationale *                                  │
│ ┌──────────────────────────────────────────┐ │
│ │ Evidence is sufficient; owner and due    │ │
│ │ date are realistic.                      │ │
│ └──────────────────────────────────────────┘ │
│ This note becomes part of the audit trail.   │
│                         [Cancel] [Approve]   │
└──────────────────────────────────────────────┘
```

### 5.5 Audit (desktop)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Audit trail                                        [Verify chain]           │
│ Append-only · SHA-256 hash chain · 12 events                                 │
│ ┌────────────┬──────────────────────┬──────────────┬──────────┬───────────┐ │
│ │ Time       │ Action               │ Actor        │ Entity   │ Hash      │ │
│ ├────────────┼──────────────────────┼──────────────┼──────────┼───────────┤ │
│ │ 10:42      │ approval.approve     │ Nusrat Jahan │ risk     │ 9f2c…a1   │ │
│ │ 10:31      │ pipeline.run         │ Rafiq Hasan  │ agent_run│ 7b1e…c4   │ │
│ │ 10:18      │ source.sync          │ Ayesha Rahman│ source   │ 3d8a…e2   │ │
│ └────────────┴──────────────────────┴──────────────┴──────────┴───────────┘ │
│ ✓ Chain verified: 12 events, no breaks                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 Mobile (390 px)

```text
┌─────────────────────────────┐
│ ☰  Chowkidar      [3]  [EN] │
├─────────────────────────────┤
│ Dashboard                   │
│ Padma Apparel · Gazipur     │
│ [Run pipeline]              │
│ ┌─────────┐ ┌─────────┐     │
│ │Open  8  │ │Critical │     │
│ │         │ │    3    │     │
│ └─────────┘ └─────────┘     │
│ Priority queue              │
│ ┌─────────────────────────┐ │
│ │ 01 UFLPA cotton    98   │ │
│ │ Dhaka Knit · verified   │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ 02 CSDDD supplier  91   │ │
│ │ Chattogram · verified   │ │
│ └─────────────────────────┘ │
│ Source health               │
│ BD Bank   ● healthy         │
│ GDELT     ◐ fallback        │
└─────────────────────────────┘
```

**Mobile rules**

- Single column; cards stack in priority order.
- The top bar keeps search, pending approvals, and the language toggle.
- Tables become stacked definition lists, never horizontal scroll for core
  content.
- Tap targets are at least 44 × 44 px.

---

## 6. Visual system

### 6.1 Color tokens

| Token | Value | Use |
|---|---|---|
| `--background` | `#060a12` | App background |
| `--foreground` | `#e6edf7` | Primary text |
| `--panel` | `#0a1220` | Card surface |
| `--panel-2` | `#0e1829` | Raised surface |
| `--panel-3` | `#131f35` | Hover / inset |
| `--border` | `#1b2a42` | Standard border |
| `--border-soft` | `#142136` | Hairline / divider |
| `--muted` | `#8da0bb` | Secondary text |
| `--muted-2` | `#60728c` | Tertiary text / labels |
| `--accent` | `#2dd4bf` | Primary action, focus, live |
| `--accent-2` | `#38bdf8` | Information, links |
| `--accent-3` | `#a78bfa` | AI / agent accent |
| `--danger` | `#fb7185` | Critical, destructive |
| `--warning` | `#fbbf24` | Fallback, degraded, medium |
| `--success` | `#34d399` | Verified, healthy, approved |
| `--info` | `#60a5fa` | Supporting / neutral info |

**Semantic mapping**

- **Priority:** critical = rose, high = orange, medium = amber, low = slate.
- **Verification:** verified = emerald, needs_review = amber,
  insufficient_evidence = rose.
- **Source mode:** live = emerald, fixture = slate, fallback = amber,
  failed = rose.
- Color is never the only signal; every badge has a word.

### 6.2 Type

| Role | Family | Size / weight |
|---|---|---|
| Display / numbers | Space Grotesk | 24–48 px, 600–700 |
| Body | Inter | 13–16 px, 400–500 |
| Labels / metadata | Inter | 9–12 px, 500–600, uppercase tracking 0.08–0.14em |
| Bengali | Noto Sans Bengali | inherits scale; line-height +10% |

### 6.3 Spacing, radius, elevation

- 4 px base unit; common gaps 8, 12, 16, 20, 24.
- Card radius `0.875rem` (14 px); controls 8–10 px; pills 999 px.
- Panel shadow: inset top highlight + soft 50 px ambient shadow.
- Background: two restrained radial glows (teal top-left, sky top-right) over
  near-black; no gradient behind body text.

### 6.4 Motion

- 120–180 ms for hover and state changes; 240 ms for dialogs.
- No looping animation except the live-status dot and skeleton shimmer.
- `prefers-reduced-motion` disables non-essential transitions.

---

## 7. Component inventory

| Component | Used on | Notes |
|---|---|---|
| `AppShell` | All app routes | Left rail, top search, approvals badge, language, user menu |
| `PageHeader` | All routes | Title, subtitle, primary action |
| `SectionHeading` | Dashboard panels | Title, description, link/action |
| `StatCard` | Dashboard | Label, value, icon, tone |
| `ScoreRing` | Dashboard, risk detail | Deterministic score, priority label |
| `StatusBadge` | Risks, approvals, runs | Word + tone, never color-only |
| `PriorityQueue` | Dashboard | Ranked top risks |
| `SourceHealthPanel` | Dashboard | Five streams, mode, status |
| `PipelinePanel` | Dashboard | Seven stages + repair count, run action |
| `TrendChart` | Dashboard | 14-day signal/risk trend |
| `LatestSignals` | Dashboard | Recent stream items |
| `RiskTable` | Risks | Filter, sort, paginate |
| `EvidenceCard` | Risk detail, search | Quote, citation, source link |
| `ActionList` | Risk detail | Owner, due date, status |
| `DecisionDialog` | Approvals | Approve/reject + rationale |
| `GraphCanvas` | Graph | Company/supplier/obligation/risk nodes |
| `AuditTable` | Audit | Event payload + hash chain |
| `ReportCard` | Reports | Format, status, checksum, download |
| `EmptyState` / `ErrorState` / `PageSkeleton` | All | Consistent loading and failure |

---

## 8. Interaction and state rules

1. **No optimistic approval.** The UI waits for the API and shows the persisted
   decision; a failed role check returns `403` and leaves the item pending.
2. **No fake live state.** A source card shows the mode returned by the API. If
   the connector fails in hybrid mode, the badge is `Fallback` and the status is
   `degraded`; in live mode the route returns an error and the card shows
   `Failed`.
3. **No unsourced risk.** A risk with no verbatim evidence is shown as
   `needs_review` or `insufficient_evidence`, never as verified.
4. **Repair is bounded.** The pipeline panel shows the number of repair attempts;
   it never implies an unbounded agent loop.
5. **Reports are durable and checksummed.** The download action exposes the
   format and checksum state; a checksum mismatch blocks the download.
6. **Role gates are explicit.** Disabled actions explain why (e.g. "Approver or
   admin access required") rather than disappearing silently.
7. **Language is persistent.** The language toggle changes chrome and keeps the
   route; source text and reports remain English and are labelled as such.

---

## 9. Accessibility

- Target: WCAG 2.2 AA for contrast on core text and controls.
- All interactive elements are keyboard reachable; focus ring is 2 px teal with
  a 2 px offset.
- Badges pair color with a word; status dots have adjacent text.
- Dialogs trap focus and close on Escape; the destructive action is not the
  default focus.
- Charts have text summaries; the graph has a list/table alternative for core
  relationships.
- Reduced motion is respected.
- The layout is tested at 390 px, 768 px, and 1440 px; the primary target is
  desktop.
- Not yet audited with a screen reader; this is disclosed in
  [`LIMITATIONS.md`](LIMITATIONS.md).

---

## 10. Content and tone

- Use **signal**, **risk**, **obligation**, **evidence**, **draft action**, and
  **decision**. Avoid **violation**, **guilty**, **compliant**, and **legal**.
- Prefer "needs review" over "failed" for evidence quality; reserve "failed" for
  a system operation.
- Every empty state says what to do next.
- Every AI-generated surface says it is a draft and requires human review.
- The disclaimer is present on the landing page, API root, reports, and
  methodology resource: *compliance risk intelligence, not legal advice.*

---

## 11. Design decisions and trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| Dark, dense workspace | Long review sessions; compliance users scan tables | Less approachable for first-time buyers; landing page carries the welcome |
| Priority-first dashboard | The user is triaging, not browsing | Hides breadth; the rail and reports expose the rest |
| Evidence card adjacent to score | Trust requires inspectability | More vertical space per risk |
| Mode badges in words | Prevents fixture/live confusion | Slightly noisier source cards |
| Human approval as a hard gate | The product must not act autonomously on material remediation | Adds a step; the queue makes it visible |
| English + Bengali chrome only | The pilot's users are in Bangladesh | Source text and reports remain English; translation is not evaluated |
| No Figma file | Time and account constraints; the working UI is the source of truth | A static design file would be easier for a designer to remix |

---

## 12. What this artifact is not

- It is not a claim that every screen is pixel-perfect in the running app.
- It is not a user-tested design. No usability study has been run.
- It is not a Figma source file. The running Next.js app and this document are
  the design record.
- It is not a claim of accessibility certification.

The public, inspectable product is the primary evidence: the Netlify pilot and
the repository. This document explains the intent behind it.
