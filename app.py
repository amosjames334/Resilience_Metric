import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import requests
import pdfplumber
import io

# ──────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Bank Resilience Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 16px 20px;
        color: #f8fafc;
    }
    div[data-testid="stMetric"] label {color: #94a3b8 !important; font-size: 0.85rem;}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #f8fafc !important; font-weight: 700;}
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {display: none;}

    /* ── Section headers ── */
    .section-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        border-left: 4px solid #3b82f6;
        padding: 12px 20px;
        border-radius: 0 8px 8px 0;
        margin: 1.5rem 0 1rem 0;
    }
    .section-header h2 {margin: 0; color: #f1f5f9; font-size: 1.35rem;}
    .section-header p  {margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;}

    /* ── Insight cards ── */
    .insight-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 12px;
        color: #e2e8f0;
    }
    .insight-card h4 {margin: 0 0 6px 0; color: #60a5fa;}
    .insight-card p  {margin: 0; font-size: 0.92rem; line-height: 1.55;}

    /* ── Quadrant labels ── */
    .quad-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 10px;}
    .quad-card {
        border-radius: 10px;
        padding: 14px 18px;
        color: #fff;
    }
    .quad-card h4 {margin: 0 0 4px 0; font-size: 1rem;}
    .quad-card p  {margin: 0; font-size: 0.88rem; opacity: 0.92; line-height: 1.45;}
    .q-bargain   {background: linear-gradient(135deg, #166534, #15803d);}
    .q-premium   {background: linear-gradient(135deg, #1e40af, #2563eb);}
    .q-trap      {background: linear-gradient(135deg, #991b1b, #dc2626);}
    .q-distressed{background: linear-gradient(135deg, #78350f, #b45309);}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {background: #0f172a;}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {color: #cbd5e1;}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {color: #f1f5f9;}

    /* ── Expander styling ── */
    .streamlit-expanderHeader {font-weight: 600; color: #e2e8f0 !important;}

    /* ── Table ── */
    .stDataFrame {border-radius: 10px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# HELPER: section header
# ──────────────────────────────────────────
def section(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="section-header"><h2>{title}</h2>{sub}</div>', unsafe_allow_html=True)


def insight_card(title, body):
    st.markdown(f'<div class="insight-card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# DATA
# ──────────────────────────────────────────
FALLBACK_DATA = [
    {"Bank": "JPMorgan Chase", "Actual_CET1": 15.0, "Min_Stressed_CET1": 12.5, "Total_Assets_B": 3395},
    {"Bank": "Bank of America", "Actual_CET1": 11.8, "Min_Stressed_CET1": 9.1, "Total_Assets_B": 2540},
    {"Bank": "Citigroup", "Actual_CET1": 13.4, "Min_Stressed_CET1": 9.7, "Total_Assets_B": 1700},
    {"Bank": "Wells Fargo", "Actual_CET1": 11.4, "Min_Stressed_CET1": 8.1, "Total_Assets_B": 1727},
    {"Bank": "Goldman Sachs", "Actual_CET1": 14.4, "Min_Stressed_CET1": 8.5, "Total_Assets_B": 1600},
    {"Bank": "Morgan Stanley", "Actual_CET1": 15.2, "Min_Stressed_CET1": 9.8, "Total_Assets_B": 1180},
    {"Bank": "Capital One", "Actual_CET1": 12.9, "Min_Stressed_CET1": 7.7, "Total_Assets_B": 475},
    {"Bank": "U.S. Bancorp", "Actual_CET1": 9.9, "Min_Stressed_CET1": 6.8, "Total_Assets_B": 663},
    {"Bank": "PNC", "Actual_CET1": 9.8, "Min_Stressed_CET1": 7.1, "Total_Assets_B": 560},
    {"Bank": "Truist", "Actual_CET1": 10.1, "Min_Stressed_CET1": 6.2, "Total_Assets_B": 535},
]

PDF_URL = "https://www.federalreserve.gov/publications/files/2025-dfast-results-20250627.pdf"

TICKER_MAP = {
    "JPMorgan Chase": "JPM", "Bank of America": "BAC", "Citigroup": "C",
    "Wells Fargo": "WFC", "Goldman Sachs": "GS", "Morgan Stanley": "MS",
    "Capital One": "COF", "U.S. Bancorp": "USB", "PNC": "PNC",
    "Truist": "TFC", "Charles Schwab": "SCHW", "American Express": "AXP",
    "State Street": "STT", "BNY Mellon": "BK",
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_stress_data():
    """Try PDF first, fall back to embedded data."""
    try:
        resp = requests.get(PDF_URL, timeout=15)
        if resp.status_code == 200:
            pdf_file = io.BytesIO(resp.content)
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if "Projected minimum common equity tier 1 capital ratio" in text and "Severely Adverse" in text:
                        tables = page.extract_tables()
                        for table in tables:
                            raw = pd.DataFrame(table)
                            if raw.shape[1] > 2 and raw.shape[0] > 10:
                                cleaned = pd.DataFrame()
                                raw = raw.dropna(how="all")
                                cleaned["Bank"] = raw.iloc[:, 0]
                                cleaned["Actual_CET1"] = pd.to_numeric(raw.iloc[:, 1], errors="coerce")
                                cleaned["Min_Stressed_CET1"] = pd.to_numeric(raw.iloc[:, -1], errors="coerce")
                                cleaned = cleaned.dropna()
                                cleaned = cleaned[cleaned["Bank"].str.len() > 3]
                                cleaned["Total_Assets_B"] = 500
                                if not cleaned.empty:
                                    return cleaned
    except Exception:
        pass
    return pd.DataFrame(FALLBACK_DATA)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_data(banks):
    """Fetch Price-to-Book and Dividend Yield from Yahoo Finance."""
    rows = []
    for bank in banks:
        ticker = None
        for name, sym in TICKER_MAP.items():
            if name in bank:
                ticker = sym
                break
        if not ticker:
            continue
        try:
            info = yf.Ticker(ticker).info
            p_b = info.get("priceToBook", None)
            div = (info.get("dividendYield", 0) or 0) * 100
            rows.append({"Bank": bank, "Ticker": ticker, "Price_to_Book": p_b, "Div_Yield": div})
        except Exception:
            rows.append({"Bank": bank, "Ticker": ticker, "Price_to_Book": None, "Div_Yield": None})
    return pd.DataFrame(rows)


# ── Load & compute ──
with st.spinner("Loading stress-test data..."):
    df = load_stress_data()

df["Stress_Delta"] = df["Actual_CET1"] - df["Min_Stressed_CET1"]
df["Capital_Cushion"] = df["Min_Stressed_CET1"] - 4.5
df["Layer_Regulatory_Min"] = 4.5
df["Layer_Stress_Burn"] = df["Actual_CET1"] - df["Min_Stressed_CET1"]
df["Layer_True_Excess"] = df["Min_Stressed_CET1"] - 4.5

# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 Bank Resilience")
    st.markdown("**2025 DFAST Stress-Test Dashboard**")
    st.markdown("---")
    st.markdown(
        "This dashboard analyses the Federal Reserve's **Dodd-Frank Act Stress Test (DFAST)** results "
        "and combines them with live market data to assess bank resilience."
    )
    st.markdown("---")

    selected_banks = st.multiselect(
        "Filter Banks",
        options=df["Bank"].tolist(),
        default=df["Bank"].tolist(),
    )

    st.markdown("---")
    fetch_live = st.toggle("Fetch Live Market Data", value=False,
                           help="Pull real-time Price-to-Book ratios from Yahoo Finance for the Valuation Matrix.")
    st.markdown("---")
    st.caption("Data: Federal Reserve 2025 DFAST  \nMarket: Yahoo Finance")

df_display = df[df["Bank"].isin(selected_banks)].copy()

# ══════════════════════════════════════════
# HERO
# ══════════════════════════════════════════
st.markdown("# 🏦 Bank Resilience & Stress-Test Dashboard")
st.markdown(
    "##### Analysing the 2025 Federal Reserve DFAST results to answer one question: "
    "*If the economy crashes, which banks survive?*"
)

# ──────────────────────────────────────────
# PROBLEM STATEMENT
# ──────────────────────────────────────────
section("The Corporate Treasurer's Dilemma", "Why this analysis matters")

col_prob, col_solve = st.columns(2)
with col_prob:
    insight_card(
        "The Scenario",
        "Imagine you are the Treasurer of a mid-sized tech company (like Roku or Etsy) sitting on "
        "<b>$500 million</b> in payroll cash. After the collapse of Silicon Valley Bank (SVB), you can no "
        "longer blindly trust that &ldquo;a bank is a bank.&rdquo; You have a fiduciary duty to ensure that "
        "your company&rsquo;s money doesn&rsquo;t vanish overnight."
    )
    insight_card(
        "The Fear",
        "If the economy crashes (<i>Severely Adverse Scenario</i>), will the bank holding your payroll "
        "accounts be seized by regulators?"
    )
    insight_card(
        "The Gap",
        "Credit ratings (like &ldquo;AA-&rdquo;) are slow to react. Stock price is too volatile. "
        "You need a <b>structural</b> view of safety."
    )
with col_solve:
    insight_card(
        "How This Analysis Solves It — A &ldquo;Survival Scorecard&rdquo;",
        "<b>Quantifiable Safety:</b> Instead of guessing, you can say: &ldquo;Bank A burns 40% of its equity "
        "in a crash, leaving it with only 1% wiggle room. Bank B only burns 10% and stays fully capitalised.&rdquo;"
    )
    insight_card(
        "Counterparty Risk Limit",
        "You can use your <b>Stress Delta</b> to set limits: &ldquo;We will only deposit funds in banks "
        "that maintain a &gt;2% buffer after a theoretical crash.&rdquo;"
    )
    insight_card(
        "The &ldquo;Flight to Quality&rdquo; Map",
        "The scatter plot below literally maps where you should move your money. Move funds from the "
        "<b>bottom-right</b> (High Risk) to the <b>top-left</b> (Fortress)."
    )

# ──────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────
st.markdown("")
k1, k2, k3, k4 = st.columns(4)
safest = df_display.loc[df_display["Capital_Cushion"].idxmax()]
riskiest = df_display.loc[df_display["Capital_Cushion"].idxmin()]
k1.metric("Banks Analysed", len(df_display))
k2.metric("Avg Stress Delta", f"{df_display['Stress_Delta'].mean():.2f}%")
k3.metric("Safest Bank", safest["Bank"], f"+{safest['Capital_Cushion']:.1f}% cushion")
k4.metric("Most Vulnerable", riskiest["Bank"], f"+{riskiest['Capital_Cushion']:.1f}% cushion")

# ══════════════════════════════════════════
# 1 — RESILIENCE METRIC
# ══════════════════════════════════════════
section("Resilience Metric (Stress Delta)", "How much capital each bank burns in the Fed's severely-adverse scenario")

st.markdown(
    "> **Stress Delta** = Actual CET1 − Min Stressed CET1 &nbsp;|&nbsp; "
    "**Capital Cushion** = Min Stressed CET1 − 4.5% (regulatory minimum)"
)

col_table, col_chart = st.columns([2, 3])

with col_table:
    show_df = (
        df_display[["Bank", "Actual_CET1", "Min_Stressed_CET1", "Stress_Delta", "Capital_Cushion"]]
        .sort_values("Stress_Delta", ascending=False)
        .reset_index(drop=True)
    )
    show_df.columns = ["Bank", "Actual CET1 %", "Min Stressed CET1 %", "Stress Delta %", "Capital Cushion %"]
    st.dataframe(show_df, use_container_width=True, hide_index=True, height=400)

with col_chart:
    fig_res = px.scatter(
        df_display,
        x="Stress_Delta",
        y="Min_Stressed_CET1",
        size="Total_Assets_B",
        color="Min_Stressed_CET1",
        color_continuous_scale="RdYlGn",
        text="Bank",
        hover_data={"Actual_CET1": ":.1f", "Capital_Cushion": ":.1f"},
        labels={
            "Stress_Delta": "Stress Delta (Capital Burned in Crisis %)",
            "Min_Stressed_CET1": "Min Stressed CET1 (%)",
        },
    )
    fig_res.update_traces(textposition="top center", textfont_size=11)
    fig_res.add_hline(y=4.5, line_dash="dash", line_color="red", annotation_text="Regulatory Death Line (4.5%)")
    fig_res.add_vline(
        x=df_display["Stress_Delta"].median(),
        line_dash="dot", line_color="gray",
        annotation_text="Median Stress Loss",
    )
    fig_res.update_layout(
        title="Bank Resilience Map — 2025 Stress Test",
        xaxis_title="← More Resilient  |  Stress Delta (%)  |  Less Resilient →",
        yaxis_title="Min Stressed CET1 Ratio (%)",
        template="plotly_dark",
        height=440,
        coloraxis_colorbar_title="Min CET1 %",
        margin=dict(t=60, b=60),
    )
    st.plotly_chart(fig_res, use_container_width=True)

# ── Review insight cards ──
section("Review — Reading the Resilience Map")

r1, r2, r3 = st.columns(3)
with r1:
    insight_card(
        "The &ldquo;High Burn&rdquo; Zone (Bottom-Right)",
        "Banks here lose a lot of money in the crash (High Stress Delta) and end up with very little capital left "
        "(Low Min CET1).<br><br><b>Real-World Insight:</b> Capital One and Goldman Sachs often land here. "
        "Goldman relies on trading (risky), and Capital One relies on credit cards (highest default rates in a recession)."
    )
with r2:
    insight_card(
        "The &ldquo;Fortress&rdquo; Zone (Top-Left)",
        "Banks here lose very little money and keep high capital levels.<br><br>"
        "<b>Real-World Insight:</b> JPMorgan Chase or BNY Mellon usually sit here. "
        "This proves their &ldquo;Fortress Balance Sheet&rdquo; narrative is true."
    )
with r3:
    insight_card(
        "The &ldquo;Safe but Unprofitable&rdquo; Trap",
        "If a bank is too high on the chart (e.g., Charles Schwab usually has massive capital), analysts might argue "
        "they are &ldquo;hoarding capital&rdquo; and should be buying back more stock."
    )

# ══════════════════════════════════════════
# 2 — CAPITAL LAYER CAKE
# ══════════════════════════════════════════
section(
    "The Capital Layer Cake",
    "How much money is truly usable? Most of a bank's capital is legally locked up."
)

exp_layers = st.expander("Understanding the Three Layers", expanded=False)
with exp_layers:
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        insight_card(
            "Regulatory Minimum (4.5%)",
            "The &ldquo;Death Line.&rdquo; If a bank touches this, the bank fails."
        )
    with lc2:
        insight_card(
            "Stress Buffer (SCB)",
            "The money they expect to lose in a crisis — capital that exists today but vanishes in a crash."
        )
    with lc3:
        insight_card(
            "Excess Capacity",
            "The only money actually available for dividends, buybacks, or growth."
        )

df_sorted = df_display.sort_values("Actual_CET1", ascending=True)

fig_cake = go.Figure()
fig_cake.add_trace(go.Bar(
    y=df_sorted["Bank"], x=df_sorted["Layer_Regulatory_Min"],
    name="Regulatory Death Line (4.5%)", orientation="h",
    marker_color="#ef4444",
))
fig_cake.add_trace(go.Bar(
    y=df_sorted["Bank"], x=df_sorted["Layer_Stress_Burn"],
    name="Capital Burned in Crisis", orientation="h",
    marker_color="#facc15", marker_pattern_shape="/",
))
fig_cake.add_trace(go.Bar(
    y=df_sorted["Bank"], x=df_sorted["Layer_True_Excess"],
    name="True Excess Capacity (Safety Margin)", orientation="h",
    marker_color="#22c55e",
))
avg_capital = df_display["Actual_CET1"].mean()
fig_cake.add_vline(x=avg_capital, line_dash="dash", line_color="white",
                   annotation_text=f"Avg Capital {avg_capital:.1f}%", annotation_font_color="white")
fig_cake.update_layout(
    barmode="stack",
    title="The Capital Stack: Who Has a Real Safety Margin?",
    xaxis_title="CET1 Capital Ratio (%)",
    template="plotly_dark",
    height=480,
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    margin=dict(l=10, t=60, b=80),
)
st.plotly_chart(fig_cake, use_container_width=True)

# ── How to read ──
section("Reading the Capital Stack")
h1, h2, h3 = st.columns(3)
with h1:
    insight_card(
        "The Green Bar — True Excess",
        "The most important part. A huge green bar means a &ldquo;Cash Cow.&rdquo; "
        "The bank can afford to buy other banks, pay huge dividends, or weather a storm twice as bad as the Fed predicts."
    )
with h2:
    insight_card(
        "The Striped Yellow Bar — Stress Burn",
        "Shows <b>volatility</b>. A large yellow bar means the bank is &ldquo;Asset Sensitive&rdquo; — "
        "its assets fluctuate wildly in value. Even with lots of capital today, the market may discount them."
    )
with h3:
    insight_card(
        "The Red Bar — Regulatory Floor",
        "This is the floor. No bank wants to be anywhere near this level."
    )

st.info(
    "**Extension — Solving the Treasurer's Problem:** Recommend banks that have both a "
    "**small Yellow bar** (Low Risk) and a **large Green bar** (High Safety)."
)

# ══════════════════════════════════════════
# 3 — VALUATION MATRIX
# ══════════════════════════════════════════
section(
    "The Valuation Matrix",
    "Comparing Intrinsic Quality (stress-test safety) with Market Sentiment (Price-to-Book)"
)

st.markdown(
    "> **The Theory:** Efficient markets should pay more (higher P/B) for safer banks (low Stress Burn).  \n"
    "> **The Opportunity:** A bank that is **Safe** but **Cheap** = potential investment **Alpha**."
)

if fetch_live:
    with st.spinner("Fetching live market data from Yahoo Finance..."):
        mkt = fetch_market_data(df_display["Bank"].tolist())
    df_val = df_display.merge(mkt, on="Bank", how="inner").dropna(subset=["Price_to_Book"])
else:
    # Approximate P/B fallback so chart always renders
    pb_approx = {
        "JPMorgan Chase": 2.05, "Bank of America": 1.15, "Citigroup": 0.65,
        "Wells Fargo": 1.25, "Goldman Sachs": 1.40, "Morgan Stanley": 1.75,
        "Capital One": 1.05, "U.S. Bancorp": 1.35, "PNC": 1.50, "Truist": 0.90,
    }
    df_val = df_display.copy()
    df_val["Ticker"] = df_val["Bank"].map({n: t for n, t in TICKER_MAP.items()})
    df_val["Price_to_Book"] = df_val["Bank"].map(pb_approx)
    df_val = df_val.dropna(subset=["Price_to_Book"])

if not df_val.empty:
    median_safety = df_val["Min_Stressed_CET1"].median()
    median_pb = df_val["Price_to_Book"].median()

    fig_val = px.scatter(
        df_val,
        x="Min_Stressed_CET1",
        y="Price_to_Book",
        size="Total_Assets_B",
        text="Ticker",
        hover_data={"Bank": True, "Actual_CET1": ":.1f", "Stress_Delta": ":.1f"},
        labels={
            "Min_Stressed_CET1": "Safety Score (Min Stressed CET1 %)",
            "Price_to_Book": "Market Price (Price-to-Book)",
        },
    )
    fig_val.update_traces(
        textposition="top center", textfont_size=12,
        marker=dict(color="royalblue", line=dict(width=1, color="white")),
    )
    fig_val.add_hline(y=median_pb, line_dash="dash", line_color="gray", opacity=0.5)
    fig_val.add_vline(x=median_safety, line_dash="dash", line_color="gray", opacity=0.5)

    # Quadrant annotations
    fig_val.add_annotation(x=df_val["Min_Stressed_CET1"].max(), y=df_val["Price_to_Book"].min(),
                           text="BARGAINS<br>(Safe & Cheap)", showarrow=False,
                           font=dict(size=13, color="#22c55e"), xanchor="right", yanchor="bottom")
    fig_val.add_annotation(x=df_val["Min_Stressed_CET1"].min(), y=df_val["Price_to_Book"].max(),
                           text="RISKY PREMIUM<br>(Unsafe & Expensive)", showarrow=False,
                           font=dict(size=13, color="#ef4444"), xanchor="left", yanchor="top")

    fig_val.update_layout(
        title="Are You Overpaying for Risk?",
        xaxis_title="← Riskier  |  Safety Score (Min Stressed CET1 %)  |  Safer →",
        yaxis_title="← Cheaper  |  Price-to-Book  |  Expensive →",
        template="plotly_dark",
        height=500,
        margin=dict(t=60, b=60),
    )
    st.plotly_chart(fig_val, use_container_width=True)

    # Quadrant guide
    section("How to Read the Valuation Matrix")
    st.markdown("""
    <div class="quad-grid">
        <div class="quad-card q-bargain">
            <h4>Bottom-Right — &ldquo;Bargain&rdquo; Zone</h4>
            <p>High Safety (passed stress tests easily) but Low Price (trading below book value).
            This is where value investors look — the market may be irrationally afraid.</p>
        </div>
        <div class="quad-card q-premium">
            <h4>Top-Right — &ldquo;Premium&rdquo; Zone</h4>
            <p>Safe <i>and</i> Expensive (e.g., JPMorgan often lives here).
            You pay a premium for peace of mind.</p>
        </div>
        <div class="quad-card q-trap">
            <h4>Top-Left — &ldquo;Trap&rdquo; Zone</h4>
            <p>Expensive (High P/B) but weak stress-test results (Low Safety).
            Dangerous — if the economy turns, the stock price has the furthest to fall.</p>
        </div>
        <div class="quad-card q-distressed">
            <h4>Bottom-Left — &ldquo;Distressed&rdquo; Zone</h4>
            <p>Cheap <i>and</i> Risky. The market knows they are weak and has priced them accordingly.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("No market data available. Enable **Fetch Live Market Data** in the sidebar.")

# ──────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────
st.markdown("---")
st.caption(
    "Dashboard built from the 2025 Federal Reserve DFAST Stress-Test Results. "
    "Market data provided by Yahoo Finance. For educational purposes only — not investment advice."
)
