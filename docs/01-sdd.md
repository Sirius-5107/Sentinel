# Software Design Document

**Status:** Active — Phase 1 complete
**Version:** 1.0

---

## 1. Purpose

This document describes the software design of Sentinel: how the system is decomposed into layers, what each layer is responsible for, and how data flows through the platform. It is the authoritative reference for any engineer contributing to the codebase.

---

## 2. System Overview

Sentinel is an autonomous financial intelligence platform. It ingests raw content from external sources, processes it into structured signals, synthesises signals into investment-grade insights, and publishes those insights to configured channels.

The system operates as a data pipeline with a persistent knowledge base. Every piece of content that enters the system is stored, classified, and linked to domain entities. Over time, the knowledge base accumulates a comprehensive picture of the markets Sentinel covers.

---

## 3. Architectural Layers

Sentinel is organised into four layers. Dependencies flow strictly downward.

```
┌─────────────────────────────────────────┐
│            Publishing Layer             │  Notion, future channels
├─────────────────────────────────────────┤
│           Application Layer             │  Collectors, processors,
│                                         │  intelligence, research, API
├─────────────────────────────────────────┤
│           sentinel_core                 │  Domain models, enums,
│         (Domain Contract Layer)         │  value objects, interfaces
├─────────────────────────────────────────┤
│         Infrastructure Layer            │  PostgreSQL, pgvector,
│                                         │  HTTP, file system
└─────────────────────────────────────────┘
```

### 3.1 Domain Contract Layer (`sentinel_core`)

The foundation of the entire system. Contains only:

- **Models** — immutable Pydantic v2 domain objects (Article, MarketEvent, DailyReport, etc.)
- **Enums** — typed string enumerations (ArticleStatus, Sentiment, AssetClass, etc.)
- **Value objects** — validated scalar types (ConfidenceScore, Ticker, CountryCode, etc.)
- **Interfaces** — protocol definitions that application layer packages must implement
- **Exceptions** — typed domain exceptions
- **Types** — shared type aliases

`sentinel_core` has no knowledge of databases, HTTP, LLMs, or external services. It is the pure domain vocabulary.

### 3.2 Application Layer (`sentinel/`)

Implements the pipeline stages. Each sub-package owns one vertical slice:

| Package | Responsibility |
|---|---|
| `sentinel/collector` | Fetches raw content from configured sources |
| `sentinel/processing` | Classifies, scores, deduplicates, and extracts entities |
| `sentinel/intelligence` | Synthesises signals into market events and insights |
| `sentinel/knowledge` | Maintains the entity and event knowledge base |
| `sentinel/research` | Generates long-form research documents |
| `sentinel/publish` | Distributes reports to Notion and other channels |
| `sentinel/scheduler` | Orchestrates pipeline execution |
| `sentinel/api` | FastAPI REST interface |
| `sentinel/cli` | Typer command-line interface |
| `sentinel/common` | Shared application utilities |

### 3.3 Infrastructure Layer

PostgreSQL (extended with pgvector for embeddings) is the primary data store. All persistence is managed by the application layer via SQLAlchemy 2. The domain contract layer never touches the database directly.

### 3.4 Publishing Layer

Notion is the primary publishing channel. Future channels (email, Slack, dashboard) are added without modifying the domain layer.

---

## 4. Data Flow

```
External Sources
      │
      ▼
  Collector  ──► Raw Articles (status=INGESTED)
      │
      ▼
  Processor  ──► Classified, scored, deduplicated Articles
      │
      ▼
 Intelligence ──► MarketEvents + DailyReport
      │
      ▼
  Knowledge  ──► Entity profiles updated (Company, Person, Theme, …)
      │
      ▼
  Publisher  ──► Notion page created
```

Every stage persists its output to PostgreSQL before passing control to the next stage. Failures are isolated: a failure in processing does not roll back already-ingested articles.

---

## 5. Domain Model Summary

The twelve domain models and their roles:

| Model | Layer | Purpose |
|---|---|---|
| `Source` | Input | External content provider |
| `Article` | Input | Single ingested piece of content |
| `Company` | Knowledge | Listed or private company entity |
| `Person` | Knowledge | Named individual |
| `Organization` | Knowledge | Non-company institution |
| `Theme` | Knowledge | Persistent investment theme |
| `Market` | Reference | Exchange or trading venue |
| `MarketEvent` | Intelligence | Synthesised financial development |
| `ReportSection` | Output | Single section of a daily report |
| `DailyReport` | Output | Published daily intelligence brief |
| `PipelineRun` | Operations | End-to-end execution audit record |
| `Task` | Operations | Single unit of work within a run |

Full field specifications are in `docs/05-contracts.md`.

---

## 6. Key Design Decisions

### 6.1 Event-Centric Data Model (ADR-0001)

All financial developments are modelled as `MarketEvent` objects with typed entities, severity, sentiment, and temporal attributes. Articles are evidence; MarketEvents are the intelligence output.

### 6.2 PostgreSQL as Primary Store (ADR-0002)

A single PostgreSQL instance (with pgvector for embeddings) serves as the complete data store. No separate vector database, no separate search index.

### 6.3 Custom Provider Interfaces (ADR-0003)

LLM and embedding providers are accessed through custom interface classes defined in `sentinel_core/interfaces/`. The application layer is never directly coupled to any specific AI provider.

### 6.4 Immutable Domain Objects

All `sentinel_core` models are frozen Pydantic v2 instances. Domain objects are immutable snapshots; state transitions produce new objects rather than mutating existing ones. See `docs/decisions/ADR-0004-immutable-domain-objects.md`.

### 6.5 UUID v4 Identifiers

All domain objects carry a UUID v4 primary key generated at construction time. This enables objects to be created and validated before any database interaction.

---

## 7. Operational Concerns

### 7.1 Pipeline Scheduling

The pipeline runs on a configurable schedule (default: daily). Each run is recorded as a `PipelineRun` with child `Task` records for observability. The scheduler is implemented in `sentinel/scheduler`.

### 7.2 Configuration

All configuration lives in `configs/`. Secrets are supplied exclusively via environment variables; they never appear in YAML files or source code.

### 7.3 Logging

Loguru is the only logging library. Every pipeline stage logs structured events with contextual fields. No `print()` statements are permitted.

---

## 8. Phase Delivery

See `docs/20-implementation-plan.md` for the phased implementation plan.

**Phase 1 (current):** Domain contract layer complete. All twelve domain models, enumerations, and value objects implemented and tested.

**Phase 2 (next):** Data collection layer — RSS, scraping, and dynamic collectors.
