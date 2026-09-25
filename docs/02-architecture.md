# Architecture

**Status:** Active — Phase 4 complete; Phase 5 architecture resolved
**Version:** 1.0

---

## 1. Component Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        External World                             │
│   RSS Feeds │ Websites │ APIs │ SEC EDGAR │ Market Data           │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Collector  │  sentinel/collector
                    │  (Phase 2)  │
                    └──────┬──────┘
                           │ Articles (INGESTED)
                    ┌──────▼──────┐
                    │  Processor  │  sentinel/processing
                    │  (Phase 3)  │
                    └──────┬──────┘
                           │ Articles (PROCESSED / DEDUPLICATED)
                    ┌──────▼──────┐
                    │ Intelligence│  sentinel/intelligence
                    │  (Phase 4)  │
                    └──────┬──────┘
                           │ MarketEvents + DailyReport
                           │ (Signal = MarketEvent)
                    ┌──────▼──────┐
                    │  Knowledge  │  sentinel/knowledge
                    │  (Phase 5)  │
                    └──────┬──────┘
                           │ Entity profiles updated
                    ┌──────▼──────┐
                    │  Publisher  │  sentinel/publish
                    │  (Phase 7)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Notion   │
                    └─────────────┘
```

---

## 2. Package Dependency Rules

The dependency graph is a strict DAG. No cycles are permitted.

```
sentinel/collector   ──┐
sentinel/processing  ──┤
sentinel/intelligence──┤──► sentinel_core ──► (stdlib + pydantic only)
sentinel/knowledge   ──┤
sentinel/research    ──┤
sentinel/publish     ──┘
sentinel/scheduler   ──► sentinel_core
sentinel/api         ──► sentinel_core
sentinel/cli         ──► sentinel_core
```

`sentinel_core` never imports from any `sentinel/` package. The arrow goes one way only: application packages import from the core; the core is self-contained.

---

## 3. Database Architecture

### Primary Store

PostgreSQL serves as the single source of truth for all persistent data.

| Concern | Solution |
|---|---|
| Relational data | Standard PostgreSQL tables |
| Semantic search | pgvector extension |
| Full-text search | PostgreSQL `tsvector` / `GIN` index |
| Migrations | Alembic |
| ORM | SQLAlchemy 2 (async-capable) |

The Phase 3 processing layer operates on `Article` evidence without introducing new persistence or domain models. Provider-backed embedding paths are optional and remain behind application-layer interfaces.

### Schema Principles

- Every table has a UUID v4 primary key matching the domain model `id`.
- Every table has `created_at` and `updated_at` timestamp columns.
- Unique constraints mirror the domain contract (e.g. `url` on Article).
- Many-to-many relationships use explicit join tables.
- The database does not generate UUIDs or timestamps; the application layer does.

---

## 4. External Integrations

| Integration | Package | Phase |
|---|---|---|
| Notion (publish) | Official Notion SDK | Phase 7 |
| LLM provider | `sentinel_core/interfaces/` + `sentinel/intelligence/` | Phase 4 |
| Embedding provider | `sentinel_core/interfaces/` + `sentinel/processing/` | Phase 3 |
| RSS feeds | `feedparser` | Phase 2 |
| Static scraping | `httpx` + `selectolax` / `beautifulsoup4` | Phase 2 |
| Dynamic scraping | `playwright` | Phase 2 |

All external integrations are isolated behind interface classes defined in `sentinel_core/interfaces/`. No implementation detail of any provider leaks into the domain layer.

---

## 5. API Architecture

FastAPI serves the REST API for external consumption. The API is implemented in `sentinel/api/` and consumes `sentinel_core` models directly for request/response schemas.

Authentication: API key (Phase 8).

---

## 6. CI/CD Architecture

```
Push to main/develop
         │
         ▼
  GitHub Actions CI
         │
    ┌────┴────┐
    │         │
   lint      test
  (ruff)   (pytest)
    │         │
  format   coverage
  check    >95% core
    │
  pyright
  (strict)
    │
  mkdocs
   build
```

Every step must pass. The workflow fails on the first error. No warnings are suppressed.

---

## 7. Infrastructure Layout

```
infrastructure/
├── docker/          Dockerfiles (Phase 10)
├── compose/         Docker Compose files (Phase 10)
├── deployment/      Deployment manifests (Phase 10)
└── scripts/         Operational scripts (Phase 10)
```

Infrastructure is not implemented until Phase 10.

---

## 8. Security Boundaries

- Secrets live only in environment variables or `.env` (never committed).
- All external input is validated through Pydantic models before processing.
- HTTP requests always use explicit timeouts.
- The API enforces authentication on all endpoints.
- Logs never contain secrets or credentials.


---

## 9. Phase 4 Intelligence Architecture

Phase 4 uses an event-centric intelligence model. `MarketEvent` is the canonical structured intelligence/signal object; the platform does not introduce a separate `Signal` domain model.

### 9.1 Evidence-to-Intelligence Flow

```text
Processed Articles
        │
        ▼
┌──────────────────────┐
│ Event Synthesis      │
│ group related        │
│ evidence and identify│
│ discrete developments│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ MarketEvent          │
│ canonical intelligence│
│ object               │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Analysis             │
│ "why it matters"     │
│ implications/context │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ ReportSection        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ DailyReport          │
└──────────────────────┘
```

### 9.2 Provenance

A `MarketEvent` is not valid for persistence without at least one source `Article`. The relationship is many-to-many at the application/database layer:

- one event may be supported by multiple Articles;
- one Article may support multiple independently justified events;
- report content must remain traceable through MarketEvents to source Articles.

The Pydantic `MarketEvent` model does not carry article IDs because provenance is represented by application/database relationships.

### 9.3 LLM Boundary

LLMs are used as bounded proposal/generation components. Their output must be parsed into structured data and validated against domain contracts before persistence. Provider failures, malformed output, unsupported claims, or missing provenance must not produce persisted intelligence objects.

### 9.4 Responsibility Boundaries

| Component | Responsibility |
|---|---|
| `synthesiser.py` | Evidence grouping and `MarketEvent` synthesis |
| `analyst.py` | Implications and "why it matters" reasoning from supported context |
| `daily_brief.py` | Deterministic report assembly into `ReportSection` and `DailyReport` |
| Phase 5 Knowledge | Historical entity/theme/event accumulation |
| Phase 7 Publisher | Notion and other external publication |

### 9.5 Explicit Non-Goals

Phase 4 does not introduce:

- a `Signal` model;
- a generic `Insight` model;
- a second intermediate intelligence layer between Article and MarketEvent;
- autonomous trading or portfolio execution;
- Notion publishing implementation;
- Phase 5 knowledge-base persistence logic.


---

## 10. Phase 5 Knowledge Architecture

Phase 5 turns validated Phase 4 intelligence into persistent, searchable historical knowledge. It does not redefine the intelligence model.

### 10.1 Knowledge Flow

```text
Processed Articles
        │
        ▼
Phase 4 Intelligence
        │
        ▼
   MarketEvents
        │
        ├───────────────► DailyReport
        │
        ▼
Knowledge Ingestion
        │
   ┌────┼───────────────┐
   ▼    ▼               ▼
Company Person   Organization / Theme
   │    │               │
   └────┴───────────────┘
             │
             ▼
      PostgreSQL Knowledge Store
             │
        ┌────┴────┐
        ▼         ▼
       FTS     pgvector
        │         │
        └────┬────┘
             ▼
          Retrieval
```

Knowledge ingestion is an independent consumer of validated Phase 4 outputs. DailyReport assembly is not a hidden trigger for knowledge persistence. This permits independent retries, deterministic rebuilds, and testing.

### 10.2 Canonical Knowledge Objects

Phase 5 uses the existing typed domain models:

- `Company`
- `Person`
- `Organization`
- `Theme`
- `MarketEvent`
- `Article` as immutable evidence

No generic `Entity`, `Event`, `Signal`, or `Insight` model is introduced.

### 10.3 Entity Resolution

Entity extraction from Phase 3 identifies mentions; Phase 5 resolves those mentions against persistent typed records.

Resolution is type-specific:

- Company: ticker/ISIN where available, then normalized identity matching.
- Person: normalized name plus contextual evidence.
- Organization: normalized name/abbreviation plus contextual evidence.
- Theme: existing theme identity/slug; creation policy must be explicit rather than arbitrary LLM invention.

A resolver must either map a mention to an existing record or create a validated typed record according to deterministic policy. Resolution must not silently merge distinct records.

### 10.4 Event History and Provenance

`MarketEvent` remains the canonical historical event object.

Every persisted event must have at least one supporting Article. Entity/theme relationships are additional knowledge links; they do not replace article provenance.

The retrieval path for event intelligence is:

`query → MarketEvent → supporting Articles`.

This keeps semantic retrieval focused on validated intelligence while preserving raw evidence for inspection.

### 10.5 Search Boundary

The knowledge package owns search orchestration. PostgreSQL/pgvector implementation details remain behind that boundary.

Initial retrieval surfaces:

| Search mode | Primary target | Purpose |
|---|---|---|
| Full-text | MarketEvents + typed entity/theme text | Exact terms, names, phrases |
| Semantic | MarketEvents | Conceptual similarity over validated intelligence |
| Evidence traversal | Articles through provenance | Inspect supporting source material |

Search results must preserve enough identity/provenance to trace returned intelligence back to source evidence.

### 10.6 Country Decision

`CountryCode` remains sufficient for Phase 5 unless a concrete country-level knowledge use case requires a persistent country entity. Introducing `Country` requires a separate ADR and domain-model change.

### 10.7 Phase 5 Non-Goals

- trading or portfolio execution;
- research-document generation (Phase 6);
- Notion publishing (Phase 7);
- REST API (Phase 8);
- dashboard work (Phase 9);
- autonomous web research;
- generic entity/event abstractions;
- automatic country-model creation without an explicit use case.
