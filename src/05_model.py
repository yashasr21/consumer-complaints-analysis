"""
Phase 5 and 6 - the classification model, and the recommendation that comes
out of it.

Two things this script does deliberately, both of which an interviewer will
ask about:

1. It splits by time, not at random. Train on the earlier period, test on the
   later one. A random split lets the model see complaints from the same week
   as the ones it is scored on, which is not how it would be deployed.

2. It reports the majority-class baseline first. Most complaints do not
   end in monetary relief, so a model that predicts "no relief" every time already scores
   high on accuracy. The baseline is printed before the model so the model's
   accuracy is never read on its own.

The threshold is picked from the precision-recall curve rather than left at
0.5, and the lift over random review is the number the README opens with.

Run:  python src/05_model.py
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import hstack, csr_matrix

FEATS = os.path.join("data", "processed", "features.csv")
NARR = os.path.join("data", "processed", "complaints.csv")
OUT = os.path.join("docs", "model_results.json")
CURVE = os.path.join("docs", "pr_curve.csv")
COMPARE = os.path.join("docs", "model_comparison.csv")

REVIEW_CAPACITY = 0.10  # the team can manually review 10% of arrivals


def time_split(df, frac=0.75):
    df = df.sort_values("date_received").reset_index(drop=True)
    cut = int(len(df) * frac)
    boundary = df.loc[cut, "date_received"]
    return df.iloc[:cut], df.iloc[cut:], boundary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="all",
                    choices=["product", "product+flags", "all"],
                    help="which layer of features to use, for the ablation")
    args = ap.parse_args()
    level = args.features

    if not os.path.exists(FEATS):
        print(f"No file at {FEATS}. Run src/04_text_features.py first.")
        sys.exit(1)

    df = pd.read_csv(FEATS, parse_dates=["date_received"], low_memory=False)

    # Pull narratives only for the rows we kept, in chunks, so the full file
    # never sits in memory at once.
    wanted = set(df["complaint_id"])
    parts = []
    for chunk in pd.read_csv(NARR, usecols=["complaint_id", "narrative"],
                             chunksize=200_000, low_memory=False):
        parts.append(chunk[chunk["complaint_id"].isin(wanted)])
    narr = pd.concat(parts, ignore_index=True)
    df = df.merge(narr, on="complaint_id", how="left")
    df["narrative"] = df["narrative"].fillna("")

    train, test, boundary = time_split(df)
    print(f"train {len(train):,} rows up to {boundary:%d %b %Y}")
    print(f"test  {len(test):,} rows after that\n")

    base_rate = test["monetary_relief"].mean()
    majority_acc = max(base_rate, 1 - base_rate)
    print(f"Relief rate in the test period  : {base_rate * 100:.2f}%")
    print(f"Majority-class baseline accuracy: {majority_acc * 100:.2f}%")
    print("Any accuracy figure below is read against that number, not zero.\n")

    hand = [c for c in df.columns if c not in
            {"complaint_id", "date_received", "product", "issue", "company", "state",
             "submitted_via", "monetary_relief", "narrative"}]

    # Build the feature blocks in layers, so each can be switched off. The point
    # of the ablation is to find out how much of the score is the product field
    # and how much is anything the consumer actually wrote.
    cats = ["product"] if level != "all" else ["product", "issue", "submitted_via", "state"]
    enc = OneHotEncoder(handle_unknown="ignore", min_frequency=50)
    blocks_tr = [enc.fit_transform(train[cats].astype(str))]
    blocks_te = [enc.transform(test[cats].astype(str))]
    described = [f"categorical ({', '.join(cats)})"]

    if level in ("product+flags", "all"):
        blocks_tr.append(csr_matrix(train[hand].fillna(0).astype(float).values))
        blocks_te.append(csr_matrix(test[hand].fillna(0).astype(float).values))
        described.append(f"{len(hand)} hand-built text flags")

    tfidf = None
    if level == "all":
        # Fitted on train only, so the test period stays unseen.
        tfidf = TfidfVectorizer(max_features=15_000, ngram_range=(1, 2),
                                min_df=5, stop_words="english", sublinear_tf=True)
        blocks_tr.append(tfidf.fit_transform(train["narrative"]))
        blocks_te.append(tfidf.transform(test["narrative"]))
        described.append("TF-IDF, 15k terms")

    print(f"Feature set '{level}': " + " + ".join(described) + "\n")
    Xtr = hstack(blocks_tr).tocsr()
    Xte = hstack(blocks_te).tocsr()
    ytr, yte = train["monetary_relief"].values, test["monetary_relief"].values

    model = LogisticRegression(max_iter=1000, class_weight="balanced", C=0.5,
                               solver="liblinear")
    model.fit(Xtr, ytr)
    prob = model.predict_proba(Xte)[:, 1]

    auc = roc_auc_score(yte, prob)
    ap = average_precision_score(yte, prob)
    print(f"ROC AUC            : {auc:.3f}")
    print(f"Average precision  : {ap:.3f}  (random = {base_rate:.3f})\n")

    prec, rec, thr = precision_recall_curve(yte, prob)
    pd.DataFrame({"precision": prec[:-1], "recall": rec[:-1], "threshold": thr}).to_csv(
        CURVE, index=False
    )

    # Operating point: the score cut-off that selects the top 10% of arrivals,
    # because that is what the review team can actually get through.
    cutoff = float(np.quantile(prob, 1 - REVIEW_CAPACITY))
    flagged = prob >= cutoff
    caught = yte[flagged].sum() / yte.sum()
    precision_at_cut = yte[flagged].mean()
    lift = precision_at_cut / base_rate

    print(f"Reviewing the top {REVIEW_CAPACITY:.0%} by score (threshold {cutoff:.3f}):")
    print(f"  catches {caught * 100:.1f}% of all relief cases")
    print(f"  {precision_at_cut * 100:.1f}% of what you review ends in relief")
    print(f"  that is {lift:.2f}x better than reviewing 10% at random\n")

    print(classification_report(yte, (prob >= cutoff).astype(int),
                               target_names=["no relief", "monetary relief"], digits=3))

    top = []
    if tfidf is not None:
        # Twenty highest-weighted text terms, to check against what you read by hand.
        names = np.array(tfidf.get_feature_names_out())
        text_coefs = model.coef_[0][-len(names):]
        top = list(names[np.argsort(text_coefs)[-20:][::-1]])
        print("Top 20 text terms pushing towards monetary relief:")
        print(", ".join(top))

    results = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "split_date": boundary.strftime("%Y-%m-%d"),
        "test_relief_rate_pct": round(base_rate * 100, 2),
        "majority_baseline_accuracy_pct": round(majority_acc * 100, 2),
        "roc_auc": round(float(auc), 3),
        "average_precision": round(float(ap), 3),
        "review_capacity_pct": int(REVIEW_CAPACITY * 100),
        "threshold": round(cutoff, 4),
        "recall_at_capacity_pct": round(float(caught) * 100, 1),
        "precision_at_capacity_pct": round(float(precision_at_cut) * 100, 1),
        "lift_vs_random": round(float(lift), 2),
        "top_terms": top,
    }
    results["feature_set"] = level

    # Only the full model feeds the dashboard; the ablation runs must not
    # overwrite the published numbers with a deliberately crippled model.
    if level == "all":
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nWritten to {OUT}")

    row = pd.DataFrame([{k: results[k] for k in
                         ("feature_set", "roc_auc", "average_precision",
                          "recall_at_capacity_pct", "precision_at_capacity_pct",
                          "lift_vs_random")}])
    row.to_csv(COMPARE, mode="a", header=not os.path.exists(COMPARE), index=False)
    print(f"Appended to {COMPARE}")
    if os.path.exists(COMPARE):
        print("\n" + pd.read_csv(COMPARE).to_string(index=False))
    print("\nPhase 6: the lift number above is your README opening sentence.")


if __name__ == "__main__":
    main()
