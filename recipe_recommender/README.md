# Recipe RAG Pipeline

A production-ready **Retrieval-Augmented Generation (RAG)** ingestion and retrieval
pipeline for a food startup's 10,000-recipe chatbot corpus.

> **Backend:** PostgreSQL + pgvector (IVFFlat index, cosine similarity)  
> **Embedding:** `all-MiniLM-L6-v2` — 384-dim, CPU-friendly, MIT licence  
> **Corpus:** 10,000 recipe PDFs → 30,000 section-level chunks

---

## Project Structure

```
recipe_recommender/
├── AGENTS.md               # AI-agent guide: overview, commands, hard constraints
├── PROGRESS.md             # Done / in-progress / blocked status
├── Makefile                # Standardised commands: setup, run, lint, check
├── requirements.txt        # All Python dependencies
├── docker-compose.yml      # PostgreSQL + pgvector container
│
├── run.py                  # PRIMARY ENTRY — 10k PDFs → full pipeline + chatbot
├── main.py                 # Legacy entry — 50 TXT recipes (kept for reference)
│
├── data/
│   ├── generate_pdfs.py    # Generates 10,000 recipe PDFs  (fpdf2)
│   ├── generate_recipes.py # Generates 50 TXT recipe files (legacy)
│   ├── recipe_pdfs/        # 10,000 PDFs (recipe_00000.pdf … recipe_09999.pdf)
│   └── recipes/            # 50 TXT files (legacy corpus)
│
├── src/
│   ├── ARCHITECTURE.md     # System design decisions (D1–D8)
│   ├── db/
│   │   └── CONSTRAINTS.md  # Database hard constraints (C1–C8)
│   ├── chunker.py          # Section-level chunking, PDF/TXT parsing, ChunkRecord
│   ├── db.py               # PostgreSQL connection, DDL, indexes
│   ├── embedder.py         # Embedding model, pgvector bulk ingest, sanity guard
│   ├── filters.py          # NL filter parsing, SQL metadata pre-filtering
│   ├── pipeline.py         # End-to-end orchestrator
│   └── retrieval.py        # Vector search, n_probe benchmark, chatbot REPL
│
└── results/
    ├── benchmark_results.json  # Latest n_probe + filter benchmark output
    └── embeddings.npy          # Raw embedding backup (for HNSW migration)
```

---

## Quick Start

### Option A — Makefile (recommended)

```bash
make setup        # create venv + pip install -r requirements.txt
make db-up        # start PostgreSQL via docker compose
make run          # generate 10k PDFs → chunk → embed → benchmark → chatbot
```

### Option B — Manual

```bash
# 1. Create venv
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL + pgvector
docker compose up -d                              # Docker
# OR: brew services start postgresql@17          # Homebrew

# 4. Set DB env vars (Docker only)
export PGHOST=localhost PGPORT=5432 PGDATABASE=recipes PGUSER=recipes PGPASSWORD=recipes

# 5. Run everything
python3 run.py
```

`run.py` is **idempotent**: PDFs already generated → skips; chunks already in DB → skips.

---

## Design Decisions

### Q1 — Chunk Unit: Section-Level

**One chunk = one recipe section** (ingredients | method | tips). Never merged, never
split to one-step-per-chunk.

User queries hit two semantic axes simultaneously — ingredient matching and constraint
filtering. Merged embeddings average all sections into one centroid, diluting both.
Per-step chunks lack ingredient context ("Flip carefully and cook another 2 minutes"
is meaningless alone).

### Q2 — Metadata Schema (14 fields per chunk)

`recipe_id · title · section · text · cuisine · tags[] · dietary[] ·
prep_time_mins · cook_time_mins · total_time_mins · servings · calories_kcal ·
chunk_index · char_count`

Stored denormalised in `recipe_chunks` — no joins at query time.

### Q3 — Overlap

150-char overlap applied only to **method sections exceeding 1,200 chars**, split at
numbered-step boundaries. Ingredients and tips carry no overlap — they are
order-independent enumerations.

### Q4 — Vector Store: pgvector over FAISS

**pgvector (IVFFlat, lists=64)** replaced FAISS because:
- FAISS cannot filter by metadata without a parallel data store and post-fetch joins.
- FAISS IVFFlat requires `nlist × 39` training vectors — fires warnings on small corpora.
- pgvector uses `SET LOCAL ivfflat.probes = K` (identical semantics to FAISS `nprobe`).
- HNSW migration at ~100k rows is zero-downtime: `CREATE INDEX CONCURRENTLY … USING hnsw`.
  No re-embedding required — `embeddings.npy` is always persisted as backup.

### Q5 — HashEmbedder Guard

Startup assertion: cosine similarity between two near-synonyms > **0.60**.
Also checks: vector dimension == 384, vector not all-zeros.

This guards against the "sometimes returns irrelevant recipes" symptom caused by
accidentally using a hash-based function (MD5, FNV) instead of a semantic model —
pgvector still returns K rows but they are semantically random.

### Q6 — n_probe Tuning

Benchmark runs `SET ivfflat.probes = K` for K ∈ {1, 5, 10, 50} and measures
recall@5 and latency per query.

**Recommended production setting: probes=10** — balances ~90% recall with ~30–80 ms
latency on 30k rows. Increase to 50 if recall matters more than speed.

### Stretch A — SQL Metadata Pre-filtering

Natural-language constraints are parsed from the query string and converted to SQL
`WHERE` clauses before the vector search:

- `"vegan"` → `tags @> ARRAY['vegan']` (GIN index)
- `"under 30 minutes"` → `total_time_mins <= 30` (btree index)
- `"under 500 calories"` → `calories_kcal <= 500` (btree index)

Fallback: if the filtered candidate pool < 10 rows, the filter is dropped and the
full corpus is searched.

---

## Running Individual Components

```bash
# Chunk 10k PDFs and print stats (no DB)
python3 -c "from src.chunker import chunk_pdf_directory; c=chunk_pdf_directory('data/recipe_pdfs/'); print(len(c),'chunks')"

# Embedding sanity check
make check

# Lint
make lint

# Pipeline phases only (no chatbot)
make run-pipeline

# Legacy 50-recipe pipeline
make run-legacy
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PGHOST` | `localhost` | PostgreSQL host |
| `PGPORT` | `5432` | PostgreSQL port |
| `PGDATABASE` | `recipes` | Database name |
| `PGUSER` | OS username | DB user |
| `PGPASSWORD` | *(none)* | DB password |
