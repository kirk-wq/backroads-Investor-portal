import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & COLORS ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Backroads Reclamation | Institutional Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; border-right: 1px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.6rem !important; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
if "password_correct" not in st.session_state:
    st.sidebar.title("🔐 Access Required")
    pw = st.sidebar.text_input("Enter Access Code", type="password")
    if pw == st.secrets["password"]:
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. RESET LOGIC ---
def reset_all_years():
    for i in range(1, 4):
        for key in ["v", "y", "p", "m", "t", "c"]:
            st.session_state[f"{key}{i}"] = 0
    st.rerun()

if st.sidebar.button("🔄 Reset All Years to Base Case"):
    reset_all_years()

# --- 4. YEAR-SPECIFIC SCENARIO LEVERS ---
st.sidebar.title("🧭 Scenario Stress Tests")
st.sidebar.info("Adjust variables for each specific year to test debt coverage and recovery.")

# Sidebar Tabs for Year-Specific Control
tabs = st.sidebar.tabs(["Year 1", "Year 2", "Year 3"])
year_params = []

for i, tab in enumerate(tabs):
    y_idx = i + 1
    with tab:
        v = st.slider(f"HEQ Volume (Homes)", -50, 50, 0, key=f"v{y_idx}") / 100
        y = st.slider(f"Recovery Yield", -25, 25, 0, key=y_idx) / 100
        p = st.slider(f"Lumber Price Market", -50, 50, 0, key=f"p{y_idx}") / 100
        m = st.slider(f"Premium Mix Shift", -20, 20, 0, key=f"m{y_idx}") / 100
        t = st.slider(f"Tipping Fee Adj", -50, 50, 0, key=f"t{y_idx}") / 100
        c = st.slider(f"Cost Sensitivity", -20, 50, 0, key=f"c{y_idx}") / 100
        year_params.append({"v": v, "y": y, "p": p, "m": m, "t": t, "c": c})

st.sidebar.divider()
view_mode = st.sidebar.radio("Dashboard View:", ["Revenue & Growth", "Debt & Cash Flow"])

# --- 5. CALIBRATED ENGINE ---
years, base_homes, base_recovery = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [0.5, 0.6, 0.65]
base_rev_targets = [4753166, 12469066, 17820600]
base_costs = [775128, 1642413, 3015339] 
era_grants = [0, 610000, 575000]

results = []
for i in range(3):
    p = year_params[i]
    h = base_homes[i] * (1 + p["v"])
    r = base_recovery[i] * (1 + p["y"])
    total_bf = h * 6615 * r
    
    # Pricing & Mix
    p_mix = [0.30, 0.35, 0.40][i] * (1 + p["m"])
    i_mix = [0.20, 0.17, 0.15][i] * (1 - p["m"])
    b_mix = 1 - p_mix - i_mix
    prices = [[3.5, 2.5, 1.5], [3.68, 2.63, 1.58], [3.86, 2.76, 1.66]][i]
    
    lum_rev = (total_bf * p_mix * prices[0] * (1+p["p"])) + (total_bf * b_mix * prices[1] * (1+p["p"])) + (total_bf * i_mix * prices[2] * (1+p["p"]))
    tip_rev = (h * 1200 * (1 + p["t"]))
    other_rev = tip_rev + (h * 600)
    
    tot_rev = lum_rev + other_rev
    costs = base_costs[i] * (1 + p["v"]) * (1 + p["c"])
    margin = tot_rev - costs
    
    results.append({
        "Year": years[i], "HEQ": h, "Tipping": tip_rev, "Lumber": lum_rev,
        "Total Revenue": tot_rev, "Margin": margin, "ERA": era_grants[i],
        "Cash": margin + era_grants[i], "Costs": costs
    })

df = pd.DataFrame(results)
y3 = df.iloc[2]

# --- 6. INVESTOR PORTAL ---
st.title(f"🌲 {view_mode} | Institutional Scenario Portal")

# THE HERO METRICS (Unit Economics Focus)
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Y3 Revenue Per Home", f"${y3['Total Revenue']/y3['HEQ']:,.0f}")
with m2: st.metric("Y3 Cost Per Home", f"${y3['Costs']/y3['HEQ']:,.0f}")
with m3: st.metric("Y3 Operational Margin", f"${y3['Margin']/1e6:.2f}M")
with m4: st.metric("Operating Efficiency", f"{(y3['Margin']/y3['Total Revenue']*100):.1f}%")

st.divider()

col1, col2 = st.columns([2, 1])

if view_mode == "Revenue & Growth":
    with col1:
        # HEQ vs Tipping Revenue per Home Stability
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Year'], y=df['HEQ'], name='HEQ (Homes Processed)', marker_color=BR_GRAY, yaxis='y2'))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Tipping'], name='Tipping Revenue Floor', line=dict(color=BR_GOLD, width=4)))
        fig.update_layout(
            title="Operational Floor: HEQ Volume vs. Tipping Revenue",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(title="Tipping Revenue ($)", side="left"),
            yaxis2=dict(title="HEQ Volume (Homes)", side="right", overlaying='y', showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Lumber Quality & Sales")
        st.write(f"**Y3 Sales / Home:** ${y3['Lumber']/y3['HEQ']:,.0f}")
        st.write(f"**Y3 Feedstock / Home:** ${y3['Tipping']/y3['HEQ']:,.0f}")
        st.info("The high correlation between HEQ and Tipping Revenue provides a structural hedge against lumber price compression.")

else: # Debt & Cash Flow
    with col1:
        # 3-Year Repayment Ladder
        fig_cash = go.Figure()
        fig_cash.add_trace(go.Bar(x=df['Year'], y=df['Cash'], name='Net Cash Inflow', marker_color=BR_GOLD))
        fig_cash.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Cash Position', line=dict(color=BR_WHITE, dash='dot')))
        fig_cash.update_layout(
            title="Debt Coverage: 3-Year Repayment Ladder",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title="Available Cash Flow ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_cash, use_container_width=True)
    with col2:
        # Year selection for Waterfall
        y_sel = st.selectbox("Detailed Walk for Year:", ["Year 1", "Year 2", "Year 3"], index=2)
        yd = df[df['Year'] == y_sel].iloc[0]
        fig_w = go.Figure(go.Waterfall(
            orientation="v", x=["Lumber", "Tipping", "Op Costs", "ERA Grant", "CASH"],
            y=[yd['Lumber'], yd['Tipping'], -yd['Costs'], yd['ERA'], yd['Cash']],
            measure=["relative", "relative", "relative", "relative", "total"],
            totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
        ))
        fig_w.update_layout(title=f"{y_sel} Liquidity Detail", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 View Audit-Ready Unit Economics Table"):
    tdf = df.copy()
    tdf["Rev/Home"] = tdf["Total Revenue"] / tdf["HEQ"]
    tdf["Cost/Home"] = tdf["Costs"] / tdf["HEQ"]
    for col in ["Lumber", "Tipping", "Total Revenue", "Margin", "Cash", "Costs", "Rev/Home", "Cost/Home"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
