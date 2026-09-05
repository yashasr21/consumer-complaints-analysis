"""
Phase 2 - load the filtered set into SQLite so the SQL phase has something to
run against. Also runs every file in sql/ and saves the output, so the numbers
in the README come from a query you can re-run rather than from a notebook cell
you have since edited.

Run:  python src/03_load_sqlite.py
"""

import glob
import os
import sqlite3
import sys

import pandas as pd

SRC = os.path.join("data", "processed", "complaints.csv")
DB = os.path.join("data", "processed", "complaints.db")
OUTDIR = os.path.join("docs", "query_output")


def load():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)

    total = 0
    for chunk in pd.read_csv(SRC, chunksize=100_000, low_memory=False):
        chunk.to_sql("complaints", con, if_exists="append", index=False)
        total += len(chunk)
        print(f"  loaded {total:,}", flush=True)

    cur = con.cursor()
    for col in ("product", "company", "date_received", "disputed", "company_response"):
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON complaints({col})")
    con.commit()
    print(f"\n{total:,} rows in {DB}")
    return con


def run_queries(con):
    os.makedirs(OUTDIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join("sql", "*.sql")))
    if not files:
        print("No .sql files found.")
        return

    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            query = f.read()
        try:
            df = pd.read_sql_query(query, con)
        except Exception as e:  # a broken query should not kill the run
            print(f"\n{name}: FAILED - {e}")
            continue
        out = os.path.join(OUTDIR, f"{name}.csv")
        df.to_csv(out, index=False)
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df.head(12).to_string(index=False))


if __name__ == "__main__":
    if not os.path.exists(SRC):
        print(f"No file at {SRC}. Run src/02_filter.py first.")
        sys.exit(1)
    connection = load()
    run_queries(connection)
    connection.close()
    print(f"\nQuery output saved to {OUTDIR}/")
    print("Write your one-sentence answer to each query in sql/findings.md.")
