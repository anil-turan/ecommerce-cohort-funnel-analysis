"""Tests for the synthetic SaaS funnel/subscription data generator."""

from src.generator import END_DATE, START_DATE, generate_saas_data


def test_referential_integrity():
    tables = generate_saas_data(seed=1)
    users, events, subs = tables["users"], tables["events"], tables["subscriptions"]
    assert set(events["user_id"]).issubset(set(users["user_id"]))
    assert set(subs["user_id"]).issubset(set(users["user_id"]))


def test_funnel_events_are_monotonic_subset():
    """Every subscribed user must have an activated event, and every
    activated user must have a signup event -- the funnel can't be skipped."""
    tables = generate_saas_data(seed=2)
    events = tables["events"]
    signup_users = set(events[events["event_name"] == "signup"]["user_id"])
    activated_users = set(events[events["event_name"] == "activated"]["user_id"])
    subscribed_users = set(events[events["event_name"] == "subscribed"]["user_id"])

    assert activated_users.issubset(signup_users)
    assert subscribed_users.issubset(activated_users)


def test_events_occur_within_window():
    tables = generate_saas_data(seed=3)
    events = tables["events"]
    assert events["event_date"].min().date() >= START_DATE
    assert events["event_date"].max().date() <= END_DATE


def test_subscription_start_matches_a_subscribed_event():
    tables = generate_saas_data(seed=4)
    events, subs = tables["events"], tables["subscriptions"]
    subscribed = events[events["event_name"] == "subscribed"]
    subscribed_dates = subscribed.set_index("user_id")["event_date"]
    merged = subs.merge(subscribed_dates.rename("event_date"), on="user_id")
    assert (merged["start_date"] == merged["event_date"]).all()


def test_referral_channel_converts_and_retains_better_than_paid_ads():
    """Sanity check the deliberate quality-vs-volume inversion that makes
    the LTV:CAC recommendation meaningful."""
    tables = generate_saas_data(seed=5)
    users, events, subs = tables["users"], tables["events"], tables["subscriptions"]

    def overall_conversion(channel):
        channel_users = set(users[users["acquisition_channel"] == channel]["user_id"])
        subscribed = events[(events["event_name"] == "subscribed")
                            & (events["user_id"].isin(channel_users))]
        return len(subscribed) / len(channel_users)

    assert overall_conversion("Referral") > overall_conversion("Paid Ads")

    def avg_tenure_days(channel):
        s = subs[subs["acquisition_channel"] == channel].copy()
        end = s["churn_date"].fillna(events["event_date"].max())
        return (end - s["start_date"]).dt.days.mean()

    assert avg_tenure_days("Referral") > avg_tenure_days("Paid Ads")
