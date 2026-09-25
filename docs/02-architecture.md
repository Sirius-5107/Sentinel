# Architecture

**Status:** Active — Phase 3 complete; Phase 4 is next
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
