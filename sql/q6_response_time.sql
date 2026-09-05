-- Q6  Median days from complaint received to complaint sent to the company.
-- SQLite has no median function, so this takes the middle row per product
-- using a row number over an ordered partition.
WITH ranked AS (
    SELECT product,
           days_to_company,
           ROW_NUMBER() OVER (PARTITION BY product ORDER BY days_to_company) AS rn,
           COUNT(*)    OVER (PARTITION BY product)                           AS n
    FROM complaints
    WHERE days_to_company IS NOT NULL AND days_to_company >= 0
)
SELECT product,
       n                        AS complaints,
       AVG(days_to_company)     AS median_days
FROM ranked
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY product, n
ORDER BY median_days DESC;
