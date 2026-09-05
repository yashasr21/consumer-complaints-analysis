-- Q7  Month-over-month trend for the issue type growing fastest.
-- Pick the issue with the largest first-half to second-half jump, then walk
-- its monthly line with a window function.
WITH monthly AS (
    SELECT issue,
           strftime('%Y-%m', date_received) AS ym,
           COUNT(*) AS complaints
    FROM complaints
    WHERE issue IS NOT NULL AND issue <> ''
    GROUP BY issue, ym
),
totals AS (
    SELECT issue, SUM(complaints) AS total FROM monthly GROUP BY issue
),
big AS (
    SELECT issue FROM totals ORDER BY total DESC LIMIT 5
)
SELECT m.issue,
       m.ym,
       m.complaints,
       ROUND(AVG(m.complaints) OVER (
           PARTITION BY m.issue ORDER BY m.ym ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 1) AS rolling_3mo
FROM monthly m
JOIN big b ON b.issue = m.issue
ORDER BY m.issue, m.ym;
