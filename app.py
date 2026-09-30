"""
RESTAURANT PERFORMANCE INTELLIGENCE  |  Executive Management Dashboard
=======================================================================
Run:      pip install streamlit pandas plotly numpy
          streamlit run app.py
Data:     areas.csv, menu.csv (required) and orders.csv, order_items.csv,
          platforms.csv (optional) in the same folder as app.py.
Nothing is hard-coded: every number is calculated from the CSV files each time
the app runs, so replacing a CSV updates the dashboard.

Terminology used throughout
  * Order Weight  = analytical demand-weight variable (areas.csv), not an order count.
  * Popularity    = analytical popularity score (menu.csv), not units sold.
  * Recorded ...  = measured from orders.csv / order_items.csv (real transactions).
  * Net revenue   = gross sales minus platform commission. It is NOT profit: food,
                    labour and delivery costs are not in the data.
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="Restaurant Performance Intelligence", page_icon="🍽️",
                   layout="wide", initial_sidebar_state="expanded")

BASE_DIR = Path(__file__).parent

# ----------------------------------------------------------------------------
# Visual identity (keep in sync with the CSS below)
# ----------------------------------------------------------------------------
INK, MUTED, BG, PANEL, LINE = "#e8ecf4", "#8f9bb3", "#0b1220", "#131d33", "#24304d"
GOLD, TEAL, BLUE, CORAL, VIOLET = "#e2b25f", "#41c9b4", "#5b8def", "#ef7a6c", "#9b8cf0"
SEQUENCE = [TEAL, GOLD, BLUE, CORAL, VIOLET, "#7fd1ff", "#f2c94c", "#b0bec5"]

CSS = """
<style>
.stApp{background:radial-gradient(1100px 560px at 88% -8%,#1b2b52 0%,rgba(27,43,82,0) 62%),linear-gradient(180deg,#0b1220 0%,#0d1526 100%);color:#e8ecf4;font-family:Inter,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
.block-container{padding-top:2rem;padding-bottom:3rem;max-width:1560px}
section[data-testid="stSidebar"]{background:#0a101e;border-right:1px solid #24304d}
section[data-testid="stSidebar"] *{color:#e8ecf4}
.stApp label p,.stApp .stMarkdown p{color:#e8ecf4}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:#8f9bb3!important}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,[data-baseweb="base-input"]{background:#131d33!important;border-color:#24304d!important;color:#e8ecf4!important}
[data-baseweb="popover"] ul,[data-baseweb="menu"],div[data-baseweb="calendar"]{background:#131d33!important;color:#e8ecf4!important}
li[role="option"],li[role="option"] *{color:#e8ecf4!important}
li[role="option"]:hover{background:#1c2a4a!important}
[data-baseweb="tag"]{background:#1c2a4a!important}
.stButton button,.stDownloadButton button{background:#131d33;color:#e8ecf4;border:1px solid #2f3e63;border-radius:10px;transition:all .2s}
.stButton button:hover,.stDownloadButton button:hover{border-color:#e2b25f;color:#e2b25f;background:#16223d}
div[role="radiogroup"] label p{font-size:.85rem}
.hdr{display:flex;justify-content:space-between;align-items:flex-end;gap:2rem;flex-wrap:wrap;padding-bottom:1.1rem;border-bottom:1px solid #24304d;margin-bottom:1.4rem}
.hdr-t{font-size:1.9rem;font-weight:800;letter-spacing:.14em;color:#fff;line-height:1.15}
.hdr-s{font-size:1rem;color:#e2b25f;letter-spacing:.06em;margin-top:.3rem;font-weight:600}
.hdr-tag{font-size:.8rem;color:#8f9bb3;letter-spacing:.22em;margin-top:.35rem;text-transform:uppercase}
.hdr-m{text-align:right;font-size:.78rem;color:#8f9bb3;line-height:1.7}
.hdr-m b{color:#e8ecf4;font-weight:600}
.kpi-h{font-size:.68rem;letter-spacing:.2em;color:#8f9bb3;margin:1.1rem 0 .55rem;text-transform:uppercase}
.kpi{background:linear-gradient(160deg,#16223d,#111a2e);border:1px solid #24304d;border-top:3px solid var(--accent);border-radius:16px;padding:16px 18px;min-height:112px;box-shadow:0 6px 22px rgba(0,0,0,.28)}
.kpi-l{font-size:.66rem;letter-spacing:.16em;color:#8f9bb3;text-transform:uppercase}
.kpi-v{font-size:1.6rem;font-weight:700;margin-top:8px;color:#fff;line-height:1.15}
.kpi-s{font-size:.74rem;color:#8f9bb3;margin-top:5px}
.sec{margin:2.8rem 0 1rem;padding-bottom:.65rem;border-bottom:1px solid #24304d}
.sec-t{font-size:1.05rem;font-weight:700;letter-spacing:.13em;color:#e2b25f}
.sec-s{color:#8f9bb3;font-size:.85rem;margin-top:3px}
.sub-t{font-size:.72rem;letter-spacing:.16em;color:#8f9bb3;text-transform:uppercase;margin:1.2rem 0 .5rem;font-weight:600}
.panel{background:linear-gradient(160deg,#16223d,#111a2e);border:1px solid #24304d;border-radius:18px;padding:20px 22px;margin-bottom:.4rem}
.panel-t{font-size:.9rem;font-weight:700;letter-spacing:.16em;color:#e2b25f;margin-bottom:.9rem}
.ins{background:#0f1729;border:1px solid #24304d;border-left:4px solid #41c9b4;border-radius:12px;padding:14px 16px;height:100%;min-height:150px}
.ins .tag{font-size:.6rem;letter-spacing:.16em;font-weight:700;color:#41c9b4}
.ins .tag.q{color:#e2b25f;margin-top:10px}
.ins .tx{font-size:.88rem;line-height:1.5;color:#e8ecf4;margin-top:3px}
.ins .fq{font-size:.8rem;line-height:1.45;color:#8f9bb3;margin-top:3px}
.note{background:rgba(226,178,95,.08);border:1px solid rgba(226,178,95,.28);color:#e8ecf4;border-radius:10px;padding:10px 14px;font-size:.8rem;line-height:1.5;margin:.6rem 0}
.tbl-wrap{overflow:auto;border:1px solid #24304d;border-radius:12px;background:#0f1729}
table.t{width:100%;border-collapse:collapse;font-size:.83rem}
table.t th{position:sticky;top:0;background:#16223d;color:#8f9bb3;text-transform:uppercase;font-size:.66rem;letter-spacing:.09em;padding:10px 12px;text-align:left;white-space:nowrap}
table.t td{padding:9px 12px;border-top:1px solid #1c2740;color:#e8ecf4;white-space:nowrap}
table.t th.n,table.t td.n{text-align:right}
table.t tr:hover td{background:#16223d}
.bar{position:relative;min-width:96px;height:22px;border-radius:6px;background:#1a2540;overflow:hidden}
.bar span{position:absolute;left:0;top:0;bottom:0;opacity:.6}
.bar b{position:relative;display:block;text-align:right;padding-right:8px;line-height:22px;font-weight:600}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;white-space:nowrap}
.pill.g{background:rgba(65,201,180,.15);color:#41c9b4}.pill.a{background:rgba(226,178,95,.16);color:#e2b25f}.pill.b{background:rgba(91,141,239,.16);color:#7fa6f5}.pill.r{background:rgba(239,122,108,.16);color:#ef7a6c}
.mx{background:#0f1729;border:1px solid #24304d;border-radius:12px;padding:12px 14px;text-align:center}
.mx-n{font-size:1.5rem;font-weight:700;color:#fff}.mx-l{font-size:.7rem;letter-spacing:.08em;color:#8f9bb3}
.foot{margin-top:3.5rem;padding-top:1rem;border-top:1px solid #24304d;text-align:center;color:#8f9bb3;font-size:.78rem;letter-spacing:.14em}
.side-t{font-size:.8rem;letter-spacing:.24em;font-weight:700;color:#e2b25f;margin-bottom:.4rem}
</style>
"""

# ----------------------------------------------------------------------------
# 1. DATA LOADING, COLUMN DETECTION AND CLEANING
# ----------------------------------------------------------------------------
# Every conceptual field lists the column names we accept (after lower-casing and
# turning spaces/dashes into underscores). "Preparation Time", "preparation_time"
# and "Preparation_Time" all normalise to the same key.
SCHEMAS = {
    "areas": dict(
        file="areas.csv", numeric=["distance", "order_weight"], keys=["area", "distance", "order_weight"],
        required={"area": ["area", "area_name", "zone"],
                  "distance": ["distance", "distance_km", "distance_in_km", "km"],
                  "order_weight": ["order_weight", "orderweight", "demand_weight", "weight"]}, optional={}),
    "menu": dict(
        file="menu.csv", numeric=["price", "prep_time", "popularity"], keys=["dish", "price", "prep_time", "popularity"],
        required={"dish": ["dish", "dish_name", "item", "menu_item"], "cuisine": ["cuisine"],
                  "category": ["category", "dish_category"],
                  "price": ["price", "price_aed", "unit_price"],
                  "prep_time": ["preparation_time", "prep_time", "prep_minutes", "prep_min", "preparation_minutes"],
                  "popularity": ["popularity", "popularity_score"]}, optional={}),
    "orders": dict(
        file="orders.csv", numeric=["gross_amount", "commission_amount", "net_revenue"],
        keys=["order_id", "order_datetime", "gross_amount"],
        dates=["order_datetime", "preparing_at", "ready_at", "dispatched_at", "completed_at"],
        required={"order_id": ["order_id", "id"],
                  "order_datetime": ["order_datetime", "order_time", "datetime", "created_at", "timestamp"],
                  "platform": ["platform"], "order_type": ["order_type", "fulfilment_type", "fulfillment_type"],
                  "area": ["area", "delivery_area"], "status": ["status", "order_status"],
                  "gross_amount": ["gross_amount", "gross", "gross_sales", "order_total"],
                  "commission_amount": ["commission_amount", "commission"],
                  "net_revenue": ["net_revenue", "net_amount", "net"]},
        optional={"channel_type": ["channel_type"], "preparing_at": ["preparing_at"], "ready_at": ["ready_at"],
                  "dispatched_at": ["dispatched_at"], "completed_at": ["completed_at"]}),
    "order_items": dict(
        file="order_items.csv", numeric=["quantity", "unit_price", "line_total"], keys=["order_id", "dish", "quantity", "line_total"],
        required={"order_id": ["order_id", "id"], "dish": ["dish", "dish_name", "item"],
                  "quantity": ["quantity", "qty"], "line_total": ["line_total", "total", "amount"]},
        optional={"unit_price": ["unit_price", "price"]}),
    "platforms": dict(
        file="platforms.csv", numeric=["commission_rate", "order_share", "pickup_share"], keys=["platform", "commission_rate"],
        required={"platform": ["platform"], "commission_rate": ["commission_rate", "commission"]},
        optional={"channel_type": ["channel_type"], "order_share": ["order_share"], "pickup_share": ["pickup_share"]}),
}
REQUIRED_TABLES = ["areas", "menu"]


def normalise(name) -> str:
    """'Preparation Time' / 'preparation-time' / 'Preparation_Time' -> 'preparation_time'."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


@st.cache_data(show_spinner=False)
def load_table(key: str, mtime: float):
    """Read, validate and clean one CSV. `mtime` is part of the cache key, so the data
    refreshes automatically whenever the file changes.
    Returns (dataframe | None, missing_columns, cleaning_notes, raw_column_names, error_text)."""
    spec = SCHEMAS[key]
    try:
        raw = pd.read_csv(BASE_DIR / spec["file"])
    except Exception as exc:   # unreadable / empty file
        return None, [], [], [], f"{spec['file']} could not be read ({exc})."
    raw.columns = [normalise(c) for c in raw.columns]
    raw = raw.dropna(how="all")                      # remove completely empty rows
    raw_columns = list(raw.columns)

    rename, missing = {}, []
    for canon, aliases in {**spec["required"], **spec["optional"]}.items():
        hit = next((a for a in [canon] + aliases if a in raw.columns), None)
        if hit:
            rename[hit] = canon
        elif canon in spec["required"]:
            missing.append(canon)
    if missing:
        return None, missing, [], raw_columns, ""

    df = raw.rename(columns=rename)[list(rename.values())].copy()
    notes = []
    for col in df.columns:                            # tidy text
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype("object").map(lambda v: v.strip() if isinstance(v, str) else v)
    for col in spec["numeric"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in spec.get("dates", []):
        if col in df:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    before = len(df)
    df = df.dropna(subset=spec["keys"])               # rows missing a key value cannot be analysed
    if len(df) < before:
        notes.append(f"{spec['file']}: {before - len(df)} row(s) with missing key values were excluded.")
    for col in ("cuisine", "category", "platform", "order_type", "status", "area"):
        if col in df:                                 # descriptive text: label rather than drop
            df[col] = df[col].fillna("Unspecified")
    return df.reset_index(drop=True), [], notes, raw_columns, ""


def enrich_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Add analysis columns. Cancelled orders are identified from the status text;
    everything else is treated as a completed sale."""
    o = orders.copy()
    o["is_cancelled"] = o["status"].astype(str).str.lower().str.contains("cancel")
    o["is_delivered"] = ~o["is_cancelled"]
    o["order_date"] = o["order_datetime"].dt.normalize()
    o["hour"] = o["order_datetime"].dt.hour
    o["weekday"] = o["order_datetime"].dt.day_name()

    def minutes(start: str, end: str):
        if start in o and end in o:
            return (o[end] - o[start]).dt.total_seconds() / 60
        return np.nan

    o["kitchen_min"] = minutes("preparing_at", "ready_at")          # kitchen time
    o["delivery_min"] = minutes("dispatched_at", "completed_at")    # rider leg
    o["total_min"] = minutes("order_datetime", "completed_at")      # order to completion
    for col in ("kitchen_min", "delivery_min", "total_min"):
        o.loc[o[col] < 0, col] = np.nan                              # negative = timestamp error
    return o


# ----------------------------------------------------------------------------
# 2. SMALL HELPERS (formatting, safe maths, HTML building blocks)
# ----------------------------------------------------------------------------
def aed(value, decimals: int = 0) -> str:
    return "n/a" if value is None or pd.isna(value) else f"AED {value:,.{decimals}f}"


def pct(value, decimals: int = 1) -> str:
    return "n/a" if value is None or pd.isna(value) else f"{value:.{decimals}f}%"


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Division that returns NaN (shown as n/a) instead of raising when the denominator is 0 or missing."""
    return numerator / denominator.where(denominator > 0)


def safe_corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
        return None
    return float(np.corrcoef(x[ok], y[ok])[0, 1])


def strength(r) -> str:
    return "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.4 else "weak"


def slider_bounds(series: pd.Series):
    lo, hi = int(np.floor(series.min())), int(np.ceil(series.max()))
    return (lo, hi if hi > lo else lo + 1)


def kpi(label, value, sub="", tip="", accent=TEAL) -> str:
    return (f'<div class="kpi" title="{html.escape(tip)}" style="--accent:{accent}"><div class="kpi-l">{html.escape(label)}</div>'
            f'<div class="kpi-v">{html.escape(str(value))}</div><div class="kpi-s">{html.escape(sub)}</div></div>')


def section(number, title, subtitle=""):
    head = f"{number}. {title}" if number else title
    st.markdown(f'<div class="sec"><div class="sec-t">{html.escape(head)}</div><div class="sec-s">{html.escape(subtitle)}</div></div>',
                unsafe_allow_html=True)


def sub_title(text, tip=""):
    hint = f' <span title="{html.escape(tip)}" style="cursor:help">ⓘ</span>' if tip else ""
    st.markdown(f'<div class="sub-t">{html.escape(text)}{hint}</div>', unsafe_allow_html=True)


def note(text):
    st.markdown(f'<div class="note">{html.escape(text)}</div>', unsafe_allow_html=True)


def table_html(df, formats=None, bars=None, pills=None, max_height=None) -> str:
    """A styled HTML table (looks the same in any Streamlit theme).
    formats: {column: function(value)->safe text}   bars: {column: (max_value, colour)}
    pills:   {column: function(value)->css class}   Text from the CSV is always HTML-escaped."""
    formats, bars, pills = formats or {}, bars or {}, pills or {}
    numeric = {c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])}
    head = "".join(f'<th class="{"n" if c in numeric else ""}">{html.escape(str(c))}</th>' for c in df.columns)
    body = []
    for row in df.itertuples(index=False):
        cells = []
        for col, value in zip(df.columns, row):
            if pd.isna(value):
                text = "&mdash;"
            elif col in formats:
                text = formats[col](value)
            else:
                text = html.escape(str(value))
            if col in bars and not pd.isna(value):
                top, colour = bars[col]
                width = 0 if not top else max(0, min(100, float(value) / top * 100))
                text = f'<div class="bar"><span style="width:{width:.0f}%;background:{colour}"></span><b>{text}</b></div>'
            elif col in pills and not pd.isna(value):
                text = f'<span class="pill {pills[col](value)}">{text}</span>'
            cells.append(f'<td class="{"n" if col in numeric else ""}">{text}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    style = f' style="max-height:{max_height}px"' if max_height else ""
    return f'<div class="tbl-wrap"{style}><table class="t"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def show_table(df, download_name=None, key=None, **kwargs):
    if df.empty:
        st.info("No records match the current filters.")
        return
    st.markdown(table_html(df, **kwargs), unsafe_allow_html=True)
    if download_name:
        st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"), file_name=download_name,
                           mime="text/csv", key=key or f"dl_{download_name}")


def finish(fig, title, height=380, legend=True):
    """One consistent professional look for every Plotly chart."""
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=16, color=INK)), height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=INK, size=12), margin=dict(l=10, r=10, t=58, b=10),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=LINE, font=dict(color=INK)), showlegend=legend,
        legend=dict(orientation="h", y=-0.2, x=0, title=dict(text=""), bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE)
    return fig


def _streamlit_supports_width_arg() -> bool:
    """`width="stretch"` replaced `use_container_width` in recent Streamlit releases."""
    try:
        major, minor = (int(x) for x in st.__version__.split(".")[:2])
        return (major, minor) >= (1, 50)
    except Exception:
        return False


def show_chart(fig, key):
    config = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}
    if _streamlit_supports_width_arg():
        st.plotly_chart(fig, width="stretch", theme=None, key=key, config=config)
    else:
        st.plotly_chart(fig, use_container_width=True, theme=None, key=key, config=config)


def add_trendline(fig, x, y):
    """Straight-line fit through the points. Returns the correlation, or None when
    there are too few points / no spread to fit safely."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.ptp(x[ok]) == 0:
        return None
    slope, intercept = np.polyfit(x[ok], y[ok], 1)
    xs = np.array([x[ok].min(), x[ok].max()])
    fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Linear trend (observed)",
                             line=dict(color=MUTED, dash="dot", width=2), hoverinfo="skip"))
    return safe_corr(x[ok], y[ok])


# ----------------------------------------------------------------------------
# 3. FILTERS AND ANALYSIS (all calculated from the filtered data)
# ----------------------------------------------------------------------------
POSITIONS = ["High Price / High Popularity", "Lower Price / High Popularity",
             "High Price / Lower Popularity", "Lower Price / Lower Popularity"]
POSITION_CLASS = dict(zip(POSITIONS, ["g", "b", "a", "r"]))
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def filter_menu(menu, f):
    m = menu[menu["price"].between(*f["price"]) & menu["popularity"].between(*f["popularity"])]
    if f["cuisine"] != "All":
        m = m[m["cuisine"] == f["cuisine"]]
    if f["category"] != "All":
        m = m[m["category"] == f["category"]]
    return m.copy()


def filter_areas(areas, f):
    a = areas[areas["distance"].between(*f["distance"])]
    if f["area"] != "All":
        a = a[a["area"] == f["area"]]
    return a.copy()


def filter_orders(orders, areas_f, f, geo_narrowed):
    """Date and platform filters always apply. When the Area or Distance filter is
    narrowed, only delivery orders in the remaining areas are kept (pickup orders have
    no delivery area or distance)."""
    o = orders[orders["order_date"].between(f["date"][0], f["date"][1])]
    if f["platforms"]:
        o = o[o["platform"].isin(f["platforms"])]
    if geo_narrowed:
        o = o[(o["order_type"].str.lower() != "pickup") & o["area"].isin(areas_f["area"])]
    return o.copy()


def add_menu_metrics(menu_f, items_f):
    """Menu rows plus the Popularity-to-Prep-Time Index and (if order lines exist) recorded sales."""
    m = menu_f.copy()
    m["pp_index"] = safe_ratio(m["popularity"], m["prep_time"])       # Popularity / Prep Time
    if items_f is not None:
        sold = items_f.groupby("dish").agg(units=("quantity", "sum"), item_sales=("line_total", "sum"))
        m = m.merge(sold, left_on="dish", right_index=True, how="left")
        m[["units", "item_sales"]] = m[["units", "item_sales"]].fillna(0)
    return m


def add_position(m):
    """Menu positioning against the MEDIAN price and MEDIAN popularity of the filtered menu.
    At or above the median counts as High. Positioning only, not profitability."""
    price_med, pop_med = m["price"].median(), m["popularity"].median()
    high_price, high_pop = m["price"] >= price_med, m["popularity"] >= pop_med
    m = m.copy()
    m["position"] = np.select(
        [high_price & high_pop, ~high_price & high_pop, high_price & ~high_pop], POSITIONS[:3], default=POSITIONS[3])
    return m, price_med, pop_med


def add_area_metrics(areas_f, orders_f):
    a = areas_f.copy()
    a["dd_index"] = safe_ratio(a["order_weight"], a["distance"])       # Demand-to-Distance Index
    if orders_f is not None:
        d = orders_f[orders_f["is_delivered"] & (orders_f["order_type"].str.lower() != "pickup")]
        g = d.groupby("area").agg(recorded_orders=("order_id", "count"), net_revenue=("net_revenue", "sum"),
                                  delivery_min=("delivery_min", "mean"))
        a = a.merge(g, left_on="area", right_index=True, how="left")
        a[["recorded_orders", "net_revenue"]] = a[["recorded_orders", "net_revenue"]].fillna(0)
    return a


def group_menu(m, by):
    spec = dict(items=("dish", "count"), avg_price=("price", "mean"), avg_prep=("prep_time", "mean"),
                avg_pop=("popularity", "mean"))
    if "units" in m:
        spec.update(units=("units", "sum"), sales=("item_sales", "sum"))
    return m.groupby(by).agg(**spec).reset_index().sort_values("avg_pop", ascending=False, kind="stable")


def platform_summary(orders_f, platforms):
    g = orders_f.groupby("platform").agg(orders=("order_id", "count"), cancelled=("is_cancelled", "sum"))
    d = orders_f[orders_f["is_delivered"]].groupby("platform").agg(
        delivered=("order_id", "count"), gross=("gross_amount", "sum"),
        commission=("commission_amount", "sum"), net=("net_revenue", "sum"))
    t = g.join(d).fillna(0)
    t["share"] = t["orders"] / t["orders"].sum() * 100
    t["cancel_rate"] = t["cancelled"] / t["orders"] * 100
    t["eff_rate"] = safe_ratio(t["commission"], t["gross"]) * 100
    t["aov"] = safe_ratio(t["gross"], t["delivered"])
    if "channel_type" in orders_f:
        t["channel"] = orders_f.groupby("platform")["channel_type"].first()
    if platforms is not None:
        p = platforms.set_index("platform")
        t["contract_rate"] = p["commission_rate"] * 100
        if "order_share" in p:
            t["ref_share"] = p["order_share"] * 100
    return t.reset_index().sort_values("gross", ascending=False)


# ----------------------------------------------------------------------------
# 4. INSIGHT GENERATION (observations only; no unsupported conclusions)
# ----------------------------------------------------------------------------
def names(frame, column, n=3):
    return ", ".join(frame[column].head(n).astype(str))


def build_insights(areas_x, menu_x, pos, orders_f, plat):
    """Each item = (what the data shows, what management may want to investigate)."""
    out = []
    price_med, pop_med = pos
    prep_med = menu_x["prep_time"].median()

    if len(areas_x) >= 2 and areas_x["order_weight"].sum() > 0:                       # demand concentration
        a = areas_x.sort_values("order_weight", ascending=False)
        total, top_n = a["order_weight"].sum(), min(3, len(a))
        near = a[a["distance"] <= a["distance"].median()]["order_weight"].sum() / total * 100
        out.append((f"{a.iloc[0]['area']} has the highest order weight ({a.iloc[0]['order_weight'] / total * 100:.0f}% of the total) "
                    f"and the top {top_n} areas hold {a.head(top_n)['order_weight'].sum() / total * 100:.0f}%. Areas within the "
                    f"median distance ({a['distance'].median():.1f} km) hold {near:.0f}% of order weight.",
                    "Check whether this concentration holds across days, hours and platforms."))

    if "recorded_orders" in areas_x and len(areas_x) >= 3:                              # weight vs recorded orders
        r = safe_corr(areas_x["order_weight"], areas_x["recorded_orders"])
        if r is not None:
            word = {"strong": "closely track", "moderate": "partly track", "weak": "only weakly track"}[strength(r)]
            out.append((f"Recorded delivered orders {word} the analytical order weight across areas (correlation r = {r:.2f}).",
                        "Confirm how order weight is derived before using it as a stand-in for actual demand."))

    if not menu_x.empty:                                                              # cuisine popularity
        c = group_menu(menu_x, "cuisine")
        lead = c.iloc[0]
        text = f"{lead['cuisine']} has the highest average popularity score ({lead['avg_pop']:.1f}) across {int(lead['items'])} menu item(s)."
        if "units" in c and c["units"].sum() > 0:
            top_units = c.sort_values("units", ascending=False).iloc[0]
            text += (f" Recorded units are highest for {top_units['cuisine']} ({int(top_units['units']):,})." if top_units["cuisine"] != lead["cuisine"]
                     else " It also has the highest recorded units.")
        out.append((text, "Compare the popularity score with recorded sales before adjusting the menu."))

    if plat is not None and plat["gross"].sum() > 0:                                  # channel commission
        total_comm, total_gross = plat["commission"].sum(), plat["gross"].sum()
        with_comm = plat[plat["commission"] > 0]
        text = (f"Platform commission totals {aed(total_comm)} ({total_comm / total_gross * 100:.1f}% of {aed(total_gross)} gross sales). ")
        if not with_comm.empty:
            big = with_comm.sort_values("commission", ascending=False).iloc[0]
            text += f"{big['platform']} accounts for {big['commission'] / total_comm * 100:.0f}% of it."
        out.append((text, "Compare net revenue per order across channels; costs beyond commission are not in the data."))

    hi_pop = menu_x[menu_x["popularity"] >= pop_med]                                  # popularity vs prep time
    slow = hi_pop[hi_pop["prep_time"] > prep_med].sort_values("popularity", ascending=False)
    quick = hi_pop[hi_pop["prep_time"] <= prep_med].sort_values("pp_index", ascending=False)
    if not hi_pop.empty:
        text = f"{len(slow)} of {len(hi_pop)} higher-popularity items need more than the median preparation time ({prep_med:.0f} min)"
        text += f"; examples: {names(slow, 'dish')}." if len(slow) else "."
        if len(quick):
            text += f" {len(quick)} combine higher popularity with median-or-lower prep time."
        out.append((text, "Potential operational attention area: slower, popular items during peak hours."))

    if orders_f is not None and not orders_f.empty:                                   # fulfilment and cancellations
        d = orders_f[orders_f["is_delivered"]]
        text = f"{orders_f['is_cancelled'].mean() * 100:.1f}% of recorded orders were cancelled."
        if d["total_min"].notna().any():
            text += f" Delivered orders average {d['total_min'].mean():.0f} min from order to completion."
        out.append((text, "Review cancellation patterns by platform and hour to see where they cluster."))
    return out[:6]


def build_investigation(areas_x, menu_x, pos, plat):
    price_med, pop_med = pos
    prep_med = menu_x["prep_time"].median()
    items = []
    if not areas_x.empty:
        top = areas_x.sort_values("order_weight", ascending=False)
        r = safe_corr(areas_x["distance"], areas_x["order_weight"])
        text = f"Evaluate demand concentration in the highest order-weight areas ({names(top, 'area')})."
        if r is not None:
            text += f" Distance and order weight show a {strength(r)} {'negative' if r < 0 else 'positive'} association (r = {r:.2f}); the data alone does not show that distance is the cause."
        items.append(text)
    hi = menu_x[menu_x["popularity"] >= pop_med]
    slow = hi[hi["prep_time"] > prep_med].sort_values("popularity", ascending=False)
    if len(slow):
        items.append(f"Review high-popularity items with longer preparation times ({names(slow, 'dish')}) as potential operational attention areas.")
    quick = hi[hi["prep_time"] <= prep_med].sort_values("pp_index", ascending=False)
    if len(quick):
        items.append(f"Evaluate highly popular, quick-to-prepare items ({names(quick, 'dish')}) for potential bundle or add-on opportunities.")
    weak = menu_x[(menu_x["popularity"] < pop_med)].sort_values("popularity")
    if len(weak):
        hp = int(((menu_x["price"] >= price_med) & (menu_x["popularity"] < pop_med)).sum())
        items.append(f"Review lower-popularity items ({names(weak, 'dish')}) in relation to pricing, prep time and menu positioning; {hp} sit in the High Price / Lower Popularity position.")
    if plat is not None and plat["gross"].sum() > 0:
        agg = plat[plat["commission"] > 0]
        share = agg["gross"].sum() / plat["gross"].sum() * 100
        items.append(f"Examine channel mix: commission-bearing platforms account for {share:.0f}% of gross sales. Compare net revenue per order and cancellation rates by channel.")
    return items[:5]


# ----------------------------------------------------------------------------
# 5. CHART BUILDERS
# ----------------------------------------------------------------------------
HOVER_DISH = ("<b>%{customdata[0]}</b><br>Cuisine: %{customdata[1]}<br>Category: %{customdata[2]}<br>"
              "Price: AED %{customdata[3]:,.1f}<br>Preparation time: %{customdata[4]:,.0f} min<br>"
              "Popularity: %{customdata[5]:,.0f}<extra></extra>")
DISH_FIELDS = ["dish", "cuisine", "category", "price", "prep_time", "popularity"]


def fig_demand_by_area(a):
    d = a.sort_values("order_weight", ascending=False)
    fig = go.Figure(go.Bar(
        x=d["order_weight"], y=d["area"], orientation="h", marker_color=TEAL, text=d["order_weight"],
        textposition="outside", customdata=d["distance"],
        hovertemplate="<b>%{y}</b><br>Order weight: %{x}<br>Distance: %{customdata} km<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(range=[0, d["order_weight"].max() * 1.15])
    return finish(fig, "Demand Concentration by Area", height=400, legend=False)


def fig_distance_vs_demand(a):
    fig = go.Figure(go.Scatter(
        x=a["distance"], y=a["order_weight"], mode="markers+text", text=a["area"], textposition="top center",
        textfont=dict(size=10, color=MUTED), name="Area",
        marker=dict(size=a["order_weight"], sizemode="area", sizeref=2 * max(a["order_weight"].max(), 1) / (34 ** 2),
                    color=GOLD, opacity=0.85, line=dict(color=BG, width=1)),
        hovertemplate="<b>%{text}</b><br>Distance: %{x} km<br>Order weight: %{y}<extra></extra>"))
    r = add_trendline(fig, a["distance"], a["order_weight"])
    fig.update_xaxes(title="Distance (km)")
    fig.update_yaxes(title="Order weight", rangemode="tozero")
    return finish(fig, "Distance vs Demand", height=400, legend=False), r


def fig_weight_vs_recorded(a):
    d = a.sort_values("order_weight", ascending=False)
    w = d["order_weight"] / d["order_weight"].sum() * 100
    total = d["recorded_orders"].sum()
    o = d["recorded_orders"] / total * 100 if total else d["recorded_orders"] * 0
    fig = go.Figure([
        go.Bar(x=d["area"], y=w, name="Analytical order weight (share %)", marker_color=TEAL,
               hovertemplate="<b>%{x}</b><br>Order weight share: %{y:.1f}%<extra></extra>"),
        go.Bar(x=d["area"], y=o, name="Recorded delivered orders (share %)", marker_color=GOLD, customdata=d["recorded_orders"],
               hovertemplate="<b>%{x}</b><br>Recorded order share: %{y:.1f}%<br>Recorded orders: %{customdata:,.0f}<extra></extra>")])
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Share of total (%)")
    return finish(fig, "Order Weight vs Recorded Orders", height=380)


def fig_time_view(o, mode):
    d = o[o["is_delivered"]]
    if mode == "Day of week":
        g = d.groupby("weekday").agg(net=("net_revenue", "sum"), orders=("order_id", "count")).reindex(WEEKDAYS).dropna(how="all")
        x = g.index
    elif mode == "Hour of day":
        g = d.groupby("hour").agg(net=("net_revenue", "sum"), orders=("order_id", "count"))
        x = [f"{int(h):02d}:00" for h in g.index]
    else:
        g = d.groupby("order_date").agg(net=("net_revenue", "sum"), orders=("order_id", "count"))
        x = g.index
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=g["net"], name="Net revenue (AED)", marker_color=TEAL, opacity=0.85,
                         hovertemplate="%{x}<br>Net revenue: AED %{y:,.0f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=g["orders"], name="Delivered orders", mode="lines+markers",
                             line=dict(color=GOLD, width=2.5), hovertemplate="%{x}<br>Orders: %{y:,.0f}<extra></extra>"), secondary_y=True)
    fig.update_yaxes(title_text="Net revenue (AED)", secondary_y=False)
    fig.update_yaxes(title_text="Orders", secondary_y=True, showgrid=False)
    return finish(fig, f"Net Revenue and Orders: {mode}", height=380)


def fig_platform_split(t):
    d = t.sort_values("gross", ascending=False)
    fig = go.Figure([
        go.Bar(x=d["platform"], y=d["net"], name="Net revenue", marker_color=TEAL,
               hovertemplate="<b>%{x}</b><br>Net revenue: AED %{y:,.0f}<extra></extra>"),
        go.Bar(x=d["platform"], y=d["commission"], name="Platform commission", marker_color=CORAL,
               hovertemplate="<b>%{x}</b><br>Commission: AED %{y:,.0f}<extra></extra>")])
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title="AED (delivered orders)")
    return finish(fig, "Gross Sales Split: Net Revenue vs Commission", height=380)


def fig_bar_avg(df, x, y, title, colour, fmt=".1f", height=340):
    d = df.sort_values(y, ascending=False)
    fig = go.Figure(go.Bar(x=d[x], y=d[y], marker_color=colour, text=d[y], texttemplate="%{text:" + fmt + "}",
                           textposition="outside", hovertemplate="<b>%{x}</b><br>%{y:" + fmt + "}<extra></extra>"))
    fig.update_yaxes(range=[0, d[y].max() * 1.18 if d[y].max() > 0 else 1], showgrid=True)
    return finish(fig, title, height=height, legend=False)


def dish_scatter(m, x, y, title, cmap, size=None, height=440):
    kwargs = dict(size=size, size_max=24) if size else {}
    fig = px.scatter(m, x=x, y=y, color="cuisine", color_discrete_map=cmap, custom_data=DISH_FIELDS, **kwargs)
    fig.update_traces(hovertemplate=HOVER_DISH, marker=dict(opacity=0.85, line=dict(width=1, color=BG),
                                                              **({} if size else {"size": 11})))
    return finish(fig, title, height=height)


def corner_labels(fig, labels):
    """labels: {(x, y): text} in paper coordinates (0-1)."""
    for (x, y), text in labels.items():
        fig.add_annotation(xref="paper", yref="paper", x=x, y=y, text=text, showarrow=False, font=dict(size=11, color=MUTED),
                           xanchor="right" if x > 0.5 else "left", yanchor="top" if y > 0.5 else "bottom")


def fig_price_vs_popularity(m, price_med, pop_med, cmap):
    fig = dish_scatter(m, "price", "popularity", "Menu Positioning: Price vs Popularity", cmap, height=470)
    fig.add_vline(x=price_med, line=dict(color=MUTED, dash="dot", width=1))
    fig.add_hline(y=pop_med, line=dict(color=MUTED, dash="dot", width=1))
    corner_labels(fig, {(0.99, 0.99): POSITIONS[0], (0.01, 0.99): POSITIONS[1], (0.99, 0.01): POSITIONS[2], (0.01, 0.01): POSITIONS[3]})
    fig.update_xaxes(title="Price (AED)")
    fig.update_yaxes(title="Popularity score")
    return fig


def fig_popularity_vs_prep(m, prep_med, pop_med, cmap):
    fig = dish_scatter(m, "prep_time", "popularity", "Popularity vs Preparation Time", cmap, size="price", height=470)
    fig.add_vline(x=prep_med, line=dict(color=MUTED, dash="dot", width=1))
    fig.add_hline(y=pop_med, line=dict(color=MUTED, dash="dot", width=1))
    corner_labels(fig, {(0.01, 0.99): "Popular / quicker prep", (0.99, 0.99): "Popular / longer prep: potential operational attention",
                        (0.99, 0.01): "Lower popularity / longer prep: potential operational attention"})
    fig.update_xaxes(title="Preparation time (min)")
    fig.update_yaxes(title="Popularity score")
    return fig


def fig_popularity_vs_units(m, cmap):
    fig = dish_scatter(m, "popularity", "units", "Popularity Score vs Recorded Units Sold", cmap, height=470)
    fig.update_traces(hovertemplate=HOVER_DISH.replace("<extra>", "<br>Recorded units: %{y:,.0f}<extra>"))
    r = add_trendline(fig, m["popularity"], m["units"])
    fig.update_xaxes(title="Popularity score (analytical)")
    fig.update_yaxes(title="Recorded units sold", rangemode="tozero")
    return fig, r


def fig_fulfilment_by_hour(o):
    d = o[o["is_delivered"]].groupby("hour").agg(kitchen=("kitchen_min", "mean"), total=("total_min", "mean"))
    x = [f"{int(h):02d}:00" for h in d.index]
    fig = go.Figure([
        go.Scatter(x=x, y=d["kitchen"], name="Kitchen time (prep start to ready)", mode="lines+markers", line=dict(color=TEAL, width=2.5),
                   hovertemplate="%{x}<br>Kitchen: %{y:.1f} min<extra></extra>"),
        go.Scatter(x=x, y=d["total"], name="Order to completion", mode="lines+markers", line=dict(color=GOLD, width=2.5),
                   hovertemplate="%{x}<br>Order to completion: %{y:.1f} min<extra></extra>")])
    fig.update_yaxes(title="Average minutes", rangemode="tozero")
    return finish(fig, "Recorded Fulfilment Time by Hour of Day", height=380)


def fig_delivery_vs_distance(a):
    d = a.dropna(subset=["delivery_min"])
    fig = go.Figure(go.Scatter(x=d["distance"], y=d["delivery_min"], mode="markers+text", text=d["area"], textposition="top center",
                               textfont=dict(size=10, color=MUTED), marker=dict(size=12, color=BLUE, line=dict(color=BG, width=1)),
                               name="Area", hovertemplate="<b>%{text}</b><br>Distance: %{x} km<br>Avg delivery leg: %{y:.1f} min<extra></extra>"))
    r = add_trendline(fig, d["distance"], d["delivery_min"])
    fig.update_xaxes(title="Distance (km)")
    fig.update_yaxes(title="Average delivery leg (min)", rangemode="tozero")
    return finish(fig, "Recorded Delivery Time vs Distance", height=380, legend=False), r


# ----------------------------------------------------------------------------
# 6. PAGE SECTIONS
# ----------------------------------------------------------------------------
def num(v) -> str:
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"


F0, F1, F2 = (lambda v: f"{v:,.0f}"), (lambda v: f"{v:,.1f}"), (lambda v: f"{v:,.2f}")
FP = lambda v: f"{v:.1f}%"


def sidebar_filters(menu, areas, orders):
    d_lo, d_hi = slider_bounds(areas["distance"])
    p_lo, p_hi = slider_bounds(menu["popularity"])
    pr_lo, pr_hi = slider_bounds(menu["price"])
    dates = (orders["order_date"].min().date(), orders["order_date"].max().date()) if orders is not None else None
    defaults = {"f_cuisine": "All", "f_category": "All", "f_area": "All", "f_distance": (d_lo, d_hi),
                "f_popularity": (p_lo, p_hi), "f_price": (pr_lo, pr_hi), "f_platforms": []}
    if dates:
        defaults["f_date"] = dates

    def reset():
        for k, v in defaults.items():
            st.session_state[k] = v

    def options_ok(key, options):                      # forget stale choices if the CSV changed
        if st.session_state.get(key) not in options:
            st.session_state.pop(key, None)

    def range_ok(key, lo, hi):
        cur = st.session_state.get(key)
        if cur is not None and (cur[0] < lo or cur[1] > hi):
            st.session_state.pop(key, None)

    cuisines = ["All"] + sorted(menu["cuisine"].unique())
    categories = ["All"] + sorted(menu["category"].unique())
    area_names = ["All"] + sorted(areas["area"].unique())
    for key, opts in (("f_cuisine", cuisines), ("f_category", categories), ("f_area", area_names)):
        options_ok(key, opts)
    range_ok("f_distance", d_lo, d_hi); range_ok("f_popularity", p_lo, p_hi); range_ok("f_price", pr_lo, pr_hi)

    with st.sidebar:
        st.markdown('<div class="side-t">FILTERS</div>', unsafe_allow_html=True)
        f = {"cuisine": st.selectbox("Cuisine", cuisines, key="f_cuisine"),
             "category": st.selectbox("Category", categories, key="f_category"),
             "area": st.selectbox("Area", area_names, key="f_area"),
             "distance": st.slider("Distance range (km)", d_lo, d_hi, (d_lo, d_hi), key="f_distance"),
             "popularity": st.slider("Popularity range", p_lo, p_hi, (p_lo, p_hi), key="f_popularity"),
             "price": st.slider("Price range (AED)", pr_lo, pr_hi, (pr_lo, pr_hi), key="f_price")}
        if orders is not None:
            st.markdown('<div class="side-t" style="margin-top:1.2rem">ORDERS</div>', unsafe_allow_html=True)
            picked = st.date_input("Order dates", value=dates, min_value=dates[0], max_value=dates[1], key="f_date")
            picked = tuple(picked) if isinstance(picked, (list, tuple)) else (picked,)
            f["date"] = pd.Timestamp(picked[0]), pd.Timestamp(picked[-1] if len(picked) > 1 else dates[1])
            f["platforms"] = st.multiselect("Platform", sorted(orders["platform"].unique()), placeholder="All platforms", key="f_platforms")
        else:
            f["date"], f["platforms"] = None, []
        st.button("Reset filters", on_click=reset)
        st.caption("Cuisine, category, price and popularity shape the menu and item views. Area, distance, dates and platform "
                   "shape the order views. Narrowing area or distance excludes pickup orders, which have no delivery area.")
    f["geo_narrowed"] = f["area"] != "All" or f["distance"] != (d_lo, d_hi)
    return f


def render_header(mtimes, counts):
    updated = datetime.fromtimestamp(max(mtimes)).strftime("%d %b %Y, %H:%M")
    st.markdown(
        '<div class="hdr"><div><div class="hdr-t">RESTAURANT PERFORMANCE INTELLIGENCE</div>'
        '<div class="hdr-s">Executive Management Dashboard</div><div class="hdr-tag">Menu • Demand • Operations</div></div>'
        f'<div class="hdr-m">Data last updated: <b>{updated}</b><br>Records analysed: <b>{html.escape(counts)}</b></div></div>',
        unsafe_allow_html=True)


def render_kpis(menu, menu_f, areas_f, areas_x, orders_f):
    pop_scale = 10 if menu["popularity"].max() <= 10 else int(np.ceil(menu["popularity"].max()))
    top = areas_x.sort_values("order_weight", ascending=False).iloc[0]
    cards = [
        kpi("Total Service Areas", f"{len(areas_f)}", "in current selection", "Distinct areas in areas.csv after filters", TEAL),
        kpi("Menu Items", f"{len(menu_f)}", f"of {len(menu)} on the menu", "Dishes in menu.csv after filters", TEAL),
        kpi("Avg Price", aed(menu_f["price"].mean(), 2), f"median {aed(menu_f['price'].median(), 2)}", "Mean menu price of filtered dishes", GOLD),
        kpi("Avg Prep Time", f"{menu_f['prep_time'].mean():.1f} min", f"median {menu_f['prep_time'].median():.1f} min", "Standard preparation time per dish (menu.csv)", GOLD),
        kpi("Avg Popularity", f"{menu_f['popularity'].mean():.1f} / {pop_scale}", f"median {menu_f['popularity'].median():.1f}", "Analytical popularity score, not units sold", BLUE),
        kpi("Top Demand Area", str(top["area"]), f"order weight {num(top['order_weight'])}", "Area with the highest analytical order weight", BLUE)]
    for col, card in zip(st.columns(6, gap="medium"), cards):
        col.markdown(card, unsafe_allow_html=True)
    if orders_f is None:
        return
    d = orders_f[orders_f["is_delivered"]]
    n = len(orders_f)
    cards = [
        kpi("Orders Recorded", f"{n:,}", f"{len(d):,} completed", "All orders in orders.csv after filters", VIOLET),
        kpi("Gross Sales", aed(d["gross_amount"].sum()), "completed orders, before commission", "Sum of gross_amount for completed orders", VIOLET),
        kpi("Net Revenue", aed(d["net_revenue"].sum()), "after commission · not profit", "Gross sales minus platform commission. Costs are not in the data.", VIOLET),
        kpi("Avg Order Value", aed(d["gross_amount"].mean(), 2) if len(d) else "n/a", "gross, completed orders", "Mean gross_amount per completed order", CORAL),
        kpi("Cancellation Rate", pct(orders_f["is_cancelled"].mean() * 100) if n else "n/a", f"{int(orders_f['is_cancelled'].sum()):,} cancelled", "Share of recorded orders with a cancelled status", CORAL),
        kpi("Avg Fulfilment Time", f"{d['total_min'].mean():.0f} min" if d["total_min"].notna().any() else "n/a", "order to completion", "Mean minutes from order placed to completed", CORAL)]
    st.markdown('<div class="kpi-h">Recorded orders &amp; sales</div>', unsafe_allow_html=True)
    for col, card in zip(st.columns(6, gap="medium"), cards):
        col.markdown(card, unsafe_allow_html=True)


def render_insights(items):
    cards = "".join(
        f'<div class="ins"><div class="tag">WHAT THE DATA SHOWS</div><div class="tx">{html.escape(a)}</div>'
        f'<div class="tag q">FOR MANAGEMENT TO INVESTIGATE</div><div class="fq">{html.escape(b)}</div></div>' for a, b in items)
    st.markdown('<div class="sec" style="margin-top:2rem"></div>'
                '<div class="panel"><div class="panel-t">EXECUTIVE INSIGHTS</div>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px">{cards}</div></div>',
                unsafe_allow_html=True)
    st.caption("Observations calculated from the currently filtered data. They describe patterns and do not establish causes or financial outcomes.")


def render_demand(areas_x):
    section(1, "DEMAND & GEOGRAPHIC PERFORMANCE", "Analytical order weight and distance by service area, compared with recorded orders")
    left, right = st.columns(2, gap="large")
    with left:
        show_chart(fig_demand_by_area(areas_x), "ch_demand_area")
    with right:
        fig, r = fig_distance_vs_demand(areas_x)
        show_chart(fig, "ch_distance_demand")
        if r is not None:
            st.caption(f"Observed relationship: correlation between distance and order weight is r = {r:.2f} ({strength(r)}). "
                       "This describes an association in the data; it does not show that distance causes lower demand.")
    left, right = st.columns([1, 1], gap="large")
    with left:
        sub_title("Demand-to-Distance Index ranking", "Order Weight / Distance. Areas at 0 km distance show n/a.")
        st.caption("Analytical indicator comparing relative order weight with delivery distance; not a profitability measure.")
        t = areas_x.sort_values("dd_index", ascending=False, na_position="last")
        cols = {"area": "Area", "distance": "Distance (km)", "order_weight": "Order Weight", "dd_index": "Demand-to-Distance Index"}
        if "recorded_orders" in t:
            cols["recorded_orders"] = "Recorded Orders"
        t = t[list(cols)].rename(columns=cols)
        top = float(t["Demand-to-Distance Index"].max()) if t["Demand-to-Distance Index"].notna().any() else 0
        show_table(t, "demand_to_distance_index.csv", formats={"Distance (km)": num, "Order Weight": num, "Demand-to-Distance Index": F2,
                                                               "Recorded Orders": F0}, bars={"Demand-to-Distance Index": (top, TEAL)})
    with right:
        if "recorded_orders" in areas_x and areas_x["recorded_orders"].sum() > 0:
            show_chart(fig_weight_vs_recorded(areas_x), "ch_weight_recorded")
            r = safe_corr(areas_x["order_weight"], areas_x["recorded_orders"])
            if r is not None:
                st.caption(f"Correlation between analytical order weight and recorded delivered orders: r = {r:.2f} ({strength(r)}).")
        else:
            st.info("Recorded orders are not available for the current selection.")


def render_sales(orders_f, plat):
    section("", "SALES & CHANNEL PERFORMANCE", "Recorded orders · gross sales before commission · net revenue after platform commission (not profit)")
    if orders_f.empty or plat is None:
        st.info("No recorded orders match the current filters.")
        return
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        mode = st.radio("Time view", ["Daily", "Day of week", "Hour of day"], horizontal=True, key="time_view",
                        help="Switch how completed orders are grouped over time.")
        show_chart(fig_time_view(orders_f, mode), "ch_time_view")
    with right:
        st.write("")
        st.write("")
        show_chart(fig_platform_split(plat), "ch_platform_split")
    sub_title("Platform performance", "Recorded orders by platform. Effective commission = commission / gross sales on completed orders.")
    cols = {"platform": "Platform", "channel": "Channel", "orders": "Orders", "share": "Order Share", "ref_share": "Reference Share",
            "gross": "Gross Sales (AED)", "commission": "Commission (AED)", "eff_rate": "Effective Commission", "contract_rate": "Contract Rate",
            "net": "Net Revenue (AED)", "aov": "Avg Order Value (AED)", "cancel_rate": "Cancellation Rate"}
    t = plat[[c for c in cols if c in plat]].rename(columns=cols)
    fm = {"Orders": F0, "Order Share": FP, "Reference Share": FP, "Gross Sales (AED)": F0, "Commission (AED)": F0, "Effective Commission": FP,
          "Contract Rate": FP, "Net Revenue (AED)": F0, "Avg Order Value (AED)": F2, "Cancellation Rate": FP}
    show_table(t, "platform_performance.csv", formats=fm, bars={"Net Revenue (AED)": (float(t["Net Revenue (AED)"].max()), TEAL)})
    if "Reference Share" in t:
        st.caption("Reference Share and Contract Rate come from platforms.csv; Order Share and Effective Commission are measured from recorded orders.")


def menu_table(g, label):
    cols = {"cuisine" if label == "Cuisine" else "category": label, "items": "Items", "avg_price": "Avg Price (AED)",
            "avg_prep": "Avg Prep Time (min)", "avg_pop": "Avg Popularity", "units": "Recorded Units", "sales": "Recorded Sales (AED)"}
    return g[[c for c in cols if c in g]].rename(columns=cols)


def render_menu(menu_x, price_med, pop_med, cmap):
    section(2, "MENU PERFORMANCE", "Popularity, price and preparation profile by cuisine and category; recorded units come from order lines")
    fm = {"Items": F0, "Avg Price (AED)": F2, "Avg Prep Time (min)": F1, "Avg Popularity": F2, "Recorded Units": F0, "Recorded Sales (AED)": F0}
    left, right = st.columns(2, gap="large")
    for col, by, label, colour in ((left, "cuisine", "Cuisine", TEAL), (right, "category", "Category", GOLD)):
        g = group_menu(menu_x, by)
        with col:
            show_chart(fig_bar_avg(g, by, "avg_pop", f"Average Popularity by {label}", colour, ".2f"), f"ch_pop_{by}")
            show_table(menu_table(g, label), f"{by}_performance.csv", formats=fm, bars={"Avg Popularity": (float(g["avg_pop"].max()), colour)})
    sub_title("Price and popularity positioning")
    if "units" in menu_x:
        left, right = st.columns([1.25, 1], gap="large")
    else:
        left, right = st.container(), None
    with left:
        show_chart(fig_price_vs_popularity(menu_x, price_med, pop_med, cmap), "ch_price_pop")
        st.caption(f"Guide lines are the median price ({aed(price_med, 2)}) and median popularity ({pop_med:.1f}) of the filtered menu. Positioning only, not profitability.")
    if right is not None:
        with right:
            fig, r = fig_popularity_vs_units(menu_x, cmap)
            show_chart(fig, "ch_pop_units")
            if r is not None:
                st.caption(f"Correlation between popularity score and recorded units: r = {r:.2f} ({strength(r)}). Popularity is an analytical score, not sales volume.")


def render_kitchen(menu_x, pop_med, cmap, orders_f, areas_x):
    section(3, "KITCHEN OPERATIONS", "Standard preparation times from the menu, plus recorded kitchen and delivery timings from orders")
    prep_med = menu_x["prep_time"].median()
    left, right = st.columns(2, gap="large")
    with left:
        g = menu_x.groupby("category").agg(avg_prep=("prep_time", "mean")).reset_index()
        show_chart(fig_bar_avg(g, "category", "avg_prep", "Average Preparation Time by Category", BLUE, ".1f"), "ch_prep_category")
    with right:
        show_chart(fig_popularity_vs_prep(menu_x, prep_med, pop_med, cmap), "ch_pop_prep")
        st.caption(f"Guide lines: median prep time ({prep_med:.0f} min) and median popularity ({pop_med:.1f}). Items in the right-hand areas are potential operational attention areas, not confirmed bottlenecks.")
    if orders_f is not None and not orders_f.empty and orders_f["kitchen_min"].notna().any():
        left, right = st.columns(2, gap="large")
        with left:
            show_chart(fig_fulfilment_by_hour(orders_f), "ch_fulfil_hour")
        with right:
            if "delivery_min" in areas_x and areas_x["delivery_min"].notna().any():
                fig, r = fig_delivery_vs_distance(areas_x)
                show_chart(fig, "ch_delivery_distance")
                if r is not None:
                    st.caption(f"Correlation between distance and average delivery leg: r = {r:.2f} ({strength(r)}).")
    sub_title("Popularity-to-Prep-Time Index: top 10", "Popularity / Preparation Time. Analytical indicator only; not a profitability metric.")
    t = menu_x.sort_values(["pp_index", "popularity"], ascending=False, na_position="last").head(10)
    t = t[["dish", "cuisine", "category", "prep_time", "popularity", "pp_index"]]
    t.columns = ["Dish", "Cuisine", "Category", "Prep Time (min)", "Popularity", "Popularity-to-Prep-Time Index"]
    show_table(t, "popularity_to_prep_time_index.csv", formats={"Prep Time (min)": num, "Popularity": num, "Popularity-to-Prep-Time Index": F2},
               bars={"Popularity-to-Prep-Time Index": (float(t["Popularity-to-Prep-Time Index"].max()), TEAL)})
    note("Analytical indicator only; not a profitability metric.")


def render_top_items(menu_x, pop_scale):
    section("", "TOP PERFORMING MENU ITEMS", "Top 10 dishes ranked by popularity score (ties ordered by recorded units, when available)")
    sort_cols = ["popularity"] + (["units"] if "units" in menu_x else ["pp_index"])
    t = menu_x.sort_values(sort_cols, ascending=False, kind="stable").head(10).reset_index(drop=True)
    t.insert(0, "rank", range(1, len(t) + 1))
    cols = {"rank": "Rank", "dish": "Dish", "cuisine": "Cuisine", "category": "Category", "price": "Price (AED)",
            "prep_time": "Prep Time (min)", "popularity": "Popularity", "units": "Recorded Units"}
    t = t[[c for c in cols if c in t]].rename(columns=cols)
    show_table(t, "top_menu_items.csv", key="dl_top_items", formats={"Price (AED)": F2, "Prep Time (min)": num, "Popularity": num, "Recorded Units": F0},
               bars={"Popularity": (pop_scale, GOLD)})


def render_matrix(menu_x, price_med, pop_med):
    section(4, "MENU PERFORMANCE MATRIX", "Median price and median popularity split the filtered menu into four positioning groups")
    counts = menu_x["position"].value_counts()
    for col, pos in zip(st.columns(4, gap="medium"), POSITIONS):
        col.markdown(f'<div class="mx"><div class="mx-n">{int(counts.get(pos, 0))}</div><div class="mx-l">{pos.upper()}</div></div>', unsafe_allow_html=True)
    choice = st.selectbox("Show position", ["All positions"] + POSITIONS, key="matrix_position")
    t = menu_x if choice == "All positions" else menu_x[menu_x["position"] == choice]
    t = t.sort_values(["position", "popularity"], ascending=[True, False])
    cols = {"dish": "Dish", "cuisine": "Cuisine", "category": "Category", "price": "Price (AED)", "popularity": "Popularity",
            "prep_time": "Prep Time (min)", "position": "Position", "units": "Recorded Units"}
    t = t[[c for c in cols if c in t]].rename(columns=cols)
    show_table(t, "menu_performance_matrix.csv", key="dl_matrix", max_height=460,
               formats={"Price (AED)": F2, "Popularity": num, "Prep Time (min)": num, "Recorded Units": F0},
               pills={"Position": lambda v: POSITION_CLASS.get(v, "b")})
    note("Price and popularity positioning only. Profitability requires sales volume, food cost and contribution margin data.")
    st.caption(f"Thresholds: median price {aed(price_med, 2)} and median popularity {pop_med:.1f} of the filtered menu; values at or above the median count as High.")


def render_investigation(items):
    section("", "MANAGEMENT AREAS TO INVESTIGATE", "Areas for management investigation, based strictly on the current filtered data")
    body = "".join(f'<div style="margin:0 0 12px;line-height:1.55;font-size:.9rem"><span style="color:#e2b25f;font-weight:700">{i}.</span> {html.escape(x)}</div>'
                   for i, x in enumerate(items, 1))
    st.markdown(f'<div class="panel">{body}</div>', unsafe_allow_html=True)
    st.caption("These are prompts for further analysis, not recommendations or financial conclusions.")


def readiness(raw_cols):
    cols = {c for v in raw_cols.values() for c in v}
    has = lambda *k: any(x in c for c in cols for x in k)
    rows = [("Order ID", has("order_id"), "orders.csv, order_items.csv"),
            ("Date", has("order_datetime", "order_date", "timestamp"), "Order date-time in orders.csv"),
            ("Time", has("order_datetime", "order_time", "timestamp"), "Order date-time in orders.csv"),
            ("Quantity", has("quantity", "qty"), "order_items.csv"),
            ("Revenue", has("gross_amount", "net_revenue", "revenue"), "Gross and net of platform commission"),
            ("Discounts", has("discount"), "Not in the current files"),
            ("Delivery Fee", has("delivery_fee", "delivery_charge"), "Not in the current files"),
            ("Food Cost", has("food_cost", "cogs"), "Needed for margin analysis"),
            ("Labour Cost", has("labour", "labor"), "Needed for margin analysis"),
            ("Customer ID", has("customer_id", "customer"), "Needed for customer analysis"),
            ("New vs Returning Customer", has("returning", "new_customer", "repeat"), "Needed for retention analysis"),
            ("Customer Rating", has("rating"), "Not in the current files"),
            ("Delivery Time", has("dispatched_at") and has("completed_at"), "Derived from order timestamps")]
    return pd.DataFrame([(a, "Available in data" if ok else "Not in current data", n) for a, ok, n in rows],
                        columns=["Data Element", "Status", "Note"])


def render_scope(tables, raw_cols):
    section("", "DATA SCOPE & LIMITATIONS", "What this dashboard can and cannot support")
    supports = ["geographic demand weight", "menu pricing, popularity and preparation time"]
    if "orders" in tables:
        supports.append("recorded orders, gross sales, platform commission, net revenue, cancellations and order timestamps")
    if "order_items" in tables:
        supports.append("units sold by dish")
    lacks = "food cost, labour cost, delivery or rider cost, discounts and customer-level information"
    st.markdown(
        f'<div class="panel"><div style="line-height:1.65;font-size:.9rem">The current dataset supports analysis of {html.escape("; ".join(supports))}. '
        f'It does not contain {lacks}. Net revenue in this dashboard means gross sales less platform commission; it is not profit. '
        'Order Weight and Popularity are analytical scores, not measured order counts or sales volumes. '
        'Therefore, profitability and margin conclusions should not be inferred from this dashboard.</div></div>', unsafe_allow_html=True)
    sub_title("Recommended future data integration")
    show_table(readiness(raw_cols), pills={"Status": lambda v: "g" if v.startswith("Available") else "a"})


# ----------------------------------------------------------------------------
# 7. APPLICATION
# ----------------------------------------------------------------------------
def load_everything():
    """Load all CSVs, showing friendly messages. Stops the app if a required file is unusable."""
    tables, raw_cols, notes, mtimes, fatal = {}, {}, [], [], False
    for key, spec in SCHEMAS.items():
        path = BASE_DIR / spec["file"]
        required = key in REQUIRED_TABLES
        if not path.exists():
            (st.error if required else st.warning)(
                f"{'Required file' if required else 'Optional file'} **{spec['file']}** was not found in `{BASE_DIR}`."
                + ("" if required else " The sections that depend on it are hidden."))
            fatal = fatal or required
            continue
        mtimes.append(path.stat().st_mtime)
        df, missing, file_notes, cols, error = load_table(key, path.stat().st_mtime)
        raw_cols[key], notes = cols, notes + file_notes
        if error or missing or df is None or df.empty:
            reason = error or (f"missing required column(s): {', '.join(missing)}" if missing else "no usable rows after cleaning")
            (st.error if required else st.warning)(f"**{spec['file']}**: {reason}." + ("" if required else " Related sections are hidden."))
            fatal = fatal or required
            continue
        tables[key] = df
    if fatal:
        st.stop()
    if "order_items" in tables and "orders" not in tables:
        tables.pop("order_items")
        st.warning("order_items.csv needs orders.csv to identify completed orders, so it was not used.")
    return tables, raw_cols, notes, mtimes


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    tables, raw_cols, notes, mtimes = load_everything()
    menu, areas = tables["menu"], tables["areas"]
    orders = enrich_orders(tables["orders"]) if "orders" in tables else None
    items, platforms = tables.get("order_items"), tables.get("platforms")

    f = sidebar_filters(menu, areas, orders)
    menu_f, areas_f = filter_menu(menu, f), filter_areas(areas, f)
    orders_f = filter_orders(orders, areas_f, f, f["geo_narrowed"]) if orders is not None else None
    items_f = None
    if items is not None:
        items_f = items.merge(orders_f.loc[orders_f["is_delivered"], ["order_id"]], on="order_id", how="inner")
        items_f = items_f[items_f["dish"].isin(menu_f["dish"])]

    counts = f"{len(menu_f)}/{len(menu)} menu items · {len(areas_f)}/{len(areas)} areas"
    if orders_f is not None:
        counts += f" · {len(orders_f):,}/{len(orders):,} orders"
    render_header(mtimes, counts)
    for text in notes:
        st.caption(f"Data cleaning: {text}")

    if menu_f.empty or areas_f.empty:
        st.warning("No menu items or areas match the current filters. Widen the filters or press Reset filters in the sidebar.")
        st.stop()

    menu_x = add_menu_metrics(menu_f, items_f)
    menu_x, price_med, pop_med = add_position(menu_x)
    areas_x = add_area_metrics(areas_f, orders_f)
    plat = platform_summary(orders_f, platforms) if orders_f is not None and not orders_f.empty else None
    cmap = {c: SEQUENCE[i % len(SEQUENCE)] for i, c in enumerate(sorted(menu["cuisine"].unique()))}
    pop_scale = 10 if menu["popularity"].max() <= 10 else int(np.ceil(menu["popularity"].max()))

    render_kpis(menu, menu_f, areas_f, areas_x, orders_f)
    render_insights(build_insights(areas_x, menu_x, (price_med, pop_med), orders_f, plat))
    render_demand(areas_x)
    if orders_f is not None:
        render_sales(orders_f, plat)
    render_menu(menu_x, price_med, pop_med, cmap)
    render_kitchen(menu_x, pop_med, cmap, orders_f, areas_x)
    render_top_items(menu_x, pop_scale)
    render_matrix(menu_x, price_med, pop_med)
    render_investigation(build_investigation(areas_x, menu_x, (price_med, pop_med), plat))
    render_scope(tables, raw_cols)
    st.markdown('<div class="foot">Restaurant Performance Intelligence • Management Dashboard</div>', unsafe_allow_html=True)


main()
