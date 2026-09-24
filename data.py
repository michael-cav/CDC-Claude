"""Loading, cleaning, and validating the natality CSV."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from dashboard.config import (
    ABBR, BIRTHS, MONTH, MONTH_CODE, MONTH_ORDER, REQUIRED_COLUMNS, SEX, SEX_OPTIONS,
    STATE, STATE_ABBR, YEAR,
)


@dataclass(frozen=True)
class Check:
    """One validation result. Critical failures stop the app; others are shown as warnings."""
    name: str
    passed: bool
    detail: str
    critical: bool = True


def validate(df: pd.DataFrame) -> list[Check]:
    """Run data-quality checks on the raw (string-cleaned) frame."""
    checks: list[Check] = []

    def add(name: str, passed: bool, detail: str, critical: bool = True) -> None:
        checks.append(Check(name, bool(passed), detail, critical))

    n_null = int(df[REQUIRED_COLUMNS].isna().sum().sum())
    add("No missing values", n_null == 0, f"{n_null} missing cells")

    births = pd.to_numeric(df[BIRTHS], errors="coerce")
    births_ok = births.notna().all() and (births >= 0).all() and (births % 1 == 0).all()
    add("Births are non-negative whole numbers", births_ok,
        f"min {births.min():,.0f}, max {births.max():,.0f}")

    sexes = sorted(set(df[SEX].dropna()))
    add("Infant sex is only Female or Male", set(sexes) <= set(SEX_OPTIONS), f"found: {', '.join(sexes)}")

    expected_code = df[MONTH].map({m: i + 1 for i, m in enumerate(MONTH_ORDER)})
    add("Month names match month codes 1-12", expected_code.eq(df[MONTH_CODE]).all(),
        "month and month_code agree on every row")

    n_dups = int(df.duplicated([STATE, MONTH_CODE, SEX]).sum())
    add("No duplicate state-month-sex rows", n_dups == 0, f"{n_dups} duplicates")

    unmapped = sorted(set(df[STATE].dropna()) - set(STATE_ABBR))
    abbr_unique = len(set(STATE_ABBR.values())) == len(STATE_ABBR)
    add("Every geography maps to a unique postal abbreviation", not unmapped and abbr_unique,
        f"unmapped: {', '.join(unmapped)}" if unmapped else f"{df[STATE].nunique()} geographies mapped")

    years = sorted(df[YEAR].dropna().unique().tolist())
    add("Single reference year", len(years) == 1, f"year(s): {years}", critical=False)

    expected_rows = df[STATE].nunique() * len(MONTH_ORDER) * len(SEX_OPTIONS)
    add("Complete state x month x sex panel", len(df) == expected_rows,
        f"{len(df):,} rows found, {expected_rows:,} expected", critical=False)
    return checks


def has_critical_failure(checks: list[Check]) -> bool:
    return any(c.critical and not c.passed for c in checks)


def checks_to_frame(checks: list[Check]) -> pd.DataFrame:
    """Readable table for the About tab (text status, not color-only)."""
    def status(c: Check) -> str:
        return "Pass" if c.passed else ("FAIL" if c.critical else "Warning")
    return pd.DataFrame({"Check": [c.name for c in checks],
                         "Status": [status(c) for c in checks],
                         "Detail": [c.detail for c in checks]})


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add types and derived columns; month becomes an ordered categorical (chronological)."""
    df = df.copy()
    df[BIRTHS] = df[BIRTHS].astype("int64")
    df[MONTH] = pd.Categorical(df[MONTH], categories=MONTH_ORDER, ordered=True)
    df[ABBR] = df[STATE].map(STATE_ABBR)
    return df.sort_values([STATE, MONTH, SEX]).reset_index(drop=True)


def load_and_validate(path: str) -> tuple[pd.DataFrame, list[Check]]:
    """Read the CSV and return (data, checks). Raises on a missing file or missing columns."""
    raw = pd.read_csv(path, encoding="utf-8-sig")  # utf-8-sig strips the BOM in this file
    raw.columns = raw.columns.str.strip()
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    for col in (STATE, MONTH, SEX):
        raw[col] = raw[col].astype("string").str.strip()
    checks = validate(raw)
    return (raw if has_critical_failure(checks) else _enrich(raw)), checks


@st.cache_data(show_spinner="Loading data...")
def load_data(path: str) -> tuple[pd.DataFrame, list[Check]]:
    """Cached wrapper used by the app. The path is a str so it can be hashed."""
    return load_and_validate(path)
