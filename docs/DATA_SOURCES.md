# Chowkidar — Data Sources & Ingestion Notes

**Last updated:** 2026-10-26

**Status:** Two live connectors implemented (GDELT + US Federal Register); three streams remain fixture-backed. `DATA_MODE=hybrid` is implemented and locally verified. `DATA_MODE=live` is implemented but externally rate-limited for GDELT; a hard failure is surfaced as `live_failed`.

**Purpose:** Track source access, reliability, licensing, and demo usage. Update as connectors are tested.

---

## 1. Source strategy

Chowkidar needs **at least two distinct external data streams** plus internal company documents.

| Stream | Examples | Demo role |
|---|---|---|
| Regulatory changes | Federal Register, EUR-Lex, Bangladesh Bank, BGMEA, Department of Environment, NBR | Detect new obligations and map them to policies/suppliers |
| Risk signals | GDELT news, OpenSanctions, UFLPA entity list | Detect supplier/counterparty risk and trigger due diligence |
| Internal documents | Supplier list, policies, contracts, audit reports | Provide the company context for mapping and remediation |

**What is actually wired:** five distinct streams. Bangladesh Bank, EUR-Lex, and UFLPA/DHS are fixture-backed. GDELT and the US Federal Register have real live connectors in `apps/api/app/connectors/`, with normalization, dedupe by `(source_id, external_id)`, evidence chunking, and honest mode labels. The seed contains 13 signals across the five streams. The catalog below distinguishes implemented connectors from design targets; it is not a claim that every listed API is called.

**Live connector contract**

| Connector | Endpoint | Key | Normalized fields | Known limits |
|---|---|---|---|---|
| `federal_register` | `https://www.federalregister.gov/api/v1/documents.json` | none | document number, title, abstract, publication date, URL, agencies | Filters by trade/supply-chain terms; 8 relevant rules in a local run |
| `gdelt` | `https://api.gdeltproject.org/api/v2/doc/doc` | none | article URL, title, seen date, domain, source country, language | Public rate limit ~1 request / 5 s; returns `429` and rate-limit HTML; hybrid mode falls back to fixtures |

**Ingestion modes**

- `fixture`: replay the local fixture; label the run `fixture`.
- `hybrid`: try the live connector; on failure, replay the fixture and label the run `fixture_fallback` with `status=degraded` and a sanitized `last_error`.
- `live`: try the live connector; on failure, record `mode=live_failed`, `status=error`, and return `502` from the sync route.

The in-process APScheduler job calls the same service path when `ENABLE_SCHEDULER=true`. n8n is optional and is not the pilot path.

---

## 2. Source catalog

### 2.1 Regulatory sources

| Source | Jurisdiction | Access | Demo use | Fallback |
|---|---|---|---|---|
| **Federal Register API** | US | REST/JSON, no key, documented API | Fetch recent rules/notices; extract obligations | Cached JSON snapshot |
| **EUR-Lex** | EU | RSS/SPARQL/HTML; public | Fetch CSDDD/CSRD/AI Act updates; extract obligations | Cached HTML/PDF snapshot |
| **Bangladesh Bank circulars** | BD | HTML pages; public | Curated snapshot of 3–5 circulars | Static JSON |
| **BGMEA/BKMEA notices** | BD | HTML pages; public | Curated buyer/labour compliance notices | Static JSON |
| **Department of Environment** | BD | HTML pages; public | Curated environmental clearance notices | Static JSON |
| **NBR** | BD | HTML pages; public | Curated tax/VAT notices | Static JSON |
| **ILO NATLEX** | Global | HTML/API; public | Labour law references | Static JSON |
| **SEC EDGAR** | US | REST/JSON, no key, user-agent required | Future: corporate filings/ownership | Cached JSON |
| **World Bank Open Data** | Global | REST/JSON, no key | Future: macro risk indicators | Cached JSON |

### 2.2 Risk signal sources

| Source | Type | Access | Demo use | Fallback |
|---|---|---|---|---|
| **GDELT** | Global news | REST/JSON, no key | Supplier labour/environmental/financial signals | Cached article list |
| **OpenSanctions** | Sanctions/PEP | API; free tier/API key for some datasets | Screen suppliers/buyers | Cached entity list |
| **UFLPA Entity List** | Forced labour | Public CSV/HTML | Check supplier/factory against list | Static CSV |
| **OFAC SDN** | Sanctions | Public CSV/HTML | Screen counterparties | Static CSV |
| **UN Consolidated List** | Sanctions | Public XML/HTML | Screen counterparties | Static XML |
| **EU Sanctions Map** | Sanctions | Public HTML | Jurisdiction risk context | Static JSON |

### 2.3 Internal documents (synthetic for demo)

| Document | Format | Contents | Label |
|---|---|---|---|
| Supplier list | CSV | 40 suppliers, country, tier, factories, certifications | Synthetic |
| Policies | PDF/DOCX | 12 policies: labour, environment, procurement, sanctions, whistleblowing | Synthetic |
| Contracts | PDF | 6 contracts: buyer, supplier, logistics | Synthetic |
| Audit reports | PDF | 3 reports with findings and corrective actions | Synthetic |
| Buyer codes | PDF/HTML | 6 buyer codes of conduct (public templates) | Public/synthetic mix |
| Risk register | CSV | Prior risks, owners, status | Synthetic |

> Clearly label synthetic data in the UI and demo. Do not attribute fabricated allegations to real companies.

---

## 3. Access and reliability notes

### Federal Register API
- Base: `https://www.federalregister.gov/api/v1/`
- No API key required; be polite with rate limits.
- Useful endpoints: `/documents.json`, `/documents/{id}.json`.
- Filter by agency, type, publication date.
- Cache responses; store raw JSON and parsed text.
- **Implemented:** the connector requests recent `RULE` documents matching a term, filters by trade/supply-chain keywords at word boundaries, and normalizes the result. A local run returned 8 relevant rules; a second run created 0 new signals because of external-ID dedupe.

### EUR-Lex
- Public; RSS feeds and SPARQL endpoint.
- HTML/PDF documents can be parsed.
- Some pages are large; use targeted document IDs.
- Cache PDFs/HTML; store document version and effective date.

### GDELT
- Base: `https://api.gdeltproject.org/api/v2/doc/doc`
- Query by keyword/entity; JSON output.
- Results can be noisy; deduplicate and classify relevance.
- **Implemented:** the connector normalizes article URL/title/seen date/domain/country, dedupes by stable URL hash, and assigns a keyword-based severity.
- **Rate limit:** the public endpoint enforces roughly one request every five seconds and may return `429` with an HTML rate-limit page. The connector retries once after five seconds; if it still fails, hybrid mode labels the run `fixture_fallback` and `status=degraded`. Do not poll it aggressively. A production deployment should use a scheduled, low-frequency query or a licensed feed.

### OpenSanctions
- API: `https://api.opensanctions.org/`
- Some datasets require an API key; check terms.
- Use for entity screening, not as a sole source of truth.
- Store match score, dataset, and evidence URL.

### UFLPA / OFAC / UN lists
- Public downloads; check update frequency.
- Store list version/date and hash.
- Use exact/fuzzy matching with human review.

### Bangladesh sources
- HTML pages may change; use curated snapshots for the demo.
- Store source URL, retrieval date, and quote.
- Do not scrape aggressively; respect robots/ToS.

---

## 4. Source registry schema

| Field | Description |
|---|---|
| `id` | UUID |
| `name` | Human-readable name |
| `type` | regulator, sanctions, news, internal |
| `jurisdiction` | US, EU, BD, global |
| `url` | Base URL |
| `cadence` | hourly, daily, weekly, manual |
| `active` | Boolean |
| `auth` | none, api_key, oauth |
| `connector_key` | `fixture`, `gdelt`, or `federal_register` |
| `connector_config` | JSON: query/term, timespan, max records, document type |
| `last_sync_at` | Timestamp |
| `last_sync_mode` | fixture, live, fixture_fallback, live_failed |
| `last_signal_count` | New signals created by the last run |
| `last_error` | Sanitized error, or null |
| `last_status` | success, partial, failed |
| `notes` | Licensing/ToS notes |

---

## 5. Ingestion pipeline

1. **Fetch:** HTTP client with retries, timeouts, user-agent, rate limits.
2. **Store raw:** object storage/S3 or Postgres JSONB; hash for dedup.
3. **Parse:** HTML/PDF → structured text; preserve headings/articles.
4. **Clean:** normalize whitespace, encoding, language; deduplicate.
5. **Chunk:** semantic/variable chunking by section.
6. **Embed:** BGE-M3/OpenAI/Cohere.
7. **Extract:** obligations/entities with citations.
8. **Index:** pgvector + BM25 + graph.
9. **Monitor:** detect changes via hash/diff.
10. **Log:** source, timestamp, status, latency, errors.

---

## 6. Data quality checks

- Required metadata present (source, URL, date, jurisdiction).
- Document hash unique.
- Text length within bounds.
- Citation quote exists in source text.
- Entity resolution confidence above threshold.
- No PII in external LLM payloads.
- Source freshness within SLA.
- Duplicate rate below threshold.
- Language detection correct.
- Broken links flagged.

---

## 7. Demo data plan

### Real public data
- One EU CSDDD document from EUR-Lex.
- One Federal Register document.
- One GDELT article about a supplier risk (real or realistic).
- One UFLPA/OpenSanctions entry (public).
- One Bangladesh labour/environment notice (public).

### Synthetic data
- Meghna Apparel Ltd. company profile.
- 40 suppliers and 60 factories.
- 12 policies, 6 contracts, 3 audit reports.
- Prior risks and actions.

### Labeling
- UI badge: "Demo data — synthetic" on synthetic records.
- README: "Synthetic company data is used for demonstration. Real public sources are cited."
- Demo voiceover: "This is a fictional company; the regulatory sources are real."

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| API rate limits | Cache, backoff, curated snapshots |
| Source HTML changes | Parser tests, fallback snapshots |
| Licensing/ToS | Use public APIs, respect robots, store only needed text |
| Data freshness | Show last sync; stale source warning |
| Hallucinated citations | Verifier agent; quote must exist in source |
| PII leakage | Presidio redaction; local models |
| Defamation | No real accusations; synthetic company; "risk signal" language |
| Broken links | Store hash and quote; link checker |

---

## 9. Open questions

- Which live source is most reliable from Bangladesh? (Federal Register, EUR-Lex, GDELT?)
- Do we have an OpenSanctions API key?
- Should the Bangladesh snapshot be scraped or manually curated?
- Do we need Bengali language support in the MVP?
- Which source should be the "second stream" in the demo: GDELT or UFLPA?
