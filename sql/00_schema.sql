-- Schema for the SaaS funnel + cohort/LTV case study.
-- Three tables: users (one row per signup), events (funnel steps:
-- signup/activated/subscribed), and subscriptions (ongoing billing with an
-- optional churn_date -- NULL means still active/censored at the data pull).

DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id             INTEGER PRIMARY KEY,
    signup_date         DATE NOT NULL,
    acquisition_channel TEXT NOT NULL
);

CREATE TABLE events (
    event_id    INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    event_name  TEXT NOT NULL CHECK (event_name IN ('signup', 'activated', 'subscribed')),
    event_date  DATE NOT NULL
);

CREATE TABLE subscriptions (
    subscription_id     INTEGER PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES users(user_id),
    acquisition_channel  TEXT NOT NULL,
    start_date           DATE NOT NULL,
    monthly_fee          REAL NOT NULL,
    churn_date           DATE  -- NULL = still subscribed (censored) as of the data pull
);

CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_name ON events(event_name);
CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_channel ON subscriptions(acquisition_channel);
