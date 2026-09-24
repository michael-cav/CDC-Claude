"""Static configuration: paths, column names, ordering, palettes, and user-facing text."""
from pathlib import Path

# Resolved relative to this file so the app works from any working directory
# (local runs, Streamlit Community Cloud, tests).
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "Provisional_Natality_2025_CDC1.csv"

# Column names as they appear in the CSV, plus one derived column.
STATE, MONTH, MONTH_CODE, YEAR, SEX, BIRTHS = (
    "state_of_residence", "month", "month_code", "year_code", "sex_of_infant", "births",
)
ABBR = "state_abbr"  # derived from STATE_ABBR below
REQUIRED_COLUMNS = [STATE, MONTH, MONTH_CODE, YEAR, SEX, BIRTHS]
EXPORT_COLUMNS = REQUIRED_COLUMNS  # CSV download keeps the original schema

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
SEX_OPTIONS = ["Female", "Male"]

# Explicit mapping (50 states + DC) so the choropleth never depends on fuzzy matching.
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# Palette: Okabe-Ito colors (colorblind-safe). Sex, rank, and totals use distinct hues
# so one color never carries two meanings.
SEX_COLORS = {"Female": "#E69F00", "Male": "#0072B2"}
TOTAL_COLOR = "#44546A"
TOP_COLOR, BOTTOM_COLOR = "#009E73", "#CC79A7"
SEQUENTIAL_SCALE = "Blues"  # single-hue scale for count magnitude (maps, heatmap)

# User-facing text
APP_TITLE = "U.S. Births by State, Month, and Infant Sex, 2025"
INTRO = (
    "Explore how birth counts differ across states, months, and infant sex. "
    "Use the sidebar filters to change the selection; every KPI, chart, and table updates to match."
)
# TODO: confirm the exact CDC product/table name, URL, and access date before publishing.
SOURCE_CITATION = "Centers for Disease Control and Prevention (CDC), provisional natality data for 2025."
SOURCE_URL = None
PROVISIONAL_NOTICE = "**Provisional data.** These 2025 figures are preliminary and may be revised by CDC."
COUNTS_NOTICE = (
    "**Birth counts, not birth rates.** Values are numbers of births, not births per 1,000 people. "
    "Larger states have more births mainly because they have more residents."
)
