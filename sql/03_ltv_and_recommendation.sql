-- LTV and LTV:CAC by channel -- the query that turns funnel + retention
-- numbers into a budget recommendation.
--
-- CAC (customer acquisition cost) isn't in the transactional data -- it's a
-- marketing-spend number that lives in an ads platform / finance system.
-- The values below are illustrative but documented (matching
-- src/generator.py's CHANNELS constants exactly, so this query's output is
-- reproducible against the generated data): Paid Ads and Social Media are
-- the expensive-per-click channels; Referral is a low-cost incentive
-- program; Organic Search / Content-SEO sit in between.

WITH cac AS (
    SELECT 'Paid Ads' AS acquisition_channel, 45.0 AS estimated_cac
    UNION ALL SELECT 'Organic Search', 20.0
    UNION ALL SELECT 'Social Media', 35.0
    UNION ALL SELECT 'Content/SEO', 15.0
    UNION ALL SELECT 'Referral', 10.0
),
subscriber_tenure AS (
    SELECT
        subscription_id,
        acquisition_channel,
        monthly_fee,
        (JULIANDAY(COALESCE(churn_date, '2026-06-30')) - JULIANDAY(start_date)) / 30.0 AS tenure_months
    FROM subscriptions
),
channel_ltv AS (
    SELECT
        acquisition_channel,
        COUNT(*)                          AS n_subscribers,
        ROUND(AVG(monthly_fee), 2)        AS avg_monthly_fee,
        ROUND(AVG(tenure_months), 2)      AS avg_tenure_months,
        ROUND(AVG(monthly_fee * tenure_months), 2) AS avg_ltv
    FROM subscriber_tenure
    GROUP BY acquisition_channel
)
SELECT
    l.acquisition_channel,
    l.n_subscribers,
    l.avg_monthly_fee,
    l.avg_tenure_months,
    l.avg_ltv,
    c.estimated_cac,
    ROUND(l.avg_ltv / c.estimated_cac, 2) AS ltv_to_cac_ratio
FROM channel_ltv l
JOIN cac c ON c.acquisition_channel = l.acquisition_channel
ORDER BY ltv_to_cac_ratio DESC;
