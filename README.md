# U.S. Births 2025 (Provisional): Streamlit Dashboard

Interactive dashboard for exploring provisional 2025 CDC birth **counts** (not rates) by
state, month, and infant sex. Built for undergraduate business-analytics students.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
Push this folder to GitHub (keep `data/` in the repo), then create an app pointing at `app.py`.
The data path is resolved relative to the code, so no configuration is needed.

## Structure
| File | Responsibility |
|---|---|
| `app.py` | Page setup and wiring only |
| `dashboard/config.py` | Paths, column names, month order, state abbreviations, palettes, text |
| `dashboard/data.py` | Cached loading, cleaning, validation checks |
| `dashboard/filters.py` | Sidebar, session state, reset/select-all, `apply_filters` |
| `dashboard/metrics.py` | KPI and aggregation functions (pure pandas) |
| `dashboard/charts.py` | One Plotly figure builder per chart |
| `dashboard/views.py` | Header, KPI cards, and one render function per tab |
| `tests/` | `pytest` tests for validation, mapping, ordering, filters, metrics |

## Maintenance notes
- **Confirm the citation:** edit `SOURCE_CITATION` / `SOURCE_URL` in `config.py` (marked TODO).
- **New data file:** replace the CSV in `data/` and keep the same columns. Validation on the
  About tab reports problems; restart the app or press `C` to clear the cache.
- **Adding a chart:** add a function in `metrics.py` (data) and `charts.py` (figure), then call it
  from a `render_*` function in `views.py`.
- Run tests with `pytest`.
