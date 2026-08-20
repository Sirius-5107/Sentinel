# Sentinel

**Autonomous financial intelligence platform.**

Sentinel continuously monitors global markets, extracts the highest-signal developments, synthesises them into investment-grade research, maintains a searchable knowledge base, and surfaces actionable insights for investors.

---

## Vision

Most financial data platforms produce summaries. Sentinel produces intelligence.

The distinction matters: a summary tells you what happened. Intelligence tells you what it means, why it matters, and what to watch next — with every claim traceable to a primary source.

Sentinel is designed to operate at institutional research quality. Every output should read as though it came from a senior analyst at a top-tier asset manager, not a news aggregator.

The five core principles that guide every decision:

1. **Evidence First** — every insight links to a primary source. Nothing is invented.
2. **Signal over Noise** — one synthesis from fifteen sources, not fifteen summaries.
3. **Explain Why It Matters** — analysis, not summarisation.
4. **Institutional Quality** — outputs at the standard of Goldman, Bridgewater, Apollo.
5. **Everything is Searchable** — the full history of intelligence is queryable.

---

## Architecture

Sentinel is organised as a pipeline of discrete stages, each owned by a separate package:

```
Collection → Processing → Intelligence → Knowledge → Research → Publishing
```

| Stage | Package | Responsibility |
|---|---|---|
| Collection | `sentinel/collector` | Ingest articles from RSS, web, and dynamic sources |
| Processing | `sentinel/processing` | Classify, score, deduplicate, and extract entities |
| Intelligence | `sentinel/intelligence` | Synthesise signals into insights and daily briefs |
| Knowledge | `sentinel/knowledge` | Maintain the entity and event knowledge base |
| Research | `sentinel/research` | Generate long-form research documents |
| Publishing | `sentinel/publish` | Distribute to Notion and other channels |
| API | `sentinel/api` | FastAPI REST interface |
| CLI | `sentinel/cli` | Operational command-line interface |

Shared domain primitives (models, interfaces, enums, exceptions) live in `sentinel_core` and are consumed by all stages.

---

## Repository Layout

```
Sentinel/
├── sentinel/               Application packages (collection, processing, intelligence, …)
├── sentinel_core/          Shared domain primitives (models, interfaces, enums, types)
├── tests/
│   ├── unit/               Fast, isolated tests — no external dependencies
│   ├── integration/        Tests requiring running services
│   └── fixtures/           Shared pytest fixtures
├── configs/                YAML configuration (no secrets)
├── docs/                   Engineering documentation
│   └── decisions/          Architecture Decision Records
├── infrastructure/
│   ├── docker/             Dockerfiles
│   ├── compose/            Docker Compose files
│   ├── deployment/         Deployment manifests
│   └── scripts/            Operational scripts
├── scripts/                Development scripts
├── .github/workflows/      GitHub Actions CI
├── pyproject.toml          Project metadata and tooling configuration
└── mkdocs.yml              Documentation site configuration
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Package Manager | uv |
| Validation | Pydantic v2 |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2 |
| Migrations | Alembic |
| HTTP | httpx |
| HTML Parsing | selectolax + BeautifulSoup |
| Dynamic Scraping | Playwright |
| RSS | feedparser |
| Logging | Loguru |
| Configuration | YAML + .env |
| API | FastAPI |
| CLI | Typer |
| Charts | Plotly |
| Documentation | MkDocs Material |
| Linting / Formatting | Ruff |
| Type Checking | Pyright (strict) |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Containers | Docker |
| Publishing | Notion SDK |

---

## Development Setup

**Prerequisites:** Python 3.13, [uv](https://docs.astral.sh/uv/), and Docker Desktop or a compatible local Docker runtime for the PostgreSQL development database.

```bash
# Clone the repository
git clone https://github.com/Sirius-5107/Sentinel.git
cd Sentinel

# Install all dependencies (including dev)
uv sync --all-extras

# Copy and populate environment variables
cp .env.example .env

# Start the local PostgreSQL + pgvector development database
docker compose -f infrastructure/compose/docker-compose.yml up -d

# Verify the setup
uv run ruff check .
uv run pyright
uv run pytest
uv run pytest tests/integration/test_postgres_persistence.py -q
uv run mkdocs build --strict
```

### Local PostgreSQL development database

The repository includes a minimal local PostgreSQL + pgvector stack for Phase 2 validation:

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

This starts a containerised PostgreSQL instance with:

- database: `sentinel`
- user: `sentinel`
- password: `sentinel`
- port: `5432`
- persistent local volume for database state
- health check

The default DSN format is:

```text
postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel
```

The SQLite unit tests remain available for fast local validation. PostgreSQL integration tests are opt-in and explicitly require the `SENTINEL_DB_URL` environment variable to start with `postgresql+psycopg://`.

---

## Documentation

Full engineering documentation is available at the MkDocs site.

To build and serve locally:

```bash
uv run mkdocs serve
```

Then open [http://localhost:8000](http://localhost:8000).

Key documents:

| Document | Path |
|---|---|
| Vision | `docs/00-vision.md` |
| Software Design Document | `docs/01-sdd.md` |
| Architecture | `docs/02-architecture.md` |
| Domain Model | `docs/03-domain-model.md` |
| Tech Stack | `docs/04-tech-stack.md` |
| Engineering Standards | `docs/10-engineering-standards.md` |
| Implementation Plan | `docs/20-implementation-plan.md` |

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 0 | Engineering foundation | In progress |
| 1 | Core domain models | Planned |
| 2 | Data collection | Planned |
| 3 | Processing pipeline | Planned |
| 4 | Intelligence synthesis | Planned |
| 5 | Knowledge base | Planned |
| 6 | Research engine | Planned |
| 7 | Publishing | Planned |
| 8 | API | Planned |
| 9 | Dashboard | Planned |
| 10 | Production hardening | Planned |

See [Implementation Plan](docs/20-implementation-plan.md) for full details.

---

## Contributing

1. Read the [Engineering Standards](docs/10-engineering-standards.md) before writing any code.
2. Branch from `develop` using the naming convention in the standards.
3. Ensure all CI checks pass before opening a PR.
4. Use the [Code Review Checklist](docs/11-code-review-checklist.md) when reviewing.
5. Record architectural decisions as ADRs in `docs/decisions/`.

---

## License

MIT — see [LICENSE](LICENSE).