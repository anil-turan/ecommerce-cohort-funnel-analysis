"""Confidence intervals and significance tests for funnel conversion rates.

The headline recommendation in this project's README ("shift budget from
Paid Ads to Referral") rests on Referral's conversion rate being genuinely
higher, not on a lucky small sample -- Referral has by far the fewest
signups (483, vs Paid Ads' 2,078), so its rate has the widest uncertainty
band of any channel. This module checks that honestly:

    Wilson score interval  -- CI for a single proportion. Preferred over the
        normal-approximation ("Wald") interval used in most intro stats
        material because it stays well-behaved for small n or a proportion
        near 0 or 1 (Wilson, 1927) -- both apply here (Referral's n=483,
        Social Media's subscribe rate is under 5%).
    Two-proportion z-test  -- whether two channels' conversion rates differ
        by more than sampling noise would produce, using the pooled
        proportion under the null of no difference (standard textbook
        approach; scipy.stats supplies the normal CDF/quantile, the
        pooling and test statistic are implemented here).
"""

from __future__ import annotations

from scipy import stats


def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> dict:
    """Wilson score confidence interval for a single proportion."""
    if n == 0:
        return {"phat": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}

    z = stats.norm.ppf(1 - alpha / 2)
    phat = successes / n
    denom = 1 + z**2 / n
    centre = phat + z**2 / (2 * n)
    margin = z * ((phat * (1 - phat) / n + z**2 / (4 * n**2)) ** 0.5)

    return {
        "phat": phat,
        "ci_low": (centre - margin) / denom,
        "ci_high": (centre + margin) / denom,
        "n": n,
    }


def two_proportion_test(
    successes_a: int, n_a: int, successes_b: int, n_b: int, alpha: float = 0.05
) -> dict:
    """Two-sample z-test for a difference in proportions (b - a).

    Uses the pooled proportion for the standard error under the null
    hypothesis of no difference (for the p-value), and the unpooled
    standard error for the confidence interval on the observed difference
    -- the standard textbook split between the two.
    """
    p_a = successes_a / n_a
    p_b = successes_b / n_b
    p_pool = (successes_a + successes_b) / (n_a + n_b)

    se_pooled = (p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b)) ** 0.5
    diff = p_b - p_a
    z = diff / se_pooled if se_pooled > 0 else float("inf") if diff != 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    z_crit = stats.norm.ppf(1 - alpha / 2)
    se_unpooled = (p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b) ** 0.5
    ci_low = diff - z_crit * se_unpooled
    ci_high = diff + z_crit * se_unpooled

    return {
        "rate_a": p_a,
        "rate_b": p_b,
        "diff": diff,
        "z": z,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "significant": bool(p_value < alpha),
    }
