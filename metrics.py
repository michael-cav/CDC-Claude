"""Pure aggregation functions (no Streamlit): KPIs and chart-ready tables."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from dashboard.config import ABBR, BIRTHS, MONTH, SEX, STATE

RATIO = "males_per_100_females"


@dataclass(frozen=True)
class Kpis:
    total: int
    n_geographies: int
    n_months: int
    avg_per_month: float
    top_geographies: tuple[str, ...]  # more than one name means a tie
    top_geography_births: int
    top_months: tuple[str, ...]
    top_month_births: int


def compute_kpis(df: pd.DataFrame) -> Kpis | None:
    """KPIs for the filtered data, or None when the selection is empty."""
    if df.empty:
        return None
    by_state = df.groupby(STATE, observed=True)[BIRTHS].sum()
    by_month = df.groupby(MONTH, observed=True)[BIRTHS].sum()
    total = int(df[BIRTHS].sum())
    return Kpis(
        total=total,
        n_geographies=int(by_state.size),
        n_months=int(by_month.size),
        avg_per_month=total / by_month.size,
        top_geographies=tuple(str(s) for s in by_state[by_state == by_state.max()].index),
        top_geography_births=int(by_state.max()),
        top_months=tuple(str(m) for m in by_month[by_month == by_month.max()].index),
        top_month_births=int(by_month.max()),
    )


def births_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Total births per month, in chronological order."""
    return df.groupby(MONTH, observed=True, as_index=False)[BIRTHS].sum()


def births_by_month_sex(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby([MONTH, SEX], observed=True, as_index=False)[BIRTHS].sum()


def births_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Total births per geography (with abbreviation), largest first."""
    out = df.groupby([STATE, ABBR], as_index=False)[BIRTHS].sum()
    out = out.astype({STATE: str, ABBR: str})
    return out.sort_values(BIRTHS, ascending=False).reset_index(drop=True)


def state_month_matrix(df: pd.DataFrame, share: bool = False) -> pd.DataFrame:
    """State x month table, rows ordered by total births. share=True gives % of each row."""
    m = df.pivot_table(index=STATE, columns=MONTH, values=BIRTHS, aggfunc="sum", observed=True)
    m.columns = m.columns.astype(str)  # plain labels; chronological order is preserved
    m.index = m.index.astype(str)
    m = m.loc[m.sum(axis=1).sort_values(ascending=False).index]
    if share:
        m = m.div(m.sum(axis=1), axis=0) * 100
    return m


def sex_ratio_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Male births per 100 female births, by month (empty if both sexes are not present)."""
    p = df.pivot_table(index=MONTH, columns=SEX, values=BIRTHS, aggfunc="sum", observed=True)
    if not {"Female", "Male"} <= set(p.columns):
        return pd.DataFrame(columns=[MONTH, RATIO])
    ratio = p["Male"] / p["Female"].where(p["Female"] > 0) * 100
    return ratio.rename(RATIO).reset_index()


def overall_sex_ratio(df: pd.DataFrame) -> float | None:
    totals = df.groupby(SEX, observed=True)[BIRTHS].sum()
    if {"Female", "Male"} <= set(totals.index) and totals["Female"] > 0:
        return float(totals["Male"] / totals["Female"] * 100)
    return None


def effective_n(n_geographies: int, requested: int) -> int:
    """Largest n <= requested such that the top n and bottom n do not overlap."""
    return max(0, min(requested, n_geographies // 2))


def top_bottom(by_state: pd.DataFrame, requested: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(top n, bottom n) from a frame sorted by births descending."""
    n = effective_n(len(by_state), requested)
    if n == 0:
        return by_state.iloc[0:0], by_state.iloc[0:0]
    return by_state.head(n), by_state.tail(n)
