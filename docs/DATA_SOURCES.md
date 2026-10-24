# Chowkidar — Data Sources & Ingestion Notes

**Last updated:** 2026-10-24

**Status:** Design + fixture replay. Live connector clients are **not implemented**; `DATA_MODE=live` is unsupported.

**Purpose:** Track source access, reliability, licensing, and demo usage. Update as connectors are tested.

---

## 1. Source strategy

Chowkidar needs **at least two distinct external data streams** plus internal company documents.

| Stream | Examples | Demo role |
|---|---|---|
| Regulatory changes | Federal Register, EUR-Lex, Bangladesh Bank, BGMEA, Department of Environment, NBR | Detect new obligations and map them to policies/suppliers |
| Risk signals | GDELT news, OpenSanctions, UFLPA entity list | Detect supplier/counterparty risk and trigger due diligence |
| Internal documents | Supplier list, policies, contracts, audit reports | Provide the company context for mapping and remediation |

**What is actually wired:** the app has four distinct fixture-backed streams (Bangladesh Bank, EUR-Lex, UFLPA/DHS, GDELT) and 12 seeded signals. Source sync replays the fixture signal set. The catalog below is the design target for live connectors, not a claim that the live APIs are currently called. Internal documents are synthetic and clearly labeled.

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

### EUR-Lex
- Public; RSS feeds and SPARQL endpoint.
- HTML/PDF documents can be parsed.
- Some pages are large; use targeted document IDs.
- Cache PDFs/HTML; store document version and effective date.

### GDELT
- Base: `https://api.gdeltproject.org/api/v2/doc/doc`
- Query by keyword/entity; JSON output.
- Results can be noisy; deduplicate and classify relevance.
- Cache queries; avoid high-frequency polling.

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
| `last_sync_at` | Timestamp |
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
