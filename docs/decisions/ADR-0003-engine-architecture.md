# ADR-0003: Custom Provider Interface Architecture

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Himanshu

---

## Context

Sentinel requires LLM capabilities for classification, scoring, synthesis, and report generation, and embedding capabilities for semantic deduplication and search. The AI provider landscape is volatile: models change rapidly, pricing changes, providers appear and disappear.

Two approaches were considered:
1. **Direct coupling:** Call OpenAI / Anthropic APIs directly from pipeline code.
2. **Provider interface:** Define abstract interfaces in `sentinel_core`; implement concrete providers in `sentinel/`.

---

## Decision

Define **custom provider interfaces** in `sentinel_core/interfaces/`.

- `LLMProviderProtocol` — interface for LLM completion calls
- `EmbeddingProviderProtocol` — interface for embedding generation

Concrete implementations (OpenAI, Anthropic, local models) live in `sentinel/intelligence/` and `sentinel/processing/`, never in `sentinel_core`.

The interfaces are defined as Python `Protocol` classes (structural subtyping), not abstract base classes. This means any class that satisfies the interface's method signatures is a valid provider — no explicit registration required.

---

## Consequences

**Positive:**
- Switching LLM providers requires only a new implementation class, not a domain model change.
- `sentinel_core` can be tested completely without network access or API keys.
- The domain layer is not exposed to provider-specific error types or rate-limit behaviour.
- Multiple providers can be used simultaneously (e.g. GPT-4o for synthesis, Claude for review).

**Negative:**
- Slightly more code than direct API calls.
- Developers must implement the interface protocol rather than calling the API directly.

**Neutral:**
- Provider configuration lives in `configs/providers.yaml`. Switching providers is a configuration change, not a code change.
