# Domain Model

**Status:** Active — Phase 1 complete
**Version:** 1.0

---

## 1. Overview

The Sentinel domain model is event-centric (ADR-0001). All financial developments are represented as `MarketEvent` objects derived from one or more source `Article` objects. The knowledge base accumulates named entities — `Company`, `Person`, `Organization`, `Theme` — that are referenced by events and articles. Reports are assembled from synthesised events.

For full field-level specifications, see `docs/05-contracts.md`.

---

## 2. Entity Relationship Diagram

```
Source ──────────────────────────────────────── 1:many ──► Article
                                                              │
                           ┌──────────────────────────────────┘
                           │  tagged to
                           ▼
Company ◄──── many:many ── Article ──── many:many ──► Person
   │                          │                          │
   │                          │ many:many                │
   │                          ▼                          │
   └──────────────────► MarketEvent ◄───────────────────┘
                              │     many:many
                              │
                    ┌─────────┼──────────────────┐
                    ▼         ▼                   ▼
               Organization  Theme           Market
                              │
                              ▼
                        ReportSection
                              │ many:1
                              ▼
                         DailyReport
                              │ 1:1
                              ▼
                         PipelineRun
                              │ 1:many
                              ▼
                            Task
```

---

## 3. Model Summaries

### 3.1 Source

Represents an external content provider (RSS feed, website, API). The entry point into the pipeline. Each Source has a type (`RSS`, `SCRAPE`, `DYNAMIC`, `API`, `MANUAL`) that determines which collector implementation fetches it.

### 3.2 Article

The fundamental unit of information. Created at ingestion with status `INGESTED` and enriched through the pipeline. Raw fields (title, url, content) are never modified after creation. Derived fields (sentiment, importance\_score, entities) are added by the processing stage.

### 3.3 Company

A publicly or privately held commercial entity. Extracted from articles and resolved against existing records. Accumulates mentions and associated events over time.

### 3.4 Person

A named individual — executive, policymaker, analyst. Extracted from articles. Accumulates mentions and events over time.

### 3.5 Organization

A non-company institution — central bank, regulator, international body (e.g. Federal Reserve, SEC, ECB, IMF). Distinct from Company because these entities are not commercially held.

### 3.6 Theme

A persistent cross-asset investment thesis (e.g. "AI Capex Cycle", "India Infrastructure"). Manually seeded and LLM-maintained. The highest-level categorisation in the knowledge base. Articles and events are tagged to themes.

### 3.7 Market

A financial exchange or trading venue (e.g. NYSE, NSE, LSE). Reference data — seeded at bootstrap and rarely changed. Provides listing context for companies and origin context for market events.

### 3.8 MarketEvent

The primary intelligence output. Represents a discrete financial or economic development synthesised from one or more articles. Implements ADR-0001: every development is an event with typed entities, severity, sentiment, importance, and a temporal anchor. The summary field enforces the "explain why it matters" principle — minimum 100 characters.

### 3.9 ReportSection

A single ordered section within a DailyReport (e.g. "Macro", "US Equities", "India", "AI"). The granular unit of report content. Sections can be individually regenerated without rebuilding the full report.

### 3.10 DailyReport

The primary published output. One report per day per report type. Assembled from ReportSections, each covering a different market segment. Published to Notion and potentially other channels.

### 3.11 PipelineRun

The operational audit record for a full pipeline execution. Tracks articles ingested, events synthesised, errors, and duration. Linked to the DailyReport it produced.

### 3.12 Task

The atomic audit unit — a single step within a PipelineRun (e.g. `collect.reuters_rss`, `process.classify`, `publish.notion`). Enables fine-grained observability.

---

## 4. Immutability Policy

All domain objects are immutable (frozen Pydantic v2 models). State transitions produce new object instances; existing objects are never mutated. See ADR-0004 for rationale.

---

## 5. Timestamp Policy

All datetime fields are UTC-aware. The policy:

- **Naive datetimes** (no `tzinfo`) are **rejected**.
- **Non-UTC timezone-aware datetimes** are **normalised to UTC** at validation time.
- **Serialised datetimes** are ISO 8601 strings with the UTC offset (`+00:00`).
- **`updated_at`** is the version timestamp of this snapshot — set at construction, never mutated on the object itself.

---

## 6. Implementation Order

Models must be implemented in dependency order (see `docs/05-contracts.md` §6):

| Level | Models |
|---|---|
| 0 | Value objects, enums |
| 1 | Market, Organization, Theme |
| 2 | Company, Person |
| 3 | Source, Article |
| 4 | MarketEvent |
| 5 | PipelineRun, Task |
| 6 | DailyReport, ReportSection |
