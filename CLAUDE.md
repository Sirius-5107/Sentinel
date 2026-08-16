\# Sentinel — Claude Project Instructions



\## 1. Project Identity



Sentinel is a long-term, production-grade financial intelligence platform.



Its purpose is to collect, normalize, validate, enrich, analyze, and publish high-quality financial and geopolitical intelligence.



The initial intelligence scope includes:



\- US equities

\- Indian equities

\- Global macroeconomics

\- Private equity

\- Private credit

\- M\&A

\- Geopolitical developments

\- AI and technology developments relevant to markets

\- Important global market-moving events



Sentinel is NOT intended to become:



\- a generic news aggregator

\- a simple news summarizer

\- an LLM wrapper

\- a trading bot

\- a dashboard-first application

\- a collection of unrelated scrapers



The long-term goal is an evidence-first intelligence system.



\---



\# 2. Core Philosophy



These principles override convenience.



\## Evidence before inference



Sentinel must distinguish:



\- what happened

\- what the source reported

\- what Sentinel inferred

\- how confident Sentinel is



Never present an inference as an observed fact.



\## Structured data before LLM reasoning



LLMs may eventually assist with:



\- classification

\- extraction

\- summarization

\- synthesis

\- prioritization



But LLMs must not become the source of truth.



Raw evidence and structured domain objects come first.



\## Event-centric architecture



Sentinel should reason primarily about events rather than individual articles.



Multiple articles may describe the same underlying event.



The architecture should eventually support:



Article

&#x20;   ↓

Event identification

&#x20;   ↓

MarketEvent

&#x20;   ↓

Company / Market / Theme relationships

&#x20;   ↓

Analysis

&#x20;   ↓

Report



\## Traceability



Important claims should eventually be traceable to their evidence.



Never create an intelligence output that cannot eventually answer:



"Where did this information come from?"



\## Immutable domain contracts



The domain layer represents immutable snapshots.



Do not mutate domain objects in place.



If a domain object's state changes, create a new version/snapshot.



\## Simplicity over cleverness



Prefer:



\- explicit code

\- small modules

\- clear interfaces

\- boring technology

\- deterministic behavior



Avoid unnecessary abstractions.



\---



\# 3. Architecture



Sentinel has two important conceptual layers.



\## sentinel\_core



`sentinel\_core` contains stable domain contracts.



It must remain:



\- deterministic

\- dependency-light

\- testable

\- independent

\- free from infrastructure concerns



It may contain:



\- domain models

\- enums

\- value objects

\- types

\- interfaces

\- domain exceptions

\- domain constants

\- configuration contracts



It must NOT contain:



\- HTTP calls

\- database access

\- filesystem I/O

\- Notion integration

\- LLM calls

\- scraping

\- scheduling

\- application services

\- external APIs



\## sentinel



`sentinel` contains application behavior.



Expected future areas include:



\- collector

\- processing

\- intelligence

\- knowledge

\- research

\- publish

\- scheduler

\- API

\- CLI

\- common



The dependency direction should be:



application/infrastructure

&#x20;       ↓

sentinel\_core



Never:



sentinel\_core

&#x20;       ↓

application/infrastructure



\---



\# 4. Repository Structure



The intended structure is:



Sentinel/



├── CLAUDE.md

├── README.md

├── LICENSE

├── pyproject.toml

├── uv.lock

├── .gitignore

├── .pre-commit-config.yaml

│

├── .github/

│   └── workflows/

│

├── docs/

│   ├── 00-vision.md

│   ├── 01-sdd.md

│   ├── 02-architecture.md

│   ├── 03-domain-model.md

│   ├── 04-tech-stack.md

│   ├── 05-contracts.md

│   ├── 10-engineering-standards.md

│   ├── 11-code-review-checklist.md

│   ├── 20-implementation-plan.md

│   ├── 30-changelog.md

│   └── decisions/

│

├── sentinel\_core/

│   ├── models/

│   ├── types/

│   ├── enums/

│   ├── exceptions/

│   ├── interfaces/

│   ├── config/

│   └── constants/

│

├── sentinel/

│   ├── collector/

│   ├── processing/

│   ├── intelligence/

│   ├── knowledge/

│   ├── research/

│   ├── publish/

│   ├── scheduler/

│   ├── api/

│   ├── cli/

│   └── common/

│

├── tests/

│   ├── unit/

│   ├── integration/

│   └── fixtures/

│

├── configs/

│

├── scripts/

│

└── infrastructure/



Do not create alternative package structures without an explicit architectural reason.



\---



\# 5. Documentation Is Authoritative



Before implementing a milestone, read:



\- CLAUDE.md

\- README.md

\- relevant docs

\- relevant ADRs

\- current implementation

\- tests



The documentation hierarchy is:



1\. ADRs for architectural decisions

2\. SDD / architecture documentation

3\. Domain contracts

4\. Implementation

5\. Tests



If implementation disagrees with documentation:



DO NOT silently choose one.



Investigate the discrepancy.



If the documented architecture is still correct, change the implementation.



If the architecture genuinely needs to change, create/update an ADR.



\---



\# 6. ADR Policy



Architectural decisions must be documented in:



`docs/decisions/`



Use sequential ADR numbers.



Examples:



ADR-0001-event-centric.md

ADR-0002-postgres.md

ADR-0003-engine-architecture.md



Create a new ADR when changing:



\- domain boundaries

\- dependency direction

\- persistence strategy

\- event architecture

\- major technology choices

\- public contracts

\- major infrastructure architecture



Do NOT create ADRs for:



\- formatting

\- typo fixes

\- ordinary bug fixes

\- minor refactors



\---



\# 7. Domain Contract Rules



The domain contracts are extremely important.



Never casually modify:



\- Source

\- Article

\- Company

\- Person

\- Organization

\- Theme

\- Market

\- MarketEvent

\- ReportSection

\- DailyReport

\- PipelineRun

\- Task



Before changing a contract:



1\. Check docs/05-contracts.md.

2\. Check the SDD.

3\. Check relevant ADRs.

4\. Check existing tests.

5\. Determine compatibility impact.

6\. Document architectural changes.



Avoid primitive obsession where a value object clearly improves correctness.



Use enums where the domain has a bounded set of values.



Use strong types where appropriate.



Do not introduce abstractions merely for theoretical purity.



\---



\# 8. Python Standards



Python version:



Python 3.13



Package manager:



uv



Use modern Python.



Prefer:



\- type hints

\- dataclasses where appropriate

\- Pydantic where domain validation is required

\- pathlib

\- context managers

\- explicit error handling



Avoid:



\- global mutable state

\- unnecessary metaprogramming

\- magic

\- wildcard imports

\- implicit side effects

\- dynamic typing without justification



\---



\# 9. Typing



Pyright runs in strict mode.



Avoid `Any`.



If `Any` is genuinely necessary:



\- document why

\- keep the scope narrow



Prefer precise types.



Use:



\- TypeAlias

\- Literal

\- Enum

\- Protocol

\- Generic

\- NewType/value objects



when they materially improve correctness.



Do not use types merely to make code look sophisticated.



\---



\# 10. Pydantic Rules



Pydantic v2 is the project's validation framework.



Domain models should:



\- validate inputs

\- be explicit

\- serialize deterministically

\- avoid hidden side effects



Domain models should not perform:



\- network calls

\- database calls

\- filesystem operations

\- external API calls



Prefer immutable/frozen models where appropriate.



\---



\# 11. Datetime Policy



All Sentinel timestamps must be timezone-aware.



The canonical representation is UTC.



Naive datetimes must not silently enter the domain.



Where appropriate:



\- reject naive datetimes

\- normalize aware datetimes to UTC



Do not implement different datetime rules in different models.



Centralize common behavior.



\---



\# 12. Logging



Do not use:



```python

print(...)
for application logging.

Use the project's logging infrastructure.

Logs should contain enough context to diagnose failures.

Never log:

API keys
passwords
tokens
credentials
sensitive personal data
13. Configuration

Never hardcode secrets.

Never commit:

API keys
tokens
passwords
credentials

Use environment variables and configuration files.

Committed configuration files should contain safe defaults or examples only.

14. Testing

Every meaningful behavior requires tests.

Tests should test behavior rather than implementation details.

Prioritize:

boundary conditions
validation
error handling
serialization
integration contracts
deterministic behavior

Do not:

weaken tests to make CI pass
skip tests without justification
delete failing tests instead of fixing the underlying issue

The core domain should have very high test coverage.

Coverage is a signal, not the sole definition of quality.

15. CI

CI must remain strict.

The project should continuously validate:

dependency installation
Ruff lint
Ruff formatting
Pyright
pytest
documentation build

Never fix CI by:

disabling a check
excluding files without justification
adding broad ignores
skipping tests

Fix the underlying problem.

16. Dependencies

Do not add dependencies casually.

Before adding one:

Check whether the standard library can solve the problem.
Check whether an existing dependency already provides the functionality.
Consider maintenance cost.
Consider security implications.
Consider whether the dependency belongs in core or application infrastructure.

sentinel_core should remain especially dependency-light.

17. File and Module Size

Prefer small modules.

As a guideline:

~500 lines per file should trigger reconsideration.
~300 lines per class should trigger reconsideration.

These are guidelines, not hard laws.

Do not split code into meaningless micro-files simply to satisfy a number.

18. Error Handling

Errors should be explicit.

Do not:

except Exception:
    pass

Do not silently swallow failures.

Catch specific exceptions where possible.

Preserve useful context.

Use domain-specific exceptions where appropriate.

19. Security

Treat external input as untrusted.

Validate:

URLs
API responses
article metadata
identifiers
configuration
external payloads

Never execute untrusted content.

Never interpolate secrets into logs.

Never commit credentials.

20. LLM Policy

LLMs are tools, not sources of truth.

Future LLM functionality must:

operate on structured evidence
preserve source attribution
distinguish facts from inference
expose uncertainty
avoid inventing facts

Do not introduce LLM dependencies into sentinel_core.

21. Current Development Philosophy

Implement Sentinel incrementally.

Do not build the entire system at once.

Each milestone should:

have a defined scope
produce a coherent artifact
pass all tests
pass CI
update documentation
avoid unrelated changes

One milestone should correspond to one focused change/PR whenever practical.

22. Forbidden Scope Creep

Unless explicitly requested for the current milestone, do NOT implement:

future collectors
future APIs
future dashboards
future LLM integrations
future database schemas
future Notion integration
future schedulers
future intelligence algorithms
speculative abstractions

If something is needed later:

document it as future work.

Do not implement it early.

23. Change Management

Before making a large change:

Understand why the change is necessary.
Check existing architecture.
Check ADRs.
Check tests.
Check downstream compatibility.
Make the smallest correct change.

Prefer additive changes over breaking changes.

If a breaking change is unavoidable:

document it.

24. Git Hygiene

Never commit generated artifacts.

Never commit:

.coverage
__pycache__
.pyc
.pytest_cache
.ruff_cache
local virtual environments
secrets
machine-specific files

Keep commits focused.

Preferred commit style:

feat:
fix:
refactor:
test:
docs:
chore:
ci:

Examples:

feat(core): add market event contract

fix(core): normalize timestamps to UTC

test(core): add event validation coverage

docs: update domain contract specification

chore: finalize phase 1 foundation

25. Review Before Finishing

Before declaring any milestone complete:

Run:

ruff check .
ruff format --check .
pyright
pytest
mkdocs build --strict

Then inspect:

git status
git diff
git ls-files

Check for:

generated files
accidental files
unrelated modifications
missing documentation
broken imports
architecture violations

Never claim success without actually running the checks.

26. Current Milestone Rule

The current milestone must always be explicitly stated in the user request.

Implement only that milestone.

If the user asks for Phase 1 finalization:

DO NOT implement Phase 2.

If the user asks for Phase 2:

implement Phase 2 only.

Never infer permission to move ahead.

27. Sentinel's Long-Term Data Flow

The intended high-level flow is:

External Sources
↓
Collection
↓
Raw Evidence
↓
Normalization
↓
Article
↓
Event Resolution
↓
MarketEvent
↓
Entities / Themes / Markets
↓
Intelligence
↓
Research
↓
Report
↓
Publishing

The exact implementation will evolve.

The conceptual separation should remain.

28. The Most Important Rule

When uncertain:

DO NOT GUESS.

Instead:

inspect the documentation
inspect existing code
inspect tests
inspect ADRs
identify the ambiguity
make the smallest defensible decision
document it if architectural

Sentinel should be built deliberately, not opportunistically.

29. Current Role of Claude

Claude is the implementation engineer.

Its responsibilities:

implement requested milestones
write tests
maintain documentation
keep CI green
explain implementation decisions
avoid scope creep

Claude does NOT independently redesign Sentinel.

Architectural changes require explicit approval.

30. Definition of Done

A milestone is NOT complete merely because code exists.

It is complete only when:

requested functionality is implemented
tests pass
Ruff passes
Pyright passes
documentation is updated
architecture remains coherent
no generated artifacts are committed
no secrets are committed
CI passes
the git diff contains only intended changes

Only then should the milestone be considered complete.
