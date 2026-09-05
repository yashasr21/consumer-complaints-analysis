-- Q4  Which products actually end up costing money?
-- Relief rate by product and sub-product. Volume and cost do not rank the
-- same way, and that gap is the finding worth putting in front of a team.
SELECT product,
       COUNT(*)                                          AS complaints,
       SUM(monetary_relief)                              AS relief_cases,
       ROUND(100.0 * SUM(monetary_relief) / COUNT(*), 1) AS relief_rate_pct
FROM complaints
WHERE product IS NOT NULL AND product <> ''
GROUP BY product
ORDER BY complaints DESC;
