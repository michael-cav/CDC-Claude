"""Sidebar filters, session-state handling, and filter application."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from dashboard.config import MONTH, MONTH_ORDER, SEX, STATE

KEY_STATES, KEY_MONTHS, KEY_SEX = "filter_states", "filter_months", "filter_sex"
SEX_CHOICES = ["Both", "Female", "Male"]


@dataclass(frozen=True)
class FilterState:
    states: tuple[str, ...]
    months: tuple[str, ...]
    sex: str  # "Both", "Female", or "Male"


# --- Callbacks: session state must be changed in on_click, before widgets render ---
def _set_all(key: str, options: list[str]) -> None:
    st.session_state[key] = list(options)


def _reset(states: list[str], months: list[str]) -> None:
    st.session_state[KEY_STATES] = list(states)
    st.session_state[KEY_MONTHS] = list(months)
    st.session_state[KEY_SEX] = "Both"


def _describe(selected: tuple[str, ...], total: int, label: str) -> str:
    if not selected:
        return f"**{label}:** none selected"
    if len(selected) == total:
        return f"**{label}:** all {total}"
    if len(selected) <= 3:
        return f"**{label}:** {', '.join(selected)}"
    return f"**{label}:** {len(selected)} of {total}"


def render_sidebar(states: list[str], months: list[str]) -> FilterState:
    """Draw the sidebar and return the current selection (all selected by default)."""
    st.session_state.setdefault(KEY_STATES, list(states))
    st.session_state.setdefault(KEY_MONTHS, list(months))
    st.session_state.setdefault(KEY_SEX, "Both")

    with st.sidebar:
        st.header("Filters")
        st.button("Reset all filters", key="btn_reset", on_click=_reset, args=(states, months))

        sel_states = st.multiselect("States / geographies", states, key=KEY_STATES,
                                    help="Includes the 50 states and the District of Columbia.")
        st.button("Select all geographies", key="btn_all_states", on_click=_set_all,
                  args=(KEY_STATES, states))

        sel_months = st.multiselect("Months", months, key=KEY_MONTHS)
        st.button("Select all months", key="btn_all_months", on_click=_set_all,
                  args=(KEY_MONTHS, months))

        sex = st.radio("Infant sex", SEX_CHOICES, key=KEY_SEX, horizontal=True,
                       help="Choose Both to include and compare female and male births.")

        fs = FilterState(
            states=tuple(sorted(sel_states)),
            months=tuple(sorted(sel_months, key=MONTH_ORDER.index)),  # keep chronological order
            sex=sex,
        )
        with st.container(border=True):
            st.markdown("**Active filters**")
            st.markdown(_describe(fs.states, len(states), "Geographies"))
            st.markdown(_describe(fs.months, len(months), "Months"))
            st.markdown(f"**Infant sex:** {'both sexes' if sex == 'Both' else sex.lower() + ' only'}")
    return fs


def apply_filters(df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
    """Return the rows matching the selection. An empty selection yields no rows."""
    mask = df[STATE].isin(list(fs.states)) & df[MONTH].isin(list(fs.months))
    if fs.sex != "Both":
        mask &= df[SEX] == fs.sex
    return df[mask]


def describe_empty(fs: FilterState) -> str:
    """Explain why a selection returned no observations."""
    reasons = []
    if not fs.states:
        reasons.append("no geographies are selected")
    if not fs.months:
        reasons.append("no months are selected")
    why = " and ".join(reasons) if reasons else "the selected combination has no rows"
    return f"No observations match the current filters: {why}. Adjust the sidebar or use Reset all filters."
