# PROGRESS.md — Recipe Recommender RAG Pipeline

Last updated: 2026-06-27

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Completed and verified |
| 🔄 | In progress |
| ⛔ | Blocked |
| 📋 | Planned / not started |

---

## Completed

### Core Pipeline
- ✅ **Ingestion pipeline** — section-level chunking (ingredients | method | tips) with 150-char overlap on long method sections
- ✅ **Metadata schema** — 14 fields per `ChunkRecord`: recipe_id, title, section, cuisine, tags[], dietary[], prep/cook/total time, servings, calories, chunk_index, char_count
- ✅ **Embedding** — `all-MiniLM-L6-v2` (384-dim), L2-normalised, batch_size=64, ~1,065 chunks/sec on CPU
- ✅ **pgvector storage** — `recipe_chunks` table with `vector(384)` column; IVFFlat index (lists=64)
- ✅ **Metadata filtering** — SQL `WHERE` on `tags[]` (GIN), `total_time_mins`, `calories_kcal`; NL parse → SQL conversion; fallback if pool < 10
- ✅ **n_probe benchmark** — `SET ivfflat.probes = K` for K ∈ {1, 5, 10, 50}; recall@5 + latency per query
- ✅ **Filter benchmark** — filtered vs unfiltered recall + latency comparison on 3 constraint queries
- ✅ **HashEmbedder guard** — startup assertion: cosine(near-synonyms) > 0.60, dim == 384, non-zero vector
- ✅ **Interactive chatbot REPL** — type queries, get top-5 chunk results with metadata
- ✅ **Single-command entry point** — `python3 run.py` does everything idempotently

### Corpus
- ✅ **50 TXT recipes** — hand-crafted + synthetic; used as benchmark ground truth (legacy)
- ✅ **10,000 PDF recipes** — generated via `fpdf2`; 200 archetypes × 50 variations; all sections parse correctly
- ✅ **PDF reader** — `pypdf` text extraction integrated into `src/chunker.py`; auto-detects PDF vs TXT corpus

### Infrastructure
- ✅ **PostgreSQL + pgvector** — Docker (`pgvector/pgvector:pg16`) and Homebrew (`postgresql@17`) both supported
- ✅ **Schema** — `CREATE TABLE IF NOT EXISTS`, `UNIQUE (recipe_id, section, chunk_index)`, GIN + btree indexes
- ✅ **docker-compose.yml** — single `db` service, credentials: `recipes/recipes`
- ✅ **Idempotent ingest** — skips re-embedding if row count matches chunk count; upsert on conflict

### Documentation
- ✅ **AGENTS.md** — project overview, layout, run commands, hard constraints, debugging guide
- ✅ **src/ARCHITECTURE.md** — 8 design decisions (D1–D8) with rationale and alternatives
- ✅ **src/db/CONSTRAINTS.md** — 8 DB hard constraints (C1–C8), safe operations reference, migrations runbook
- ✅ **PROGRESS.md** — this file
- ✅ **Makefile** — setup, db-up, run, lint, check, clean targets
- ✅ **requirements.txt** — all dependencies including `pypdf` and `fpdf2` now listed

---

## In Progress

- 🔄 Nothing actively in progress.

---

## Blocked

- ⛔ Nothing currently blocked.

---

## Planned / Not Started

### Benchmark Quality
- 📋 **Benchmark ground truth fix** — current `run_nprobe_benchmark()` compares against expected titles from the 50 TXT recipes; those titles don't exist in the 10k PDF corpus. Need to generate matched ground truth from the PDF corpus so recall@5 is meaningful.

### Testing
- 📋 **Test suite** — `src/embedder.py` docstring mentions a CI gate; no `tests/` directory exists. Priority tests:
  - `test_chunker.py` — verify ChunkRecord fields, overlap logic, PDF extraction
  - `test_embedder.py` — `assert_real_embedder()` as a pytest test
  - `test_retrieval.py` — smoke test: ingest 5 chunks, query, verify top result is relevant
  - `test_filters.py` — verify NL → SQL filter parsing for each filter type

### RAG Enhancement
- 📋 **LLM response generation** — chatbot REPL currently returns raw chunk text. Integrate an LLM (GPT-4o-mini via OpenAI API, or `ollama` for local) to generate fluent answers from retrieved chunks.
- 📋 **Cross-encoder reranking** — after ANN retrieval, apply a cross-encoder (e.g. `cross-encoder/ms-marco-MiniLM-L6-v2`) to rerank top-20 candidates before returning top-5.
- 📋 **Multi-query retrieval** — decompose compound queries ("vegan pasta under 30 mins with mushrooms") into sub-queries; merge ranked lists.

### Scale / Production
- 📋 **HNSW migration** — at ~100k rows, migrate from IVFFlat to HNSW for better recall and zero-probe-tuning overhead. Zero-downtime via `CREATE INDEX CONCURRENTLY`. See `src/db/CONSTRAINTS.md` runbook.
- 📋 **Connection pooling** — replace raw `psycopg2` with `psycopg2.pool.ThreadedConnectionPool` or `asyncpg` for concurrent request handling.
- 📋 **REST API** — wrap `retrieve()` and `filtered_retrieve()` in a FastAPI endpoint for integration with front-end chatbot UI.

---

## Performance Baselines (10k PDF Corpus, 2026-06-11)

| Metric | Value |
|---|---|
| Recipes | 10,000 PDFs |
| Chunks in DB | 30,000 |
| Embedding model | all-MiniLM-L6-v2 (384-dim) |
| Embedding throughput | ~1,065 chunks/sec |
| Embedding time (30k) | ~28 seconds |
| Query latency (cold) | ~100–350 ms |
| Query latency (warm) | ~35–80 ms |
| recall@5 (probes=10) | ~0.00–0.22 (benchmark mismatch — see planned work) |
| Filter recall improvement | low-carb query: 0.0 → 0.5 with SQL filter |
| Semantic guard cosine | 0.762 ✓ |
