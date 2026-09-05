"""
Phase 4 - build features out of the narrative text by hand, before any
vectoriser gets involved.

Read fifty narratives yourself first (this script prints a sample to help),
note the patterns you actually see, and only then decide whether the list of
flag words below matches what you noticed. If it does not, change it. The
point of this phase is that every feature is one you can explain out loud.

One thing that catches people out: CFPB redacts personal details as XXXX and
dates as XX/XX/XXXX. A naive "count the capitalised words" feature ends up
measuring how much was redacted, not how much the person was shouting. The
redaction tokens are stripped before the shouting count is taken.

Run:  python src/04_text_features.py
      python src/04_text_features.py --sample 50    (just print narratives)
"""

import argparse
import os
import re
import sys

import pandas as pd

SRC = os.path.join("data", "processed", "complaints.csv")
OUT = os.path.join("data", "processed", "features.csv")
REPORT = os.path.join("docs", "feature_rates.csv")

# The three-year window holds well over a million narratives. Loading them all
# at once needs several GB of memory, and a logistic regression on that many
# rows takes long enough that you stop iterating. A random sample of this size
# is plenty for the effect sizes involved, and it is a sample, not a filter -
# the SQL phase still runs against every row. Raise it if your machine copes.
MAX_ROWS = 400_000
SEED = 7

REDACTION = re.compile(r"\bX{2,}(?:/X{2,})*\b")
MONEY = re.compile(r"(?:\$\s?[\d,]+(?:\.\d{2})?|\b\d[\d,]*\.\d{2}\s?(?:dollars|USD)\b)", re.I)
CAPS_WORD = re.compile(r"\b[A-Z]{3,}\b")

# Words worth flagging, grouped so the README can explain why each is here.
FLAGS = {
    "mentions_attorney": r"\b(attorney|lawyer|legal action|sue|lawsuit|litigation)\b",
    "mentions_fraud": r"\b(fraud|fraudulent|scam|identity theft|stolen)\b",
    "mentions_credit_score": r"\b(credit score|credit report|fico|credit bureau)\b",
    "says_repeatedly": r"\b(repeatedly|again and again|multiple times|over and over|numerous times)\b",
    "says_still": r"\b(still (?:no|not|have|has|hasn|haven|waiting)|to this day|as of today)\b",
    "mentions_regulator": r"\b(cfpb|attorney general|ftc|regulator|consumer protection)\b",
    "mentions_hardship": r"\b(hardship|unemployed|disabled|foreclosure|evict|bankrupt)\b",
    "cites_statute": r"(\b\d{1,2}\s?U\.?S\.?C\.?\s?\d|\bFCRA\b|\bFDCPA\b|\bRESPA\b|\bsection\s+\d{3}\b)",
}


def clean_for_caps(text):
    return REDACTION.sub(" ", text)


def build(df):
    narr = df["narrative"].fillna("")
    out = pd.DataFrame(index=df.index)

    out["narrative_words"] = narr.str.split().str.len()
    out["has_dollar_amount"] = narr.str.contains(MONEY, regex=True).astype(int)

    stripped = narr.map(clean_for_caps)
    out["caps_words"] = stripped.str.count(CAPS_WORD)
    out["shouting"] = (out["caps_words"] >= 3).astype(int)

    out["exclamations"] = narr.str.count("!")
    out["question_marks"] = narr.str.count(r"\?")
    out["redaction_count"] = narr.str.count(REDACTION)

    for name, pattern in FLAGS.items():
        out[name] = narr.str.contains(pattern, case=False, regex=True).astype(int)

    return out


def rate_table(df, feats):
    """Relief rate when each binary feature is present versus absent."""
    binary = [c for c in feats.columns if set(feats[c].unique()) == {0, 1}]
    if not binary:
        print("No flag fired on any narrative. Check the FLAGS patterns.")
    rows = []
    base = df["monetary_relief"].mean()
    for c in binary:
        present = df.loc[feats[c] == 1, "monetary_relief"]
        absent = df.loc[feats[c] == 0, "monetary_relief"]
        rows.append(
            {
                "feature": c,
                "n_present": len(present),
                "rate_present_pct": round(present.mean() * 100, 2) if len(present) else None,
                "rate_absent_pct": round(absent.mean() * 100, 2) if len(absent) else None,
                "lift_pct_points": round((present.mean() - absent.mean()) * 100, 2)
                if len(present) and len(absent)
                else None,
            }
        )
    table = pd.DataFrame(rows).sort_values("lift_pct_points", ascending=False)
    print(f"\nBaseline monetary-relief rate: {base * 100:.2f}%\n")
    print(table.to_string(index=False))
    return table


def load(path):
    """Read the filtered file, sampling down if it is larger than MAX_ROWS."""
    total = sum(len(c) for c in pd.read_csv(path, usecols=["complaint_id"], chunksize=200_000))
    if total <= MAX_ROWS:
        print(f"{total:,} rows, reading all of them.")
        return pd.read_csv(path, low_memory=False)

    frac = MAX_ROWS / total
    print(f"{total:,} rows. Sampling {frac:.1%} of them to keep memory sane.")
    parts = []
    for chunk in pd.read_csv(path, chunksize=200_000, low_memory=False):
        parts.append(chunk.sample(frac=frac, random_state=SEED))
    df = pd.concat(parts, ignore_index=True)
    print(f"Working with {len(df):,} rows.")
    print("Record this in the README - it is a sampling decision, not a filter.\n")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="print N random narratives and stop")
    ap.add_argument("--compare", type=int, default=0,
                    help="print N narratives, half of them relief cases, and stop")
    args = ap.parse_args()

    if not os.path.exists(SRC):
        print(f"No file at {SRC}. Run src/02_filter.py first.")
        sys.exit(1)

    df = load(SRC)

    if args.compare:
        # A random sample at a 1.8% base rate is almost all non-relief cases,
        # so reading one tells you nothing about what separates the two. This
        # takes half from each class and interleaves them, labelled, so you can
        # actually see the contrast.
        half = max(1, args.compare // 2)
        yes = df[df["monetary_relief"] == 1].sample(
            min(half, int((df["monetary_relief"] == 1).sum())), random_state=SEED)
        no = df[df["monetary_relief"] == 0].sample(min(half, len(df)), random_state=SEED)
        print(f"Showing {len(yes)} that got monetary relief and {len(no)} that did not.")
        print("They are interleaved. Cover the label and guess before you look.\n")
        pairs = [r for pair in zip(yes.itertuples(), no.itertuples()) for r in pair]
        for i, row in enumerate(pairs, start=1):
            print(f"\n--- {i}  [{row.product}] relief={row.monetary_relief} ---")
            print(str(row.narrative)[:900])
        print("\nWrite what you noticed into notes.md before running this again.")
        return

    if args.sample:
        sample = df.sample(min(args.sample, len(df)), random_state=SEED)
        for i, row in enumerate(sample.itertuples(), start=1):
            print(f"\n--- {i}  [{row.product}] relief={row.monetary_relief} ---")
            print(str(row.narrative)[:900])
        print("\nWrite what you noticed into notes.md before running this again.")
        return

    feats = build(df)
    table = rate_table(df, feats)

    # company_response is deliberately left out: the target is derived from it,
    # so feeding it to the model would be leakage.
    combined = pd.concat([df[["complaint_id", "date_received", "product", "issue",
                              "company", "state", "submitted_via", "days_to_company",
                              "monetary_relief"]], feats], axis=1)
    combined.to_csv(OUT, index=False)
    os.makedirs("docs", exist_ok=True)
    table.to_csv(REPORT, index=False)
    print(f"\nFeatures written to {OUT}")
    print(f"Rate table written to {REPORT}")


if __name__ == "__main__":
    main()
