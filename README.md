# What makes a consumer complaint escalate

Dashboard: https://yashasr21.github.io/consumer-complaints-analysis/

**Every blank below is deliberate.** Fill each one in from your own run. If a number
is not on your screen from a script in this repository, it does not go in.

---

## 1. The question

A financial company receives thousands of complaints a month. Most close quietly. A
minority turn into disputes, and a dispute costs far more to resolve than a complaint
that closes first time. If the risky ones could be spotted from the text that arrives
on day one, a review team could look at those first.

The question this repository answers: **can the words in a complaint, on the day it
arrives, tell you whether the person will end up disputing the outcome?**

## 2. The data

US Consumer Financial Protection Bureau, Consumer Complaint Database. Public domain.
Provenance and download date are recorded in `data/raw/SOURCE.md`.

Downloaded ____________, ______________ rows in the full file.

**The constraint that shaped this project.** CFPB stopped collecting the
*Consumer disputed?* field part-way through the life of the database, and complaint
narratives were only published from partway through as well. Rows carrying both a
narrative and a dispute outcome sit in the overlap between those two changes.

`src/02_filter.py` finds that overlap from the data rather than assuming dates:

| | |
|---|---|
| Rows read | ____________ |
| Dropped, no dispute outcome recorded | ____________ |
| Dropped, no narrative published | ____________ |
| Rows kept | ____________ (____% of the file) |
| Window | ____________ to ____________ |

That is a large drop and it is the first thing worth being straight about. The model
below is trained on the years where the outcome was still recorded. It would need
re-validating before being pointed at complaints arriving today.

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

- Dispute rate across the whole window: ______%
- Dispute rate after *closed with monetary relief*: ______% against ______% after
  *closed with explanation*. ______________________________________________
- The channel a complaint arrives on ____________________________________
- Volume and dispute rate rank companies differently: ____________________
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
| Disputes caught in that top 10% | ______% |
| Precision at that threshold | ______% |

**The recommendation, in one sentence:**
_____________________________________________________________________________

That sentence is what you open with in an interview. It should contain a number you
can re-derive on paper.

## 6. What this does not tell you

- The dispute field was retired, so nothing here is validated on recent complaints.
- Complaints that reach CFPB are not a random sample of unhappy customers. People who
  escalate to a federal regulator have already self-selected.
- A recorded dispute is an action someone took, not a measure of who was wronged.
  Someone who gave up and never disputed does not appear as a problem in this data.
- Narratives are only published when the consumer consented, so the text-based part of
  this analysis covers a subset of a subset.
- ______________________________________________ *(add your own — you will find one)*

---

Built by Yashas R · [github.com/yashasr21](https://github.com/yashasr21) ·
[linkedin.com/in/yashas-r-637870433](https://linkedin.com/in/yashas-r-637870433)
