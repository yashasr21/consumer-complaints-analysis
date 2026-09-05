# What makes a complaint cost money

Dashboard: https://yashasr21.github.io/consumer-complaints-analysis/

**Every blank below is deliberate.** Fill each one in from your own run. If a number
is not on your screen from a script in this repository, it does not go in.

---

## 1. The question

A financial company receives thousands of complaints a month. Most are closed with an
explanation and cost nothing but staff time. A minority end with the company paying the
person something, and those are the expensive ones. If they could be spotted from the
text that arrives on day one, a review team could look at those first.

The question this repository answers: **can the words in a complaint, on the day it
arrives, tell you whether it will end in monetary relief?**

This is not the question the project started with. See below.

## 2. The data

US Consumer Financial Protection Bureau, Consumer Complaint Database. Public domain.
Provenance and download date are recorded in `data/raw/SOURCE.md`.

Downloaded ____________, ______________ rows in the full file.

**The change of target, and why.** This project set out to predict whether a consumer
*disputed* the company's response. `src/01_profile.py` checks the file header before
reading anything, and it stopped: CFPB no longer publishes *Consumer disputed?* or
*Consumer consent provided?* in the export. The original target does not exist in the
data any more.

Rather than force it, the target moved to something the file does still carry:
**Company response to consumer**, and specifically whether it reads *Closed with
monetary relief*. That is the outcome the original question was a proxy for anyway —
which complaints turn expensive — and it is recorded for every year, so the recent
three-year window is usable.

`src/02_filter.py` reports its own filtering:

| | |
|---|---|
| Rows read | ____________ |
| Dropped, older than the three-year window | ____________ |
| Dropped, no narrative published | ____________ |
| Dropped, no outcome recorded yet | ____________ |
| Rows kept | ____________ (____% of the file) |
| Closed with monetary relief | ______% |

## 3. What I did

```
pip install -r requirements.txt
bash run_all.sh                 # or run the six scripts in src/ in order
```

| Stage | Script | What it produces |
|---|---|---|
| Profile | `src/01_profile.py` | `docs/data_profile.txt` — shape, nulls, coverage by year |
| Filter | `src/02_filter.py` | `data/processed/complaints.csv` |
| SQL | `src/03_load_sqlite.py` | SQLite database, plus every query in `sql/` run and saved |
| Text features | `src/04_text_features.py` | hand-built flags and their dispute rates |
| Model | `src/05_model.py` | `docs/model_results.json` |
| Dashboard | `src/06_build_figures.py` | `docs/figures.json`, read by the page |

Eight SQL queries live in `sql/`, one per question. One-sentence answers are in
`sql/findings.md`.

## 4. What I found

Write one line per finding, each traceable to a query.

- Relief rate across the whole window: ______%
- The product with the highest relief rate was ____________ at ______%, against
  ______% for the highest-volume product. ________________________________
- The channel a complaint arrives on ____________________________________
- Volume and relief rate rank companies differently: ____________________
- The hand-built text flag with the largest lift was ____________, worth
  ______ percentage points.

## 5. The model and what to do with it

Logistic regression. Hand-built text flags, categorical context, and TF-IDF terms.
**Split by time, not at random** — trained on the earlier part of the window and
tested on the later part, because that is how it would actually be used.

| | |
|---|---|
| Majority-class baseline accuracy | ______% |
| ROC AUC | ______ |
| Average precision | ______ against ______ at random |
| Threshold | ______, chosen to flag the top 10% by score |
| Relief cases caught in that top 10% | ______% |
| Precision at that threshold | ______% |

**The recommendation, in one sentence:**
_____________________________________________________________________________

That sentence is what you open with in an interview. It should contain a number you
can re-derive on paper.

## 6. What this does not tell you

- Monetary relief is a company's decision to pay, not a measure of who was wronged. A
  firm that settles readily looks worse here than one that refuses everything.
- Complaints that reach CFPB are not a random sample of unhappy customers. People who
  escalate to a federal regulator have already self-selected.
- Narratives are only published when the consumer consented, so this covers a subset.
  Whatever makes someone consent to publication may also relate to the outcome.
- The company's own response field is the source of the label, so it is deliberately
  kept out of the features. Leaving it in would have leaked the answer into the model.
- ______________________________________________ *(add your own — you will find one)*

---

Built by Yashas R · [github.com/yashasr21](https://github.com/yashasr21)
