"""
Phase 1 - look at the data before touching it.

Reads the CFPB export in chunks because the full file does not fit in memory
comfortably. Writes a plain-text profile to docs/data_profile.txt.

Run:  python src/01_profile.py
"""

import os
import sys

import pandas as pd

RAW = os.path.join("data", "raw", "complaints.csv")
OUT = os.path.join("docs", "data_profile.txt")
CHUNK = 200_000

# The names CFPB ships in the header, mapped to something typeable.
RENAME = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Consumer consent provided?": "consumer_consent",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response",
    "Consumer disputed?": "consumer_disputed",
    "Complaint ID": "complaint_id",
}


def check_header(path):
    """Read only the header row and complain loudly if CFPB changed it."""
    head = pd.read_csv(path, nrows=0)
    found = list(head.columns)
    missing = [c for c in RENAME if c not in found]
    if missing:
        print("The file header is not what this script expects.")
        print("Missing columns:", missing)
        print("Columns actually in the file:")
        for c in found:
            print("   ", repr(c))
        print("\nFix the RENAME dict at the top of this script, then re-run.")
        sys.exit(1)
    return found


def main():
    if not os.path.exists(RAW):
        print(f"No file at {RAW}.")
        print("Download the CFPB export first - see README, step 1.")
        sys.exit(1)

    size_gb = os.path.getsize(RAW) / 1e9
    check_header(RAW)

    rows = 0
    nulls = None
    per_year = {}
    disputed_per_year = {}
    narrative_per_year = {}
    products = {}

    reader = pd.read_csv(
        RAW,
        chunksize=CHUNK,
        dtype=str,
        usecols=list(RENAME.keys()),
        low_memory=False,
    )

    for i, chunk in enumerate(reader, start=1):
        chunk = chunk.rename(columns=RENAME)
        rows += len(chunk)

        n = chunk.isna().sum()
        nulls = n if nulls is None else nulls.add(n, fill_value=0)

        year = pd.to_datetime(chunk["date_received"], errors="coerce").dt.year
        for y, c in year.value_counts().items():
            per_year[y] = per_year.get(y, 0) + int(c)

        # How many rows in each year actually carry a dispute flag, and a narrative.
        has_disp = chunk["consumer_disputed"].notna()
        for y, c in year[has_disp].value_counts().items():
            disputed_per_year[y] = disputed_per_year.get(y, 0) + int(c)

        has_narr = chunk["narrative"].notna()
        for y, c in year[has_narr].value_counts().items():
            narrative_per_year[y] = narrative_per_year.get(y, 0) + int(c)

        for p, c in chunk["product"].value_counts().items():
            products[p] = products.get(p, 0) + int(c)

        print(f"  chunk {i:>3}  running total {rows:,}", flush=True)

    lines = []
    add = lines.append
    add("CFPB Consumer Complaint Database - profile")
    add(f"source file: {RAW}  ({size_gb:.2f} GB on disk)")
    add(f"rows: {rows:,}")
    add(f"columns: {len(RENAME)}")
    add("")

    add("Missing values by column")
    add(f"{'column':<28}{'missing':>14}{'% missing':>12}")
    for col in RENAME.values():
        m = int(nulls.get(col, 0))
        add(f"{col:<28}{m:>14,}{m / rows * 100:>11.1f}%")
    add("")

    add("Rows per year, and how many carry the two fields the model needs")
    add(f"{'year':<8}{'complaints':>14}{'dispute flag':>16}{'narrative':>14}{'both':>10}")
    for y in sorted(per_year):
        d = disputed_per_year.get(y, 0)
        nn = narrative_per_year.get(y, 0)
        both = "yes" if d and nn else "no"
        add(f"{int(y):<8}{per_year[y]:>14,}{d:>16,}{nn:>14,}{both:>10}")
    add("")

    add("Products by volume")
    for p, c in sorted(products.items(), key=lambda kv: -kv[1]):
        add(f"{c:>12,}  {p}")

    os.makedirs("docs", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines[:40]))
    print(f"\nFull profile written to {OUT}")


if __name__ == "__main__":
    main()
