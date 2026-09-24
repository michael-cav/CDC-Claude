"""Streamlit rendering for the header, KPI cards, and each tab."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import charts, config, data, metrics

PLOT_CONFIG = {"displaylogo": False}


def _show(fig) -> None:
    # theme=None keeps the accessible palette defined in config instead of Streamlit's theme colors.
    st.plotly_chart(fig, theme=None, config=PLOT_CONFIG)


def _empty_notice() -> None:
    st.info("No data to display for the current filters. Adjust the sidebar to see results.")


def _with_ties(names: tuple[str, ...]) -> str:
    return names[0] if len(names) == 1 else f"{names[0]} (+{len(names) - 1} tied)"


# --- Header and KPIs -------------------------------------------------------------
def render_header() -> None:
    st.title(config.APP_TITLE)
    st.write(config.INTRO)
    source = config.SOURCE_CITATION
    if config.SOURCE_URL:
        source += f" [Source link]({config.SOURCE_URL})"
    st.caption(f"Source: {source}")
    left, right = st.columns(2)
    left.warning(config.PROVISIONAL_NOTICE)
    right.info(config.COUNTS_NOTICE)


def _card(col, label: str, value: str, note: str, help_text: str) -> None:
    with col.container(border=True):
        st.metric(label, value, help=help_text)
        st.caption(note)


def render_kpis(k: metrics.Kpis, total_geographies: int) -> None:
    cols = st.columns(5)  # Streamlit stacks these on narrow screens
    _card(cols[0], "Total births", f"{k.total:,}", "current selection",
          "Sum of births over all selected geographies, months, and sexes.")
    _card(cols[1], "Geographies", f"{k.n_geographies:,}", f"of {total_geographies:,} available",
          "Number of states/geographies with data in the current selection.")
    _card(cols[2], "Avg. births per month", f"{k.avg_per_month:,.0f}", f"over {k.n_months} month(s)",
          "Total births divided by the number of selected months (all selected geographies combined).")
    _card(cols[3], "Highest geography", _with_ties(k.top_geographies), f"{k.top_geography_births:,} births",
          "Geography with the most births in the selection. Counts reflect population size.")
    _card(cols[4], "Highest month", _with_ties(k.top_months), f"{k.top_month_births:,} births",
          "Month with the most births across all selected geographies.")


# --- Tabs ------------------------------------------------------------------------
def render_overview(df: pd.DataFrame) -> None:
    if df.empty:
        return _empty_notice()
    left, right = st.columns([3, 2])
    with left:
        _show(charts.monthly_trend(metrics.births_by_month(df)))
        st.caption("Vertical axis starts at zero, so month-to-month differences are shown at true scale.")
    with right:
        _show(charts.state_ranking(metrics.births_by_state(df).head(10), "Top 10 geographies by births"))
        st.caption("Ranked by total births in the selection, not by birth rate.")


def render_geographic(df: pd.DataFrame) -> None:
    if df.empty:
        return _empty_notice()
    by_state = metrics.births_by_state(df)

    _show(charts.choropleth(by_state))
    st.caption("Darker shading means more births. Large states look darker mainly because they have "
               "more residents. Geographies outside the selection are left blank. "
               "The District of Columbia is too small to see on the map; find it in the ranking below.")

    st.subheader("Top and bottom geographies")
    requested = st.radio("Geographies per side", [3, 5, 10], index=1, horizontal=True)
    n = metrics.effective_n(len(by_state), requested)
    if n == 0:
        st.info("Select at least two geographies to compare the top and bottom of the selection.")
    else:
        if n < requested:
            st.caption(f"Showing {n} per side because only {len(by_state)} geographies are selected.")
        _show(charts.top_bottom(*metrics.top_bottom(by_state, requested)))

    st.subheader("Full ranking")
    _show(charts.state_ranking(by_state, f"All {len(by_state)} selected geographies, ranked by births"))


def render_monthly_sex(df: pd.DataFrame, sex_filter: str) -> None:
    if df.empty:
        return _empty_notice()

    st.subheader("Female and male births")
    if sex_filter != "Both":
        st.info(f"The infant-sex filter is set to {sex_filter.lower()} only. "
                "Choose Both in the sidebar to compare female and male births.")
    else:
        left, right = st.columns([3, 2])
        with left:
            _show(charts.sex_comparison(metrics.births_by_month_sex(df)))
        with right:
            overall = metrics.overall_sex_ratio(df)
            if overall is not None:
                st.metric("Male births per 100 female births", f"{overall:.1f}",
                          help="Ratio of male to female birth counts in the selection. "
                               "Above 100 means more male than female births.")
            _show(charts.sex_ratio(metrics.sex_ratio_by_month(df)))
        st.caption("Bars start at zero. The ratio compares counts of male and female births; it is not a rate.")

    st.subheader("State-by-month heatmap")
    share = st.toggle("Show each cell as a share of that state's births",
                      help="Removes the effect of state size so seasonal patterns are comparable across states.")
    _show(charts.heatmap(metrics.state_month_matrix(df, share=share), share))
    st.caption("Rows are ordered by total births. In share mode, each row sums to 100% "
               "across the selected months.")


def render_table(df: pd.DataFrame) -> None:
    if df.empty:
        return _empty_notice()
    term = st.text_input("Search by state or month", placeholder="e.g. Texas or March").strip()
    table = df[config.EXPORT_COLUMNS].copy()
    table[config.MONTH] = table[config.MONTH].astype(str)
    if term:
        hit = (table[config.STATE].astype(str).str.contains(term, case=False, regex=False)
               | table[config.MONTH].str.contains(term, case=False, regex=False))
        table = table[hit]

    st.caption(f"Showing {len(table):,} of {len(df):,} rows in the current filter selection. "
               "Sort chronologically with the Month # column.")
    if table.empty:
        st.info("No rows match that search. Try a different state or month name.")
    st.dataframe(
        table, hide_index=True,
        column_config={
            config.STATE: st.column_config.TextColumn("State"),
            config.MONTH: st.column_config.TextColumn("Month"),
            config.MONTH_CODE: st.column_config.NumberColumn("Month #", format="%d"),
            config.YEAR: st.column_config.NumberColumn("Year", format="%d"),
            config.SEX: st.column_config.TextColumn("Infant sex"),
            config.BIRTHS: st.column_config.NumberColumn("Births", format="localized"),
        },
    )
    st.download_button(f"Download {len(table):,} rows as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="natality_2025_filtered.csv", mime="text/csv", disabled=table.empty)


def render_about(full: pd.DataFrame, checks: list[data.Check]) -> None:
    st.subheader("About the data")
    st.markdown(
        f"- **Source:** {config.SOURCE_CITATION}\n"
        f"- **Coverage in this file:** {len(full):,} rows covering {full[config.STATE].nunique()} geographies "
        f"(50 states and DC), 12 months, and 2 infant-sex categories for {full[config.YEAR].iloc[0]}.\n"
        f"- **Total births in the file:** {int(full[config.BIRTHS].sum()):,}.\n"
        "- **Provisional:** figures are preliminary and may change when CDC revises them.\n"
        "- **Counts, not rates:** no population or fertility denominators are included, so differences "
        "between states mostly reflect population size. Do not read rankings as measures of fertility."
    )
    st.subheader("Columns")
    st.dataframe(pd.DataFrame({
        "Column": config.REQUIRED_COLUMNS,
        "Meaning": ["State or DC of residence as recorded in the file", "Month name",
                    "Month number (1-12), used for chronological order", "Reference year",
                    "Infant sex (Female or Male)", "Number of births (count)"],
    }), hide_index=True)
    st.subheader("Data validation")
    st.caption("Checks run every time the data load. Critical failures stop the dashboard.")
    st.dataframe(data.checks_to_frame(checks), hide_index=True)
