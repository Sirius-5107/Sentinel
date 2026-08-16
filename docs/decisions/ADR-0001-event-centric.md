# ADR-0001: Event-Centric Data Model

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Himanshu

---

## Context

Sentinel monitors financial markets and produces investment research. The core challenge is representing financial developments in a way that is:

- Traceable to source evidence
- Queryable by time, entity, and theme
- Extensible to new asset classes and regions
- Consistent with the "explain why it matters" principle

Two broad modelling approaches were considered:
1. **Article-centric:** Articles are the primary records; insights are annotations on articles.
2. **Event-centric:** Discrete financial developments (events) are first-class objects; articles are evidence.

---

## Decision

Adopt an **event-centric data model**.

All financial developments are modelled as `MarketEvent` objects. A `MarketEvent`:

- Has a concise `title` (what happened)
- Has a substantive `summary` (why it matters — minimum 100 characters)
- Carries typed metadata: `asset_class`, `region`, `sector`, `severity`, `sentiment`, `importance_score`
- References the `Article` objects that are its evidence (many-to-many)
- References the entities involved: `Company`, `Person`, `Organization`
- References the `Theme` objects it contributes signal to
- Has a temporal anchor: `occurred_at`

Articles are ingestion artefacts. MarketEvents are the intelligence output.

---

## Consequences

**Positive:**
- Report assembly operates on MarketEvents, not raw articles — cleaner, more structured.
- The knowledge base (companies, themes, people) links to events, not articles — richer context.
- The "explain why it matters" principle is enforced structurally by the `summary` minimum length.
- Deduplication at the event level (one event from many articles) implements "signal over noise".

**Negative:**
- More complex than a simple article → summary pipeline.
- Requires the intelligence layer to synthesise events before reports can be assembled.
- Event-article linkage adds join table complexity.

**Neutral:**
- Articles are still stored in full — nothing is discarded (supports the searchability principle).
