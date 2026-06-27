# AGENTS.md — Recipe Recommender RAG Pipeline

This file is the **first thing any AI agent or new contributor should read**.
It describes the project purpose, how to run it, the file map, and hard constraints
that must never be violated.

---

## Project Overview

A **Retrieval-Augmented Generation (RAG) pipeline** for a food-startup recipe chatbot.
The system ingests 10,000 recipe PDFs, chunks each recipe by section, embeds the chunks
with a sentence-transformer model, stores them in **PostgreSQL + pgvector**, and exposes
a retrieval loop that powers an interactive chatbot.

### Problem it solves
> "A food startup wants a chatbot that answers user questions from a library of 10,000
> recipe PDFs. Build the ingestion pipeline and a working retrieval loop — then diagnose
> why it sometimes returns irrelevant recipes."

Key design answers:
- **Chunk unit**: one section per chunk (ingredients | method | tips) — not whole-recipe,
  not one-step-per-chunk.
- **Overlap**: 150-char overlap on long method sections only (>1,200 chars).
- **Embedding model**: `all-MiniLM-L6-v2` (384-dim, CPU-friendly, MIT licence).
- **Vector store**: pgvector IVFFlat (`lists=64`); migrate to HNSW at ~100k rows.
- **Metadata filtering**: SQL `WHERE` clauses on `tags[]`, `total_time_mins`,
  `calories_kcal`; GIN index on `tags`.
- **Irrelevant-result diagnosis**: the "HashEmbedder trap" — using a hash function
  instead of a semantic model produces random vectors. Guard: cosine similarity between
  two near-synonyms must be > 0.60 at startup.

---

## Repo Layout

```
recipe_recommender/
├── AGENTS.md               ← you are here
├── PROGRESS.md             ← current status: done / in-progress / blocked
├── README.md               ← high-level project & design explanation
├── Makefile                ← standardised commands (setup, run, lint, check)
├── requirements.txt        ← all Python dependencies
├── docker-compose.yml      ← PostgreSQL + pgvector container
│
├── run.py                  ← PRIMARY ENTRY POINT (10k PDFs → full pipeline + chatbot)
├── main.py                 ← legacy entry (50 TXT recipes, kept for comparison)
│
├── data/
│   ├── generate_pdfs.py    ← generates 10,000 recipe PDFs in data/recipe_pdfs/
│   ├── generate_recipes.py ← generates 50 TXT recipe files in data/recipes/
│   ├── recipe_pdfs/        ← 10,000 PDFs (recipe_00000.pdf … recipe_09999.pdf)
│   └── recipes/            ← 50 TXT files (legacy corpus)
│
├── src/
│   ├── ARCHITECTURE.md     ← system-wide design decisions
│   ├── chunker.py          ← section-level chunking, PDF/TXT parsing, ChunkRecord
│   ├── db.py               ← PostgreSQL connection, DDL, indexes
│   ├── embedder.py         ← embedding model, pgvector bulk ingest, sanity guard
│   ├── filters.py          ← NL filter parsing, SQL metadata pre-filtering
│   ├── pipeline.py         ← end-to-end orchestrator
│   └── retrieval.py        ← vector search, n_probe benchmark, chatbot REPL
│
└── results/
    ├── benchmark_results.json  ← latest n_probe + filter benchmark output
    └── embeddings.npy          ← raw embedding backup for HNSW migration
```

> `venv/`, `data/recipe_pdfs/`, `results/embeddings.npy`, and legacy FAISS artifacts
> (`results/recipe_index.faiss`, `results/chunk_metadata.pkl`) are gitignored or
> should be treated as ephemeral.

---

## How to Run (Quick Reference)

### Prerequisites
- Python 3.10+
- PostgreSQL 16/17 with pgvector extension  
  **Docker (recommended):** `docker compose up -d`  
  **Homebrew:** `brew services start postgresql@17`

### First-time setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Using Makefile targets

```bash
make setup       # create venv + install deps
make db-up       # start PostgreSQL via docker compose
make run         # run full pipeline + chatbot (10k PDFs)
make run-legacy  # run legacy 50-recipe pipeline
make lint        # run ruff linter
make check       # run embedding sanity check
make clean       # remove __pycache__, .pyc files
```

### Manual run

```bash
source venv/bin/activate

# Docker DB (uses docker-compose.yml credentials):
export PGHOST=localhost PGPORT=5432 PGDATABASE=recipes PGUSER=recipes PGPASSWORD=recipes

# Homebrew local DB (no password, OS user):
# unset PGPASSWORD; export PGDATABASE=recipes

python3 run.py
```

`run.py` is **idempotent**: PDFs already generated → skips generation; chunks already
in DB → skips re-embedding. Safe to re-run.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PGHOST` | `localhost` | PostgreSQL host |
| `PGPORT` | `5432` | PostgreSQL port |
| `PGDATABASE` | `recipes` | Database name |
| `PGUSER` | OS username | DB user |
| `PGPASSWORD` | *(none)* | DB password |

---

## Hard Constraints (Never Violate)

1. **Do NOT use a hash-based embedder.** Any function mapping text → vector via MD5,
   SHA, or similar produces semantically random vectors. The startup guard in
   `src/embedder.py::assert_real_embedder()` enforces cosine > 0.60 between near-synonyms.
   If this assertion fails, fix the model — do not lower the threshold.

2. **Do NOT change the chunk schema without a DB migration.** The `recipe_chunks` table
   has a `UNIQUE (recipe_id, section, chunk_index)` constraint. Adding columns requires
   `ALTER TABLE`, not a schema drop (which would destroy all embeddings).
   See `src/db/CONSTRAINTS.md`.

3. **Do NOT re-embed unless necessary.** Embedding 30k chunks takes ~30 seconds. The
   ingest function is idempotent — if row count matches chunk count it skips embedding.
   Set `force_reingest=True` only when the model or chunking strategy changes.

4. **Do NOT merge `data/recipe_pdfs/` into git.** 10,000 PDFs × ~20KB = ~200 MB.
   Regenerate with `python3 data/generate_pdfs.py` or `make generate-pdfs`.

5. **Do NOT drop the IVFFlat index during normal operation.** It is created after ingest
   in `src/embedder.py`. Dropping it forces a sequential scan (O(N) instead of O(√N)).
   At 30k rows the difference is negligible but matters at scale.

6. **The primary entry point is `run.py`.** Do not modify `main.py` unless explicitly
   asked — it is the legacy reference pipeline for comparison.

---

## Key Module Responsibilities

| Module | Single responsibility |
|---|---|
| `src/chunker.py` | Parse recipe text → `ChunkRecord` list. No DB, no embedding. |
| `src/db.py` | PostgreSQL connection + DDL only. No business logic. |
| `src/embedder.py` | Load model, embed texts, bulk-insert to pgvector. No retrieval. |
| `src/retrieval.py` | Cosine vector search + chatbot REPL. No ingestion. |
| `src/filters.py` | NL → SQL filter conversion + filtered retrieval. Calls retrieval. |
| `src/pipeline.py` | Orchestrate all phases. No raw SQL. No model loading directly. |

---

## Adding New Recipes

1. Add PDFs to `data/recipe_pdfs/` following the structured format:
   ```
   Title: <name>
   Cuisine: <region>
   Prep Time: X mins | Cook Time: Y mins | Servings: Z | Calories: N kcal
   Tags: tag1, tag2, ...

   Ingredients
   -----------
   - ...

   Method
   ------
   1. ...

   Tips
   ----
   • ...
   ```
2. Re-run `python3 run.py` — the pipeline detects changed row count and re-ingests
   only the new chunks (via upsert).

---

## Debugging Common Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` on startup | PostgreSQL not running | `docker compose up -d` or `brew services start postgresql@17` |
| `extension "vector" does not exist` | pgvector not installed | Use `pgvector/pgvector:pg16` Docker image or `brew install pgvector` |
| Low recall in benchmark | Ground-truth from 50 TXT recipes; PDF titles differ | Benchmark is approximate; retrieval still works correctly |
| `UnicodeEncodeError` in PDF generation | Non-latin-1 char in template | `generate_pdfs.py` sanitises via `encode("latin-1", errors="replace")` |
| Slow first query (~100ms) | Model cold-start; subsequent queries <40ms | Expected; cache the model singleton via `get_model()` |
