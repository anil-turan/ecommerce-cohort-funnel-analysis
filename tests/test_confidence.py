import pytest

from src.confidence import two_proportion_test, wilson_ci


def test_wilson_ci_contains_point_estimate():
    result = wilson_ci(150, 500)
    assert result["ci_low"] < result["phat"] < result["ci_high"]


def test_wilson_ci_widens_for_smaller_n():
    small = wilson_ci(30, 100)
    large = wilson_ci(300, 1000)
    assert (small["ci_high"] - small["ci_low"]) > (large["ci_high"] - large["ci_low"])


def test_wilson_ci_stays_within_bounds_for_extreme_rate():
    result = wilson_ci(2, 100)  # 2% rate, small n -- exactly where Wald intervals misbehave
    assert 0.0 <= result["ci_low"]
    assert result["ci_high"] <= 1.0


def test_wilson_ci_zero_n_returns_nan():
    result = wilson_ci(0, 0)
    assert result["n"] == 0


def test_two_proportion_test_not_significant_for_equal_rates():
    result = two_proportion_test(100, 1000, 105, 1000)
    assert result["significant"] is False
    assert result["ci_low"] < 0 < result["ci_high"]


def test_two_proportion_test_significant_for_large_gap():
    # Mirrors this project's Referral (n=483, ~158 subscribed) vs Paid Ads
    # (n=2078, ~154 subscribed) comparison.
    result = two_proportion_test(154, 2078, 158, 483)
    assert result["significant"] is True
    assert result["diff"] > 0  # Referral (b) higher than Paid Ads (a)
    assert result["ci_low"] > 0


def test_two_proportion_test_diff_sign_convention():
    result = two_proportion_test(50, 500, 100, 500)  # b has double the rate
    assert result["rate_a"] == pytest.approx(0.10)
    assert result["rate_b"] == pytest.approx(0.20)
    assert result["diff"] == pytest.approx(0.10)


def test_two_proportion_test_p_value_decreases_with_larger_samples():
    # Same rates, same gap, but the larger-sample version should be at
    # least as significant (smaller or equal p-value) -- more data narrows
    # the CI around a real, fixed effect size.
    small = two_proportion_test(10, 100, 20, 100)
    large = two_proportion_test(100, 1000, 200, 1000)
    assert large["p_value"] <= small["p_value"]
