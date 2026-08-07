# Code Review Checklist

This checklist is for reviewers. Work through each section before approving a PR. Not every item applies to every PR — use judgement, but do not skip sections without reason.

---

## Architecture

- [ ] Does the change respect the layering rules? (`sentinel_core` ← `sentinel`, never reversed)
- [ ] Are cross-package dependencies going through `sentinel_core` interfaces?
- [ ] Is there any circular import risk?
- [ ] Does the change introduce a new dependency? If so, has it been evaluated for security, licence, and maintenance?
- [ ] Does the change require an ADR? If so, has one been written?
- [ ] Is the scope of the change minimal? Is it doing exactly one thing?

---

## Testing

- [ ] Do unit tests exist for all new public functions?
- [ ] Are tests in the correct directory (`unit/` vs `integration/`)?
- [ ] Are tests marked with the correct marker (`@pytest.mark.unit` / `@pytest.mark.integration`)?
- [ ] Do tests assert meaningful outcomes, not just that code runs without error?
- [ ] Are external dependencies mocked in unit tests?
- [ ] Is test coverage maintained or improved?
- [ ] Are edge cases covered (empty input, maximum values, error conditions)?

---

## Performance

- [ ] Are there any N+1 query patterns?
- [ ] Are database queries appropriately indexed? (check if new columns need indices)
- [ ] Are there unbounded loops over potentially large collections?
- [ ] Are expensive operations (HTTP calls, LLM calls) appropriately batched or cached?
- [ ] Are timeouts set on all external calls?

---

## Typing

- [ ] Are all new public functions and methods fully annotated?
- [ ] Does Pyright pass without errors?
- [ ] Is `Any` used anywhere? If so, is it justified with a comment?
- [ ] Are return types correct? No implicit `None` where a value is expected?
- [ ] Are Protocol classes used instead of inheritance where appropriate?

---

## Documentation

- [ ] Do all new public modules, classes, and functions have docstrings?
- [ ] Are docstrings in Google style?
- [ ] Has the relevant documentation page been updated?
- [ ] If a new config key was added, is it documented in `configs/README.md`?
- [ ] If a new package was added, is its purpose clear from the `__init__.py` docstring?

---

## Security

- [ ] Is any secret, API key, or credential being logged or hardcoded?
- [ ] Is all external input validated with Pydantic before use?
- [ ] Are HTTP requests made with explicit timeouts?
- [ ] Is there any SQL constructed via string concatenation? (Use parameterised queries only)
- [ ] Are file paths constructed from user input validated or sanitised?

---

## Logging

- [ ] Are log statements using Loguru? No `print()`, no `logging.getLogger()`.
- [ ] Are log levels appropriate?
- [ ] Is structured context included in log calls?
- [ ] Are any secrets or sensitive values being logged?

---

## Error Handling

- [ ] Are bare `except:` clauses absent?
- [ ] Are caught exceptions logged with `exc_info=True`?
- [ ] Are domain exceptions raised instead of built-in exceptions?
- [ ] Is failure signalled by raising an exception, not by returning `None`?

---

## Maintainability

- [ ] Are file, function, and class size limits respected?
- [ ] Is the code decomposed into small, single-purpose functions?
- [ ] Are there any magic numbers or strings that should be named constants?
- [ ] Is there dead code (commented-out blocks, unused imports, unreachable branches)?

---

## Readability

- [ ] Is the intent of the code immediately clear to someone unfamiliar with it?
- [ ] Are variable and function names descriptive?
- [ ] Are complex expressions explained with a comment?
- [ ] Is the commit message following Conventional Commits and written in the imperative mood?

---

## Imports

- [ ] Are imports grouped correctly (stdlib → third-party → first-party)?
- [ ] Are there any wildcard imports (`from x import *`)?
- [ ] Are there any relative imports (`from . import`)?
- [ ] Are type-only imports guarded with `TYPE_CHECKING`?

---

## Configuration

- [ ] Are new configuration keys added to the appropriate YAML file with sensible defaults?
- [ ] Are secrets referenced via environment variables, not hardcoded?
- [ ] Is new configuration validated with Pydantic at startup?

---

## Dependency Management

- [ ] Are new dependencies declared in `pyproject.toml` with appropriate version constraints?
- [ ] Have new dependencies been evaluated for security vulnerabilities?
- [ ] Is the dependency necessary, or could it be avoided?
