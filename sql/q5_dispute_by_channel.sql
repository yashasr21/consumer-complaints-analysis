-- Q5  Dispute rate by the channel the complaint arrived on.
-- Someone who posts on the web has already chosen to put it in writing;
-- someone who phones may not have. Worth checking whether that shows up.
SELECT submitted_via,
       COUNT(*)                                   AS complaints,
       ROUND(100.0 * SUM(disputed) / COUNT(*), 1) AS dispute_rate_pct,
       ROUND(AVG(narrative_len), 0)               AS avg_words
FROM complaints
WHERE submitted_via IS NOT NULL AND submitted_via <> ''
GROUP BY submitted_via
ORDER BY complaints DESC;
