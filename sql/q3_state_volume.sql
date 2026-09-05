-- Q3  Complaints by state, as a share of the total.
--
-- Per-capita is the honest version of this question and it needs population
-- data this repo does not ship. To add it: download state population from
-- census.gov, save as data/raw/state_population.csv with columns
-- state,population and load it as a table called state_population, then
-- uncomment the join below. Until then this is volume only - say so in the
-- README rather than implying California has the angriest consumers.
SELECT state,
       COUNT(*)                                                   AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total,
       ROUND(100.0 * SUM(disputed) / COUNT(*), 1)                 AS dispute_rate_pct
       -- , ROUND(1000000.0 * COUNT(*) / p.population, 1) AS per_million
FROM complaints c
-- LEFT JOIN state_population p ON p.state = c.state
WHERE state IS NOT NULL AND state <> ''
GROUP BY state
HAVING COUNT(*) >= 100
ORDER BY complaints DESC;
