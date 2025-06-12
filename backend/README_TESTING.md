# Backend Testing Guide

This document explains how to run the unit-test suite **locally** and how the
**CI pipeline** avoids external network calls to Mem0 and Neo4j.

---

## 1. Quick start

```bash
# Inside the virtual-env
pip install -r requirements.txt
pytest -v  # runs ~100 s with streaming fixtures mocked
```

All external services are mocked via `backend/tests/conftest.py`, therefore no
Mem0 API key or Neo4j instance is required for unit tests.

---

## 2. CI configuration

CI (GitHub Actions or any other runner) only needs Python 3.11 and `pip`:

```yaml
# .github/workflows/python-tests.yml (example)
name: Backend tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest -q backend/tests
```

*Because the test-suite mocks Mem0/Neo4j*, the CI pipeline requires **no secret
environment variables**.

---

## 3. Writing tests for new features

1. Place new test modules under `backend/tests/`.
2. If real Mem0/Neo4j calls are required, prefer `unittest.mock.patch` (see
   existing tests) so that CI remains hermetic.
3. Follow the testing rules in `implementation-guide.mdc` (expected/edge/failure
   cases).

---

## 4. Common issues

| Problem | Fix |
|---------|------|
| `ModuleNotFoundError: subconscious` | Ensure `sys.path` is adjusted in the test or use the relative patch already in place (`sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))`). |
| External network call during CI | Patch the offending method in the test or extend the global mocks in `conftest.py`. | 