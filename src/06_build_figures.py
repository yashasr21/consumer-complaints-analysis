"""
Phase 7 - collect everything the pipeline computed into one file the dashboard
reads.

The dashboard has no numbers hard-coded into it. It fetches docs/figures.json,
and every value in that file was produced by a script in src/ or a query in
sql/. If a stage has not been run, the dashboard shows a dash rather than a
made-up figure.

Run:  python src/06_build_figures.py
"""

import json
import os

import pandas as pd

QOUT = os.path.join("docs", "query_output")
OUT = os.path.join("docs", "figures.json")


def read_csv(name):
    path = os.path.join(QOUT, f"{name}.csv")
    return pd.read_csv(path) if os.path.exists(path) else None


def records(df):
    """to_dict('records'), but with NaN turned into None.

    json.dump writes a bare NaN for a pandas null, which is not valid JSON -
    the browser refuses the whole file and every panel falls back to its empty
    state. This is why the dashboard looked unrun when it was not.
    """
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def read_json(name):
    path = os.path.join("docs", name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    fig = {"generated": pd.Timestamp.now().strftime("%d %B %Y")}

    processed = os.path.join("data", "processed", "complaints.csv")
    if os.path.exists(processed):
        df = pd.read_csv(processed, usecols=["date_received", "monetary_relief"],
                         parse_dates=["date_received"], low_memory=False)
        fig["rows_analysed"] = int(len(df))
        fig["relief_rate_pct"] = round(float(df["monetary_relief"].mean()) * 100, 1)
        fig["window_from"] = df["date_received"].min().strftime("%b %Y")
        fig["window_to"] = df["date_received"].max().strftime("%b %Y")

    model = read_json("model_results.json")
    if model:
        fig["model"] = model

    q2 = read_csv("q2_top_companies_relief_rate")
    if q2 is not None:
        fig["top_companies"] = records(q2.head(8))

    q4 = read_csv("q4_relief_by_product")
    if q4 is not None:
        fig["by_product"] = records(q4)

    q5 = read_csv("q5_relief_by_channel")
    if q5 is not None:
        fig["by_channel"] = records(q5)

    q1 = read_csv("q1_volume_by_product_year")
    if q1 is not None:
        top = (q1.groupby("product")["complaints"].sum()
                 .sort_values(ascending=False).head(6).index.tolist())
        fig["volume_by_year"] = records(q1[q1["product"].isin(top)])

    feat = os.path.join("docs", "feature_rates.csv")
    if os.path.exists(feat):
        fr = pd.read_csv(feat).dropna(subset=["lift_pct_points"])
        fig["feature_lift"] = records(fr.head(8))

    with open(OUT, "w", encoding="utf-8") as f:
        # allow_nan=False makes this fail loudly rather than writing a file
        # the browser will silently reject.
        json.dump(fig, f, indent=2, allow_nan=False)

    have = [k for k in ("rows_analysed", "model", "top_companies", "by_product",
                        "by_channel", "volume_by_year", "feature_lift") if k in fig]
    missing = [k for k in ("rows_analysed", "model", "top_companies", "by_product",
                           "by_channel", "volume_by_year", "feature_lift") if k not in fig]
    print(f"Written {OUT}")
    print("  present:", ", ".join(have) or "nothing")
    if missing:
        print("  missing:", ", ".join(missing))
        print("  (those panels will show a dash until the matching stage runs)")


if __name__ == "__main__":
    main()
