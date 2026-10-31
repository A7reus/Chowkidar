# Chowkidar — Demo video package

**Status:** a real captioned screen recording exists in the repository; it has
**not** been uploaded to YouTube, and the official form still uses a
placeholder. Do not claim a YouTube URL until one exists.

| Item | Value |
|---|---|
| File | [`docs/assets/demo-walkthrough.mp4`](assets/demo-walkthrough.mp4) (4.1 MB) |
| Thumbnail | [`docs/assets/demo-walkthrough-thumbnail.png`](assets/demo-walkthrough-thumbnail.png) (1280×720) |
| Length | 2:45 |
| Resolution | 1280×720, H.264 MP4, no audio |
| Captions | Burned into the bottom of the frame |
| Recorded | 2026-10-31 against the local seeded demo |
| Runtime mode | Local `AUTH_MODE=dev`, `DEMO_MODE=true`, deterministic mock LLM path |
| Hosted pilot shown | No — the recording is local; the hosted pilot is <https://ch0wkidar.netlify.app/> |
| MP4 SHA-256 | `09b03ede127580814197e0790b739afd5aa0bcbfcb599ba168a00a9672b524b6` |
| Thumbnail SHA-256 | `92343937c1d477c3327accfdda2b75efd59aa0110ab3a5de588b3b63a8d9a946` |

## What the recording shows

| Time | Scene | Claim |
|---:|---|---|
| 0:00 | Login | Demo workspace with four roles |
| 0:08 | Dashboard | Five labelled streams, eight cited risks, three critical |
| 0:26 | Risk register | Deterministic score ordering |
| 0:36 | Risk detail | Verbatim quote, citation, score breakdown, review boundary |
| 0:46 | Data lineage | Source → signal → obligation → risk → evidence/actions/approvals; persisted trace ID |
| 1:04 | Signals | Raw source text with live/fixture/fallback labels |
| 1:14 | Supply-chain graph | Company, suppliers, obligations, risks, and policies |
| 1:24 | Approvals | Approver records a rationale-backed decision |
| 1:38 | Audit trail | Admin verifies the SHA-256 hash chain |
| 1:52 | Reports | PDF audit pack generation |
| 2:08 | Evidence search | Cited source chunks, not generated answers |
| 2:22 | Evaluations | 13/13 golden cases and five gates on the deterministic path |
| 2:40 | Close | Tagline, live URL, repository URL, not-legal-advice boundary |

## Honest boundaries

- The video is a **local deterministic demo**, not a recording of the hosted
  Supabase deployment. The top bar shows `MOCK`; this is intentional.
- It does **not** demonstrate live Gemini/Groq inference, hosted Supabase login,
  a local Ollama model, an external MCP server, or a tunnel.
- The data is the synthetic Padma Apparel pilot seed. The approval shown is a
  local demo decision, not a real compliance decision.
- The 13/13 evaluation result is synthetic and deterministic-only; the video
  caption says so.

## YouTube upload metadata

**Title**

```text
Chowkidar — Agentic Compliance Risk Sentinel | 2:45 Demo
```

**Description**

```text
Chowkidar monitors regulatory and supplier-risk streams, extracts cited obligations, maps them to a fictional exporter's suppliers, scores risk deterministically, and drafts owned remediation. A human approver records every material decision, and every action is written to a hash-chained audit trail.

This 2:45 walkthrough covers:
0:00 Login and dashboard
0:26 Risk register
0:36 Risk detail and score breakdown
0:46 Source-to-risk lineage with trace ID
1:04 Signals and supply-chain graph
1:24 Human approval
1:38 Hash-chained audit verification
1:52 Reports
2:08 Cited evidence search
2:22 13-case evaluation

Live pilot: https://ch0wkidar.netlify.app/
Repository: https://github.com/A7reus/Chowkidar
Architecture: https://github.com/A7reus/Chowkidar/blob/main/docs/ARCHITECTURE.md

Recorded locally against the seeded demo with the deterministic mock LLM path. The hosted pilot uses Supabase auth and hybrid live/fixture data. Pilot data is synthetic. Chowkidar is compliance risk intelligence, not legal advice.
```

**Tags**

```text
compliance, RegTech, supply chain, export compliance, AI agents, LangGraph, risk management, UFLPA, CSDDD, Bangladesh RMG, FastAPI, Next.js
```

**Settings**

- Visibility: public (preferred for judges) or unlisted if the team prefers.
- Audience: not made for kids.
- Category: Science & Technology.
- Language: English.
- Thumbnail: `docs/assets/demo-walkthrough-thumbnail.png`.
- Captions: burned in; no separate subtitle file is required.

## After uploading

1. Copy the YouTube URL into `docs/SUBMISSION.md` section 9 (team-data
   checklist), section 10.1 (YouTube Video), and the README link.
2. Remove the `[PLACEHOLDER — ...]` wording only after the URL resolves.
3. Keep the local MP4 link as a backup; it is not a substitute for the YouTube
   field.
4. Do not submit the official form without separate explicit approval.

## How the recording was produced

The recording used Playwright Chromium at 1280×720 against a production Next.js
build and the local FastAPI server, with a fixed caption overlay injected into
the page. It was converted to H.264 with ffmpeg. The demo database was reseeded
before recording. No hosted data or credentials were used.
