# What makes a complaint cost money

Dashboard: https://yashasr21.github.io/consumer-complaints-analysis/

## 1. The question

A financial company receives thousands of complaints a month. Most are closed with an
explanation and cost nothing but staff time. A minority end with the company paying the
person something, and those are the expensive ones. If they could be spotted from the
text that arrives on day one, a review team could look at those first.

The question this repository answers: **can the words in a complaint, on the day it
arrives, tell you whether it will end in monetary relief?**

The short answer turned out to be *yes, but not for the reason I expected*. See section 4.

## 2. The data

US Consumer Financial Protection Bureau, Consumer Complaint Database. Public domain.
Provenance and download date are in `data/raw/SOURCE.md`.

**17,571,890 rows, 16 columns, 9.28 GB.** Too large for Excel and too large to load into
memory, so every script reads it in chunks.

**The target had to change.** This project set out to predict whether a consumer
*disputed* the company's response. `src/01_profile.py` checks the header before reading
anything, and it stopped: CFPB no longer publishes *Consumer disputed?* or *Consumer
consent provided?* in the export. The original target does not exist in the data.

The replacement is **Company response to consumer**, specifically whether it reads
*Closed with monetary relief*. It is present for every year, and it is the outcome the
dispute question was standing in for anyway — which complaints turn expensive.

`src/02_filter.py` reports its own filtering:

| | |
|---|---|
| Rows read | 17,571,890 |
| Dropped, older than the three-year window | 4,049,415 |
| Dropped, no narrative published | 11,206,747 |
| Dropped, no outcome recorded yet | 127 |
| Rows kept | 2,315,601 (13.2% of the file) |
| Window | Sep 2023 – Aug 2026 |
| Closed with monetary relief | 1.78% (41,189 complaints) |

Note which filter did the work. The three-year window dropped 4 million rows; the
narrative requirement dropped 11.2 million. **Narratives are missing on 78% of the
database** — they are only published when the consumer consents. This analysis is about
complaints where someone agreed to publish their words, not about complaints in general.

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
| Text features | `src/04_text_features.py` | hand-built flags and their relief rates |
| Model | `src/05_model.py` | `docs/model_results.json` |
| Dashboard | `src/06_build_figures.py` | `docs/figures.json`, read by the page |

Eight SQL queries live in `sql/`, one per question, with one-sentence answers in
`sql/findings.md`.

**One sampling decision.** The three-year window holds 2.3 million narratives. The
feature and model stages take a random 400,000-row sample of those, because the full set
needs several GB of memory and makes iteration too slow to be useful. The SQL in
`sql/` still runs against every row. The sample is fixed by seed, so results reproduce.

## 4. What I found

**Relief is concentrated in a tenth of the volume.**

| Product | Complaints | Relief cases | Relief rate |
|---|---|---|---|
| Credit reporting or other personal consumer reports | 1,661,995 | 1,038 | 0.1% |
| Debt collection | 221,546 | 615 | 0.3% |
| Checking or savings account | 110,183 | 13,922 | 12.6% |
| Credit card | 108,718 | 17,841 | 16.4% |
| Money transfer, virtual currency, or money service | 87,448 | 3,295 | 3.8% |
| Mortgage | 37,718 | 739 | 2.0% |
| Prepaid card | 10,199 | 2,017 | 19.8% |

Credit reporting is **71.8% of all complaints and 2.5% of all payouts**. Prepaid card,
credit card and checking together are **9.9% of complaints and 82.0% of payouts** — a
hundredfold spread in relief rate between the top and bottom product lines.

That single fact reframes the whole project, and it is why section 5 does not claim what
it looks like it should claim.

This concentration is the single largest effect in the project, and section 5 quantifies
how much of the model is simply rediscovering it.

*To fill in from `docs/query_output/` — see `sql/findings.md`:*
- Do the highest-volume companies have the worst relief rates, or just the most complaints? (q2)
- Which companies sit furthest above their own product's average? (q8) — this is the
  query that controls for the product effect above, so it is the most useful one here.
- Does the submission channel matter once you know the product? (q5)
- Which issue types are growing? (q7)

## 5. The model, and what it is really doing

Logistic regression. Hand-built text flags, categorical context (product, issue, channel,
state) and TF-IDF terms. **Split by time, not at random** — trained on the earlier part
of the window, tested on the later part, because that is how it would be used.

`Company response to consumer` is the source of the label, so it is deliberately excluded
from the features. Leaving it in would have leaked the answer.

| | |
|---|---|
| Test period | 100,000 complaints, 2.59% relief rate |
| Majority-class baseline accuracy | 97.41% |
| ROC AUC | 0.953 |
| Threshold | chosen to flag the top 10% by score |
| Relief cases caught in that top 10% | 80.3% |
| Precision at that threshold | 20.8% |
| **Lift over reviewing 10% at random** | **8.03×** |

Read the accuracy against 97.41%, not against zero. Predicting "no relief" every single
time scores 97.41% on this data.

**Why that 0.953 needed checking.** Look again at the product table. Selecting the three
product lines with the highest relief rates — also about 10% of volume — captures 82% of
relief cases. A `GROUP BY` gets most of the way there on its own, which is a strong hint
that a model scoring 0.953 might be learning product identity rather than language. The
top-weighted text terms reinforce the suspicion: many are company names (comenity,
coinbase, citibank, amex) rather than descriptions of what went wrong, though genuine
content words appear alongside them (atm, refund, escrow, escalated).

That suspicion turned out to be about 71% right, and the ablation below quantifies it
rather than leaving it as a hunch.

### How much of that is actually the text?

Because the product field alone separates the classes so well, the model was run three
times with the feature blocks switched on in layers (`src/05_model.py --features ...`).
Full output in `docs/model_comparison.csv`.

| Features | ROC AUC | Avg precision | Precision @10% | Lift |
|---|---|---|---|---|
| Product only | 0.914 | 0.146 | 14.7% | 5.69× |
| Product + hand-built flags | 0.930 | 0.194 | 17.9% | 6.92× |
| Product + flags + TF-IDF | 0.953 | 0.328 | 20.8% | 8.02× |

**Product alone accounts for about 71% of the lift.** Knowing only which product line a
complaint belongs to gets you 5.69× over random review, which matches the `GROUP BY`
result above and confirms the product effect is the single biggest signal.

**The text adds the remaining 29%, and it is real.** Average precision more than doubles
from 0.146 to 0.328. In operational terms: reviewing the same 10,000 complaints, the full
model surfaces 20.8% genuine relief cases against 14.7% for product routing alone — **41%
more payouts found for the same review effort.**

The hand-built flags and the TF-IDF terms contribute roughly equally, which is worth
noting: seven explainable flags recover about half of what 15,000 opaque TF-IDF features
do. If the model had to be defensible to a compliance team, the flags-only version costs
little and explains itself.

One caveat on the product-only row. Its recall at the 10% threshold is *higher* than the
full model's (82.4% against 80.2%) while its precision is much lower. That is because a
product-only model can only assign a handful of distinct scores, so its "top 10%" is
really "these product lines", which sweeps in nearly every relief case along with a great
deal of noise. Precision, not recall, is the number to read here.

**The recommendation, in one sentence:**
_____________________________________________________________________________

*(Yours to write, now that the ablation is in. The shape the evidence supports: route
review capacity to the three high-relief product lines first, since that alone is worth
5.69×, then use the text model to rank within them for the remaining 41% gain. Put a
number in it that you can re-derive on paper.)*

## 6. What this does not tell you

- About 71% of the model's lift comes from the product field alone. The complaint text
  adds a real but secondary 29%. Anyone reading the 0.953 AUC as "the language predicts
  payouts" would be overstating it by roughly threefold.
- Monetary relief is a company's decision to pay, not a measure of who was wronged. A
  firm that settles readily looks worse here than one that refuses everything.
- Narratives are missing on 78% of the database and are only published with consent.
  Whatever makes someone consent to publication may also relate to the outcome.
- Complaints that reach CFPB are not a random sample of unhappy customers. People who
  escalate to a federal regulator have already self-selected.
- The base relief rate fell from 9.1% in 2012 to 0.9% in 2024 — the target is drifting
  underneath the model, and the test period behaves differently from the training period.
- The feature and model stages run on a 400,000-row sample, not the full 2.3 million.

---

Built by Yashas R · [github.com/yashasr21](https://github.com/yashasr21)
