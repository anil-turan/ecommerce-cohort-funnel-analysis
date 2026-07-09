-- Funnel conversion: signup -> activated -> subscribed, overall and by
-- acquisition channel. This is the first place a "which channel is best"
-- question gets a wrong answer if you only look at raw signup volume.

-- Q1: Overall funnel
SELECT
    COUNT(DISTINCT u.user_id)                                                    AS signups,
    COUNT(DISTINCT CASE WHEN e.event_name = 'activated'  THEN e.user_id END)     AS activated,
    COUNT(DISTINCT CASE WHEN e.event_name = 'subscribed' THEN e.user_id END)     AS subscribed
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id;

-- Q2: Funnel conversion by acquisition channel -- volume vs. quality
SELECT
    u.acquisition_channel,
    COUNT(DISTINCT u.user_id)                                                    AS signups,
    COUNT(DISTINCT CASE WHEN e.event_name = 'activated'  THEN e.user_id END)     AS activated,
    COUNT(DISTINCT CASE WHEN e.event_name = 'subscribed' THEN e.user_id END)     AS subscribed,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN e.event_name = 'activated' THEN e.user_id END)
        / COUNT(DISTINCT u.user_id), 1)                                          AS activation_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN e.event_name = 'subscribed' THEN e.user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN e.event_name = 'activated' THEN e.user_id END), 0), 1)
                                                                                  AS subscribe_given_activated_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN e.event_name = 'subscribed' THEN e.user_id END)
        / COUNT(DISTINCT u.user_id), 1)                                          AS overall_conversion_pct
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY u.acquisition_channel
ORDER BY overall_conversion_pct DESC;

-- Q3: Time-to-convert -- median days from signup to each funnel step,
-- overall (spots friction: a long activation lag is an onboarding problem)
WITH step_dates AS (
    SELECT
        u.user_id,
        u.signup_date,
        MAX(CASE WHEN e.event_name = 'activated'  THEN e.event_date END)  AS activated_date,
        MAX(CASE WHEN e.event_name = 'subscribed' THEN e.event_date END)  AS subscribed_date
    FROM users u
    LEFT JOIN events e ON e.user_id = u.user_id
    GROUP BY u.user_id
)
SELECT
    AVG(julianday(activated_date) - julianday(signup_date))   AS avg_days_signup_to_activation,
    AVG(julianday(subscribed_date) - julianday(activated_date)) AS avg_days_activation_to_subscribe
FROM step_dates
WHERE activated_date IS NOT NULL;
