-- Q1  Complaint volume by product and year. Which products are growing?
-- The year-on-year column is the point; raw counts alone hide the direction.
WITH by_year AS (
    SELECT product,
           CAST(strftime('%Y', date_received) AS INTEGER) AS yr,
           COUNT(*) AS complaints
    FROM complaints
    GROUP BY product, yr
)
SELECT product,
       yr,
       complaints,
       LAG(complaints) OVER (PARTITION BY product ORDER BY yr) AS prev_year,
       ROUND(
           100.0 * (complaints - LAG(complaints) OVER (PARTITION BY product ORDER BY yr))
           / NULLIF(LAG(complaints) OVER (PARTITION BY product ORDER BY yr), 0)
       , 1) AS pct_change
FROM by_year
ORDER BY product, yr;
