# ADR-0003: Knowledge Base Architecture

**Status:** Accepted  
**Date:** 2026-09-26  
**Decision:** Phase 5 uses typed knowledge objects and independent knowledge ingestion; `MarketEvent` remains the canonical historical intelligence object.

---

## Context

Phase 4 establishes `MarketEvent` as Sentinel's canonical intelligence/signal object and persists its Article provenance. Phase 5 needs to accumulate this validated intelligence into a searchable knowledge base spanning companies, people, organizations, themes, and historical events.

The original Phase 5 plan was intentionally high-level. Without a more explicit boundary, implementation could introduce duplicate abstractions such as a generic `Entity` or `Event`, couple knowledge persistence to DailyReport generation, or embed raw articles as the primary semantic intelligence unit.

The existing domain already contains the required typed models:

- `Company`
- `Person`
- `Organization`
- `Theme`
- `MarketEvent`
- `Article`

PostgreSQL with pgvector is already the persistence/search foundation.

## Decision

### 1. MarketEvent remains the canonical historical intelligence object

Phase 5 stores and retrieves `MarketEvent` records. It does not introduce `Signal`, `Event`, `Insight`, `HistoricalEvent`, or another intermediate intelligence model.

The historical intelligence path is:

`MarketEvent → supporting Article(s)`

### 2. Knowledge ingestion is independent of DailyReport assembly

Phase 5 consumes validated Phase 4 outputs as an independent application-layer operation.

Conceptually:

```text
Phase 4
  │
  ├──→ DailyReport
  │
  └──→ Knowledge Ingestion → Knowledge Store
```

DailyReport generation must not be the hidden trigger for knowledge persistence.

This allows knowledge updates to be retried, tested, and rebuilt independently.

### 3. Knowledge entities remain typed

Entity resolution operates against the existing typed models:

- Company
- Person
- Organization
- Theme

No generic `Entity` table or domain model is introduced.

Extraction identifies mentions; resolution maps those mentions to persistent typed identities using type-specific deterministic rules and contextual evidence.

### 4. Article remains immutable evidence

Articles remain the fundamental evidence unit. Knowledge accumulation may add relationships and derived profile information, but must not rewrite the raw Article evidence.

Every persisted MarketEvent must retain at least one supporting Article.

### 5. Semantic retrieval initially targets MarketEvent

The primary pgvector semantic-search unit is `MarketEvent`, because it represents validated, synthesized intelligence rather than raw source noise.

The initial retrieval path is:

`query → MarketEvent → supporting Article(s)`

Embedding additional object types requires a concrete use case and should not be added speculatively.

### 6. Full-text and vector search are knowledge-layer concerns

The `sentinel/knowledge/` package owns retrieval orchestration. PostgreSQL FTS and pgvector implementation details remain behind this application boundary.

Initial search surfaces are:

- full-text search over MarketEvents and typed entity/theme text;
- semantic search over MarketEvents;
- provenance traversal to supporting Articles.

### 7. Country remains deferred

`CountryCode` remains sufficient for Phase 5. A persistent `Country` domain model will only be introduced if a concrete country-level knowledge use case requires it, with a separate architecture decision.

## Consequences

### Positive

- Preserves the Phase 4 event-centric architecture.
- Avoids generic abstractions that weaken domain semantics.
- Separates report generation from long-lived knowledge persistence.
- Makes knowledge ingestion independently retryable and rebuildable.
- Keeps raw evidence traceable from retrieved intelligence.
- Provides a clear boundary for future research and API layers.
- Avoids premature expansion of the embedding surface.

### Negative / Trade-offs

- Entity resolution requires type-specific logic rather than one generic resolver.
- Knowledge ingestion must explicitly coordinate multiple relationship types.
- Semantic search initially covers MarketEvents rather than every possible object.
- A future Country entity may require a new ADR and migration if country-level use cases emerge.

## Rejected Alternatives

### Generic Entity model

Rejected because the domain already has meaningful typed identities with different identifiers and resolution rules.

### Separate historical Event model

Rejected because `MarketEvent` already represents the canonical event and is explicitly designed to be tracked over time.

### Knowledge persistence as a DailyReport side effect

Rejected because it couples two independently retryable concerns and makes rebuilding knowledge from validated intelligence harder.

### Embed every object immediately

Rejected as premature. The first semantic retrieval target is MarketEvent; additional embedding targets should follow demonstrated retrieval requirements.

## Scope for Phase 5

This ADR governs:

- knowledge ingestion;
- entity resolution;
- typed relationship persistence;
- MarketEvent history;
- full-text retrieval;
- pgvector semantic retrieval;
- provenance-preserving knowledge queries.

It does not authorize:

- research generation;
- publishing;
- API exposure;
- dashboard implementation;
- trading/portfolio execution;
- autonomous web research.
