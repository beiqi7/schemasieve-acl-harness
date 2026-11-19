# SchemaSieve & Zero-Trust ACL Harness

Reference POC for offline data-plumbing & CI verification in enterprise RAG/Text-to-SQL pipelines:

1. **Snowflake Lineage & Join Profiler (`lineage_profiler.py`)**: Normalizes raw `QUERY_HISTORY` SQL via `sqlglot.optimizer.qualify` against `INFORMATION_SCHEMA` metadata to extract verified production join graphs and filter dead tables (`prod_final_v2`).
2. **Adversarial ACL Leak Suite (`test_acl_isolation.py`)**: Uses ephemeral RS256 JWTs (`PyJWT`) and in-memory Qdrant pre-retrieval metadata pushdown to guarantee 0% chunk leakage across broken SharePoint/Okta group inheritance boundaries.
3. **Async Devin Bot CI Integration (`.github/workflows/devin-ci.yml`)**: Runs adversarial ACL regression tests on connector PRs and triggers background schema profiling on undocumented high-weight tables.

## Quickstart
```bash
pip install -r requirements.txt
pytest -v
