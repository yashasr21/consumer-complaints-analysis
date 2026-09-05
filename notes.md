# Working notes

Two lines per session. What I tried, why it did not work. This file is for the
dead ends, and it stays in the repo.

---

**Before the first session — checking what the file actually contains**

Planned to keep the most recent three years, as the build guide suggested, and
predict whether a complaint was disputed. Those two do not go together. The
*Consumer disputed?* field was discontinued part-way through the database, so the
most recent years have no target variable in them at all. Narratives run the other
way: they only start appearing partway through, once CFPB began publishing them
with consumer consent.

So the usable rows are the overlap between "dispute outcome still recorded" and
"narrative published", which is a much narrower window than three years of recent
data. `src/02_filter.py` finds the window from the file rather than hard-coding
dates, so it will still be right if CFPB changes what it publishes again.

Considered switching the target to something that exists across all years —
*closed with monetary relief*, or *timely response = No* — which would let the
model use the full file. Kept dispute as the target because it is the outcome the
question is actually about. Worth mentioning as the alternative if asked.

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

