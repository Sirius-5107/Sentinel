# Implementation Plan

This document describes the phased delivery of Sentinel. Each phase has clear objectives, deliverables, exit criteria, dependencies, and a complexity estimate. Phases are sequential — the exit criteria of each phase must be met before the next begins.

> **Reconciliation note (2026-08-16):** This document was updated to reflect the canonical Phase 1 scope as defined in `docs/05-contracts.md`, which supersedes the original Phase 1 deliverables list. Specifically: (a) persistence moves to Phase 2; (b) stale model names (`Entity`, `Event`, `Signal`, `Report`) are replaced with the concrete implemented models; (c) `Signal` and `Country` are formally deferred; (d) Phase 0 status corrected to Complete. See `docs/06-phase-1-audit.md` for the full reconciliation audit.

---

## Phase 0 — Foundation

**Status:** Complete

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
- `uv sync --locked` succeeds from a clean checkout ✓
- `ruff check .` passes with zero warnings ✓
- `pyright` passes with zero errors ✓
- `pytest` passes (no failures; coverage threshold met) ✓
- `mkdocs build --strict` succeeds ✓
- CI pipeline passes on `main` ✓

### Dependencies
None.

### Complexity
Low — configuration and scaffolding only.

---

## Phase 1 — Core Domain

**Status:** In Progress (models complete; interfaces and exceptions remaining)

### Objectives
Define the shared domain vocabulary that all other phases consume. This is the complete, immutable contract for domain objects. No persistence, no I/O, no external services.

### Canonical Model Set

The following twelve models are the authoritative Phase 1 domain model, as specified in `docs/05-contracts.md`:

| Model | Purpose |
|---|---|
| `Source` | External content provider |
| `Article` | Single ingested piece of content (fundamental evidence unit) |
| `Company` | Commercial entity in Sentinel's coverage universe |
| `Person` | Named individual relevant to financial markets |
| `Organization` | Non-commercial institution (central bank, regulator, etc.) |
| `Theme` | Persistent investment thesis |
| `Market` | Financial exchange or trading venue (reference data) |
| `MarketEvent` | Synthesised financial development (primary intelligence output) |
| `ReportSection` | Single ordered section within a daily report |
| `DailyReport` | Published daily intelligence brief |
| `PipelineRun` | End-to-end pipeline execution audit record |
| `Task` | Atomic unit of work within a pipeline run |

> **Deferred — `Signal`:** The term `Signal` appears in earlier documentation but has no formal model definition. Its intended meaning (synonym for MarketEvent, curated subset, or intermediate layer) is unresolved. Decision is deferred to Phase 4 (Intelligence). See `docs/06-phase-1-audit.md` §15.

> **Deferred — `Country`:** A `Country` knowledge-base entity may be needed for Phase 5. The `CountryCode` value object is sufficient for Phase 1. A full `Country` model will be introduced only if Phase 5 use cases require it.

> **Superseded — `Entity`, `Event`, `Report`:** These generic names from the original plan are superseded by the typed models above. Do not use these names for new code.

### Deliverables

**Implemented ✓**
- `sentinel_core/models/` — all 12 models above, frozen Pydantic v2, fully validated
- `sentinel_core/enums/` — `ArticleStatus`, `AssetClass`, `MarketRegion`, `Sector`, `Sentiment`, `EventSeverity`, `EntityType`, `ReportType`, `ReportStatus`, `PipelineStatus`, `TaskStatus`, `SourceType`, `SourceStatus`
- `sentinel_core/types/` — `ConfidenceScore`, `ImportanceScore`, `CountryCode`, `LanguageCode`, `Ticker`, `Url`, `IanaTimezone`, `CurrencyCode`, `MicCode`, `IsinCode`, `SlugField`
- Unit tests for all models and enums
- 99% coverage for `sentinel_core`

**Remaining ✗**
- `sentinel_core/exceptions/` — domain exception hierarchy (`SentinelError` base + typed subclasses)
- `sentinel_core/interfaces/` — `CollectorProtocol`, `ProcessorProtocol`, `PublisherProtocol`
- `sentinel_core/config/` — Pydantic settings model validated against YAML configs
- `sentinel_core/constants/` — system-wide constants (max retries, timeouts, etc.)

### Exit Criteria
- All 12 models validated by Pyright in strict mode ✓
- Unit test coverage ≥ 90% for `sentinel_core` ✓ (99%)
- `sentinel_core/exceptions/`, `sentinel_core/interfaces/`, `sentinel_core/config/`, `sentinel_core/constants/` implemented and tested
- `ruff check .` passes ✓
- `pyright` passes ✓
- `mkdocs build --strict` succeeds ✓

> **Persistence is NOT a Phase 1 exit criterion.** PostgreSQL, SQLAlchemy, and Alembic are dependencies declared in `pyproject.toml` for future use. No migration, schema, or database connection is required to complete Phase 1. Persistence baseline moves to Phase 2.

### Dependencies
Phase 0 complete.

### Complexity
Medium — establishing the right abstractions is the hardest part.

---

## Phase 2 — Data Layer and Collection

**Status:** Planned

### Objectives
Establish the persistence layer and implement the first data collection capability. Articles flow from external sources into the database for the first time.

### Deliverables

**Persistence baseline (moved from Phase 1):**
- SQLAlchemy ORM models for all 12 domain models (in `sentinel/`, not `sentinel_core/`)
- Alembic `env.py` configuration
- Initial Alembic migration covering all 12 domain models
- Docker Compose stack for local development (PostgreSQL + pgvector)
- Repository pattern in `sentinel/` (application layer, not domain layer)

**Collection:**
- `sentinel/collector/rss.py` — RSS feed collector implementing `CollectorProtocol`
- `sentinel/collector/scraper.py` — HTTP + HTML scraper (selectolax + BeautifulSoup)
- `sentinel/collector/dynamic.py` — Playwright-based dynamic page collector
- `sentinel/collector/base.py` — abstract base implementing `CollectorProtocol`
- Content hash deduplication on ingest
- Unit and integration tests

### Exit Criteria
- `alembic upgrade head` runs against a clean Postgres instance
- RSS collector ingests articles from all sources in `sources.yaml`
- Duplicate URLs and content hashes are rejected
- Articles are persisted to the database with correct status transitions
- Unit test coverage ≥ 80% for `sentinel/collector/`
- Integration tests pass against local Docker Compose Postgres

### Dependencies
Phase 1 complete. Docker available. `CollectorProtocol` defined in `sentinel_core/interfaces/`.

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
- `sentinel/processing/extractor.py` — entity extraction (companies, people, organisations)
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

> **Signal decision required before this phase begins.** The `Signal` concept (deferred from Phase 1) must be defined before the intelligence layer is designed. See `docs/06-phase-1-audit.md` §15, Q1.

### Objectives
Synthesise processed articles into investment-grade market events and assemble the daily intelligence brief.

### Deliverables
- `sentinel/intelligence/synthesiser.py` — MarketEvent synthesis from Articles
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

> **Country model decision may arise in this phase.** If country-level knowledge base entries (India macro, US equities landscape) are required, a `Country` domain model will be introduced here. See `docs/06-phase-1-audit.md` §15, Q2.

### Objectives
Build and maintain a structured, searchable knowledge base of entities, themes, and historical events.

### Deliverables
- `sentinel/knowledge/company.py` — company profiles
- `sentinel/knowledge/theme.py` — investment theme tracking
- `sentinel/knowledge/person.py` — key person profiles
- `sentinel/knowledge/country.py` — country/region profiles (if `Country` model is introduced)
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
- Endpoints: articles, market events, briefs, search, entities
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
Provide an interactive intelligence dashboard and operational CLI.

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
