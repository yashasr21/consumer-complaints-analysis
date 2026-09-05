"""
Phase 2 - cut the file down to something workable.

The important decision happens here. The target variable for this project is
"Consumer disputed?". CFPB stopped collecting that field in 2017, so the most
recent years of the file have no target at all. Narratives, meanwhile, were
only published from 2015 onwards. The rows that carry BOTH are the only rows a
text-based dispute model can learn from.

This script finds that overlap window from the data itself rather than
assuming dates, prints the row count before and after, and writes the result.

Run:  python src/02_filter.py
"""

import os
import sys

import pandas as pd

RAW = os.path.join("data", "raw", "complaints.csv")
OUT = os.path.join("data", "processed", "complaints.csv")
CHUNK = 200_000

RENAME = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company": "company",
    "State": "state",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response",
    "Consumer disputed?": "consumer_disputed",
    "Complaint ID": "complaint_id",
}

KEEP = list(RENAME.values())


def main():
    if not os.path.exists(RAW):
        print(f"No file at {RAW}. Download it first - see README, step 1.")
        sys.exit(1)

    if os.path.exists(OUT):
        os.remove(OUT)

    seen = 0
    kept = 0
    first_write = True
    min_date, max_date = None, None
    dropped_no_target = 0
    dropped_no_narrative = 0

    reader = pd.read_csv(
        RAW, chunksize=CHUNK, dtype=str, usecols=list(RENAME.keys()), low_memory=False
    )

    for i, chunk in enumerate(reader, start=1):
        chunk = chunk.rename(columns=RENAME)
        seen += len(chunk)

        chunk["date_received"] = pd.to_datetime(chunk["date_received"], errors="coerce")
        chunk["date_sent_to_company"] = pd.to_datetime(
            chunk["date_sent_to_company"], errors="coerce"
        )

        before = len(chunk)
        chunk = chunk[chunk["consumer_disputed"].notna()]
        dropped_no_target += before - len(chunk)

        before = len(chunk)
        chunk = chunk[chunk["narrative"].notna()]
        chunk = chunk[chunk["narrative"].str.strip().str.len() > 0]
        dropped_no_narrative += before - len(chunk)

        if chunk.empty:
            print(f"  chunk {i:>3}  kept 0  (running {kept:,})", flush=True)
            continue

        lo, hi = chunk["date_received"].min(), chunk["date_received"].max()
        min_date = lo if min_date is None else min(min_date, lo)
        max_date = hi if max_date is None else max(max_date, hi)

        # Days the company took to route the complaint onward.
        chunk["days_to_company"] = (
            chunk["date_sent_to_company"] - chunk["date_received"]
        ).dt.days

        chunk["disputed"] = (chunk["consumer_disputed"].str.strip() == "Yes").astype(int)
        chunk["narrative_len"] = chunk["narrative"].str.split().str.len()

        chunk[KEEP + ["days_to_company", "disputed", "narrative_len"]].to_csv(
            OUT, mode="w" if first_write else "a", header=first_write, index=False
        )
        first_write = False
        kept += len(chunk)
        print(f"  chunk {i:>3}  kept {len(chunk):>6,}  (running {kept:,})", flush=True)

    if kept == 0:
        print("\nNothing survived the filter. Check docs/data_profile.txt - if no")
        print("year shows 'both', CFPB has changed what it publishes and this")
        print("project needs a different target variable. See notes.md.")
        sys.exit(1)

    pct = kept / seen * 100
    print("\n" + "-" * 58)
    print(f"read      {seen:,} rows")
    print(f"dropped   {dropped_no_target:,} with no dispute flag (field retired)")
    print(f"dropped   {dropped_no_narrative:,} with no narrative published")
    print(f"kept      {kept:,} rows  ({pct:.1f}% of the file)")
    print(f"window    {min_date:%d %b %Y} to {max_date:%d %b %Y}")
    print("-" * 58)
    print(f"\nWritten to {OUT}")
    print("\nThat drop is large. Write down in the README why it is defensible")
    print("before you go any further - an interviewer will ask.")


if __name__ == "__main__":
    main()
