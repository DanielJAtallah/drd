<!-- Short, actionable instructions to help an AI coding agent be productive in this repo -->
# Copilot instructions — drd

This repository contains small data-collection experiments that use Reddit APIs (praw/requests), numpy/pandas for processing, and optionally GLoVe vectors. The agent should focus on lightweight, durable data collection and follow the project's existing conventions.

Key files and places to look
- `src/reddit_subreddit_category.py` — main script doing auth, search-term generation, and subreddit listing collection. Look for `search_terms`, the GLoVe ingestion block, and the top-level loops that make API calls.
- `requirements.txt` — shows runtime deps: `pandas`, `numpy`, `praw`, `requests`, `scipy`, `dotenv`.
- `data/` — target directory for persisted datasets and temporary files.
- `.envrc` (referenced via `load_dotenv(os.path.abspath('..') + '/.envrc')`) — contains Reddit credentials; do not expose or hard-code secrets.

Project-specific patterns and constraints
- Environment: credentials come from `../.envrc` via `dotenv`. Keep secret handling unchanged.
- API usage: code uses both `praw` and direct `requests` (manual OAuth). Respect rate limits and do small batch fetches.
- Data shape: mixed numeric and string fields (e.g., scores, timestamps, titles, bodies). The code base currently imports `pandas`/`numpy` — prefer solutions that interoperate with pandas but avoid building huge in-memory DataFrames.

Recommended, concrete ways to grow a dataset (readable, fast, memory-conscious)
1) Buffered in-memory rows → periodic pandas flush (simple, readable)
   - Collect rows as list-of-dicts and call `pd.DataFrame(rows)` every N rows (e.g., N=5000), then append to disk (CSV or parquet).
   - Use CSV for simplest compatibility, but be careful with headers when appending (use mode='a', header=not exists).
   - Example target: `data/collected.csv` (small utility to append batches).

2) Append-only CSV with csv.DictWriter (low memory, minimal deps)
   - Use Python's built-in `csv` with a pre-defined header order. Open the file once and keep it open, write rows as they arrive.
   - Commit frequency: flush every 100–1000 rows to keep data durable without excessive IO.

3) SQLite (recommended for durability and low memory)
   - Use built-in `sqlite3`. Create a fixed schema (TEXT for strings, REAL/INTEGER for numbers). Insert rows inside transactions and commit in batches (e.g., every 1000 inserts).
   - Benefit: small memory footprint, fast writes, simple queries without loading into pandas. Use `pd.read_sql_query()` to analyze later.

Quick examples (conceptual; implement in `src/data_writer.py` if adding code):
- CSV append: use `csv.DictWriter(fieldnames=...)` with `open('data/collected.csv','a',newline='')` and call `writer.writerow(row)`; flush periodically.
- SQLite: `conn = sqlite3.connect('data/collected.db', timeout=30)`; use `conn.executemany('INSERT INTO items (...) VALUES (?,?,...)', batch)` inside a transaction.

Trade-offs and hints
- If you need high-speed columnar analytics later, consider adding `pyarrow`/`fastparquet` or `polars`, but these are not in `requirements.txt` now.
- For heavy streaming (> millions of rows), prefer SQLite or periodic parquet files over a single in-memory DataFrame.
- Always normalize types: convert missing numerics to `None`/`np.nan` before insertion, and store timestamps as ISO strings or integers consistently.

Files an agent may change safely
- Add a small `src/data_writer.py` with an interface: `append(row: dict)`, `flush()`, `close()` and use it from `src/reddit_subreddit_category.py`.
- Add an entry in `README.md` documenting how to run collection and where outputs are written (`data/`).

When making edits
- Preserve the dotenv pattern and never write credentials into source.
- Keep rate-limit behavior: prefer introducing sleeps or batch sizes rather than broad parallelism.
- Add tests/examples in a new `tests/` small harness if touching data writing logic.

If anything in this file is unclear, say which part of the data flow or auth you want clarified and I will expand with code examples or implement the `data_writer` helper.
