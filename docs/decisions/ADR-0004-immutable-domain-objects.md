# ADR-0004: Immutable Domain Objects

**Status:** Accepted
**Date:** 2026-08-15
**Deciders:** Himanshu

---

## Context

The `SentinelModel` base class uses Pydantic v2's `frozen=True` configuration, making all domain objects immutable after construction. However, the original documentation described `updated_at` as "updated on every mutation", which is contradictory: frozen objects cannot be mutated.

This inconsistency needed to be resolved without:
- Removing `frozen=True` (which would weaken the design)
- Introducing mutable setters (which would contradict the intent)

---

## Decision

Preserve `frozen=True` and reinterpret `updated_at` as a **version timestamp**.

Domain objects are **immutable snapshots**. The semantics are:

- An object, once constructed, never changes.
- `updated_at` is set once at construction time and represents "this snapshot was current as of this timestamp".
- When a state transition is required (e.g. an Article moving from `INGESTED` to `PROCESSED`), the application layer constructs a **new** `SentinelModel` instance with the updated field values and a fresh `updated_at`.
- The old object is discarded (or archived in the database via a new row / update operation).

This is consistent with the event-centric philosophy of ADR-0001: all state changes are explicit, traceable, and produce new versions rather than silently mutating existing records.

---

## Consequences

**Positive:**
- Domain objects are safe to pass between functions without defensive copying.
- No mutation bugs: once constructed, a domain object's fields are guaranteed correct.
- Thread-safe by construction.
- Consistent with the event-centric design: state changes are explicit.
- `updated_at` has unambiguous semantics: the timestamp of this version.

**Negative:**
- Application layer must construct new instances for state transitions rather than calling setters.
- Slightly more verbose than `obj.status = NEW_STATUS`.

**Neutral:**
- The database persistence layer (Phase 2+) handles the mechanics of "updating" a row — from the domain's perspective, a new object was constructed and the old one superseded.

---

## Implementation

- `SentinelModel.model_config` has `frozen=True`.
- `updated_at` docstring clarifies it is a version timestamp.
- The module docstring in `sentinel_core/models/_base.py` documents both the immutability policy and the UTC timestamp policy.
- Tests in `test_models_level1.py::TestSentinelModelImmutability` prove the behaviour.
