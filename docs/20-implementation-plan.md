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

**Status:** Complete

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
- `sentinel_core/exceptions/` — domain exception hierarchy (`SentinelError` base + typed subclasses)
- `sentinel_core/interfaces/` — `CollectorProtocol`, `ProcessorProtocol`, `PublisherProtocol`, and provider protocols for LLM and embedding access
- `sentinel_core/constants/` — system-wide constants (max retries, timeouts, etc.)
- Unit tests for all models and enums
- 99% coverage for `sentinel_core`

**Remaining ✗**
- `sentinel_core/config/` — Pydantic settings model validated against YAML configs

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

**Status:** Complete

### Objectives
Establish the persistence and collection baseline required for the application pipeline. Articles move from source inputs into the application layer with the expected ingest and status semantics.

### Deliverables

**Persistence baseline (completed):**
- SQLAlchemy ORM models for the application-layer persistence surface (in `sentinel/`, not `sentinel_core/`)
- Alembic `env.py` configuration and migration flow
- Initial Alembic migration covering the core domain model set
- Docker Compose stack for local development (PostgreSQL + pgvector)
- Repository pattern in `sentinel/` (application layer, not domain layer)

**Collection (completed):**
- `sentinel/collector/rss.py` — RSS feed collector implementing `CollectorProtocol`
- `sentinel/collector/scraper.py` — HTTP + HTML scraper
- `sentinel/collector/dynamic.py` — dynamic page collector where the repository implementation requires it
- `sentinel/collector/base.py` — abstract base implementing `CollectorProtocol`
- Content hash deduplication on ingest
- Unit and integration tests

### Exit Criteria
- `alembic upgrade head` runs against a clean Postgres instance
- RSS collector ingests articles from configured sources
- Duplicate URLs and content hashes are rejected
- Articles are persisted with correct status transitions
- Unit test coverage ≥ 80% for `sentinel/collector/`
- Integration tests pass against local Docker Compose Postgres

### Dependencies
Phase 1 complete. Docker available. `CollectorProtocol` defined in `sentinel_core/interfaces/`.

### Complexity
Medium.

---

## Phase 3 — Processing

**Status:** Complete

### Objectives
Transform raw ingested articles into classified, scored, and validated processing outputs without altering the immutable `sentinel_core` domain layer. The processor coordinates classification, importance scoring, entity extraction, and candidate-based deduplication while preserving raw evidence and Pydantic invariants.

### Deliverables
- `sentinel/processing/classifier.py` — deterministic article classification with optional provider integration
- `sentinel/processing/scorer.py` — importance scoring with bounded output
- `sentinel/processing/extractor.py` — entity extraction for companies, people, and organisations
- `sentinel/processing/dedup.py` — deduplication using candidate lookup plus embedding-provider assistance when available
- `sentinel/processing/processor.py` — thin orchestration layer for the processing flow
- Provider interfaces for optional LLM/embedding usage behind the application boundary
- Unit and integration tests for classification, scoring, extraction, and deduplication behaviour

### Processing Flow
`INGESTED → PROCESSING → classification → scoring → entity extraction → candidate lookup → deduplication → PROCESSED / DEDUPLICATED`

### Exit Criteria
- Every ingested article is classified and scored within the repository's processing contract
- Candidate-based duplicate detection behaves deterministically and preserves raw evidence
- Provider-backed paths are optional; deterministic fallbacks remain valid when providers are absent or malformed
- `Article` invariants remain valid during reconstruction; raw evidence fields are preserved exactly
- Phase 3 tests cover classification, scoring, extraction, deduplication, and processor status transitions

### Dependencies
Phase 2 complete. LLM and embedding provider interfaces are available behind the application boundary.

### Complexity
High — provider boundaries, deterministic fallback behaviour, and validation safety.

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
