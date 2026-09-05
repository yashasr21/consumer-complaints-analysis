-- Q2  Top 20 companies by complaint count, with their relief rate.
-- Do the biggest names have the worst rates, or just the most complaints?
SELECT company,
       COUNT(*)                                   AS complaints,
       SUM(monetary_relief)                              AS relief_cases,
       ROUND(100.0 * SUM(monetary_relief) / COUNT(*), 1) AS relief_rate_pct
FROM complaints
GROUP BY company
ORDER BY complaints DESC
LIMIT 20;
