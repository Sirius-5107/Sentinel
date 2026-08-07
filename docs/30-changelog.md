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
