# Implementation Plan

This document describes the phased delivery of Sentinel. Each phase has clear objectives, deliverables, exit criteria, dependencies, and a complexity estimate. Phases are sequential — the exit criteria of each phase must be met before the next begins.

---

## Phase 0 — Foundation

**Status:** In progress

### Objectives
Establish the engineering foundation that all future phases build upon. No business logic is implemented in this phase.

### Deliverables
- Repository structure and package layout
- `pyproject.toml` with all dependencies declared
- Ruff, Pyright, pytest, and pre-commit configured
- GitHub Actions CI pipeline
- MkDocs documentation site
- Empty `sentinel` and `sentinel_core` package skeletons
- Config file stubs (`app.yaml`, `logging.yaml`, `providers.yaml`, `sources.yaml`)
- Engineering standards and code review checklist
- All ADRs for foundational decisions

### Exit Criteria
- `uv sync` succeeds from a clean checkout
- `ruff check .` passes with zero warnings
- `pyright` passes with zero errors
- `pytest` passes (no failures; coverage threshold met)
- `mkdocs build --strict` succeeds
- CI pipeline passes on `main`

### Dependencies
None.

### Complexity
Low — configuration and scaffolding only.

---

## Phase 1 — Core Domain

**Status:** Planned

### Objectives
Define the shared domain model that all other phases consume. This is the vocabulary of the entire system.

### Deliverables
- `sentinel_core/models/` — Pydantic v2 models for: `Article`, `Source`, `Entity`, `Event`, `Signal`, `Report`, `Theme`, `Company`, `Country`
- `sentinel_core/enums/` — `AssetClass`, `Region`, `Sector`, `Sentiment`, `Importance`, `ArticleStatus`, `ReportType`
- `sentinel_core/exceptions/` — domain exception hierarchy
- `sentinel_core/types/` — typed identifiers (`ArticleId`, `SourceId`, `EntityId`)
- `sentinel_core/interfaces/` — `CollectorProtocol`, `ProcessorProtocol`, `PublisherProtocol`
- `sentinel_core/config/` — Pydantic settings model that loads and validates all YAML configs
- `sentinel_core/constants/` — system-wide constants
- Unit tests for all models, enums, and config loading
- Database migration baseline (Alembic `env.py` + initial migration)

### Exit Criteria
- All models validated by Pyright in strict mode
- Unit test coverage ≥ 90% for `sentinel_core`
- Config loader validated against all YAML files in `configs/`
- Alembic `upgrade head` runs against a clean Postgres instance

### Dependencies
Phase 0 complete.

### Complexity
Medium — establishing the right abstractions is the hardest part.

---

## Phase 2 — Collection

**Status:** Planned

### Objectives
Implement the data collection layer. Ingest news and financial data from configured sources.

### Deliverables
- `sentinel/collector/rss.py` — RSS feed collector
- `sentinel/collector/scraper.py` — HTTP + HTML scraper (selectolax + BeautifulSoup)
- `sentinel/collector/dynamic.py` — Playwright-based dynamic page collector
- `sentinel/collector/base.py` — abstract base implementing `CollectorProtocol`
- Deduplication logic (fingerprinting by URL + title hash)
- Persistence to PostgreSQL
- Unit and integration tests

### Exit Criteria
- RSS collector ingests articles from all sources in `sources.yaml`
- Duplicates are rejected
- Articles are persisted to the database
- Unit test coverage ≥ 80%

### Dependencies
Phase 1 complete. Postgres running.

### Complexity
Medium.

---

## Phase 3 — Processing

**Status:** Planned

### Objectives
Transform raw ingested articles into classified, scored, and entity-tagged signals.

### Deliverables
- `sentinel/processing/classifier.py` — topic and asset class classification
- `sentinel/processing/scorer.py` — importance scoring
- `sentinel/processing/extractor.py` — entity extraction (companies, people, countries)
- `sentinel/processing/dedup.py` — semantic deduplication via embeddings
- Unit and integration tests

### Exit Criteria
- Every ingested article is classified and scored within 60 seconds of ingestion
- Entity extraction precision ≥ 85% on held-out test set
- Semantic duplicates are merged, not duplicated

### Dependencies
Phase 2 complete. LLM and embedding provider interfaces implemented.

### Complexity
High — LLM integration, embedding pipeline, and quality thresholds.

---

## Phase 4 — Intelligence

**Status:** Planned

### Objectives
Synthesise processed signals into investment-grade insights.

### Deliverables
- `sentinel/intelligence/synthesiser.py` — multi-signal synthesis
- `sentinel/intelligence/analyst.py` — "why it matters" reasoning layer
- `sentinel/intelligence/daily_brief.py` — daily brief assembly
- Prompt templates versioned in `sentinel/intelligence/prompts/`
- Unit and integration tests

### Exit Criteria
- Daily brief generated on schedule
- Every insight links to at least one source article
- LLM cost tracked per brief

### Dependencies
Phase 3 complete.

### Complexity
High — prompt engineering and output quality validation.

---

## Phase 5 — Knowledge Base

**Status:** Planned

### Objectives
Build and maintain a structured, searchable knowledge base of entities, themes, and historical events.

### Deliverables
- `sentinel/knowledge/company.py` — company profiles
- `sentinel/knowledge/theme.py` — investment theme tracking
- `sentinel/knowledge/person.py` — key person profiles
- `sentinel/knowledge/country.py` — country/region profiles
- `sentinel/knowledge/event.py` — event history
- Vector search via pgvector
- Full-text search via PostgreSQL

### Exit Criteria
- Entity pages updated incrementally with each pipeline run
- Search returns results in < 500ms at target data volume
- All entities link to source evidence

### Dependencies
Phase 4 complete. pgvector extension installed.

### Complexity
High.

---

## Phase 6 — Research Engine

**Status:** Planned

### Objectives
Generate long-form, investment-grade research documents.

### Deliverables
- `sentinel/research/dossier.py` — company dossiers
- `sentinel/research/theme_report.py` — investment theme reports
- `sentinel/research/sector.py` — sector analysis
- `sentinel/research/outlook.py` — weekly and monthly outlook generation
- Report templates

### Exit Criteria
- Company dossier generated on demand within 30 seconds
- Weekly outlook published every Monday at 07:00 UTC
- All reports pass quality review checklist

### Dependencies
Phase 5 complete.

### Complexity
High.

---

## Phase 7 — Publishing

**Status:** Planned

### Objectives
Publish research to Notion and other configured channels.

### Deliverables
- `sentinel/publish/notion.py` — Notion publisher
- `sentinel/publish/formatter.py` — output formatting layer
- Publishing queue with retry logic

### Exit Criteria
- Daily brief published to Notion by 07:30 UTC
- Failed publications retried with exponential backoff
- Published reports are idempotent (re-publish does not duplicate)

### Dependencies
Phase 6 complete. Notion workspace configured.

### Complexity
Medium.

---

## Phase 8 — API

**Status:** Planned

### Objectives
Expose Sentinel capabilities via a FastAPI REST API.

### Deliverables
- `sentinel/api/` — FastAPI application
- Endpoints: articles, signals, briefs, search, entities
- Authentication (API key)
- OpenAPI documentation

### Exit Criteria
- All endpoints return correct responses
- API documentation accessible at `/docs`
- Authentication enforced on all endpoints
- Response time < 200ms for read endpoints at target load

### Dependencies
Phase 5 complete.

### Complexity
Medium.

---

## Phase 9 — Dashboard

**Status:** Planned

### Objectives
Provide an interactive intelligence dashboard.

### Deliverables
- `sentinel/cli/` — Typer CLI for operational tasks
- Dashboard powered by Plotly
- Market overview, sector heatmaps, signal timeline

### Exit Criteria
- Dashboard renders without errors
- All charts link to source data

### Dependencies
Phase 8 complete.

### Complexity
Medium.

---

## Phase 10 — Production

**Status:** Planned

### Objectives
Harden Sentinel for continuous production operation.

### Deliverables
- Docker images for all services
- Docker Compose for local and staging environments
- Monitoring and alerting (structured logs, error rates, pipeline latency)
- Deployment runbook
- Load and performance testing
- Security review

### Exit Criteria
- System runs continuously for 30 days without manual intervention
- P99 pipeline latency within target
- All secrets managed outside source control
- Disaster recovery procedure documented and tested

### Dependencies
All previous phases complete.

### Complexity
High — operational hardening is never trivial.
