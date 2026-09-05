-- Q2  Top 20 companies by complaint count, with their dispute rate.
-- Do the biggest names have the worst rates, or just the most complaints?
SELECT company,
       COUNT(*)                                   AS complaints,
       SUM(disputed)                              AS disputes,
       ROUND(100.0 * SUM(disputed) / COUNT(*), 1) AS dispute_rate_pct
FROM complaints
GROUP BY company
ORDER BY complaints DESC
LIMIT 20;
