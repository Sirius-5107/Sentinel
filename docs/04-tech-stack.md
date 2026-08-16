# Technology Stack

**Status:** Active — Phase 1 complete
**Version:** 1.0

---

## 1. Chosen Technologies

| Layer | Technology | Rationale |
|---|---|---|
| Language | Python 3.13 | Latest stable; best ecosystem for data + AI |
| Package manager | uv | Fast, lockfile-native, uv.lock committed |
| Validation | Pydantic v2 | Industry standard; strict mode; JSON schema |
| Database | PostgreSQL | Mature, reliable, ACID; pgvector extension available |
| Vector search | pgvector | Avoids a separate vector database |
| ORM | SQLAlchemy 2 | Async-capable; integrates with Alembic |
| Migrations | Alembic | Standard for SQLAlchemy projects |
| HTTP | httpx | Async-capable; explicit timeouts |
| HTML parsing | selectolax + BeautifulSoup | selectolax for speed; BS4 for complex cases |
| Dynamic scraping | Playwright | Headless browser for JS-rendered pages |
| RSS | feedparser | Mature; handles edge-case feed formats |
| LLM abstraction | Custom provider interface | Decouples core from any specific AI vendor |
| Embeddings | Custom provider interface | Same principle as LLM abstraction |
| Logging | Loguru | Structured; zero-config; superior to stdlib |
| Configuration | YAML + python-dotenv | Human-readable; secrets via env vars |
| Scheduling | Cron / GitHub Actions | Simple; no broker dependency at this scale |
| Testing | pytest + pytest-cov | Standard; extensive plugin ecosystem |
| Linting | Ruff | Replaces Flake8 + isort + pyupgrade; fast |
| Type checking | Pyright (strict) | Strictest available; catches real bugs |
| Documentation | MkDocs Material | Beautiful; Markdown-native; hot reload |
| API | FastAPI | Async; automatic OpenAPI docs |
| CLI | Typer | Built on Click; type-annotated |
| Charts | Plotly | Interactive; Python-native |
| Containers | Docker | Standard; reproducible deployments |
| CI/CD | GitHub Actions | Integrated with repository |
| Publishing | Official Notion SDK | First-party; stable API |

---

## 2. Key Constraints

### Python Version

**3.13 minimum, 3.13 target.** The project uses `StrEnum` (3.11+), `datetime.UTC` (3.11+), `zoneinfo` (3.9+), and pattern matching. No compatibility shims for older versions.

### Package Manager

**uv only.** No `pip install` in CI or documentation. `uv.lock` is committed because Sentinel is an application (not a library). The lockfile guarantees identical dependency trees everywhere.

### Type Checking

**Pyright strict mode.** `Any` is forbidden unless explicitly justified with a comment. All public functions are fully annotated. Pyright is run in CI and failures block merge.

### No Direct LLM Coupling

The domain contract layer (`sentinel_core`) does not import any LLM library. All LLM interaction is behind the `CollectorProtocol` / provider interface defined in `sentinel_core/interfaces/`. This means the core can be tested without any LLM.

---

## 3. Dependency Philosophy

> Never add a dependency to solve a problem that is trivial to solve in Python.

Every dependency is evaluated against:
- Security history
- Maintenance status
- Licence compatibility
- Whether the functionality could reasonably be implemented in-house

New dependencies require a `pyproject.toml` change and `uv lock` update committed in the same PR.

---

## 4. Why Not X?

| Alternative | Why Not |
|---|---|
| Pinecone / Weaviate | pgvector satisfies our vector search needs without a separate service |
| Redis | No caching or queue requirements in Phase 1 |
| Celery | Complexity not warranted at current scale; simple scheduler suffices |
| Django | Too opinionated; brings ORM and admin we don't need |
| Black | Replaced entirely by Ruff format |
| Flake8 / isort | Replaced entirely by Ruff |
| mypy | Pyright is stricter and faster |
| MongoDB | ACID and relational structure are required for financial data |
