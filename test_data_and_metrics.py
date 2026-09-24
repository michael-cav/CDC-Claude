"""Tests for validation, mapping, ordering, filtering, and metrics. Run: pytest"""
import pandas as pd

from dashboard import config, data, filters, metrics
from dashboard.config import ABBR, BIRTHS, MONTH, SEX, STATE

DF, CHECKS = data.load_and_validate(str(config.DATA_PATH))


def _fs(states=None, months=None, sex="Both"):
    return filters.FilterState(tuple(states if states is not None else sorted(DF[STATE].unique())),
                               tuple(months if months is not None else config.MONTH_ORDER), sex)


def test_real_file_passes_all_checks():
    assert all(c.passed for c in CHECKS), data.checks_to_frame(CHECKS)
    assert len(DF) == 51 * 12 * 2


def test_abbreviations_complete_and_unique():
    assert len(config.STATE_ABBR) == 51 and len(set(config.STATE_ABBR.values())) == 51
    assert DF[ABBR].notna().all()


def test_months_are_chronological():
    assert list(DF[MONTH].cat.categories) == config.MONTH_ORDER
    monthly = metrics.births_by_month(DF)
    assert [str(m) for m in monthly[MONTH]] == config.MONTH_ORDER


def test_validation_flags_duplicates_and_bad_sex():
    bad = pd.concat([DF.astype({MONTH: str}), DF.astype({MONTH: str}).iloc[[0]]], ignore_index=True)
    bad.loc[1, SEX] = "Unknown"
    failed = {c.name for c in data.validate(bad) if not c.passed}
    assert "No duplicate state-month-sex rows" in failed
    assert "Infant sex is only Female or Male" in failed


def test_filters_subset_and_empty():
    one = filters.apply_filters(DF, _fs(["Texas"], ["March"], "Female"))
    assert len(one) == 1 and one[STATE].iloc[0] == "Texas"
    assert filters.apply_filters(DF, _fs(states=[])).empty
    assert filters.apply_filters(DF, _fs(months=[])).empty
    assert "no months" in filters.describe_empty(_fs(months=[]))


def test_kpis_match_pandas_and_handle_empty():
    k = metrics.compute_kpis(DF)
    assert k.total == DF[BIRTHS].sum() and k.n_geographies == 51 and k.n_months == 12
    assert k.avg_per_month == k.total / 12
    assert k.top_geographies == ("California",)
    assert metrics.compute_kpis(DF.iloc[0:0]) is None


def test_heatmap_share_rows_sum_to_100():
    share = metrics.state_month_matrix(DF, share=True)
    assert ((share.sum(axis=1) - 100).abs() < 1e-9).all()
    assert list(share.columns) == config.MONTH_ORDER


def test_top_bottom_never_overlap():
    by_state = metrics.births_by_state(filters.apply_filters(DF, _fs(["Texas", "Ohio", "Utah"])))
    top, bottom = metrics.top_bottom(by_state, 10)
    assert len(top) == len(bottom) == 1 and top[STATE].iloc[0] == "Texas"
    assert metrics.top_bottom(by_state.head(1), 5)[0].empty
