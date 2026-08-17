# Sentinel Engineering Rules

Sentinel is a long-term production software project.

This repository is not a prototype.

Always optimize for maintainability over speed.

Never implement functionality that was not explicitly requested.

Read all documentation before coding.

The documentation is authoritative.

Architecture decisions are recorded as ADRs in docs/decisions/.

Never violate an ADR.

When documentation and code disagree, update the documentation or ask for clarification.

Prefer small pull requests.

Prefer composition over inheritance.

Prefer explicitness over cleverness.

Never introduce frameworks unnecessarily.

Never create files larger than ~500 lines without strong justification.

Never create classes larger than ~300 lines without strong justification.

Every public function should eventually have tests.

Every public object should have documentation.

Never hardcode secrets.

Never use print().

Always use structured logging (Loguru).

Never invent domain fields.

Never invent business rules.

Never implement future roadmap items.

Only implement the requested milestone.

---

## Phase Boundary Rules

**Current phase:** Phase 1 — Core Domain

**Phase 1 scope** (from docs/05-contracts.md):

- Immutable Pydantic v2 domain models in sentinel_core/
- No persistence (no SQLAlchemy, no Alembic, no database connections)
- No HTTP calls
- No LLM calls
- No file I/O beyond reading this file
- No collectors, processors, publishers, or schedulers

**Phase 1 is NOT complete.** The following sentinel_core sub-packages still need implementation:
- sentinel_core/exceptions/ — implemented (Phase 1 reconciliation)
- sentinel_core/interfaces/ — implemented (Phase 1 reconciliation)
- sentinel_core/constants/ — implemented (Phase 1 reconciliation)
- sentinel_core/config/ — stub only; implement at Phase 2 start

---

## Deferred Decisions

**Signal:** The term "Signal" appears in early documentation but has no
formal model. Do NOT create a Signal model until the Intelligence phase
(Phase 4) decision is made. See docs/06-phase-1-audit.md §15 Q1.

**Country:** A Country model may be needed in Phase 5 (Knowledge Base).
Do NOT create it now. CountryCode value object is sufficient for Phase 1.
See docs/06-phase-1-audit.md §15 Q2.

---

## Key Architectural Rules

1. sentinel_core never imports from sentinel/*
2. All domain objects are frozen (immutable snapshots)
3. updated_at is a version timestamp set once at construction (ADR-0004)
4. All datetimes are UTC-aware; non-UTC datetimes are normalised, not rejected
5. uv.lock is committed (Sentinel is an application, not a library)
6. All datetime fields: naive → rejected, aware → normalised to UTC

---

## Canonical Domain Model

The 12 authoritative Phase 1 models (docs/05-contracts.md):
Source, Article, Company, Person, Organization, Theme, Market,
MarketEvent, ReportSection, DailyReport, PipelineRun, Task

Do NOT add: Entity, Event, Signal, Report, Country (stale/deferred names)

---

## Windows-Specific Notes

- PowerShell, not bash
- Use `uv run` for all Python commands
- Use `datetime.now(tz=UTC)` not `date.today()` in tests (IST = UTC+5:30)
- tzdata package required for IANA timezone support on Windows
