# Engineering Standards

This document is the authoritative engineering handbook for Sentinel. Every contributor is expected to read, understand, and follow these standards. They exist not to create bureaucracy but to ensure that a platform intended to run for many years remains readable, maintainable, and safe.

---

## Project Philosophy

Sentinel is a long-term production system, not a prototype. Every decision must be made with this in mind.

- **Correctness over speed.** A financial intelligence platform that produces incorrect output is worse than one that produces no output.
- **Explicitness over cleverness.** Code is read far more than it is written. Prefer the obvious solution.
- **Evidence first.** Every claim the platform makes must be traceable to a source. This principle applies equally to code — every architectural decision must be traceable to a documented rationale.
- **Signal over noise.** Do not add abstractions, dependencies, or configuration that do not serve a clear current need.

---

## Python Style

- Python **3.13** is the minimum and target version.
- Follow [PEP 8](https://peps.python.org/pep-0008/) as enforced by Ruff.
- Line length: **100 characters**.
- Use **double quotes** for strings.
- Use **f-strings** for string interpolation. Never `%` or `.format()`.
- Prefer **list/dict/set comprehensions** over `map`/`filter` where readability is maintained.
- Never use `lambda` outside of `sort(key=...)` calls. Name your functions.
- Avoid `*args` and `**kwargs` unless genuinely required by an interface contract.

---

## Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `news_collector.py` |
| Packages | `snake_case` | `sentinel/collector/` |
| Classes | `PascalCase` | `NewsArticle` |
| Functions / methods | `snake_case` | `fetch_articles()` |
| Variables | `snake_case` | `article_count` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Type aliases | `PascalCase` | `ArticleId` |
| Private symbols | `_leading_underscore` | `_parse_date()` |
| Abstract base classes | `Abstract` prefix | `AbstractCollector` |
| Protocol classes | `Protocol` suffix | `CollectorProtocol` |
| Enum members | `UPPER_SNAKE_CASE` | `AssetClass.US_EQUITY` |

---

## Folder Conventions

```
sentinel/           Top-level application package
sentinel_core/      Shared domain primitives (models, interfaces, enums)
tests/unit/         Isolated, fast tests with no external dependencies
tests/integration/  Tests that require running services (database, etc.)
tests/fixtures/     Shared pytest fixtures
configs/            YAML configuration files — no secrets
infrastructure/     Docker, compose, deployment manifests
docs/               All documentation — markdown only
scripts/            One-off operational scripts
```

Every Python package must contain an `__init__.py`. Every directory without Python files must contain a `.gitkeep` until substantive files are added.

---

## Typing Policy

- **Strict Pyright** is enforced. The CI pipeline will fail on any type error.
- All public functions and methods must be fully annotated — parameters and return type.
- Private helpers must be annotated unless the types are trivially obvious.
- `Any` is forbidden unless explicitly justified with an inline comment explaining why.
- Use `TypeVar`, `Generic`, and `Protocol` to express polymorphism. Avoid inheritance where protocols suffice.
- Use `TypeAlias` for domain-specific type names (e.g., `ArticleId = NewType("ArticleId", str)`).
- Prefer `Sequence` over `list` and `Mapping` over `dict` in function signatures where mutation is not intended.
- Use `Final` for constants.

---

## Logging Policy

- **Loguru** is the only permitted logging library.
- Never use `print()` in application code. Use `logger.debug()` or `logger.info()`.
- Never import `logging` from the standard library directly.
- Log at the appropriate level:
  - `DEBUG` — internal state useful during development
  - `INFO` — normal operational events (pipeline started, article ingested)
  - `WARNING` — unexpected but recoverable conditions
  - `ERROR` — failures that require attention
  - `CRITICAL` — failures that halt the system
- Always include structured context: `logger.info("Article ingested", id=article_id, source=source_name)`.
- Never log secrets, credentials, or personally identifiable information.

---

## Configuration Policy

- All configuration lives in `configs/`.
- Application code reads configuration once at startup via a config loader in `sentinel_core/config/`.
- Secrets are supplied exclusively via environment variables. They must never appear in YAML files or source code.
- Configuration must be validated with Pydantic at startup. The application must fail fast on invalid configuration.
- `.env` files are for local development only. They are never committed.

---

## Testing Policy

- Every public function must have at least one unit test.
- Unit tests live in `tests/unit/` and must not touch the database, network, or filesystem.
- Integration tests live in `tests/integration/` and require running services.
- Tests must be deterministic. Random values must be seeded.
- Use `pytest.mark.unit` and `pytest.mark.integration` to label tests.
- Coverage threshold starts at 0% and increases as features are implemented. The target is **90%** for `sentinel_core` and **80%** for `sentinel`.
- Mock external dependencies with `unittest.mock` or `pytest-mock`. Never make real HTTP calls in unit tests.

---

## Documentation Policy

- Every public module, class, and function must have a docstring.
- Docstrings follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Architecture decisions are recorded as ADRs in `docs/decisions/`.
- All documentation is written in Markdown and lives in `docs/`.
- The documentation must build without warnings: `mkdocs build --strict`.

---

## Architecture Rules

- `sentinel_core` contains only primitives: models, interfaces, enums, exceptions, config schemas, types, and constants. It must have zero business logic.
- `sentinel` packages import from `sentinel_core`. `sentinel_core` never imports from `sentinel`.
- No circular imports. The dependency graph must be a DAG.
- Each `sentinel` sub-package owns one vertical slice of functionality (collect, process, publish, etc.).
- Cross-package communication goes through `sentinel_core` interfaces, never through direct imports between `sentinel` sub-packages.

---

## Dependency Rules

- All dependencies are declared in `pyproject.toml`. No `requirements.txt`.
- Pin minor versions for production dependencies (e.g., `pydantic>=2.10,<3`).
- Evaluate every new dependency against: security history, maintenance status, licence compatibility, and whether the functionality could reasonably be implemented in-house.
- Development dependencies go in `[project.optional-dependencies] dev`.
- Never add a dependency to solve a problem that is trivial to solve in Python.

---

## Import Rules

- Imports are grouped: stdlib → third-party → first-party, separated by blank lines. Ruff enforces this.
- Absolute imports only. No relative imports (e.g., no `from . import foo`).
- Never use wildcard imports (`from module import *`).
- Type-only imports must use `from __future__ import annotations` or `TYPE_CHECKING` guard.

---

## File, Function, and Class Size Limits

| Unit | Soft limit | Hard limit |
|---|---|---|
| File | 300 lines | 500 lines |
| Function / method | 30 lines | 50 lines |
| Class | 150 lines | 250 lines |
| Module-level constants | 20 | — |

If you are approaching a hard limit, the code needs to be decomposed.

---

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`.

Examples:
- `feat(collector): add RSS ingestion for Reuters feed`
- `fix(processing): handle missing publication date in articles`
- `docs(adr): record decision to use PostgreSQL for primary store`
- `chore(deps): bump pydantic to 2.10`

Commit messages must be in the imperative mood. "Add feature" not "Added feature".

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code. Protected. Requires PR + review. |
| `main` | Default integration branch. Requires PR. |
| `feat/<name>` | Feature branches. Branch from `main`. |
| `fix/<name>` | Bug fix branches. Branch from `main`. |
| `chore/<name>` | Non-functional changes. |
| `docs/<name>` | Documentation-only changes. |

---

## Security Practices

- Never commit secrets, API keys, tokens, or passwords.
- Use environment variables for all credentials.
- Validate all external input with Pydantic before processing.
- Treat every external data source as untrusted.
- Use `httpx` with explicit timeouts on every request.
- Log security-relevant events (authentication failures, rate limit hits).

---

## Error Handling

- Never silently swallow exceptions with a bare `except:` or `except Exception:` without re-raising or logging.
- Define domain-specific exceptions in `sentinel_core/exceptions/`. Never raise built-in exceptions directly from business logic.
- Use structured logging when catching exceptions: `logger.error("Failed to fetch article", exc_info=True, url=url)`.
- Functions that can fail in expected ways should return a `Result` type or raise a typed domain exception — never return `None` to signal failure.

---

## ADR Policy

Any decision that affects the system architecture, technology stack, or data model must be recorded as an Architecture Decision Record (ADR) in `docs/decisions/`.

ADR filename format: `ADR-NNNN-short-title.md`

Each ADR must contain: **Status**, **Context**, **Decision**, **Consequences**.

Once an ADR is marked `Accepted`, it may not be silently overridden. A new ADR superseding it must be created.

---

## LLM Usage Policy

- LLMs are never called in unit tests.
- Every LLM call must be logged with the model name, prompt token count, and completion token count.
- LLM output must always be validated before being persisted or published.
- Prompt templates are versioned — changes to prompts that affect output format require a new prompt version.
- Cost must be tracked per pipeline run.

---

## Definition of Done

A feature is done when:

1. Implementation is complete and matches the design documented in the SDD.
2. All public symbols are typed and documented.
3. Unit tests are written and pass.
4. Integration tests are written where applicable.
5. The CI pipeline passes without warnings.
6. A PR has been reviewed and approved.
7. Relevant documentation has been updated.
8. If an architectural decision was made, an ADR has been recorded.