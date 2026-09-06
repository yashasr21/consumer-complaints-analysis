# Working notes

What I tried, what broke, and what I decided. The dead ends stay in.

\---

**Checking the source before starting**

Ran the profiler on the fresh export and it refused to read the file. Two columns I was
expecting, *Consumer disputed?* and *Consumer consent provided?*, are not in the export
any more. The dispute field was the entire point of the project.

Options I weighed:

* Find an archived older copy that still has the column. Works, but it means analysing
data that is years stale and cannot be refreshed.
* Switch to *Timely response?*. Present everywhere, but it is about company operations,
not about the complaint, and it is very heavily imbalanced.
* Switch to *Closed with monetary relief*, from Company response to consumer. Present for
every year, and it is the outcome the dispute question was standing in for.

Went with monetary relief. Side effect: the target is no longer tied to a retired field,
so the most recent three years became usable, which is what I wanted originally.

The trap this created: *Company response to consumer* is where the label comes from, so it
cannot also be a feature. Took it out of the model inputs. Left in, the model would have
scored beautifully and learned nothing.

\---

**Profiling, 17.6 million rows**

Narratives are missing on 78.1% of rows and do not exist at all before 2015. The narrative
requirement, not the date window, is what shrinks this dataset — it drops 11.2 million
rows against the window's 4 million.

The relief rate is falling steadily: 9.1% in 2012, 4.1% in 2019, 0.9% in 2024. My
three-year window sits in the thin end at 1.78%. That also means the time-based split
trains on a period with roughly twice the base rate of the period it is tested on. Kept
the time split anyway because a random split would be worse, but it is a real limitation.

\---

**Reading narratives by hand**

First attempt: 50 at random. Useless. At a 1.78% base rate a random 50 contains about one
relief case, so I read fifty examples of the outcome I am *not* predicting and learned
nothing about the contrast. Rewrote the sampler to draw half from each class and
interleave them (`--compare 40`).

\- The ones that got paid described one specific incident with a real amount - an ATM

&#x20; that miscounted, a loan payoff that went wrong, a card charged after a fraud claim.

\- The ones that got an explanation were mostly credit-report letters that all started

&#x20; the same way and quoted FCRA and 15 USC 1681 back at the company.

\- I expected angry language and capital letters to matter. It was everywhere in both

&#x20; groups.

**The dashboard looked broken and was not**

Every panel on the published page said "Nothing here yet" even though the pipeline had
run and `figures.json` existed. Cause: pandas leaves `NaN` in empty cells — the first year
of the volume query has no previous year to compare against — and `json.dump` writes that
out as a bare `NaN`. That is not valid JSON, so the browser rejected the *entire file*,
not just that one value, and every panel fell back to its empty state.

Fixed by converting nulls to `None` before writing, and set `allow\_nan=False` so that if
it ever happens again the script fails loudly instead of producing a file that looks fine
and is not.

Lesson: an empty-state message is not proof that a stage did not run.

\---

**The result is suspicious in a useful way**

ROC AUC came out at 0.953, which is far too good for predicting a 1.78% event from
complaint text. Looked at relief rate by product: credit reporting 0.1%, prepaid card
19.8%. A hundredfold spread.

Selecting the three highest-rate products captures 82% of all relief cases from 9.9% of
volume. The model, flagging its top 10% by score, captures 80.3%. A `GROUP BY` matches
the machine learning model, which strongly suggests the model is mostly learning product
identity. The top-weighted TF-IDF terms back this up — many are company names rather than
descriptions of a problem.

Ran it three ways. Product only 5.69x lift, plus hand-built flags 6.92x, plus TF-IDF
8.02x. So product alone is about 71% of the lift and the text is the other 29% — my
suspicion was right in direction but I would have overstated it if I had written "the
text does nothing". Average precision doubling from 0.146 to 0.328 is the number that
convinced me the text is genuinely contributing rather than just reshuffling ties.

The odd row is product-only recall at 82.4%, higher than the full model's 80.2% despite
being a much worse model. A product-only model can only emit a few distinct scores, so
its top 10% is really "these product lines" and it sweeps in almost every relief case at
terrible precision. Reading recall alone would have made the worst model look best.

