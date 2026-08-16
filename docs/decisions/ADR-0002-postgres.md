# ADR-0002: PostgreSQL as Primary Data Store

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Himanshu

---

## Context

Sentinel needs a persistent data store that supports:

- Relational data with complex joins (articles ↔ entities ↔ events ↔ reports)
- Semantic search for deduplication and knowledge retrieval
- Full-text search for the searchability principle
- ACID guarantees for financial data integrity
- A single operational service rather than multiple specialised databases

---

## Decision

Use **PostgreSQL** as the sole persistent data store, extended with the **pgvector** extension for semantic search.

- SQLAlchemy 2 (async-capable) as the ORM
- Alembic for schema migrations
- pgvector for embedding storage and similarity search
- PostgreSQL `tsvector` / `GIN` index for full-text search

---

## Consequences

**Positive:**
- Single service to operate and monitor.
- pgvector satisfies semantic search without a dedicated vector database.
- ACID guarantees ensure consistency for financial data.
- PostgreSQL's full-text search is sufficient for Phase 5 knowledge base queries.
- SQLAlchemy 2 async support enables high-throughput pipeline stages.

**Negative:**
- At very large scale (>100M vectors), a dedicated vector database may outperform pgvector.
- PostgreSQL full-text search may need augmentation if query complexity grows significantly.

**Neutral:**
- The choice of PostgreSQL does not constrain the domain layer — `sentinel_core` has no database dependency.
- If a separate vector database is ever needed, the embedding\_id field on Article and MarketEvent provides a migration path.
