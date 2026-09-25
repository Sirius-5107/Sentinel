# ADR-0002: MarketEvent Is the Canonical Intelligence / Signal Object

**Status:** Accepted
**Date:** 2026-09-25

## Context

Early Sentinel documentation used the term `Signal` as a possible domain model between processed Articles and the intelligence/reporting layers. The Phase 1 audit therefore deferred the decision to Phase 4.

The implemented domain contract does not define a `Signal` model. Instead, `MarketEvent` is explicitly defined as the output of the intelligence synthesis step and as the primary signal object tracked by the knowledge base and used to build report sections.

Introducing both `Signal` and `MarketEvent` without a demonstrated semantic distinction would create two competing representations of the same intelligence concept.

## Decision

`Signal` is a conceptual term, not a domain model.

`MarketEvent` is Sentinel's canonical structured intelligence/signal object.

Phase 4 therefore uses this flow:

```text
Processed Article(s)
        ↓
MarketEvent synthesis
        ↓
MarketEvent
        ↓
Analysis / "why it matters"
        ↓
ReportSection
        ↓
DailyReport
```

No separate `Signal`, `Insight`, or generic intermediate intelligence model is introduced.

## Provenance Rules

Every persisted `MarketEvent` must have at least one source Article.

The Article ↔ MarketEvent relationship is many-to-many at the application/database layer:

- multiple Articles may support one MarketEvent;
- one Article may support multiple independently justified MarketEvents;
- report content must remain traceable to source Articles through its MarketEvents.

## LLM Boundary

LLM output is treated as a candidate, not as trusted domain state. Structured output must pass domain validation and provenance checks before persistence. Unsupported or malformed output must be rejected or deterministically reconciled.

## Consequences

### Positive

- One canonical intelligence object.
- No duplicate semantic layer.
- Clear evidence → intelligence → analysis → report architecture.
- Simpler persistence and future knowledge-base relationships.
- Easier provenance and citation enforcement.

### Trade-off

If a future use case requires a genuinely distinct concept called `Signal` — for example, a mathematically derived trading signal with different lifecycle, inputs, and semantics — it must be introduced through a new architecture decision rather than reusing this term implicitly.

## Phase 4 Boundary

Phase 4 owns event synthesis, analysis, and daily report assembly. It does not own Notion publication or the Phase 5 knowledge base.