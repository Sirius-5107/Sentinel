# Changelog

All significant changes to Sentinel are recorded here. This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.

---

## [0.1.0] — 2026-08-07

### Summary
Initial engineering foundation. Repository scaffold, tooling configuration, documentation structure, and package skeletons. No business logic implemented.

### Major Architectural Decisions

- **ADR-0001:** Event-centric data model — all financial developments are modelled as events with typed entities and temporal attributes.
- **ADR-0002:** PostgreSQL as the primary data store, extended with pgvector for semantic search.
- **ADR-0003:** Custom provider interfaces for LLM and embedding integrations, keeping the core domain decoupled from any specific AI provider.

### Breaking Changes
None — initial release.

### What Was Delivered
- Repository structure and package layout
- `pyproject.toml` with full dependency declaration
- Ruff, Pyright, pytest, and pre-commit configuration
- GitHub Actions CI pipeline
- MkDocs Material documentation site
- `sentinel` and `sentinel_core` package skeletons
- Configuration file stubs
- Engineering standards handbook
- Code review checklist
- Phased implementation plan

### Future Work
- Phase 1: Core domain models (`sentinel_core`)
- Phase 2: Data collection layer
- Phase 3: Processing pipeline
- See `20-implementation-plan.md` for the full roadmap

---

## [0.1.1] — 2026-08-15

### Summary
Phase 1 finalization. Repository hygiene, CI fixes, UTC policy, immutability clarification, documentation restoration, and test hardening. No new functionality.

### Repository Hygiene
- Renamed `gitignore` → `.gitignore` (was incorrectly named and not functioning)
- Removed 34 tracked generated artifacts (`.coverage`, `__pycache__/`, `*.pyc`)

### CI Fixes
- Fixed E501 (line too long) in `test_models_level3.py`
- Excluded `docs/` from Ruff format scope (docs contain illustrative code blocks)

### Domain Model Fixes
- Removed orphaned `model_validator` import from `source.py`

### Timestamp Policy
- Centralised UTC normalisation in `SentinelModel._normalise_to_utc` base validator
- Changed policy from "reject non-UTC" to "normalise to UTC" — non-UTC aware datetimes are now converted rather than rejected
- Propagated consistent normalisation to all per-field datetime validators
- All error messages consistently mention "timezone-aware (UTC-aware)"

### Immutability Policy (ADR-0004)
- Clarified that `updated_at` is a version timestamp, not a mutable field
- Updated `_base.py` module docstring with full immutability and UTC policy documentation
- Added ADR-0004 documenting the decision and rationale
- Added `TestSentinelModelImmutability` and `TestUTCNormalisationPolicy` test classes

### Documentation Restored
- `docs/01-sdd.md` — Software Design Document (was empty stub)
- `docs/02-architecture.md` — Architecture reference (was empty stub)
- `docs/03-domain-model.md` — Domain model summary (was empty stub)
- `docs/04-tech-stack.md` — Technology stack and rationale (was empty stub)
- `docs/00-vision.md` — Restored Success Metrics section
- All ADRs (0001–0003) restored with full content
- `docs/decisions/ADR-0004-immutable-domain-objects.md` — new ADR

### Test Results
- 293 tests passing (up from 283)
- Coverage: 99% sentinel_core
- Ruff: clean
- Pyright: clean
- MkDocs: builds successfully

### Future Work
- Phase 2: Data collection layer (RSS, scraping, dynamic collectors)
- Phase 3: Processing pipeline (classification, scoring, entity extraction)
