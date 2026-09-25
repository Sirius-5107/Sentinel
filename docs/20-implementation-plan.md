# Implementation Plan

This document describes the phased delivery of Sentinel. Each phase has clear objectives, deliverables, exit criteria, dependencies, and a complexity estimate. Phases are sequential — the exit criteria of each phase must be met before the next begins.

> **Reconciliation note (2026-08-16):** This document was updated to reflect the canonical Phase 1 scope as defined in `docs/05-contracts.md`, which supersedes the original Phase 1 deliverables list. Specifically: (a) persistence moves to Phase 2; (b) stale model names (`Entity`, `Event`, `Signal`, `Report`) are replaced with the concrete implemented models; (c) `Signal` and `Country` were initially deferred. The Phase 4 architecture decision now formally resolves `Signal` as a conceptual term only: `MarketEvent` is the canonical intelligence/signal object. `Country` remains deferred to Phase 5. See `docs/decisions/ADR-0002-market-event-as-signal.md`.

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

> **Resolved — `Signal`:** `Signal` is a conceptual term, not a domain model. `MarketEvent` is Sentinel's canonical intelligence/signal object. Do not introduce a separate `Signal` model or intermediate signal layer unless a future architecture decision establishes a distinct semantic need. See `docs/decisions/ADR-0002-market-event-as-signal.md`.

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

**Status:** Complete

> **Architecture decision resolved:** `Signal` is not a separate domain model. `MarketEvent` is the canonical intelligence/signal object. Phase 4 therefore operates directly on `Processed Article → MarketEvent → ReportSection → DailyReport`. See `docs/decisions/ADR-0002-market-event-as-signal.md`.

### Objectives
Synthesise processed articles into evidence-backed `MarketEvent` objects, analyse their implications, and assemble the daily intelligence brief.

### Core Flow
`Processed Articles → event synthesis → MarketEvents → analysis → ReportSections → DailyReport`

`MarketEvent` is the canonical intelligence object. There is no separate `Signal` model.

### Deliverables
- `sentinel/intelligence/synthesiser.py` — group related processed articles and produce validated `MarketEvent` candidates
- `sentinel/intelligence/analyst.py` — analyse implications and "why it matters" using only supported event/evidence context
- `sentinel/intelligence/daily_brief.py` — assemble `ReportSection` and `DailyReport` outputs
- Prompt templates versioned in `sentinel/intelligence/prompts/`
- Provenance/evidence handling so every persisted `MarketEvent` has at least one source Article
- Structured LLM output validation and deterministic rejection/fallback for malformed or unsupported output
- LLM usage and cost accounting per intelligence run / daily brief
- Unit and integration tests

### Architecture Rules
- `Article` remains the evidence unit; raw evidence is never rewritten by intelligence.
- One `MarketEvent` may be supported by multiple Articles.
- One Article may support multiple independently justified MarketEvents.
- LLM output is a candidate, never an implicitly trusted domain object.
- Analysts may derive implications but must not introduce unsupported factual claims.
- Phase 4 does not introduce `Signal`, `Insight`, or other generic intelligence models.
- Persistence and external providers remain behind the existing application-layer boundaries.

### Exit Criteria
- Every persisted `MarketEvent` has at least one source Article
- Related Articles can be synthesised into a single event without losing provenance
- Invalid or unsupported LLM output cannot bypass domain validation
- ReportSections and DailyReports are assembled deterministically from validated events
- Every report insight/section can be traced to one or more source Articles through its MarketEvents
- LLM usage and cost are tracked for each intelligence run / daily brief
- Re-running the same input is idempotent or produces a documented deterministic reconciliation path

### Dependencies
Phase 3 complete.

### Complexity
High — prompt engineering and output quality validation.

---

## Phase 5 — Knowledge Base

**Status:** Architecture resolved

> **Architecture decision:** Phase 5 treats `MarketEvent` as the canonical historical intelligence object. It does not introduce a second event/signal/insight model. Knowledge updates consume validated Phase 4 outputs independently of DailyReport assembly. See `docs/decisions/ADR-0003-knowledge-base-architecture.md`.

### Objectives
Build a persistent, searchable knowledge base that accumulates typed entities, themes, MarketEvents, and their evidence relationships over time.

### Canonical Flow
`Processed Articles → Phase 4 Intelligence → MarketEvents`

Then, independently:

`MarketEvents + processed entity references → Knowledge Ingestion → PostgreSQL Knowledge Store → FTS / pgvector Retrieval`

Daily report assembly is not the persistence trigger for knowledge updates.

### Deliverables
- `sentinel/knowledge/` application layer for knowledge ingestion, resolution, persistence, and retrieval
- Typed knowledge handling for existing `Company`, `Person`, `Organization`, and `Theme` models
- MarketEvent history and entity/theme relationship persistence
- Entity resolution that maps extracted mentions to existing typed records without introducing a generic `Entity` model
- Semantic retrieval using pgvector
- PostgreSQL full-text retrieval
- Source provenance preserved through `MarketEvent → Article` relationships and entity/theme evidence links
- Deterministic/idempotent knowledge updates for repeated pipeline inputs
- Unit and integration tests

### Architecture Rules
- `sentinel_core` remains dependency-free from `sentinel/` application packages.
- `MarketEvent` remains the canonical event/intelligence object.
- Do not introduce `Signal`, `Event`, `Insight`, or another generic intelligence model.
- Do not introduce a generic `Entity` model; resolution remains typed by Company/Person/Organization/Theme.
- Knowledge ingestion consumes validated Phase 4 outputs and is independently retryable/rebuildable.
- DailyReport generation must not be the hidden side effect that persists the knowledge base.
- Articles remain immutable evidence.
- Country remains deferred. A `Country` domain model requires a separate architecture decision based on a concrete use case.
- Vector search initially targets `MarketEvent` as the primary semantic intelligence unit; article evidence is reached through provenance. Additional embedding targets require a documented use case.
- Search infrastructure remains behind the knowledge/search application boundary; downstream phases should not depend directly on PostgreSQL or pgvector APIs.

### Exit Criteria
- Validated MarketEvents can be ingested into the knowledge base with their entity/theme relationships.
- Re-running the same knowledge input does not create duplicate entity or event records.
- Every persisted MarketEvent remains traceable to at least one supporting Article.
- Typed entity records can be resolved and retrieved from accumulated evidence.
- Full-text and semantic search return deterministic, source-traceable results at the target data volume.
- Knowledge ingestion can be retried independently from DailyReport generation.
- Tests cover entity resolution, relationship persistence, provenance, idempotency, and search behaviour.

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
