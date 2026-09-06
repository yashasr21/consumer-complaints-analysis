# One sentence per query

Written after looking at the output in `docs/query_output/`. If a query did not tell me
anything, that is recorded too — two of these came back degenerate, and that turned out to
matter more than some of the ones that worked.

**q1 — volume by product and year**
Volume grows across the window for every product, but the percentage-change column is not
usable as growth: the window starts in Sep 2023 and ends in Aug 2026, so the first and
last years are partial. The one movement a partial year cannot explain is credit reporting
falling from 912,743 complaints in 2025 to 4,818 in 2026 — a 99.5% collapse in the
category that makes up two thirds of the database, which needs an explanation from CFPB
before anything in the 2026 slice is trusted.

**q2 — top companies and their relief rates**
Volume and cost are almost inversely related at the top of the table: Equifax, TransUnion
and Experian together account for 69.2% of all complaints and 0.34% of all monetary
relief, while Bank of America accounts for 0.97% of complaints and 16.5% of all relief —
a seventeenfold concentration. Ranking companies by complaint count identifies almost
exactly the wrong ones to staff a review team against.

**q3 — complaints by state**
Texas, Florida and California generate a third of all complaints, but state relief rates
sit in a narrow band (0.9% in Georgia to 2.8% in California) that is almost certainly
product mix rather than geography, and without population data this is volume only — so
this query does not support any claim about which states' consumers fare better.

**q4 — relief rate by product**
Relief is concentrated in a tenth of the volume: prepaid card (19.8%), credit card (16.4%)
and checking or savings (12.6%) are 9.9% of complaints and 82.0% of all payouts, while
credit reporting is 71.8% of complaints and 0.1% relief — a hundredfold spread that turns
out to be the single largest effect in the whole project.

**q5 — relief rate by channel**
This query is degenerate and that is the finding: it returned a single row, Web, covering
all 2,315,601 rows, because CFPB only publishes narratives for web-submitted complaints.
Requiring a narrative silently restricted the entire analysis to one channel, so
`submitted_via` is a constant that contributes nothing to the model, and no conclusion here
generalises to phone, mail or referral complaints.

**q6 — median days to reach the company**
Also degenerate: the median is 0.0 days for every product, because CFPB forwards complaints
to the company on the day they arrive. `days_to_company` carries no information and should
be dropped from the feature set rather than left in looking useful.

**q7 — monthly trend for the largest issue types**
"Attempts to collect debt not owed" roughly doubled over the window, from a three-month
average of 1,214 in late 2023 to over 3,000 by late 2024, and the rolling average shows it
as steady growth rather than a single spike — but debt collection carries a 0.3% relief
rate, so this is a rising volume problem, not a rising cost problem.

**q8 — companies above their product's average**
This is the query that survives the product effect, and it finds real company-level
outliers: American Express pays out on 56.4% of prepaid card complaints against a 19.8%
product average, and Bank of America sits 2–3× above average in three separate product
lines (checking 40.2% vs 12.6%, credit card 38.2% vs 16.4%, money transfer 21.3% vs 3.8%),
which cannot be product mix and points at something in how that company handles
complaints. Coinbase appearing here at 25.1% against a 3.8% average also explains why
"coinbase" was one of the model's highest-weighted terms.
