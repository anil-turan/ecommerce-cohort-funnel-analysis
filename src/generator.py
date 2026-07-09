"""Synthetic SaaS product data generator: signups, a 3-step conversion
funnel (signup -> activated -> subscribed), and ongoing subscriptions with a
per-channel monthly churn hazard.

Channel quality is deliberately inverted from channel volume -- Paid Ads
brings the most signups but converts and retains worst; Referral brings the
fewest signups but converts and retains best. This is what makes the LTV:CAC
analysis surface a genuine "shift budget" recommendation rather than a
trivial "the biggest channel is best" result. Not real data: no public
dataset has this funnel/subscription shape with known ground truth, so every
number the analysis surfaces traces back to a parameter here.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

START_DATE = date(2024, 7, 1)
END_DATE = date(2026, 6, 30)
N_USERS = 6000

# channel: (signup_share, activation_rate, subscribe_rate_given_activated,
#           monthly_churn_hazard, avg_monthly_plan_price, estimated_cac)
CHANNELS = {
    "Paid Ads":       (0.35, 0.40, 0.20, 0.10, 30.0, 45.0),
    "Organic Search": (0.25, 0.55, 0.35, 0.06, 35.0, 20.0),
    "Social Media":   (0.20, 0.35, 0.15, 0.09, 25.0, 35.0),
    "Content/SEO":    (0.12, 0.60, 0.30, 0.05, 32.0, 15.0),
    "Referral":       (0.08, 0.70, 0.50, 0.03, 45.0, 10.0),
}


def _channel_frame() -> pd.DataFrame:
    return pd.DataFrame.from_dict(
        CHANNELS, orient="index",
        columns=["signup_share", "activation_rate", "subscribe_rate",
                "monthly_churn_hazard", "avg_plan_price", "estimated_cac"],
    ).rename_axis("acquisition_channel").reset_index()


def generate_saas_data(seed: int = 42) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    channel_df = _channel_frame()
    total_days = (END_DATE - START_DATE).days

    signup_offsets = np.sort(
        rng.triangular(0, total_days, total_days, size=N_USERS)
    ).astype(int)
    signup_dates = [START_DATE + timedelta(days=int(d)) for d in signup_offsets]
    channels = rng.choice(
        channel_df["acquisition_channel"], size=N_USERS, p=channel_df["signup_share"]
    )

    users_rows = []
    events_rows = []
    subs_rows = []
    sub_id = 1

    channel_params = channel_df.set_index("acquisition_channel")

    for uid in range(1, N_USERS + 1):
        signup_date = signup_dates[uid - 1]
        channel = channels[uid - 1]
        params = channel_params.loc[channel]

        users_rows.append({
            "user_id": uid, "signup_date": signup_date, "acquisition_channel": channel,
        })
        events_rows.append({
            "user_id": uid, "event_name": "signup", "event_date": signup_date,
        })

        if rng.random() >= params["activation_rate"]:
            continue
        activation_date = signup_date + timedelta(days=int(rng.integers(1, 14)))
        if activation_date > END_DATE:
            continue
        events_rows.append({
            "user_id": uid, "event_name": "activated", "event_date": activation_date,
        })

        if rng.random() >= params["subscribe_rate"]:
            continue
        subscribe_date = activation_date + timedelta(days=int(rng.integers(1, 14)))
        if subscribe_date > END_DATE:
            continue
        events_rows.append({
            "user_id": uid, "event_name": "subscribed", "event_date": subscribe_date,
        })

        # simulate monthly churn hazard from subscription start
        hazard = params["monthly_churn_hazard"]
        max_months = ((END_DATE - subscribe_date).days) // 30
        churn_month = None
        for m in range(max_months + 1):
            if rng.random() < hazard:
                churn_month = m
                break
        churn_date = (
            subscribe_date + timedelta(days=int(churn_month * 30))
            if churn_month is not None else None
        )

        fee_mean, fee_sigma = params["avg_plan_price"], params["avg_plan_price"] * 0.15
        monthly_fee = round(float(rng.normal(fee_mean, fee_sigma)), 2)
        monthly_fee = max(monthly_fee, 5.0)

        subs_rows.append({
            "subscription_id": sub_id,
            "user_id": uid,
            "acquisition_channel": channel,
            "start_date": subscribe_date,
            "monthly_fee": monthly_fee,
            "churn_date": churn_date,
        })
        sub_id += 1

    users = pd.DataFrame(users_rows)
    users["signup_date"] = pd.to_datetime(users["signup_date"])

    events = pd.DataFrame(events_rows)
    events["event_date"] = pd.to_datetime(events["event_date"])

    subscriptions = pd.DataFrame(subs_rows)
    subscriptions["start_date"] = pd.to_datetime(subscriptions["start_date"])
    subscriptions["churn_date"] = pd.to_datetime(subscriptions["churn_date"])

    return {"users": users, "events": events, "subscriptions": subscriptions,
            "channel_params": channel_df}
