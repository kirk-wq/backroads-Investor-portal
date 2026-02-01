import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & THEME ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Northmark Materials | Institutional Portal", layout="wide")

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
tabs = st.sidebar.tabs(["Year 1", "Year 2", "Year 3"])
year_params = []

for i, tab in enumerate(tabs):
    y_idx = i + 1
    with tab:
        v = st.slider(f"HEQ Volume (Homes)", -50, 50, 0, key=f"v{y_idx}") / 100
        y = st.slider(f"Recovery Yield", -25, 25, 0, key=f"y{y_idx}") / 100
        p = st.slider(f"Lumber Market Price", -50, 50, 0, key=f"p{y_idx}") / 100
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
    
    # Mix & Pricing
    p_mix = [0.30, 0.35, 0.40][i] * (1 + p["m"])
    i_mix = [0.20, 0.17, 0.15][i] * (1 - p["m"])
    b_mix = 1 - p_mix - i_mix
    prices = [[3.5, 2.5, 1.5], [3.68, 2.63, 1.58], [3.86, 2.76, 1.66]][i]
    
    lum_rev = (total_bf * p_mix * prices[0] * (1+p["p"])) + (total_bf * b_mix * prices[1] * (1+p["p"])) + (total_bf * i_mix * prices[2] * (1+p["p"]))
    tip_fee_rev = (h * 1200 * (1 + p["t"]))
    mat_rev = (h * 600)
    
    tot_rev = lum_rev + tip_fee_rev + mat_rev
    costs = base_costs[i] * (1 + p["v"]) * (1 + p["c"])
    margin = tot_rev - costs
    
    results.append({
        "Year": years[i], "HEQ": h, "Lumber": lum_rev, "Tipping": tip_fee_rev, 
        "Materials": mat_rev, "Total Revenue": tot_rev, "Margin": margin, 
        "ERA": era_grants[i], "Cash": margin + era_grants[i], "Costs": costs,
        "Base Case Plan": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 6. INVESTOR PORTAL ---
st.title(f" {view_mode} | Institutional Scenario Portal")

# THE DYNAMIC FOCUS SELECTOR
focus_year = st.selectbox("🎯 Select Focus Year for Unit Economic Metrics:", ["Year 1", "Year 2", "Year 3"], index=2)
f_idx = ["Year 1", "Year 2", "Year 3"].index(focus_year)
fd = df.iloc[f_idx] # Focused Data Row

# HERO METRICS (Updating Based on Selector)
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric(f"{focus_year} Revenue / Home", f"${fd['Total Revenue']/fd['HEQ']:,.0f}")
with m2: st.metric(f"{focus_year} Cost / Home", f"${fd['Costs']/fd['HEQ']:,.0f}")
with m3: st.metric(f"{focus_year} Net Margin", f"${fd['Margin']/1e6:.2f}M")
with m4: st.metric(f"{focus_year} Efficiency", f"{(fd['Margin']/fd['Total Revenue']*100):.1f}%")

st.divider()

col1, col2 = st.columns([2, 1])

if view_mode == "Revenue & Growth":
    with col1:
        # Chart with Interactivity Note
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Year'], y=df['HEQ'], name='HEQ Volume', marker_color=BR_GRAY, yaxis='y2'))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Tipping'], name='Tipping Revenue Floor', line=dict(color=BR_GOLD, width=4)))
        fig.update_layout(
            title="Operational Floor: Volume vs. Contracted Fees",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(title="Tipping Revenue ($)", side="left"),
            yaxis2=dict(title="HEQ (Homes)", side="right", overlaying='y', showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 Note: Hover over bars/lines for data. Click legend items to toggle visibility.")

    with col2:
        st.subheader(f"Unit Composition ({focus_year})")
        st.write(f"**Lumber Recovered / Home:** ${fd['Lumber']/fd['HEQ']:,.0f}")
        st.write(f"**Feedstock Tipping / Home:** ${fd['Tipping']/fd['HEQ']:,.0f}")
        st.write(f"**Materials Salvage / Home:** ${fd['Materials']/fd['HEQ']:,.0f}")
        st.markdown(f"---")
        st.write(f"**Total Revenue / Home:** ${fd['Total Revenue']/fd['HEQ']:,.0f}")
        st.info("The feedstock tipping fee provides a structural hedge, ensuring positive unit economics regardless of lumber pricing.")

else: # Debt & Cash Flow
    with col1:
        fig_cash = go.Figure()
        fig_cash.add_trace(go.Bar(x=df['Year'], y=df['Cash'], name='Annual Net Cash Inflow', marker_color=BR_GOLD))
        fig_cash.add_trace(go.Scatter(x=df['Year'], y=df['Cash'].cumsum(), name='Cumulative Surplus', line=dict(color=BR_WHITE, dash='dot')))
        fig_cash.update_layout(
            title="Debt Coverage: Cash Surplus Ladder",
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_cash, use_container_width=True)
        st.caption("💡 Note: Cumulative surplus indicates total debt repayment capacity over the project term.")

    with col2:
        # Waterfall always shows focus year
        fig_w = go.Figure(go.Waterfall(
            orientation="v", x=["Lumber", "Tipping", "Costs", "ERA Grant", "CASH FLOW"],
            y=[fd['Lumber'], fd['Tipping'], -fd['Costs'], fd['ERA'], fd['Cash']],
            measure=["relative", "relative", "relative", "relative", "total"],
            totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
        ))
        fig_w.update_layout(title=f"{focus_year} Cash Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 View Audit-Ready Financial Data Table"):
    tdf = df.copy()
    tdf["Rev/Home"] = tdf["Total Revenue"] / tdf["HEQ"]
    tdf["Cost/Home"] = tdf["Costs"] / tdf["HEQ"]
    # Re-order columns for clarity
    tdf = tdf[["Year", "HEQ", "Lumber", "Tipping", "Materials", "Total Revenue", "Costs", "Margin", "ERA", "Cash", "Rev/Home", "Cost/Home"]]
    for col in tdf.columns[2:]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
