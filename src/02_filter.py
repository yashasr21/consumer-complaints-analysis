"""
Phase 2 - cut the file down to something workable.

The important decision happens here, and it is not the one this project started
with. The original plan was to predict whether a consumer disputed the outcome.
CFPB has removed "Consumer disputed?" from the export, so that target no longer
exists in the data at all. `src/01_profile.py` prints the column list it does
have.

The replacement target is monetary relief: did the company close this complaint
by paying the person something? That is recorded in "Company response to
consumer", it is present across the whole file, and it is the more useful
question anyway - these are the complaints that cost money.

Because the target is no longer tied to a retired field, the most recent three
full years are usable, which is what the build guide wanted in the first place.

Run:  python src/02_filter.py
"""

import os
import sys

import pandas as pd

RAW = os.path.join("data", "raw", "complaints.csv")
OUT = os.path.join("data", "processed", "complaints.csv")
CHUNK = 200_000
YEARS_KEPT = 3

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
    "Complaint ID": "complaint_id",
}

KEEP = list(RENAME.values())
RELIEF = "Closed with monetary relief"


def latest_date(path):
    """One cheap pass to find the most recent complaint date in the file."""
    newest = None
    for chunk in pd.read_csv(path, chunksize=500_000, usecols=["Date received"], dtype=str):
        d = pd.to_datetime(chunk["Date received"], errors="coerce").max()
        newest = d if newest is None else max(newest, d)
    return newest


def main():
    if not os.path.exists(RAW):
        print(f"No file at {RAW}. Download it first - see README, step 1.")
        sys.exit(1)

    print("Finding the most recent date in the file...")
    newest = latest_date(RAW)
    cutoff = newest - pd.DateOffset(years=YEARS_KEPT)
    print(f"Most recent complaint: {newest:%d %b %Y}")
    print(f"Keeping everything from {cutoff:%d %b %Y} onwards\n")

    if os.path.exists(OUT):
        os.remove(OUT)

    seen = kept = 0
    first_write = True
    dropped_old = dropped_no_narrative = dropped_no_response = 0

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
        chunk = chunk[chunk["date_received"] >= cutoff]
        dropped_old += before - len(chunk)

        before = len(chunk)
        chunk = chunk[chunk["narrative"].notna()]
        chunk = chunk[chunk["narrative"].str.strip().str.len() > 0]
        dropped_no_narrative += before - len(chunk)

        before = len(chunk)
        chunk = chunk[chunk["company_response"].notna()]
        # Complaints still open have no outcome yet, so they cannot be labelled.
        chunk = chunk[~chunk["company_response"].str.strip().isin(["In progress", ""])]
        dropped_no_response += before - len(chunk)

        if chunk.empty:
            continue

        chunk["days_to_company"] = (
            chunk["date_sent_to_company"] - chunk["date_received"]
        ).dt.days
        chunk["monetary_relief"] = (
            chunk["company_response"].str.strip() == RELIEF
        ).astype(int)
        chunk["narrative_len"] = chunk["narrative"].str.split().str.len()

        chunk[KEEP + ["days_to_company", "monetary_relief", "narrative_len"]].to_csv(
            OUT, mode="w" if first_write else "a", header=first_write, index=False
        )
        first_write = False
        kept += len(chunk)
        print(f"  chunk {i:>3}  kept {len(chunk):>6,}  (running {kept:,})", flush=True)

    if kept == 0:
        print("\nNothing survived the filter. Check docs/data_profile.txt.")
        sys.exit(1)

    rate = pd.read_csv(OUT, usecols=["monetary_relief"])["monetary_relief"].mean()

    print("\n" + "-" * 60)
    print(f"read      {seen:,} rows")
    print(f"dropped   {dropped_old:,} older than the {YEARS_KEPT}-year window")
    print(f"dropped   {dropped_no_narrative:,} with no narrative published")
    print(f"dropped   {dropped_no_response:,} with no outcome recorded yet")
    print(f"kept      {kept:,} rows  ({kept / seen * 100:.1f}% of the file)")
    print(f"target    {rate * 100:.2f}% closed with monetary relief")
    print("-" * 60)
    print(f"\nWritten to {OUT}")
    print("\nNarratives are only published with the consumer's consent, so this is")
    print("a subset of all complaints. Say so in the README.")


if __name__ == "__main__":
    main()
