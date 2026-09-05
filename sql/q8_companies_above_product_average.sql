-- Q8  Companies whose dispute rate sits well above the average for the
-- product they are being complained about. This is the query that produces a
-- name worth putting in front of an operations team.
WITH company_product AS (
    SELECT company,
           product,
           COUNT(*)                             AS complaints,
           1.0 * SUM(disputed) / COUNT(*)       AS rate
    FROM complaints
    GROUP BY company, product
    HAVING COUNT(*) >= 200
),
product_avg AS (
    SELECT product, 1.0 * SUM(disputed) / COUNT(*) AS product_rate
    FROM complaints
    GROUP BY product
)
SELECT cp.company,
       cp.product,
       cp.complaints,
       ROUND(100.0 * cp.rate, 1)                       AS dispute_rate_pct,
       ROUND(100.0 * pa.product_rate, 1)               AS product_avg_pct,
       ROUND(100.0 * (cp.rate - pa.product_rate), 1)   AS gap_pct_points
FROM company_product cp
JOIN product_avg pa ON pa.product = cp.product
ORDER BY gap_pct_points DESC
LIMIT 25;
