-- Q5  Relief rate by the channel the complaint arrived on, with how long
-- people write. Someone who puts it in writing on the web has already made an
-- effort a phone caller has not. Worth checking whether that shows up.
SELECT submitted_via,
       COUNT(*)                                          AS complaints,
       ROUND(100.0 * SUM(monetary_relief) / COUNT(*), 1) AS relief_rate_pct,
       ROUND(AVG(narrative_len), 0)                      AS avg_words
FROM complaints
WHERE submitted_via IS NOT NULL AND submitted_via <> ''
GROUP BY submitted_via
ORDER BY complaints DESC;
