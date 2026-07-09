-- Subscription cohort retention (survival): of subscriptions that started
-- in month X, what % are still active (not yet churned) N months later?
-- Built with a recursive CTE to generate the 0..12 month-offset series, then
-- only counting a (cohort, offset) pair once that many months have actually
-- elapsed since start_date -- otherwise early cohorts would look
-- artificially more "retained" just because we haven't had time to observe
-- their churn yet.

WITH RECURSIVE month_offsets(n) AS (
    SELECT 0
    UNION ALL
    SELECT n + 1 FROM month_offsets WHERE n < 12
),
cohort AS (
    SELECT
        subscription_id,
        acquisition_channel,
        strftime('%Y-%m', start_date) AS cohort_month,
        start_date,
        churn_date
    FROM subscriptions
),
observable AS (
    SELECT
        c.cohort_month,
        o.n                                                                AS month_offset,
        c.subscription_id,
        CASE
            WHEN c.churn_date IS NULL THEN 1
            WHEN julianday(c.churn_date) > julianday(date(c.start_date, printf('+%d months', o.n))) THEN 1
            ELSE 0
        END                                                                AS is_retained
    FROM cohort c
    JOIN month_offsets o
        ON date(c.start_date, printf('+%d months', o.n)) <= '2026-06-30'
)
SELECT
    cohort_month,
    month_offset,
    COUNT(*)                                    AS cohort_size_observable,
    SUM(is_retained)                            AS retained,
    ROUND(100.0 * SUM(is_retained) / COUNT(*), 1) AS retention_pct
FROM observable
GROUP BY cohort_month, month_offset
ORDER BY cohort_month, month_offset;
