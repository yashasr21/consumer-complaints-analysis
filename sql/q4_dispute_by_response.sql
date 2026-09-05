-- Q4  Dispute rate by how the company closed the complaint.
-- The question worth asking: does "closed with monetary relief" actually
-- calm people down, or do people who get money still dispute?
SELECT company_response,
       COUNT(*)                                   AS complaints,
       SUM(disputed)                              AS disputes,
       ROUND(100.0 * SUM(disputed) / COUNT(*), 1) AS dispute_rate_pct
FROM complaints
WHERE company_response IS NOT NULL AND company_response <> ''
GROUP BY company_response
ORDER BY complaints DESC;
