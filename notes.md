# Working notes

Two lines per session. What I tried, why it did not work. This file is for the
dead ends, and it stays in the repo.

---

**Session 1 — the target variable does not exist**

Downloaded the export and ran the profiler. It refused to read the file: two of the
columns I was expecting, *Consumer disputed?* and *Consumer consent provided?*, are
not in the export any more. The dispute field was the whole point of the project.

Options I weighed:
- Find an archived older copy of the file that still has the column. Would work, but
  it means analysing data that is years stale and cannot be refreshed.
- Switch to *Timely response?*. Exists everywhere, but it is about company operations,
  not about the complaint, and it is very heavily imbalanced.
- Switch to *Closed with monetary relief*, from Company response to consumer. Present
  for every year, and it is the outcome the dispute question was standing in for —
  which complaints end up costing money.

Went with monetary relief. Side effect: the target is no longer tied to a retired
field, so the most recent three years are usable, which is what I wanted originally.

One trap this created. *Company response to consumer* is where the label comes from,
so it cannot also be a feature. Took it out of the model inputs. If I had left it in,
the model would have scored beautifully and learned nothing.

---

**Session __ — reading fifty narratives**

`python src/04_text_features.py --sample 50`

Patterns I actually noticed:
-
-
-

Words I expected to matter but did not appear:
-

---

**Session __ —**

