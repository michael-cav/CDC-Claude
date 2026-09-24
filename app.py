"""Streamlit entry point: page setup and wiring. Run with `streamlit run app.py`."""
import streamlit as st

from dashboard import config, data, filters, metrics, views

st.set_page_config(page_title="U.S. Births 2025 (Provisional)", layout="wide")


def main() -> None:
    views.render_header()

    try:
        df, checks = data.load_data(str(config.DATA_PATH))
    except (FileNotFoundError, ValueError) as err:
        st.error(f"Could not load the data file: {err}")
        st.stop()
    if data.has_critical_failure(checks):
        st.error("The data failed critical validation checks, so the dashboard cannot display it safely.")
        st.dataframe(data.checks_to_frame(checks), hide_index=True)
        st.stop()

    states = sorted(df[config.STATE].unique())
    months = [m for m in config.MONTH_ORDER if m in set(df[config.MONTH].astype(str))]
    fs = filters.render_sidebar(states, months)
    filtered = filters.apply_filters(df, fs)

    kpis = metrics.compute_kpis(filtered)
    if kpis is None:
        st.warning(filters.describe_empty(fs))
    else:
        views.render_kpis(kpis, total_geographies=len(states))

    overview, geographic, monthly, table, about = st.tabs([
        "Overview", "Geographic Analysis", "Monthly and Sex Analysis",
        "Data Table and Download", "About the Data",
    ])
    with overview:
        views.render_overview(filtered)
    with geographic:
        views.render_geographic(filtered)
    with monthly:
        views.render_monthly_sex(filtered, fs.sex)
    with table:
        views.render_table(filtered)
    with about:
        views.render_about(df, checks)


main()
